#!/usr/bin/env python3
"""Install DevCovenant in a target repository."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

from devcovenant.core import cli_options
from devcovenant.core import manifest as manifest_module
from devcovenant.core import profiles, uninstall
from devcovenant.core.refresh_policies import refresh_policies

DEV_COVENANT_DIR = "devcovenant"
CORE_PATHS = [
    DEV_COVENANT_DIR,
]

CONFIG_PATHS = [
    ".github/workflows/ci.yml",
    ".gitignore",
]

DOC_PATHS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
]

METADATA_PATHS = [
    "devcovenant/VERSION",
    "LICENSE",
    "pyproject.toml",
]

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
LICENSE_TEMPLATE = "LICENSE"
PROFILE_MANIFEST_FALLBACK = "profile.yaml"
PROFILE_ROOT_NAME = "profiles"
POLICY_ROOT_NAME = "policies"
PROFILE_ASSETS_DIR = "assets"
POLICY_ASSETS_DIR = "assets"
GLOBAL_PROFILE_NAME = "global"
GITIGNORE_BASE_TEMPLATE = "gitignore_base.txt"
GITIGNORE_OS_TEMPLATE = "gitignore_os.txt"
DEFAULT_BOOTSTRAP_VERSION = "0.0.1"
DEFAULT_ON_PROFILES = ["docs", "data", "suffixes"]
DEFAULT_PROFILE_SELECTION = [
    "global",
    "devcovuser",
    "python",
    *DEFAULT_ON_PROFILES,
]
GITIGNORE_USER_BEGIN = "# --- User entries (preserved) ---"
GITIGNORE_USER_END = "# --- End user entries ---"
DEFAULT_PRESERVE_PATHS = [
    "custom/policies",
    "custom/profiles",
    "config.yaml",
]

_CORE_CONFIG_INCLUDE_KEY = "devcov_core_include:"
_CORE_CONFIG_PATHS_KEY = "devcov_core_paths:"
_DEFAULT_CORE_PATHS = [
    "devcovenant/core",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/registry",
    "devcovenant/run_pre_commit.py",
    "devcovenant/run_tests.py",
    "devcovenant/update_test_status.py",
    "devcovenant/core/check.py",
]

LEGACY_ROOT_PATHS = [
    "devcov_check.py",
    "devcovenant/core/policy_scripts",
    "devcovenant/custom/policy_scripts",
    "devcovenant/core/fixers",
    "devcovenant/custom/fixers",
    "devcovenant/core/templates",
    "devcovenant/custom/templates",
]

_VERSION_INPUT_PATTERN = re.compile(r"^\d+\.\d+(\.\d+)?$")
_LAST_UPDATED_PATTERN = re.compile(
    r"^\s*(\*\*Last Updated:\*\*|Last Updated:|# Last Updated)",
    re.IGNORECASE,
)
_VERSION_PATTERN = re.compile(r"^\s*\*\*Version:\*\*", re.IGNORECASE)

_DOC_NAME_MAP = {
    "README": "README.md",
    "AGENTS": "AGENTS.md",
    "CONTRIBUTING": "CONTRIBUTING.md",
    "SPEC": "SPEC.md",
    "PLAN": "PLAN.md",
    "CHANGELOG": "CHANGELOG.md",
}

_MANAGED_DOCS = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "README.md",
    "devcovenant/README.md",
)

_BACKUP_ROOT: Path | None = None
_BACKUP_LOG: list[str] = []
_BACKUP_ORIGINALS: set[Path] = set()
_BACKUPS_ENABLED = False


def _set_backups_enabled(enabled: bool) -> None:
    """Enable or disable backup file creation."""
    global _BACKUPS_ENABLED
    _BACKUPS_ENABLED = bool(enabled)


def _reset_backup_state(root: Path) -> None:
    """Reset backup tracking for the install session."""
    global _BACKUP_ROOT, _BACKUP_LOG, _BACKUP_ORIGINALS
    _BACKUP_ROOT = root
    _BACKUP_LOG = []
    _BACKUP_ORIGINALS = set()


def _record_backup(path: Path) -> None:
    """Record a backup path for install logging."""
    if _BACKUP_ROOT is None:
        return
    try:
        label = str(path.relative_to(_BACKUP_ROOT))
    except ValueError:
        label = str(path)
    if label not in _BACKUP_LOG:
        _BACKUP_LOG.append(label)


def _backup_log() -> list[str]:
    """Return the collected backup log entries."""
    return list(_BACKUP_LOG)


def _utc_today() -> str:
    """Return today's UTC date as an ISO string."""
    return datetime.now(timezone.utc).date().isoformat()


def _normalize_version(version_text: str) -> str:
    """Normalize user version input to MAJOR.MINOR.PATCH."""
    text = version_text.strip()
    if not _VERSION_INPUT_PATTERN.match(text):
        raise ValueError(
            "Version must be in MAJOR.MINOR or MAJOR.MINOR.PATCH format."
        )
    if text.count(".") == 1:
        return f"{text}.0"
    return text


def _version_key(raw: str | None) -> tuple[int, int, int]:
    """Return a comparable version tuple."""
    if not raw:
        return (0, 0, 0)
    parts = [part.strip() for part in raw.split(".") if part.strip()]
    numbers: list[int] = []
    for part in parts:
        try:
            numbers.append(int(part))
        except ValueError:
            numbers.append(0)
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers[:3])


def _normalize_doc_name(raw: str) -> str:
    """Normalize a doc selector to its canonical key."""
    text = raw.strip()
    if not text:
        return ""
    upper = text.upper()
    if upper.endswith(".MD"):
        upper = upper.rsplit(".", 1)[0]
    return upper


def _parse_doc_names(raw: str | None) -> set[str] | None:
    """Parse a comma-separated list of doc names."""
    if raw is None:
        return None
    entries = [part.strip() for part in raw.split(",")]
    names: set[str] = set()
    for entry in entries:
        if not entry:
            continue
        normalized = _normalize_doc_name(entry)
        if normalized not in _DOC_NAME_MAP:
            raise ValueError(f"Unknown doc name: {entry}")
        names.add(normalized)
    return names


def _parse_policy_ids(raw: str | None) -> list[str]:
    """Parse a comma-separated list of policy ids."""
    if raw is None:
        return []
    entries = [part.strip() for part in raw.split(",")]
    return [entry for entry in entries if entry]


def _load_yaml(path: Path) -> dict:
    """Load YAML data from path or return an empty dict."""
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _normalize_profile_name(raw: str) -> str:
    """Normalize a profile name for matching."""
    return str(raw or "").strip().lower()


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Return unique values while preserving the original order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in values:
        if entry in seen:
            continue
        seen.add(entry)
        ordered.append(entry)
    return ordered


def _ensure_global_profile(active_profiles: list[str]) -> list[str]:
    """Ensure the global profile is present and first in the list."""
    cleaned = [entry for entry in active_profiles if entry]
    if "global" in cleaned:
        cleaned = [entry for entry in cleaned if entry != "global"]
    return ["global", *cleaned]


def _load_profile_registry(package_root: Path, target_root: Path) -> dict:
    """Load the profile registry by scanning template roots."""
    core_root = package_root / "core" / PROFILE_ROOT_NAME
    custom_root = target_root / DEV_COVENANT_DIR / "custom" / PROFILE_ROOT_NAME
    return profiles.discover_profiles(
        target_root, core_root=core_root, custom_root=custom_root
    )


def _load_active_profiles(target_root: Path) -> list[str]:
    """Load active profiles from the target config when available."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    config_data = _load_yaml(config_path)
    profiles = (
        config_data.get("profiles", {})
        if isinstance(config_data, dict)
        else {}
    )
    active = profiles.get("active", [])
    if isinstance(active, str):
        candidates = [active]
    elif isinstance(active, list):
        candidates = active
    else:
        candidates = [active] if active else []
    normalized = []
    for entry in candidates:
        normalized_value = _normalize_profile_name(entry)
        if normalized_value and normalized_value != "__none__":
            normalized.append(normalized_value)
    return _dedupe_preserve_order(normalized)


def _load_devcov_core_include(target_root: Path) -> bool:
    """Return devcov_core_include from config.yaml when present."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    config_data = _load_yaml(config_path)
    if not isinstance(config_data, dict):
        return False
    return bool(config_data.get("devcov_core_include", False))


def _load_config_version_override(target_root: Path) -> str | None:
    """Return the configured version override from config.yaml when set."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return None
    config_data = _load_yaml(config_path)
    if not isinstance(config_data, dict):
        return None
    version_block = config_data.get("version")
    candidates: list[str | None] = []
    if isinstance(version_block, dict):
        candidates.append(version_block.get("override"))
        candidates.append(version_block.get("value"))
        candidates.append(version_block.get("project"))
    elif isinstance(version_block, str):
        candidates.append(version_block)
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            return _normalize_version(candidate)
        except ValueError:
            continue
    return None


def _normalize_existing_version(raw_value: str | None) -> str | None:
    """Normalize an existing version value, returning None when invalid."""
    if not raw_value:
        return None
    candidate = raw_value.strip()
    if not candidate:
        return None
    try:
        return _normalize_version(candidate)
    except ValueError:
        return None


def _flatten_profile_names(registry: dict) -> list[str]:
    """Return a sorted list of profile names from the registry."""
    return sorted(name for name in registry.keys() if name)


def _parse_profile_selection(raw: str, profiles: list[str]) -> list[str]:
    """Parse a selection string into profile names."""
    tokens = [part.strip() for part in raw.replace(" ", ",").split(",")]
    selected: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token.isdigit():
            index = int(token)
            if 1 <= index <= len(profiles):
                selected.append(profiles[index - 1])
            continue
        normalized = _normalize_profile_name(token)
        if normalized in profiles:
            selected.append(normalized)
    return sorted(set(selected))


def _prompt_profiles(registry: dict) -> list[str]:
    """Prompt for profile selection from the registry."""
    profiles = _flatten_profile_names(registry)
    if not profiles:
        return list(DEFAULT_PROFILE_SELECTION)
    if not sys.stdin.isatty():
        return list(DEFAULT_PROFILE_SELECTION)
    print("Available profiles (select one or more):")
    for idx, name in enumerate(profiles, start=1):
        print(f"{idx}) {name}")
    while True:
        raw = input("Selection: ").strip()
        if not raw:
            return list(DEFAULT_PROFILE_SELECTION)
        selected = _parse_profile_selection(raw, profiles)
        if selected:
            return selected
        print("Please enter one or more profile names or numbers.")


def _resolve_template_path(
    target_root: Path,
    core_root: Path,
    rel_path: str,
    *,
    profile: str | None = None,
    policy_id: str | None = None,
) -> Path:
    """Resolve an asset template path with custom overrides."""
    rel_path = rel_path.lstrip("/")
    custom_root = target_root / DEV_COVENANT_DIR / "custom"
    core_profiles = core_root / PROFILE_ROOT_NAME
    core_policies = core_root / POLICY_ROOT_NAME
    candidates: list[Path] = []
    prefixed = rel_path.startswith(
        f"{PROFILE_ROOT_NAME}/"
    ) or rel_path.startswith(f"{POLICY_ROOT_NAME}/")
    if prefixed:
        custom_candidate = custom_root / rel_path
        core_candidate = core_root / rel_path
        if custom_candidate.exists():
            return custom_candidate
        if core_candidate.exists():
            return core_candidate
        return target_root / rel_path
    if policy_id:
        policy_dir_name = policy_id.replace("-", "_")
        candidates.append(
            custom_root
            / POLICY_ROOT_NAME
            / policy_dir_name
            / POLICY_ASSETS_DIR
            / rel_path
        )
    if profile:
        candidates.append(
            custom_root
            / PROFILE_ROOT_NAME
            / profile
            / PROFILE_ASSETS_DIR
            / rel_path
        )
    candidates.append(
        custom_root
        / PROFILE_ROOT_NAME
        / GLOBAL_PROFILE_NAME
        / PROFILE_ASSETS_DIR
        / rel_path
    )
    if policy_id:
        policy_dir_name = policy_id.replace("-", "_")
        candidates.append(
            core_policies / policy_dir_name / POLICY_ASSETS_DIR / rel_path
        )
    if profile:
        candidates.append(
            core_profiles / profile / PROFILE_ASSETS_DIR / rel_path
        )
    candidates.append(
        core_profiles / GLOBAL_PROFILE_NAME / PROFILE_ASSETS_DIR / rel_path
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return core_root / rel_path


def _load_policy_assets(target_root: Path) -> dict[str, dict[str, object]]:
    """Load fallback assets declared by custom policy descriptors."""
    assets: dict[str, dict[str, object]] = {}
    custom_root = target_root / DEV_COVENANT_DIR / "custom" / POLICY_ROOT_NAME
    if not custom_root.exists():
        return assets
    for policy_dir in sorted(custom_root.iterdir()):
        if not policy_dir.is_dir():
            continue
        policy_name = policy_dir.name
        descriptor_path = policy_dir / f"{policy_name}.yaml"
        if not descriptor_path.exists():
            continue
        descriptor = _load_yaml(descriptor_path) or {}
        if not isinstance(descriptor, dict):
            continue
        entries = descriptor.get("assets") or []
        cleaned = _clean_asset_entries(entries)
        if cleaned:
            policy_id = descriptor.get("id") or policy_name.replace("_", "-")
            metadata = descriptor.get("metadata")
            if isinstance(metadata, dict):
                descriptor_enabled = _coerce_bool(
                    metadata.get("enabled"), default=True
                )
            else:
                descriptor_enabled = True
            assets[policy_id] = {
                "assets": cleaned,
                "enabled": descriptor_enabled,
            }
    return assets


def _allow_custom_policy_asset_fallback(target_root: Path) -> bool:
    """Return whether custom policy asset fallback is enabled."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return True
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return True
    install_cfg = payload.get("install", {})
    if not isinstance(install_cfg, dict):
        return True
    return _coerce_bool(
        install_cfg.get("allow_custom_policy_asset_fallback"),
        default=True,
    )


def _load_policy_state_config(target_root: Path) -> dict[str, bool]:
    """Return normalized policy_state values from config.yaml."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return {}
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return _normalize_policy_state_map(payload.get("policy_state"))


def _load_profile_manifest(
    package_root: Path,
    target_root: Path,
    profile: str,
) -> dict:
    """Load a profile manifest from custom/core profiles."""
    core_root = package_root / "core" / PROFILE_ROOT_NAME
    custom_root = target_root / DEV_COVENANT_DIR / "custom" / PROFILE_ROOT_NAME
    manifest_name = f"{profile}.yaml"
    custom_manifest = custom_root / profile / manifest_name
    core_manifest = core_root / profile / manifest_name
    if custom_manifest.exists():
        return _load_yaml(custom_manifest) or {}
    if core_manifest.exists():
        return _load_yaml(core_manifest) or {}
    return {}


def _load_profile_manifests(
    package_root: Path,
    target_root: Path,
    active_profiles: list[str],
) -> dict[str, dict]:
    """Load profile manifests for active profiles."""
    manifests: dict[str, dict] = {}
    for profile in active_profiles:
        if not profile or profile == "__none__":
            continue
        manifest = _load_profile_manifest(package_root, target_root, profile)
        if manifest:
            manifests[profile] = manifest
    return manifests


def _clean_asset_entries(entries: list[dict] | list[str]) -> list[dict]:
    """Normalize asset entries, skipping placeholders."""
    if not entries:
        return []
    if entries == ["__none__"]:
        return []
    cleaned: list[dict] = []
    for entry in entries:
        if isinstance(entry, str):
            if entry == "__none__":
                continue
            cleaned.append(
                {"path": entry, "template": entry, "mode": "replace"}
            )
            continue
        if isinstance(entry, dict):
            cleaned.append(entry)
    return cleaned


def _merge_text_assets(existing: str, incoming: str) -> str:
    """Merge template lines into an existing text blob."""
    existing_lines = [line.rstrip() for line in existing.splitlines()]
    incoming_lines = [line.rstrip() for line in incoming.splitlines()]
    merged = list(existing_lines)
    for line in incoming_lines:
        if line and line not in merged:
            merged.append(line)
    return "\n".join(merged).rstrip() + "\n"


def _render_template_text(
    template_path: Path, context: dict[str, str] | None
) -> str | None:
    """Return rendered template text when context is provided."""
    if not context:
        return None
    try:
        text = template_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    for key, replacement in context.items():
        placeholder = f"{{{{{key}}}}}"
        text = text.replace(placeholder, replacement)
    return text


def _apply_asset(
    template_path: Path,
    target_path: Path,
    mode: str,
    render_context: dict[str, str] | None = None,
) -> bool:
    """Apply a template asset to the target path."""
    mode_text = (mode or "replace").lower()
    if mode_text == "generate":
        return False
    if not template_path.exists():
        return False
    rendered = _render_template_text(template_path, render_context)
    if target_path.exists():
        if mode_text == "skip":
            return False
        if mode_text == "merge":
            existing = target_path.read_text(encoding="utf-8")
            incoming = (
                rendered
                if rendered is not None
                else template_path.read_text(encoding="utf-8")
            )
            merged = _merge_text_assets(existing, incoming)
            if merged != existing:
                _rename_existing_file(target_path)
                target_path.write_text(merged, encoding="utf-8")
                return True
            return False
        _rename_existing_file(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if rendered is not None:
        target_path.write_text(rendered, encoding="utf-8")
        return True
    shutil.copy2(template_path, target_path)
    return True


def _apply_profile_assets(
    package_root: Path,
    template_root: Path,
    target_root: Path,
    active_profiles: list[str],
    profile_manifests: dict[str, dict],
    disabled_policies: set[str],
    asset_context: dict[str, str] | None = None,
) -> list[str]:
    """Install profile assets and custom-policy fallback assets."""
    installed: list[str] = []
    reserved_targets: set[str] = set()

    for profile, manifest in profile_manifests.items():
        entries = _clean_asset_entries(manifest.get("assets", []))
        for entry in entries:
            rel_path = str(entry.get("path", "")).strip()
            if not rel_path:
                continue
            reserved_targets.add(rel_path)
            template_path = _resolve_template_path(
                target_root,
                template_root,
                entry.get("template", ""),
                profile=profile,
            )
            target_path = target_root / rel_path
            if _apply_asset(
                template_path,
                target_path,
                entry.get("mode", "replace"),
                render_context=asset_context,
            ):
                installed.append(str(target_path.relative_to(target_root)))

    if not _allow_custom_policy_asset_fallback(target_root):
        return installed

    policy_assets = _load_policy_assets(target_root)
    policy_state = _load_policy_state_config(target_root)
    for policy_id, spec in policy_assets.items():
        if policy_id in disabled_policies:
            continue
        descriptor_enabled = bool(spec.get("enabled", True))
        policy_enabled = policy_state.get(policy_id, descriptor_enabled)
        if not policy_enabled:
            continue
        entries = spec.get("assets", [])
        for entry in _clean_asset_entries(entries):
            rel_path = str(entry.get("path", "")).strip()
            if not rel_path or rel_path in reserved_targets:
                continue
            template_path = _resolve_template_path(
                target_root,
                template_root,
                entry.get("template", ""),
                policy_id=policy_id,
            )
            target_path = target_root / rel_path
            if _apply_asset(
                template_path,
                target_path,
                entry.get("mode", "replace"),
                render_context=asset_context,
            ):
                installed.append(str(target_path.relative_to(target_root)))
    return installed


def _prompt_version() -> str | None:
    """Prompt the user for a version override."""
    while True:
        raw = input(
            "Enter version (MAJOR.MINOR[.PATCH]) or blank to skip: "
        ).strip()
        if not raw:
            return None
        try:
            return _normalize_version(raw)
        except ValueError as exc:
            print(str(exc))


def _read_pyproject_version(path: Path) -> str | None:
    """Extract a version from pyproject.toml when present."""
    if not path.exists():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    section = None
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]")
            continue
        if section not in {"project", "tool.poetry"}:
            continue
        if stripped.startswith("version") and "=" in stripped:
            key, _, raw_value = stripped.partition("=")
            if key.strip() != "version":
                continue
            candidate = raw_value.strip().strip('"').strip("'")
            if candidate:
                return candidate
    return None


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for a yes/no answer and return the response."""
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def _resolve_source_path(
    target_root: Path, template_root: Path, rel_path: str
) -> Path:
    """Return the source path for rel_path with template fallback."""
    return _resolve_template_path(target_root, template_root, rel_path)


def _remove_legacy_paths(target_root: Path, paths: list[str]) -> None:
    """Remove legacy paths left behind by older installs."""
    for rel_path in paths:
        target = target_root / rel_path
        if target.is_dir():
            shutil.rmtree(target)
            continue
        if target.exists():
            target.unlink()


def _strip_devcov_block(text: str) -> str:
    """Return text without any DevCovenant managed block."""
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, rest = text.split(BLOCK_BEGIN, 1)
        _block, after = rest.split(BLOCK_END, 1)
        return f"{before}{after}"
    return text


def _has_heading(text: str, heading: str) -> bool:
    """Return True if text includes a markdown heading."""
    pattern = re.compile(
        rf"^#+\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE
    )
    return bool(pattern.search(text))


def _ensure_standard_header(
    text: str, last_updated: str, version: str, title: str | None = None
) -> str:
    """Ensure Last Updated and Version lines appear near the top."""
    lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        if _LAST_UPDATED_PATTERN.match(line):
            continue
        if _VERSION_PATTERN.match(line):
            continue
        cleaned.append(line.rstrip())

    title_line = None
    remaining = cleaned
    if cleaned and cleaned[0].lstrip().startswith("#"):
        title_line = cleaned[0]
        remaining = cleaned[1:]
    elif title:
        title_line = f"# {title}"

    header_lines: list[str] = []
    if title_line is not None:
        header_lines.append(title_line)
    header_lines.append(f"**Last Updated:** {last_updated}")
    header_lines.append(f"**Version:** {version}")

    if remaining and remaining[0].strip() != "":
        header_lines.append("")
    elif not remaining:
        header_lines.append("")

    updated = "\n".join(header_lines + remaining).rstrip() + "\n"
    return updated


def _apply_standard_header(
    path: Path, last_updated: str, version: str, title: str | None = None
) -> bool:
    """Update a file with the standard header."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = _ensure_standard_header(text, last_updated, version, title)
    if updated == text:
        return False
    _rename_existing_file(path)
    path.write_text(updated, encoding="utf-8")
    return True


def _update_devcovenant_version(path: Path, devcov_version: str) -> bool:
    """Update the DevCovenant Version line in a doc if present."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^\s*\*\*DevCovenant Version:\*\*.*$",
        re.IGNORECASE | re.MULTILINE,
    )
    updated = pattern.sub(
        f"**DevCovenant Version:** {devcov_version}", text, count=1
    )
    if updated == text:
        return False
    _rename_existing_file(path)
    path.write_text(updated, encoding="utf-8")
    return True


def _extract_user_gitignore(text: str) -> str:
    """Extract user entries from an existing gitignore."""
    if GITIGNORE_USER_BEGIN in text and GITIGNORE_USER_END in text:
        _, rest = text.split(GITIGNORE_USER_BEGIN, 1)
        user_block, _tail = rest.split(GITIGNORE_USER_END, 1)
        return user_block.strip("\n")
    return text.strip("\n")


def _load_gitignore_fragment(
    target_root: Path,
    template_root: Path,
    rel_path: str,
    *,
    profile: str | None = None,
) -> str:
    """Return a gitignore fragment from profile assets when present."""
    fragment_path = _resolve_template_path(
        target_root,
        template_root,
        rel_path,
        profile=profile,
    )
    if not fragment_path.exists():
        return ""
    return fragment_path.read_text(encoding="utf-8").strip("\n")


def _render_gitignore(
    user_text: str,
    target_root: Path,
    template_root: Path,
    active_profiles: list[str],
) -> str:
    """Render a profile-aware gitignore and append user entries."""
    fragments: list[str] = []
    base_text = _load_gitignore_fragment(
        target_root,
        template_root,
        GITIGNORE_BASE_TEMPLATE,
    )
    if base_text:
        fragments.append(base_text)
    for profile in active_profiles:
        if not profile or profile == "__none__":
            continue
        profile_text = _load_gitignore_fragment(
            target_root,
            template_root,
            ".gitignore",
            profile=profile,
        )
        if profile_text:
            fragments.append(f"# Profile: {profile}\n{profile_text}")
    os_text = _load_gitignore_fragment(
        target_root,
        template_root,
        GITIGNORE_OS_TEMPLATE,
    )
    if os_text:
        fragments.append(os_text)

    base = "\n\n".join(fragments).rstrip() + "\n"
    user_block = _extract_user_gitignore(user_text)
    return (
        f"{base}\n{GITIGNORE_USER_BEGIN}\n{user_block}\n"
        f"{GITIGNORE_USER_END}\n"
    )


def _load_pre_commit_block(config_data: dict | None) -> tuple[bool, dict]:
    """Return (enabled, overrides) for pre-commit config generation."""
    if not isinstance(config_data, dict):
        return True, {}
    block = config_data.get("pre_commit")
    if block is None:
        return True, {}
    if isinstance(block, bool):
        return bool(block), {}
    if not isinstance(block, dict):
        return True, {}
    enabled = block.get("enabled", True)
    overrides = block.get("overrides")
    if isinstance(overrides, dict):
        return bool(enabled), overrides
    filtered = {key: value for key, value in block.items() if key != "enabled"}
    return bool(enabled), filtered


def _collect_pre_commit_fragments(
    manifests: dict[str, dict], active_profiles: list[str]
) -> list[dict]:
    """Collect pre-commit fragments from profile manifests."""
    fragments: list[dict] = []
    for profile in active_profiles:
        manifest = manifests.get(profile)
        if not isinstance(manifest, dict):
            continue
        fragment = manifest.get("pre_commit")
        if isinstance(fragment, dict) and fragment:
            fragments.append(fragment)
    return fragments


def _merge_pre_commit_config(base: dict, fragment: dict) -> dict:
    """Merge a pre-commit fragment into the base config."""
    if not isinstance(fragment, dict):
        return base
    for key, fragment_value in fragment.items():
        if key == "repos" and isinstance(fragment_value, list):
            repos = base.get("repos")
            if not isinstance(repos, list):
                repos = []
            repos.extend(fragment_value)
            base["repos"] = repos
            continue
        if isinstance(fragment_value, dict) and isinstance(
            base.get(key), dict
        ):
            merged = dict(base.get(key) or {})
            _merge_pre_commit_config(merged, fragment_value)
            base[key] = merged
            continue
        base[key] = fragment_value
    return base


def _build_pre_commit_exclude(ignore_dirs: Iterable[str]) -> str | None:
    """Build a pre-commit exclude regex from ignored directory names."""
    cleaned: list[str] = []
    for entry in ignore_dirs:
        normalized_entry = str(entry or "").strip().strip("/")
        if not normalized_entry or normalized_entry == "__none__":
            continue
        if normalized_entry not in cleaned:
            cleaned.append(normalized_entry)
    if not cleaned:
        return None
    escaped = [re.escape(value) for value in cleaned]
    lines = ["(?x)", "(^|/)", "("]
    for index, escaped_entry in enumerate(escaped):
        prefix = "  " if index == 0 else "  | "
        lines.append(f"{prefix}{escaped_entry}")
    lines.append(")")
    lines.append("(/|$)")
    return "\n".join(lines)


def _combine_pre_commit_exclude(
    existing: str | None, extra: str | None
) -> str | None:
    """Combine two pre-commit exclude regex strings."""
    patterns = [pattern for pattern in (existing, extra) if pattern]
    if not patterns:
        return None
    if len(patterns) == 1:
        return patterns[0]
    lines = ["(?x)", "(?:"]
    for index, pattern in enumerate(patterns):
        if index:
            lines.append("  |")
        lines.append("  (?:")
        for line in str(pattern).splitlines():
            lines.append(f"    {line}")
        lines.append("  )")
    lines.append(")")
    return "\n".join(lines)


def _build_pre_commit_config(
    fragments: list[dict],
    overrides: dict,
    ignore_dirs: Iterable[str],
) -> dict:
    """Assemble a pre-commit config from fragments and overrides."""
    config: dict = {}
    for fragment in fragments:
        _merge_pre_commit_config(config, fragment)
    _merge_pre_commit_config(config, overrides)
    exclude = _build_pre_commit_exclude(ignore_dirs)
    if exclude:
        config["exclude"] = _combine_pre_commit_exclude(
            config.get("exclude"), exclude
        )
    return config


def _render_pre_commit_config(config: dict) -> str:
    """Return the YAML text for a pre-commit config."""
    payload = dict(config)
    exclude = payload.pop("exclude", None)
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    if not rendered.endswith("\n"):
        rendered += "\n"
    if exclude:
        block_lines = ["exclude: |-"]
        for line in str(exclude).splitlines():
            block_lines.append(f"  {line}")
        rendered = rendered.rstrip() + "\n" + "\n".join(block_lines) + "\n"
    return rendered


def refresh_pre_commit_config(
    repo_root: Path,
    *,
    package_root: Path | None = None,
    active_profiles: list[str] | None = None,
    profile_registry: dict[str, dict] | None = None,
) -> bool:
    """Regenerate .pre-commit-config.yaml from profiles and config."""
    if package_root is None:
        package_root = Path(__file__).resolve().parents[1]
    if active_profiles is None:
        active_profiles = _ensure_global_profile(
            _dedupe_preserve_order(_load_active_profiles(repo_root))
        )
    if profile_registry is None:
        profile_registry = profiles.load_profile_registry(repo_root)
    config_data = _load_yaml(repo_root / DEV_COVENANT_DIR / "config.yaml")
    enabled, overrides = _load_pre_commit_block(config_data)
    if not enabled:
        return False
    manifests = _load_profile_manifests(
        package_root, repo_root, active_profiles
    )
    fragments = _collect_pre_commit_fragments(manifests, active_profiles)
    ignore_dirs = profiles.resolve_profile_ignore_dirs(
        profile_registry, active_profiles
    )
    assembled = _build_pre_commit_config(fragments, overrides, ignore_dirs)
    if not assembled:
        return False
    rendered = _render_pre_commit_config(assembled)
    pre_commit_path = repo_root / ".pre-commit-config.yaml"
    existing = (
        pre_commit_path.read_text(encoding="utf-8")
        if pre_commit_path.exists()
        else ""
    )
    if existing == rendered:
        return False
    pre_commit_path.write_text(rendered, encoding="utf-8")
    return True


def _build_doc_metadata_lines(doc_id: str, doc_type: str) -> list[str]:
    """Return metadata lines for a managed doc block."""
    return [
        f"**Doc ID:** {doc_id}",
        f"**Doc Type:** {doc_type}",
        "**Managed By:** DevCovenant",
    ]


def _build_doc_block(
    doc_id: str, doc_type: str, extra_lines: list[str] | None = None
) -> str:
    """Return a small managed block for a document."""
    lines = [BLOCK_BEGIN]
    if extra_lines and extra_lines[0].strip().startswith("**Doc ID:**"):
        # Descriptor already supplies the metadata lines.
        lines.extend(extra_lines)
    else:
        lines.extend(_build_doc_metadata_lines(doc_id, doc_type))
        if extra_lines:
            lines.append("")
            lines.extend(extra_lines)
    lines.append(BLOCK_END)
    return "\n".join(lines)


def _doc_asset_path(
    target_root: Path, doc_name: str, template_root: Path | None = None
) -> Path:
    """Return the asset descriptor path for a managed doc."""
    if template_root is None:
        assets_root = (
            target_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "global"
            / "assets"
        )
    else:
        if template_root.name == "core":
            assets_root = template_root / "profiles" / "global" / "assets"
        else:
            assets_root = (
                template_root / "core" / "profiles" / "global" / "assets"
            )
    rel_path = Path(doc_name)
    if rel_path.parent != Path("."):
        return assets_root / rel_path.with_suffix(".yaml")
    doc_id = rel_path.stem
    return assets_root / f"{doc_id}.yaml"


def _load_doc_descriptor(
    target_root: Path,
    doc_name: str,
    template_root: Path | None = None,
) -> dict[str, object] | None:
    """Load the descriptor YAML for a managed document."""
    path = _doc_asset_path(target_root, doc_name, template_root)
    if not path.exists():
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _ensure_header_lines(path: Path, header_lines: list[str]) -> bool:
    """Ensure the document starts with the provided header lines."""
    if not header_lines or not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rest_index = 0
    while rest_index < len(lines):
        if lines[rest_index].strip() == "":
            rest_index += 1
            break
        rest_index += 1
    while rest_index < len(lines) and lines[rest_index].strip() == "":
        rest_index += 1
    rest = lines[rest_index:]
    updated_lines = header_lines + [""] + rest
    updated_text = "\n".join(updated_lines).rstrip() + "\n"
    if updated_text == text:
        return False
    _rename_existing_file(path)
    path.write_text(updated_text, encoding="utf-8")
    return True


def _apply_header_overrides(
    header_lines: list[str],
    *,
    last_updated: str | None = None,
    version: str | None = None,
    title: str | None = None,
) -> list[str]:
    """Return header lines updated with explicit metadata values."""
    updated: list[str] = []
    used_title = False
    used_last_updated = False
    used_version = False
    for line in header_lines:
        if title and line.lstrip().startswith("#") and not used_title:
            updated.append(f"# {title}")
            used_title = True
            continue
        if last_updated and _LAST_UPDATED_PATTERN.match(line):
            updated.append(f"**Last Updated:** {last_updated}")
            used_last_updated = True
            continue
        if version and _VERSION_PATTERN.match(line):
            updated.append(f"**Version:** {version}")
            used_version = True
            continue
        updated.append(line.rstrip())
    if title and not used_title:
        updated.insert(0, f"# {title}")
    insert_index = 1 if updated and updated[0].lstrip().startswith("#") else 0
    if last_updated and not used_last_updated:
        updated.insert(insert_index, f"**Last Updated:** {last_updated}")
        insert_index += 1
    if version and not used_version:
        updated.insert(insert_index, f"**Version:** {version}")
    return updated


def _doc_needs_bootstrap(text: str) -> bool:
    """Return True when a doc is empty or a single-line placeholder."""
    non_empty = [line for line in text.splitlines() if line.strip()]
    return len(non_empty) <= 1


def _normalize_doc_asset_entries(raw_value: object) -> list[str]:
    """Return normalized managed-doc paths from config values."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        candidates = [
            part.strip() for part in raw_value.replace("\n", ",").split(",")
        ]
    elif isinstance(raw_value, list):
        candidates = [str(part).strip() for part in raw_value]
    else:
        candidates = [str(raw_value).strip()]
    normalized: list[str] = []
    for candidate in candidates:
        if not candidate or candidate == "__none__":
            continue
        doc_name = candidate
        upper_name = candidate.upper()
        if upper_name in _DOC_NAME_MAP:
            doc_name = _DOC_NAME_MAP[upper_name]
        elif upper_name.endswith(".MD"):
            doc_id = upper_name[:-3]
            if doc_id in _DOC_NAME_MAP:
                doc_name = _DOC_NAME_MAP[doc_id]
        if doc_name not in _MANAGED_DOCS:
            continue
        if doc_name not in normalized:
            normalized.append(doc_name)
    return normalized


def _configured_managed_docs(
    target_root: Path, *, include_agents: bool = True
) -> tuple[str, ...]:
    """Return managed docs resolved from config doc_assets values."""
    defaults = [
        doc_name
        for doc_name in _MANAGED_DOCS
        if include_agents or doc_name != "AGENTS.md"
    ]
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return tuple(defaults)
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return tuple(defaults)
    if not isinstance(payload, dict):
        return tuple(defaults)
    doc_assets = payload.get("doc_assets")
    if not isinstance(doc_assets, dict):
        return tuple(defaults)
    autogen_docs = _normalize_doc_asset_entries(doc_assets.get("autogen"))
    user_docs = set(_normalize_doc_asset_entries(doc_assets.get("user")))
    if not autogen_docs:
        autogen_docs = list(defaults)
    selected = [
        doc_name
        for doc_name in autogen_docs
        if doc_name not in user_docs
        and (include_agents or doc_name != "AGENTS.md")
    ]
    if include_agents and "AGENTS.md" not in selected:
        selected.insert(0, "AGENTS.md")
    selected = _dedupe_preserve_order(selected)
    if not selected:
        return tuple(defaults)
    return tuple(selected)


def _normalize_body_lines(raw_value: object) -> list[str]:
    """Return body lines from a descriptor field."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [line.rstrip() for line in raw_value.splitlines()]
    if isinstance(raw_value, list):
        return [str(line).rstrip() for line in raw_value]
    return [str(raw_value).rstrip()]


def _render_doc_from_descriptor(
    target_root: Path,
    doc_name: str,
    *,
    last_updated: str | None = None,
    version: str | None = None,
    title: str | None = None,
    template_root: Path | None = None,
) -> tuple[str | None, str, list[str]]:
    """Render a managed doc from its descriptor and return text + block."""
    descriptor = _load_doc_descriptor(target_root, doc_name, template_root)
    if not descriptor:
        return None, "", []
    header_lines = descriptor.get("header_lines") or []
    header_lines = _apply_header_overrides(
        header_lines,
        last_updated=last_updated,
        version=version,
        title=title,
    )
    doc_id = descriptor.get("doc_id")
    doc_type = descriptor.get("doc_type")
    managed_block = descriptor.get("managed_block", "")
    extra_lines = [line.rstrip() for line in managed_block.splitlines()]
    body_lines = _normalize_body_lines(descriptor.get("body_lines"))
    if not body_lines:
        body_lines = _normalize_body_lines(descriptor.get("body"))
    template_block = (
        _build_doc_block(doc_id, doc_type, extra_lines)
        if doc_id and doc_type
        else ""
    )
    lines: list[str] = []
    if header_lines:
        lines.extend(header_lines)
    lines.append("")
    if template_block:
        lines.append(template_block)
    if body_lines:
        lines.append("")
        lines.extend(body_lines)
    text = "\n".join(lines).rstrip() + "\n"
    return text, template_block, header_lines


def _ensure_doc_from_descriptor(
    target_root: Path,
    doc_name: str,
    *,
    last_updated: str | None = None,
    version: str | None = None,
    title: str | None = None,
    force: bool = False,
    template_root: Path | None = None,
) -> tuple[bool, bool]:
    """Ensure a managed doc exists and return (changed, wrote_full)."""
    rendered, template_block, _header_lines = _render_doc_from_descriptor(
        target_root,
        doc_name,
        last_updated=last_updated,
        version=version,
        title=title,
        template_root=template_root,
    )
    if rendered is None:
        return False, False
    doc_path = target_root / doc_name
    if not doc_path.exists():
        doc_path.write_text(rendered, encoding="utf-8")
        return True, True
    existing_text = doc_path.read_text(encoding="utf-8")
    if force or _doc_needs_bootstrap(existing_text):
        _rename_existing_file(doc_path)
        doc_path.write_text(rendered, encoding="utf-8")
        return True, True
    changed = False
    if last_updated and version:
        changed |= _apply_standard_header(
            doc_path, last_updated, version, title=title
        )
    if template_block:
        changed |= _sync_blocks_from_template(doc_path, template_block)
    return changed, False


def _sync_doc_from_descriptor(
    target_root: Path,
    doc_name: str,
    *,
    last_updated: str | None = None,
    version: str | None = None,
    title: str | None = None,
    force: bool = False,
    template_root: Path | None = None,
) -> bool:
    """Sync a managed document from its descriptor asset."""
    changed, _wrote_full = _ensure_doc_from_descriptor(
        target_root,
        doc_name,
        last_updated=last_updated,
        version=version,
        title=title,
        force=force,
        template_root=template_root,
    )
    return changed


def sync_managed_doc_assets(
    target_root: Path,
    doc_names: Iterable[str] | None = None,
    *,
    last_updated: str | None = None,
    version: str | None = None,
    title_overrides: dict[str, str] | None = None,
    template_root: Path | None = None,
) -> list[str]:
    """Ensure the managed docs reflect their descriptor assets."""

    names = tuple(doc_names or _configured_managed_docs(target_root))
    updated: list[str] = []
    title_overrides = title_overrides or {}
    for doc_name in names:
        if _sync_doc_from_descriptor(
            target_root,
            doc_name,
            last_updated=last_updated,
            version=version,
            title=title_overrides.get(doc_name),
            template_root=template_root,
        ):
            updated.append(doc_name)
    return updated


def _render_spec_template(version: str, date_stamp: str) -> str:
    """Return a minimal SPEC.md template."""
    doc_block = _build_doc_block("SPEC", "specification")
    return (
        "# Specification\n"
        f"**Last Updated:** {date_stamp}\n"
        f"**Version:** {version}\n\n"
        f"{doc_block}\n"
        "This specification captures the required behavior for this "
        "repository.\n"
        "It describes what the system must do, the constraints it must "
        "respect,\n"
        "and the workflow expectations that keep policy text and "
        "implementation\n"
        "aligned.\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n"
        "3. [Functional Requirements](#functional-requirements)\n"
        "4. [Non-Functional Requirements](#non-functional-requirements)\n\n"
        "## Overview\n"
        "This document defines the scope, goals, and user-facing outcomes "
        "for\n"
        "the project. Keep it concise but specific, and update it whenever "
        "the\n"
        "behavior, interfaces, or integration points change so contributors "
        "can\n"
        "trust it.\n\n"
        "## Workflow\n"
        "DevCovenant requires the gated workflow for every change. Run the "
        "pre-\n"
        "commit start, tests, and pre-commit end steps in order, then record "
        "the\n"
        "change in `CHANGELOG.md` with the files touched during\n"
        "the update.\n\n"
        "## Functional Requirements\n"
        "- Describe the primary behaviors the system must implement.\n"
        "- List the critical APIs, commands, or automation outcomes that must "
        "exist.\n\n"
        "## Non-Functional Requirements\n"
        "- Document performance, reliability, or security constraints.\n"
        "- Note any compliance or operational requirements for production "
        "use.\n"
    )


def _render_plan_template(version: str, date_stamp: str) -> str:
    """Return a minimal PLAN.md template."""
    doc_block = _build_doc_block("PLAN", "plan")
    return (
        "# Plan\n"
        f"**Last Updated:** {date_stamp}\n"
        f"**Version:** {version}\n\n"
        f"{doc_block}\n"
        "This plan tracks the roadmap for the repository. It should "
        "enumerate\n"
        "upcoming milestones, sequencing decisions, and the work needed to "
        "keep\n"
        "docs, policies, and implementation aligned.\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n"
        "3. [Roadmap](#roadmap)\n"
        "4. [Near-Term Tasks](#near-term-tasks)\n\n"
        "## Overview\n"
        "Use this plan to describe the scope of upcoming releases and major "
        "efforts.\n"
        "Update it whenever priorities change so contributors can see the "
        "current\n"
        "direction at a glance.\n\n"
        "## Workflow\n"
        "DevCovenant expects the gated workflow for every change. Log each "
        "step in\n"
        "`CHANGELOG.md` and keep this plan consistent with the active "
        "policies in\n"
        "`AGENTS.md`.\n\n"
        "## Roadmap\n"
        "- Outline multi-week or multi-release initiatives.\n"
        "- Record dependencies or prerequisites that drive sequencing.\n\n"
        "## Near-Term Tasks\n"
        "- List the next concrete milestones and their owners.\n"
        "- Note any open questions that block delivery.\n"
    )


def _render_changelog_template(version: str, date_stamp: str) -> str:
    """Return a standard CHANGELOG.md template."""
    changelog_block = _build_doc_block(
        "CHANGELOG",
        "changelog",
        extra_lines=[
            "## How to Log Changes",
            "Add one line for each substantive change under the current "
            "version header.",
            "Keep entries newest-first and record dates in ISO format "
            "(`YYYY-MM-DD`).",
            "Example entry:",
            f"- {date_stamp}: Updated dependency manifests and license "
            "report.",
            "  Files:",
            "  requirements.in",
            "  requirements.lock",
            "  THIRD_PARTY_LICENSES.md",
            "  devcovenant/core/policies/documentation_growth_tracking/",
            "    documentation_growth_tracking.py",
        ],
    )
    return (
        "# Changelog\n\n"
        f"{changelog_block}\n"
        "## Log changes here\n\n"
        f"## Version {version}\n"
        f"- {date_stamp}: Initialized DevCovenant policy scaffolding and "
        "tooling.\n"
        "  Files:\n"
        "  AGENTS.md\n"
        "  README.md\n"
        "  CHANGELOG.md\n"
        "  CONTRIBUTING.md\n"
        "  devcovenant/\n"
        "  tools/\n"
        "  .github/\n"
        "  .pre-commit-config.yaml\n"
    )


def _build_readme_block(
    has_overview: bool,
    has_workflow: bool,
    has_toc: bool,
    has_devcovenant: bool,
) -> str:
    """Build a managed README block with missing sections."""
    include_overview = not has_overview
    include_workflow = not has_workflow
    include_devcovenant = not has_devcovenant
    include_toc = not has_toc

    toc_headings: list[str] = []
    if has_overview or include_overview:
        toc_headings.append("Overview")
    if has_workflow or include_workflow:
        toc_headings.append("Workflow")
    if has_devcovenant or include_devcovenant:
        toc_headings.append("DevCovenant")

    lines = [BLOCK_BEGIN]
    lines.extend(_build_doc_metadata_lines("README", "repo-readme"))
    lines.extend(
        [
            "",
            "**DevCovenant:** `AGENTS.md` is canonical. See "
            "`devcovenant/README.md`.",
        ]
    )

    if include_toc:
        lines.extend(["", "## Table of Contents"])
        for index, heading in enumerate(toc_headings, start=1):
            anchor = heading.lower().replace(" ", "-")
            lines.append(f"{index}. [{heading}](#{anchor})")

    if include_overview:
        lines.extend(
            [
                "",
                "## Overview",
                "This README describes the repository's purpose and the "
                "expectations",
                "for contributors. Replace this overview with a project-"
                "specific",
                "summary that covers scope, audience, and the most important "
                "interfaces.",
            ]
        )

    if include_workflow:
        lines.extend(
            [
                "",
                "## Workflow",
                "DevCovenant enforces a gated workflow for every change, "
                "including docs:",
                "1. `devcovenant check --start`",
                "2. `python3 devcovenant/run_tests.py`",
                "3. `devcovenant check --end`",
                "Record changes in `CHANGELOG.md` and keep `AGENTS.md` in "
                "sync with",
                "policy updates.",
            ]
        )

    if include_devcovenant:
        lines.extend(
            [
                "",
                "## DevCovenant",
                "`AGENTS.md` is the canonical policy source for this repo. "
                "See",
                "`devcovenant/README.md` for the local workflow guide and "
                "policy",
                "routines. Keep repo-specific decisions in the editable "
                "section",
                "of `AGENTS.md`.",
            ]
        )

    lines.append(BLOCK_END)
    return "\n".join(lines)


def _update_policy_block_value(
    text: str, policy_id: str, key: str, field_value: str
) -> str:
    """Update a policy-def block field value."""
    marker = "```policy-def"
    position = 0
    while True:
        start = text.find(marker, position)
        if start == -1:
            break
        end = text.find("```", start + len(marker))
        if end == -1:
            break
        block = text[start:end]
        if f"id: {policy_id}" not in block:
            position = end + 3
            continue
        lines = block.splitlines()
        updated_lines: list[str] = []
        found_key = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"{key}:"):
                prefix = line[: line.find(stripped)]
                updated_lines.append(f"{prefix}{key}: {field_value}")
                found_key = True
            else:
                updated_lines.append(line)
        if not found_key:
            updated_lines.append(f"{key}: {field_value}")
        updated_block = "\n".join(updated_lines)
        return text[:start] + updated_block + text[end:]
    return text


def _normalize_core_paths(paths: list[str]) -> list[str]:
    """Return cleaned core path entries."""
    cleaned: list[str] = []
    for entry in paths:
        text = str(entry).strip()
        if text:
            cleaned.append(text)
    return cleaned or list(_DEFAULT_CORE_PATHS)


def _update_core_config_text(
    text: str, include_core: bool, core_paths: list[str]
) -> tuple[str, bool]:
    """Update devcov core configuration values in config.yaml."""
    lines = text.splitlines()
    updated_lines: list[str] = []
    found_include = False
    found_paths = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith(_CORE_CONFIG_INCLUDE_KEY):
            updated_lines.append(
                f"devcov_core_include: {'true' if include_core else 'false'}"
            )
            found_include = True
            index += 1
            continue
        if stripped.startswith(_CORE_CONFIG_PATHS_KEY):
            updated_lines.append("devcov_core_paths:")
            found_paths = True
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.strip().startswith("-"):
                    index += 1
                    continue
                break
            for path in _normalize_core_paths(core_paths):
                updated_lines.append(f"  - {path}")
            continue
        updated_lines.append(line)
        index += 1

    if found_include and found_paths:
        updated = "\n".join(updated_lines) + "\n"
        return updated, updated != text

    insert_block = [
        "# DevCovenant core exclusion guard.",
        "devcov_core_include: " + ("true" if include_core else "false"),
        "devcov_core_paths:",
    ]
    insert_block.extend(
        f"  - {path}" for path in _normalize_core_paths(core_paths)
    )
    insert_block.append("")
    insert_at = 0
    for idx, line in enumerate(updated_lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_at = idx
            break
    updated_lines[insert_at:insert_at] = insert_block
    updated = "\n".join(updated_lines) + "\n"
    return updated, updated != text


def _apply_core_config(target_root: Path, include_core: bool) -> bool:
    """Ensure devcov core config matches the install target."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_core_config_text(
        text,
        include_core=include_core,
        core_paths=_DEFAULT_CORE_PATHS,
    )
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


def _ensure_config_from_profile(
    target_root: Path,
    template_root: Path,
    *,
    profile: str = "global",
    force: bool = False,
) -> bool:
    """Ensure devcovenant/config.yaml exists from the global profile asset."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if config_path.exists() and not force:
        return False
    template_path = _resolve_template_path(
        target_root,
        template_root,
        "config.yaml",
        profile=profile,
    )
    if not template_path.exists():
        return False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        _rename_existing_file(config_path)
    shutil.copy2(template_path, config_path)
    return True


def _read_generic_config_flag(target_root: Path) -> bool:
    """Return True when config.yaml is marked as generic."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    try:
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(config_data, dict):
        return False
    install_block = config_data.get("install")
    if not isinstance(install_block, dict):
        return False
    return bool(install_block.get("generic_config", False))


def _update_generic_config_text(
    text: str, is_generic: bool
) -> tuple[str, bool]:
    """Update the install.generic_config flag inside config text."""
    lines = text.splitlines()
    updated_lines: list[str] = []
    found_install = False
    found_generic = False
    index = 0
    generic_value = "true" if is_generic else "false"
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("install:"):
            found_install = True
            updated_lines.append(line.rstrip())
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  "):
                    if next_line.strip().startswith("generic_config:"):
                        updated_lines.append(
                            f"  generic_config: {generic_value}"
                        )
                        found_generic = True
                    else:
                        updated_lines.append(next_line.rstrip())
                    index += 1
                    continue
                if not next_line.strip():
                    updated_lines.append(next_line.rstrip())
                    index += 1
                    continue
                break
            if not found_generic:
                updated_lines.append(f"  generic_config: {generic_value}")
            continue
        updated_lines.append(line.rstrip())
        index += 1
    if not found_install:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append("install:")
        updated_lines.append(f"  generic_config: {generic_value}")
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, updated != text


def _set_generic_config_flag(target_root: Path, is_generic: bool) -> bool:
    """Ensure config.yaml install.generic_config matches the flag."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_generic_config_text(text, is_generic)
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


def _format_profile_list(active_profiles: list[str]) -> list[str]:
    """Return a normalized profile list for config storage."""
    if not active_profiles:
        return ["__none__"]
    return list(active_profiles)


def _format_profile_block(
    active_profiles: list[str],
    profile_registry: dict[str, dict],
) -> list[str]:
    """Return the profiles block for config.yaml."""
    profile_list = _format_profile_list(active_profiles)
    suffixes = profiles.resolve_profile_suffixes(
        profile_registry, active_profiles
    )
    cleaned: list[str] = []
    for entry in suffixes:
        suffix_value = str(entry).strip()
        if not suffix_value:
            continue
        if suffix_value not in cleaned:
            cleaned.append(suffix_value)
    if not cleaned:
        cleaned = ["__none__"]
    block = ["profiles:", "  active:"]
    for profile in profile_list:
        block.append(f"    - {profile}")
    block.append("  generated:")
    block.append("    file_suffixes:")
    for suffix in cleaned:
        block.append(f"      - {suffix}")
    return block


def _update_profile_config_text(
    text: str,
    active_profiles: list[str],
    profile_registry: dict[str, dict],
) -> tuple[str, bool]:
    """Update profile selection inside config.yaml text."""
    lines = text.splitlines()
    profile_block = _format_profile_block(active_profiles, profile_registry)
    updated_lines: list[str] = []
    found_profiles = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("profiles:"):
            found_profiles = True
            updated_lines.extend(profile_block)
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  "):
                    index += 1
                    continue
                if not next_line.strip():
                    index += 1
                    continue
                break
            continue
        updated_lines.append(line)
        index += 1

    if not found_profiles:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.extend(profile_block)
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, updated != text


def _normalize_overlay_list(raw_value: object) -> list[str]:
    """Normalize a metadata overlay entry into a list."""
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        items = [str(item).strip() for item in raw_value]
    elif isinstance(raw_value, str):
        parts = [part.strip() for part in raw_value.split(",")]
        items = [part for part in parts if part]
    else:
        items = [str(raw_value).strip()]
    return [item for item in items if item and item != "__none__"]


def _merge_overlay_value(existing: object, incoming: object) -> object:
    """Merge an incoming overlay value into an existing value."""
    if incoming is None:
        return existing
    if isinstance(existing, list) or isinstance(incoming, list):
        merged: list[str] = []
        for entry in _normalize_overlay_list(existing):
            if entry not in merged:
                merged.append(entry)
        for entry in _normalize_overlay_list(incoming):
            if entry not in merged:
                merged.append(entry)
        return merged
    if existing not in (None, "", "__none__"):
        return existing
    return incoming


def _merge_overlay_map(
    base: dict[str, object], overlay: dict[str, object]
) -> dict[str, object]:
    """Merge an overlay mapping into a base mapping."""
    merged = dict(base)
    for key, overlay_value in (overlay or {}).items():
        merged[key] = _merge_overlay_value(merged.get(key), overlay_value)
    return merged


def _coerce_bool(raw_value: object, *, default: bool) -> bool:
    """Return a boolean for common scalar values with a fallback."""
    if isinstance(raw_value, bool):
        return raw_value
    token = str(raw_value).strip().lower()
    if token in {"true", "1", "yes", "y", "on"}:
        return True
    if token in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _normalize_policy_state_map(raw_value: object | None) -> dict[str, bool]:
    """Normalize a policy_state map into boolean policy flags."""
    if not isinstance(raw_value, dict):
        return {}
    normalized: dict[str, bool] = {}
    for policy_id, enabled_value in raw_value.items():
        key = str(policy_id or "").strip()
        if not key:
            continue
        normalized[key] = _coerce_bool(enabled_value, default=True)
    return normalized


def _collect_profile_policy_state(
    profile_manifests: dict[str, dict],
) -> dict[str, bool]:
    """Collect profile-declared policy_state defaults."""
    merged: dict[str, bool] = {}
    for manifest in profile_manifests.values():
        raw_state = manifest.get("policy_state")
        profile_state = _normalize_policy_state_map(raw_state)
        for policy_id, state in profile_state.items():
            merged[policy_id] = state
    return merged


def _update_policy_state_config_text(
    text: str, policy_state: dict[str, bool]
) -> tuple[str, bool]:
    """Update the policy_state block inside config.yaml text."""
    block = {"policy_state": policy_state}
    block_text = yaml.safe_dump(block, sort_keys=False).rstrip()
    block_lines = block_text.splitlines()
    lines = text.splitlines()
    updated_lines: list[str] = []
    found = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("policy_state:"):
            found = True
            updated_lines.extend(block_lines)
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  ") or not next_line.strip():
                    index += 1
                    continue
                break
            continue
        updated_lines.append(line)
        index += 1
    if not found:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.extend(block_lines)
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, updated != text


def _collect_profile_overlays(
    profile_manifests: dict[str, dict],
) -> dict[str, dict[str, object]]:
    """Collect policy metadata overlays from active profiles."""
    overlays: dict[str, dict[str, object]] = {}
    for manifest in profile_manifests.values():
        raw_overlays = manifest.get("policy_overlays") or {}
        if raw_overlays == "__none__":
            continue
        for policy_id, overlay in raw_overlays.items():
            if not overlay or overlay == "__none__":
                continue
            existing = overlays.get(policy_id, {})
            overlays[policy_id] = _merge_overlay_map(existing, overlay)
    return overlays


def _build_metadata_overrides_block(
    block_key: str, overrides: dict[str, object] | None
) -> list[str]:
    """Return a config block for policy metadata overrides."""
    if overrides is None:
        return []
    if not isinstance(overrides, dict):
        overrides = {}
    block = yaml.safe_dump(
        {block_key: overrides},
        sort_keys=False,
    ).rstrip()
    return block.splitlines()


def _update_metadata_overrides_config_text(
    text: str, block_key: str, overrides: dict[str, object] | None
) -> tuple[str, bool]:
    """Update a metadata overrides block inside config.yaml text."""
    block_lines = _build_metadata_overrides_block(block_key, overrides)
    if not block_lines:
        return text, False
    lines = text.splitlines()
    updated_lines: list[str] = []
    found_block = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith(f"{block_key}:"):
            found_block = True
            updated_lines.extend(block_lines)
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  "):
                    index += 1
                    continue
                if not next_line.strip():
                    index += 1
                    continue
                break
            continue
        updated_lines.append(line)
        index += 1

    if not found_block:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.extend(block_lines)
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, updated != text


def _remove_legacy_policies_block(text: str) -> tuple[str, bool]:
    """Remove the legacy policies block from config.yaml text."""
    lines = text.splitlines()
    updated_lines: list[str] = []
    removed = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("policies:"):
            removed = True
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  ") or not next_line.strip():
                    index += 1
                    continue
                break
            continue
        updated_lines.append(line)
        index += 1
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, removed


def _apply_profile_policy_overlays(
    target_root: Path,
    overlays: dict[str, dict[str, object]],
) -> bool:
    """Apply profile policy overlays to config.yaml."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    config_data = yaml.safe_load(text) or {}
    user_overrides = config_data.get("user_metadata_overrides")
    autogen_overrides = config_data.get("autogen_metadata_overrides")
    legacy_overrides = config_data.get("policies")
    if not isinstance(user_overrides, dict):
        if isinstance(legacy_overrides, dict):
            user_overrides = legacy_overrides
        else:
            user_overrides = {}
    if not isinstance(autogen_overrides, dict):
        autogen_overrides = {}
    for policy_id, overlay in (overlays or {}).items():
        current = autogen_overrides.get(policy_id, {}) or {}
        autogen_overrides[policy_id] = _merge_overlay_map(current, overlay)
    updated, changed = _update_metadata_overrides_config_text(
        text, "autogen_metadata_overrides", autogen_overrides
    )
    updated, user_changed = _update_metadata_overrides_config_text(
        updated, "user_metadata_overrides", user_overrides
    )
    changed = changed or user_changed
    updated, removed_legacy = _remove_legacy_policies_block(updated)
    changed = changed or removed_legacy
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


def _remove_legacy_policy_control_keys(text: str) -> tuple[str, bool]:
    """Remove legacy activation keys from config.yaml text."""
    legacy_keys = {"autogen_disable:", "manual_force_enable:"}
    lines = text.splitlines()
    updated_lines: list[str] = []
    removed = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if any(stripped.startswith(key) for key in legacy_keys):
            removed = True
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  -") or not next_line.strip():
                    index += 1
                    continue
                break
            continue
        updated_lines.append(line)
        index += 1
    updated = "\n".join(updated_lines).rstrip() + "\n"
    return updated, removed


def _apply_profile_policy_state(
    target_root: Path,
    profile_policy_state: dict[str, bool],
) -> bool:
    """Update policy_state defaults inside config.yaml."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    config_data = yaml.safe_load(text) or {}
    existing_state = _normalize_policy_state_map(
        config_data.get("policy_state")
    )
    for policy_id, state in profile_policy_state.items():
        existing_state.setdefault(policy_id, state)
    updated, changed = _update_policy_state_config_text(text, existing_state)
    updated, removed_legacy = _remove_legacy_policy_control_keys(updated)
    changed = changed or removed_legacy
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


def _apply_profile_config(
    target_root: Path,
    active_profiles: list[str],
    profile_registry: dict[str, dict],
) -> bool:
    """Ensure profile selection is recorded in config.yaml."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_profile_config_text(
        text, active_profiles, profile_registry
    )
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


def apply_autogen_metadata_overrides(
    target_root: Path, package_root: Path | None = None
) -> bool:
    """Refresh autogen policy overrides based on active profiles."""
    if package_root is None:
        package_root = Path(__file__).resolve().parents[1]
    active_profiles = _ensure_global_profile(
        _dedupe_preserve_order(_load_active_profiles(target_root))
    )
    manifests = _load_profile_manifests(
        package_root, target_root, active_profiles
    )
    overlays = _collect_profile_overlays(manifests)
    changed = _apply_profile_policy_overlays(target_root, overlays)
    profile_state = _collect_profile_policy_state(manifests)
    state_changed = _apply_profile_policy_state(target_root, profile_state)
    return changed or state_changed


def _copy_path(source: Path, target: Path) -> None:
    """Copy a file or directory from source to target."""
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return
    if target.exists():
        _rename_existing_file(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _rename_existing_file(target: Path) -> Path | None:
    """Rename an existing file to preserve it before overwriting."""
    if not _BACKUPS_ENABLED:
        return None
    if not target.exists() or target.is_dir():
        return None
    if target in _BACKUP_ORIGINALS:
        return None
    suffix = target.suffix
    stem = target.stem
    candidate = target.with_name(f"{stem}_old{suffix}")
    index = 2
    while candidate.exists():
        candidate = target.with_name(f"{stem}_old{index}{suffix}")
        index += 1
    target.rename(candidate)
    _BACKUP_ORIGINALS.add(target)
    _record_backup(candidate)
    return candidate


def _copy_dir_contents(source: Path, target: Path) -> None:
    """Copy contents of source dir into target dir."""
    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        dest = target / entry.name
        if entry.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(entry, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, dest)


def _backup_paths(root: Path, paths: list[str], backup_root: Path) -> None:
    """Backup selected paths into backup_root."""
    for rel in paths:
        src = root / rel
        if not src.exists():
            continue
        dest = backup_root / rel
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _restore_paths(backup_root: Path, root: Path, paths: list[str]) -> None:
    """Restore backed-up paths into root."""
    for rel in paths:
        src = backup_root / rel
        if not src.exists():
            continue
        dest = root / rel
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _preserve_editable_section(target: Path, user_content: str) -> None:
    """Merge existing user AGENTS content into the new editable section."""
    if not target.exists() or not user_content.strip():
        return
    text = target.read_text(encoding="utf-8")
    start = text.find("<!-- DEVCOV:END -->")
    if start == -1:
        return
    remainder = text[start:]
    middle_end = remainder.find("<!-- DEVCOV:BEGIN -->")
    if middle_end == -1:
        return
    middle = remainder[:middle_end]
    after = remainder[middle_end:]
    marker = "# EDITABLE SECTION"
    marker_idx = middle.find(marker)
    if marker_idx == -1:
        insertion = f"{middle}{marker}\n\n{user_content.strip()}\n\n"
    else:
        prefix = middle[: marker_idx + len(marker)]
        suffix = middle[marker_idx + len(marker) :]
        rest = suffix.lstrip("\n")
        insertion = f"{prefix}\n\n{user_content.strip()}\n\n{rest}"
    updated = text[:start] + insertion + after
    target.write_text(updated, encoding="utf-8")


def _extract_editable_notes(text: str) -> str:
    """Extract editable notes from an existing AGENTS.md."""
    start = text.find("<!-- DEVCOV:END -->")
    if start == -1:
        return text.strip()
    remainder = text[start:]
    middle_end = remainder.find("<!-- DEVCOV:BEGIN -->")
    if middle_end == -1:
        return text.strip()
    middle = remainder[:middle_end]
    marker = "# EDITABLE SECTION"
    marker_idx = middle.find(marker)
    if marker_idx == -1:
        return middle.strip()
    return middle[marker_idx + len(marker) :].strip()


def _install_devcovenant_dir(
    source_root: Path,
    target_root: Path,
    preserve_paths: list[str],
    preserve_existing: bool,
) -> list[str]:
    """Install the devcovenant directory while preserving custom paths."""
    source = source_root / DEV_COVENANT_DIR
    target = target_root / DEV_COVENANT_DIR
    installed: list[str] = []
    if not source.exists():
        return installed

    if not target.exists() or not preserve_existing:
        _copy_path(source, target)
        installed.append(DEV_COVENANT_DIR)
        return installed

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_root = Path(tmpdir)
        _backup_paths(target, preserve_paths, backup_root)
        _copy_path(source, target)
        _restore_paths(backup_root, target, preserve_paths)

    installed.append(DEV_COVENANT_DIR)
    return installed


def _ensure_custom_tree(target_root: Path) -> None:
    """Ensure devcovenant/custom and its policy/profile dirs exist."""
    custom_root = target_root / DEV_COVENANT_DIR / "custom"
    policies_dir = custom_root / "policies"
    profiles_dir = custom_root / "profiles"
    policies_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    init_path = custom_root / "__init__.py"
    if not init_path.exists():
        init_path.write_text(
            "# Custom DevCovenant overrides.\n", encoding="utf-8"
        )


def _ensure_tests_mirror(target_root: Path, include_core: bool) -> None:
    """Ensure tests/devcovenant mirrors the expected structure."""
    tests_root = target_root / "tests" / "devcovenant"
    custom_root = tests_root / "custom"
    core_root = tests_root / "core"
    custom_root.mkdir(parents=True, exist_ok=True)
    if include_core:
        core_root.mkdir(parents=True, exist_ok=True)
    elif core_root.exists():
        shutil.rmtree(core_root)

    def _ensure_init(path: Path, comment: str) -> None:
        """Ensure a package marker exists in the mirror directory."""
        init_path = path / "__init__.py"
        if not init_path.exists():
            init_path.write_text(comment, encoding="utf-8")

    _ensure_init(tests_root, "# DevCovenant test mirror.\n")
    _ensure_init(custom_root, "# DevCovenant custom test mirror.\n")
    if include_core:
        _ensure_init(core_root, "# DevCovenant core test mirror.\n")

    def _mirror_subdirs(source_root: Path, target_root: Path) -> None:
        """Create policy/profile mirror folders under the test tree."""
        for folder in ("policies", "profiles"):
            target_folder = target_root / folder
            target_folder.mkdir(parents=True, exist_ok=True)
            _ensure_init(target_folder, "# DevCovenant test mirror.\n")
            source_folder = source_root / folder
            expected_dirs: set[str] = set()
            if source_folder.exists():
                for entry in source_folder.iterdir():
                    if not entry.is_dir():
                        continue
                    if entry.name.startswith("__"):
                        continue
                    expected_dirs.add(entry.name)
                    dest = target_folder / entry.name
                    dest.mkdir(parents=True, exist_ok=True)
                    _ensure_init(dest, "# DevCovenant test mirror.\n")

            # Prune empty stale mirrors for removed policies/profiles.
            for existing in target_folder.iterdir():
                if not existing.is_dir():
                    continue
                if existing.name.startswith("__"):
                    continue
                if existing.name in expected_dirs:
                    continue
                if any(existing.iterdir()):
                    continue
                existing.rmdir()

    _mirror_subdirs(target_root / DEV_COVENANT_DIR / "custom", custom_root)
    if include_core:
        _mirror_subdirs(
            target_root / DEV_COVENANT_DIR / "core",
            core_root,
        )


def _prune_devcovrepo_overrides(
    target_root: Path, include_core: bool
) -> list[str]:
    """Remove devcovrepo-prefixed overrides unless core is enabled."""
    if include_core:
        return []
    removed: list[str] = []
    custom_root = target_root / DEV_COVENANT_DIR / "custom"
    for folder in ("policies", "profiles"):
        root = custom_root / folder
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            name = entry.name.lower()
            if name.startswith("devcovrepo"):
                shutil.rmtree(entry)
                removed.append(str(entry.relative_to(target_root)))
    return removed


def _install_paths(
    repo_root: Path,
    target_root: Path,
    paths: list[str],
    skip_existing: bool,
    source_overrides: dict[str, Path] | None = None,
) -> list[str]:
    """Copy paths and return installed file list."""
    installed: list[str] = []
    overrides = source_overrides or {}
    for rel_path in paths:
        source = overrides.get(rel_path, repo_root / rel_path)
        target = target_root / rel_path
        if not source.exists():
            continue
        if skip_existing and target.exists():
            continue
        _copy_path(source, target)
        installed.append(rel_path)
    return installed


def _inject_block(path: Path, block: str) -> bool:
    """Insert or replace a DevCovenant block in a documentation file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, _rest = text.split(BLOCK_BEGIN, 1)
        _old_block, after = _rest.split(BLOCK_END, 1)
        updated = f"{before}{block}{after}"
        if updated == text:
            return False
        _rename_existing_file(path)
        path.write_text(updated, encoding="utf-8")
        return True

    lines = text.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            insert_at = index + 1
            while insert_at < len(lines):
                candidate = lines[insert_at].strip()
                if not candidate:
                    insert_at += 1
                    continue
                if _LAST_UPDATED_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                if _VERSION_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                break
            break
    lines.insert(insert_at, block)
    _rename_existing_file(path)
    _rename_existing_file(path)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def _ensure_doc_block(path: Path, doc_id: str, doc_type: str) -> bool:
    """Ensure a doc metadata block exists near the top of the file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            insert_at = index + 1
            while insert_at < len(lines):
                candidate = lines[insert_at].strip()
                if not candidate:
                    insert_at += 1
                    continue
                if _LAST_UPDATED_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                if _VERSION_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                break
            break

    if insert_at < len(lines) and lines[insert_at].lstrip().startswith(
        BLOCK_BEGIN
    ):
        return False

    block = _build_doc_block(doc_id, doc_type)
    lines.insert(insert_at, block)
    if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
        lines.insert(insert_at + 1, "\n")
    path.write_text("".join(lines), encoding="utf-8")
    return True


def _ensure_changelog_block(
    path: Path, last_updated: str, version: str
) -> bool:
    """Ensure the changelog uses the managed block layout."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    log_marker = re.search(r"^## Log changes here\s*$", text, re.MULTILINE)
    if log_marker:
        log_section = text[log_marker.start() :].lstrip()
    else:
        version_marker = re.search(r"^## Version\b", text, re.MULTILINE)
        if version_marker:
            log_section = (
                "## Log changes here\n\n" + text[version_marker.start() :]
            )
        else:
            log_section = (
                "## Log changes here\n\n"
                f"## Version {version}\n"
                f"- {last_updated}: Initialized changelog entries.\n"
            )

    header = (
        "# Changelog\n"
        f"**Last Updated:** {last_updated}\n"
        f"**Version:** {version}\n\n"
    )
    changelog_block = _build_doc_block(
        "CHANGELOG",
        "changelog",
        extra_lines=[
            "## How to Log Changes",
            "Add one line for each substantive change under the current "
            "version header.",
            "Keep entries newest-first and record dates in ISO format "
            "(`YYYY-MM-DD`).",
            "Example entry:",
            f"- {last_updated}: Updated dependency manifests and license "
            "report.",
            "  Files:",
            "  requirements.in",
            "  requirements.lock",
            "  THIRD_PARTY_LICENSES.md",
            "  devcovenant/core/policies/documentation_growth_tracking/",
            "    documentation_growth_tracking.py",
        ],
    )
    updated = header + changelog_block + "\n" + log_section.lstrip()
    if updated == text:
        return False
    _rename_existing_file(path)
    path.write_text(updated, encoding="utf-8")
    return True


def _extract_blocks(text: str) -> list[str]:
    """Return all managed blocks from text in order."""
    blocks: list[str] = []
    start = 0
    while True:
        begin = text.find(BLOCK_BEGIN, start)
        if begin == -1:
            break
        end = text.find(BLOCK_END, begin)
        if end == -1:
            break
        end += len(BLOCK_END)
        blocks.append(text[begin:end])
        start = end
    return blocks


def _replace_blocks(text: str, template_blocks: list[str]) -> tuple[str, bool]:
    """Replace managed blocks in text using template blocks in order."""
    if not template_blocks:
        return text, False
    start = 0
    index = 0
    updated = False
    parts: list[str] = []
    while True:
        begin = text.find(BLOCK_BEGIN, start)
        if begin == -1:
            parts.append(text[start:])
            break
        end = text.find(BLOCK_END, begin)
        if end == -1:
            parts.append(text[start:])
            break
        end += len(BLOCK_END)
        parts.append(text[start:begin])
        if index < len(template_blocks):
            parts.append(template_blocks[index])
            if text[begin:end] != template_blocks[index]:
                updated = True
        else:
            parts.append(text[begin:end])
        index += 1
        start = end
    if index < len(template_blocks):
        if parts and not parts[-1].endswith("\n"):
            parts.append("\n")
        parts.append("\n\n".join(template_blocks[index:]) + "\n")
        updated = True
    return "".join(parts), updated


def _sync_blocks_from_template(target: Path, template_text: str) -> bool:
    """Update all managed blocks in target from template text."""
    if not target.exists():
        return False
    template_blocks = _extract_blocks(template_text)
    if not template_blocks:
        return False
    current = target.read_text(encoding="utf-8")
    updated_text, changed = _replace_blocks(current, template_blocks)
    if changed:
        _rename_existing_file(target)
        target.write_text(updated_text, encoding="utf-8")
    return changed


def _parse_metadata_block(
    block: str,
) -> tuple[list[str], dict[str, list[str]]]:
    """Return ordered keys and per-key values from metadata."""
    order: list[str] = []
    values: dict[str, list[str]] = {}
    current_key = ""
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped:
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            value_text = raw_value.strip()
            order.append(key)
            values[key] = [] if not value_text else [value_text]
            current_key = key
            continue
        if current_key:
            values[current_key].append(stripped)
    return order, values


def _render_metadata_block(
    keys: list[str], values: dict[str, list[str]]
) -> str:
    """Render a policy-def block from ordered keys and values."""
    lines: list[str] = []
    for key in keys:
        entries = values.get(key, [])
        if not entries:
            lines.append(f"{key}:")
            continue
        first = entries[0]
        if first:
            lines.append(f"{key}: {first}")
        else:
            lines.append(f"{key}:")
        for extra in entries[1:]:
            lines.append(f"  {extra}")
    return "\n".join(lines)


def _ensure_key(
    keys: list[str], values: dict[str, list[str]], key: str
) -> None:
    """Ensure a metadata key exists in order and value map."""
    if key not in values:
        values[key] = []
    if key not in keys:
        keys.append(key)


def _apply_policy_state_disables(
    target_root: Path, disable_ids: list[str]
) -> list[str]:
    """Disable policies by setting policy_state entries in config.yaml."""
    if not disable_ids:
        return []
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return []
    disable_set = {
        policy_id.strip() for policy_id in disable_ids if policy_id.strip()
    }
    if not disable_set:
        return []
    text = config_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text) or {}
    policy_state = _normalize_policy_state_map(payload.get("policy_state"))
    for policy_id in sorted(disable_set):
        policy_state[policy_id] = False
    updated, changed = _update_policy_state_config_text(text, policy_state)
    updated, removed_legacy = _remove_legacy_policy_control_keys(updated)
    changed = changed or removed_legacy
    if changed:
        _rename_existing_file(config_path)
        config_path.write_text(updated, encoding="utf-8")
    return sorted(disable_set)


def _extract_block(text: str) -> str | None:
    """Return the managed block from text, if present."""
    if BLOCK_BEGIN not in text or BLOCK_END not in text:
        return None
    _before, rest = text.split(BLOCK_BEGIN, 1)
    block_body, _after = rest.split(BLOCK_END, 1)
    return f"{BLOCK_BEGIN}{block_body}{BLOCK_END}"


def _sync_block(path: Path, block: str | None) -> bool:
    """Replace or insert the managed block in a file."""
    if not block or not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, rest = text.split(BLOCK_BEGIN, 1)
        _old_block, after = rest.split(BLOCK_END, 1)
        updated = f"{before}{block}{after}"
        if updated != text:
            _rename_existing_file(path)
            path.write_text(updated, encoding="utf-8")
            return True
        return False
    return _inject_block(path, block)


def _build_manifest_options(
    *,
    docs_mode: str,
    config_mode: str,
    license_mode: str,
    version_mode: str,
    target_version: str,
    pyproject_mode: str,
    ci_mode: str,
    docs_include: set[str] | None,
    docs_exclude: set[str],
    policy_mode: str,
    preserve_custom: bool,
    devcov_core_include: bool,
    disabled_policies: list[str],
    auto_uninstall: bool,
) -> dict[str, object]:
    """Return the manifest options payload for the install run."""
    return {
        "docs_mode": docs_mode,
        "config_mode": config_mode,
        "license_mode": license_mode,
        "version_mode": version_mode,
        "target_version": target_version,
        "pyproject_mode": pyproject_mode,
        "ci_mode": ci_mode,
        "docs_include": sorted(docs_include or []),
        "docs_exclude": sorted(docs_exclude),
        "policy_mode": policy_mode,
        "preserve_custom": preserve_custom,
        "devcov_core_include": devcov_core_include,
        "disable_policies": sorted(disabled_policies),
        "auto_uninstall": auto_uninstall,
    }


def _finalize_manifest(
    target_root: Path,
    options: dict[str, object],
    installed: dict[str, list[str]],
    doc_blocks: list[str],
    mode: str,
    active_profiles: list[str],
    profile_registry: dict[str, dict],
) -> None:
    """Write the manifest file for the install/update run."""
    manifest = manifest_module.build_manifest(
        options=options,
        installed=installed,
        doc_blocks=doc_blocks,
        mode=mode,
    )
    manifest["profiles"]["active"] = list(active_profiles)
    manifest["profiles"]["registry"] = sorted(profile_registry.keys())
    manifest_module.write_manifest(target_root, manifest)


def main(argv=None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Install DevCovenant in a target repository."
    )
    cli_options.add_install_update_args(
        parser,
        defaults=cli_options.DEFAULT_INSTALL_DEFAULTS,
        include_mode=True,
        include_allow_existing=True,
    )
    args = parser.parse_args(argv)
    _set_backups_enabled(bool(getattr(args, "backup_existing", False)))
    no_touch = bool(getattr(args, "no_touch", False))
    skip_refresh = bool(getattr(args, "skip_refresh", False))
    skip_core = bool(getattr(args, "skip_core", False))
    deploy_mode = bool(getattr(args, "deploy", False))
    require_non_generic = bool(getattr(args, "require_non_generic", False))

    disable_policies = _parse_policy_ids(args.disable_policy)
    disabled_policies = list(disable_policies)

    if skip_core:
        target_root = Path(args.target).resolve()
        package_root = target_root / DEV_COVENANT_DIR
        if not package_root.exists():
            raise SystemExit(
                "DevCovenant core not found in target; run install or upgrade."
            )
        repo_root = target_root
    else:
        package_root = Path(__file__).resolve().parents[1]
        repo_root = package_root.parent
    template_root = package_root / "core"
    target_root = Path(args.target).resolve()
    config_existed = (target_root / DEV_COVENANT_DIR / "config.yaml").exists()
    include_core = (
        _load_devcov_core_include(target_root)
        if skip_core
        else target_root == repo_root
    )
    schema_path = None
    _reset_backup_state(target_root)
    manifest_file = manifest_module.manifest_path(target_root)
    legacy_paths = manifest_module.legacy_manifest_paths(target_root)
    has_manifest = manifest_file.exists() or any(
        path.exists() for path in legacy_paths
    )
    has_existing = has_manifest or (target_root / DEV_COVENANT_DIR).exists()
    if args.mode == "auto":
        mode = "existing" if has_existing else "empty"
    else:
        mode = args.mode

    if has_existing and not args.allow_existing:
        if args.auto_uninstall:
            uninstall.main(["--target", str(target_root)])
            has_existing = False
            mode = "empty"
        else:
            args.allow_existing = True

    if args.allow_existing:
        mode = "existing"

    manifest_mode = "update" if mode == "existing" else "install"

    docs_mode = args.docs_mode
    config_mode = args.config_mode
    policy_mode = args.policy_mode

    if args.force_docs:
        docs_mode = "overwrite"
    if args.force_config:
        config_mode = "overwrite"

    if docs_mode is None:
        docs_mode = "overwrite" if mode == "empty" else "preserve"
    if policy_mode is None:
        policy_mode = "overwrite" if mode == "empty" else "preserve"
    try:
        docs_include = _parse_doc_names(args.docs_include)
        docs_exclude = _parse_doc_names(args.docs_exclude) or set()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    required_docs = set(_DOC_NAME_MAP.keys())

    always_overwrite_docs = set()
    if mode != "existing":
        always_overwrite_docs = {"CHANGELOG", "CONTRIBUTING"}

    overwrite_targets = (
        set(docs_include) if docs_include is not None else set(required_docs)
    )
    overwrite_targets |= always_overwrite_docs
    overwrite_targets -= docs_exclude
    docs_exclude -= always_overwrite_docs

    def _should_overwrite(doc_name: str) -> bool:
        """Return True when overwrite mode targets the doc name."""
        if doc_name in always_overwrite_docs:
            return True
        return docs_mode == "overwrite" and doc_name in overwrite_targets

    agents_path = target_root / "AGENTS.md"
    existing_agents_text = None
    if agents_path.exists():
        existing_agents_text = _extract_editable_notes(
            agents_path.read_text(encoding="utf-8")
        )
    if config_mode is None:
        config_mode = "overwrite" if mode == "empty" else "preserve"

    def _resolve_override(override_value: str, inherited: str) -> str:
        """Return the resolved mode for a CLI override."""
        return inherited if override_value == "inherit" else override_value

    metadata_mode = "overwrite" if mode == "empty" else "preserve"
    license_mode = _resolve_override(args.license_mode, metadata_mode)
    version_mode = _resolve_override(args.version_mode, metadata_mode)
    pyproject_mode = _resolve_override(args.pyproject_mode, config_mode)
    ci_mode = config_mode if args.ci_mode == "inherit" else args.ci_mode

    preserve_custom = args.preserve_custom
    if preserve_custom is None:
        preserve_custom = mode == "existing"

    last_updated = _utc_today()
    repo_name = target_root.name

    source_version_path = package_root / "VERSION"
    devcovenant_version = None
    if source_version_path.exists():
        devcovenant_version = source_version_path.read_text(
            encoding="utf-8"
        ).strip()
    else:
        devcovenant_version = "0.0.0"

    version_path = target_root / DEV_COVENANT_DIR / "VERSION"
    raw_existing_version = None
    if version_path.exists():
        raw_existing_version = version_path.read_text(encoding="utf-8").strip()
    existing_version = _normalize_existing_version(raw_existing_version)
    version_file_exists = version_path.exists()
    version_existed = existing_version is not None

    if require_non_generic and _read_generic_config_flag(target_root):
        raise SystemExit(
            "Config is still generic. Edit devcovenant/config.yaml and set "
            "install.generic_config to false before running deploy."
        )

    if has_existing and not skip_core and not deploy_mode:
        if _version_key(devcovenant_version) > _version_key(existing_version):
            if sys.stdin.isatty() and _prompt_yes_no(
                "Newer DevCovenant core detected. Run upgrade now?",
                default=True,
            ):
                from devcovenant.core.upgrade import main as upgrade_main

                upgrade_main(["--target", str(target_root)])
                return
            print(
                "Newer DevCovenant core detected. Run `devcovenant upgrade` "
                "to apply."
            )

    requested_version = None
    if args.version_value:
        requested_version = _normalize_version(args.version_value)

    pyproject_version = _read_pyproject_version(target_root / "pyproject.toml")
    if pyproject_version:
        try:
            pyproject_version = _normalize_version(pyproject_version)
        except ValueError:
            pyproject_version = None

    config_override = _load_config_version_override(target_root)
    detected_version: str | None = None
    if requested_version:
        detected_version = requested_version
    elif config_override:
        detected_version = config_override
    else:
        detected_version = existing_version or pyproject_version
    if not detected_version:
        if sys.stdin.isatty():
            detected_version = _prompt_version()
        if not detected_version:
            detected_version = DEFAULT_BOOTSTRAP_VERSION

    if version_mode == "preserve" and existing_version:
        target_version = existing_version
    else:
        target_version = detected_version

    profile_registry = _load_profile_registry(package_root, target_root)
    if mode == "existing":
        active_profiles = _load_active_profiles(target_root)
        if not active_profiles:
            active_profiles = _prompt_profiles(profile_registry)
    else:
        active_profiles = _prompt_profiles(profile_registry)
    active_profiles = _ensure_global_profile(
        _dedupe_preserve_order(active_profiles)
    )

    installed: dict[str, list[str]] = {
        "core": [],
        "config": [],
        "docs": [],
        "assets": [],
    }
    doc_blocks: list[str] = []

    core_preserve_paths: list[str] = []
    if preserve_custom:
        core_preserve_paths.extend(DEFAULT_PRESERVE_PATHS)
    if mode == "existing" and version_mode in {"preserve", "skip"}:
        if version_file_exists:
            core_preserve_paths.append("VERSION")
    core_preserve_paths = _dedupe_preserve_order(core_preserve_paths)

    core_files = [path for path in CORE_PATHS if path != DEV_COVENANT_DIR]
    core_sources = {
        path: _resolve_source_path(target_root, template_root, path)
        for path in core_files
    }
    if not skip_core:
        installed["core"].extend(
            _install_devcovenant_dir(
                repo_root,
                target_root,
                core_preserve_paths,
                preserve_existing=preserve_custom,
            )
        )
    core_profile_root = package_root / "core" / PROFILE_ROOT_NAME
    custom_profile_root = (
        target_root / DEV_COVENANT_DIR / "custom" / PROFILE_ROOT_NAME
    )
    profiles.write_profile_registry(
        target_root,
        profiles.build_profile_registry(
            target_root,
            active_profiles,
            core_root=core_profile_root,
            custom_root=custom_profile_root,
        ),
    )
    if not skip_core:
        installed["core"].extend(
            _install_paths(
                repo_root,
                target_root,
                core_files,
                skip_existing=False,
                source_overrides=core_sources,
            )
        )

    if not no_touch:
        config_created = _ensure_config_from_profile(
            target_root,
            template_root,
            force=not config_existed,
        )
        if config_created:
            installed["config"].append(f"{DEV_COVENANT_DIR}/config.yaml")

    if mode == "existing":
        _remove_legacy_paths(target_root, LEGACY_ROOT_PATHS)

    if no_touch:
        options = _build_manifest_options(
            docs_mode=docs_mode,
            config_mode=config_mode,
            license_mode=license_mode,
            version_mode=version_mode,
            target_version=target_version,
            pyproject_mode=pyproject_mode,
            ci_mode=ci_mode,
            docs_include=docs_include,
            docs_exclude=docs_exclude,
            policy_mode=policy_mode,
            preserve_custom=preserve_custom,
            devcov_core_include=include_core,
            disabled_policies=disabled_policies,
            auto_uninstall=bool(args.auto_uninstall),
        )
        _finalize_manifest(
            target_root,
            options,
            installed,
            doc_blocks,
            manifest_mode,
            active_profiles,
            profile_registry,
        )
        backups = _backup_log()
        if backups:
            print("Backed up files before overwrite/merge:")
            for entry in backups:
                print(f"- {entry}")
        return

    _apply_core_config(target_root, include_core)
    _apply_profile_config(target_root, active_profiles, profile_registry)
    _ensure_custom_tree(target_root)
    _ensure_tests_mirror(target_root, include_core)
    removed_overrides = _prune_devcovrepo_overrides(target_root, include_core)
    if removed_overrides:
        manifest_module.append_notifications(
            target_root,
            [
                (
                    "Removed devcovrepo-prefixed overrides:"
                    f" {', '.join(removed_overrides)}"
                )
            ],
        )

    if not deploy_mode:
        _set_generic_config_flag(target_root, True)
        if version_mode != "skip" and (
            version_mode == "overwrite" or not version_existed
        ):
            version_path.write_text(f"{target_version}\n", encoding="utf-8")
            if not version_file_exists:
                installed["core"].append(f"{DEV_COVENANT_DIR}/VERSION")
        docs_mode = "preserve"
        policy_mode = "preserve"
        options = _build_manifest_options(
            docs_mode=docs_mode,
            config_mode=config_mode,
            license_mode=license_mode,
            version_mode=version_mode,
            target_version=target_version,
            pyproject_mode=pyproject_mode,
            ci_mode=ci_mode,
            docs_include=docs_include,
            docs_exclude=docs_exclude,
            policy_mode=policy_mode,
            preserve_custom=preserve_custom,
            devcov_core_include=include_core,
            disabled_policies=disabled_policies,
            auto_uninstall=bool(args.auto_uninstall),
        )
        _finalize_manifest(
            target_root,
            options,
            installed,
            doc_blocks,
            manifest_mode,
            active_profiles,
            profile_registry,
        )
        return

    config_paths = [path for path in CONFIG_PATHS if path != ".gitignore"]
    if ci_mode == "skip":
        config_paths = [
            path for path in config_paths if path != ".github/workflows/ci.yml"
        ]
    config_sources = {
        path: _resolve_source_path(target_root, template_root, path)
        for path in config_paths
    }
    installed["config"] = _install_paths(
        repo_root,
        target_root,
        config_paths,
        skip_existing=(mode == "existing" and config_mode == "preserve"),
        source_overrides=config_sources,
    )

    gitignore_path = target_root / ".gitignore"
    existing_gitignore = (
        gitignore_path.read_text(encoding="utf-8")
        if gitignore_path.exists()
        else ""
    )
    gitignore_text = _render_gitignore(
        existing_gitignore,
        target_root,
        template_root,
        active_profiles,
    )
    if not gitignore_path.exists():
        installed["config"].append(".gitignore")
    gitignore_path.parent.mkdir(parents=True, exist_ok=True)
    if not gitignore_path.exists() or existing_gitignore != gitignore_text:
        if gitignore_path.exists():
            _rename_existing_file(gitignore_path)
        gitignore_path.write_text(gitignore_text, encoding="utf-8")

    refresh_pre_commit_config(
        target_root,
        package_root=package_root,
        active_profiles=active_profiles,
        profile_registry=profile_registry,
    )
    pre_commit_path = target_root / ".pre-commit-config.yaml"
    if (
        pre_commit_path.exists()
        and ".pre-commit-config.yaml" not in installed["config"]
    ):
        installed["config"].append(".pre-commit-config.yaml")

    if version_mode != "skip" and (
        version_mode == "overwrite" or not version_existed
    ):
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        if not version_file_exists:
            installed["core"].append(f"{DEV_COVENANT_DIR}/VERSION")

    license_path = target_root / "LICENSE"
    license_existed = license_path.exists()
    if license_mode != "skip" and (
        license_mode == "overwrite" or not license_existed
    ):
        if license_existed and license_mode == "overwrite":
            _rename_existing_file(license_path)
        license_template = _resolve_source_path(
            target_root, template_root, LICENSE_TEMPLATE
        )
        if not license_template.exists():
            fallback_candidates = [
                package_root.parent / LICENSE_TEMPLATE,
                Path(__file__).resolve().parents[2] / LICENSE_TEMPLATE,
            ]
            for candidate in fallback_candidates:
                if candidate.exists():
                    license_template = candidate
                    break
        if license_template.exists():
            license_body = license_template.read_text(encoding="utf-8")
            license_text = (
                f"Project Version: {target_version}\n\n{license_body}"
            )
            license_path.write_text(license_text, encoding="utf-8")
            if not license_existed:
                installed["docs"].append("LICENSE")

    if pyproject_mode != "skip":
        pyproject_sources = {
            "pyproject.toml": _resolve_source_path(
                target_root, template_root, "pyproject.toml"
            )
        }
        installed["docs"].extend(
            _install_paths(
                repo_root,
                target_root,
                ["pyproject.toml"],
                skip_existing=(
                    mode == "existing" and pyproject_mode == "preserve"
                ),
                source_overrides=pyproject_sources,
            )
        )

    doc_key_by_name = {value: key for key, value in _DOC_NAME_MAP.items()}

    def _doc_force(doc_name: str) -> bool:
        """Return True when managed doc overwrite mode targets the doc."""
        doc_key = doc_key_by_name.get(doc_name)
        return _should_overwrite(doc_key) if doc_key else False

    def _track_managed_doc(doc_name: str, existed: bool) -> None:
        """Record installed docs and managed blocks for the manifest."""
        doc_path = target_root / doc_name
        if not existed and doc_path.exists():
            installed["docs"].append(doc_name)
        if doc_path.exists():
            if BLOCK_BEGIN in doc_path.read_text(encoding="utf-8"):
                doc_blocks.append(doc_name)

    agents_existed = agents_path.exists()
    agents_force = policy_mode == "overwrite"
    _agents_changed, agents_rebuilt = _ensure_doc_from_descriptor(
        target_root,
        "AGENTS.md",
        last_updated=last_updated,
        version=target_version,
        template_root=template_root,
        force=agents_force,
    )
    if agents_rebuilt and existing_agents_text:
        _preserve_editable_section(agents_path, existing_agents_text)
    _track_managed_doc("AGENTS.md", agents_existed)

    disabled_policies = _apply_policy_state_disables(
        target_root, disable_policies
    )
    profile_manifests = _load_profile_manifests(
        package_root,
        target_root,
        active_profiles,
    )
    profile_overlays = _collect_profile_overlays(profile_manifests)
    _apply_profile_policy_overlays(target_root, profile_overlays)
    asset_context = {
        "version": target_version,
        "project_version": target_version,
    }
    installed["assets"].extend(
        _apply_profile_assets(
            package_root,
            template_root,
            target_root,
            active_profiles,
            profile_manifests,
            set(disabled_policies),
            asset_context=asset_context,
        )
    )

    managed_docs = _configured_managed_docs(target_root, include_agents=False)
    for doc_name in managed_docs:
        title_override = repo_name if doc_name == "README.md" else None
        doc_path = target_root / doc_name
        existed = doc_path.exists()
        _ensure_doc_from_descriptor(
            target_root,
            doc_name,
            last_updated=last_updated,
            version=target_version,
            title=title_override,
            template_root=template_root,
            force=_doc_force(doc_name),
        )
        _track_managed_doc(doc_name, existed)
    if devcovenant_version:
        _update_devcovenant_version(
            target_root / "devcovenant/README.md", devcovenant_version
        )

    if not args.skip_policy_refresh:
        refresh_policies(
            agents_path,
            schema_path,
        )
    options = _build_manifest_options(
        docs_mode=docs_mode,
        config_mode=config_mode,
        license_mode=license_mode,
        version_mode=version_mode,
        target_version=target_version,
        pyproject_mode=pyproject_mode,
        ci_mode=ci_mode,
        docs_include=docs_include,
        docs_exclude=docs_exclude,
        policy_mode=policy_mode,
        preserve_custom=preserve_custom,
        devcov_core_include=include_core,
        disabled_policies=disabled_policies,
        auto_uninstall=bool(args.auto_uninstall),
    )
    _finalize_manifest(
        target_root,
        options,
        installed,
        doc_blocks,
        manifest_mode,
        active_profiles,
        profile_registry,
    )

    if not skip_refresh:
        from devcovenant.core import refresh_all as refresh_all_module

        if args.skip_policy_refresh:
            refresh_all_module.refresh_registry(
                target_root, schema_path=schema_path
            )
            refreshed_registry = profiles.build_profile_registry(target_root)
            refresh_all_module.refresh_config(
                target_root, refreshed_registry, include_core
            )
            refresh_all_module.refresh_gitignore(target_root)
            refresh_all_module.refresh_pre_commit_config(
                target_root, profile_registry=refreshed_registry
            )
        else:
            refresh_all_module.refresh_all(
                target_root,
                backup_existing=bool(getattr(args, "backup_existing", False)),
            )

    backups = _backup_log()
    if backups:
        print("Backed up files before overwrite/merge:")
        for entry in backups:
            print(f"- {entry}")


if __name__ == "__main__":
    main()
