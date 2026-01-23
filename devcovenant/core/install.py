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

import yaml

from devcovenant.core import cli_options
from devcovenant.core import manifest as manifest_module
from devcovenant.core import uninstall
from devcovenant.core.parser import PolicyParser
from devcovenant.core.profiles import resolve_profile_suffixes

DEV_COVENANT_DIR = "devcovenant"
CORE_PATHS = [
    DEV_COVENANT_DIR,
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]

CONFIG_PATHS = [
    ".pre-commit-config.yaml",
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
    "VERSION",
    "LICENSE",
    "pyproject.toml",
]

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
LICENSE_TEMPLATE = "LICENSE_GPL-3.0.txt"
TEMPLATE_ROOT_NAME = "templates"
TEMPLATE_GLOBAL_DIR = "global"
TEMPLATE_PROFILES_DIR = "profiles"
TEMPLATE_POLICIES_DIR = "policies"
PROFILE_CATALOG_FILE = "profile_catalog.yaml"
POLICY_ASSETS_FILE = "policy_assets.yaml"
DEFAULT_BOOTSTRAP_VERSION = "0.0.1"
DEFAULT_PROFILE_SELECTION = ["python", "docs", "data"]
GITIGNORE_USER_BEGIN = "# --- User entries (preserved) ---"
GITIGNORE_USER_END = "# --- End user entries ---"
DEFAULT_PRESERVE_PATHS = [
    "custom/policy_scripts",
    "custom/fixers",
    "config.yaml",
]

_CORE_CONFIG_INCLUDE_KEY = "devcov_core_include:"
_CORE_CONFIG_PATHS_KEY = "devcov_core_paths:"
_DEFAULT_CORE_PATHS = [
    "devcovenant/core",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]

LEGACY_ROOT_PATHS = [
    "devcov_check.py",
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

_BACKUP_ROOT: Path | None = None
_BACKUP_LOG: list[str] = []
_BACKUP_ORIGINALS: set[Path] = set()


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


def _load_profile_catalog(package_root: Path, target_root: Path) -> dict:
    """Load the profile catalog from core and custom sources."""
    catalog: dict[str, dict] = {}
    core_path = package_root / "core" / PROFILE_CATALOG_FILE
    core_data = _load_yaml(core_path)
    for name, meta in (core_data.get("profiles") or {}).items():
        catalog[_normalize_profile_name(name)] = dict(meta or {})
    custom_path = package_root / "custom" / PROFILE_CATALOG_FILE
    custom_data = _load_yaml(custom_path)
    for name, meta in (custom_data.get("profiles") or {}).items():
        catalog[_normalize_profile_name(name)] = dict(meta or {})
    custom_dir = (
        target_root
        / DEV_COVENANT_DIR
        / "custom"
        / "templates"
        / TEMPLATE_PROFILES_DIR
    )
    if custom_dir.exists():
        for entry in custom_dir.iterdir():
            if entry.is_dir():
                catalog.setdefault(_normalize_profile_name(entry.name), {})
    return catalog


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
    return sorted(set(normalized))


def _flatten_profile_names(catalog: dict) -> list[str]:
    """Return a sorted list of catalog profile names."""
    return sorted(name for name in catalog.keys() if name)


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


def _prompt_profiles(catalog: dict) -> list[str]:
    """Prompt for profile selection from the catalog."""
    profiles = _flatten_profile_names(catalog)
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
    """Resolve a template path with custom overrides."""
    candidates: list[Path] = []
    custom_root = (
        target_root / DEV_COVENANT_DIR / "custom" / TEMPLATE_ROOT_NAME
    )
    rel_path = rel_path.lstrip("/")
    prefixed = (
        rel_path.startswith(f"{TEMPLATE_GLOBAL_DIR}/")
        or rel_path.startswith(f"{TEMPLATE_PROFILES_DIR}/")
        or rel_path.startswith(f"{TEMPLATE_POLICIES_DIR}/")
    )
    if prefixed:
        prefixed_candidates = [
            custom_root / rel_path,
            core_root / rel_path,
        ]
        for candidate in prefixed_candidates:
            if candidate.exists():
                return candidate
        return target_root / rel_path
    if policy_id:
        candidates.append(
            custom_root / TEMPLATE_POLICIES_DIR / policy_id / rel_path
        )
    if profile:
        candidates.append(
            custom_root / TEMPLATE_PROFILES_DIR / profile / rel_path
        )
    candidates.append(custom_root / TEMPLATE_GLOBAL_DIR / rel_path)
    if policy_id:
        candidates.append(
            core_root / TEMPLATE_POLICIES_DIR / policy_id / rel_path
        )
    if profile:
        candidates.append(
            core_root / TEMPLATE_PROFILES_DIR / profile / rel_path
        )
    candidates.append(core_root / TEMPLATE_GLOBAL_DIR / rel_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return target_root / rel_path


def _parse_profile_scopes(raw: str | None) -> list[str]:
    """Parse profile_scopes metadata into a normalized list."""
    if not raw:
        return ["global"]
    scopes = [entry.strip() for entry in raw.split(",")]
    return [entry for entry in scopes if entry]


def _load_policy_metadata(agents_path: Path) -> dict[str, dict[str, object]]:
    """Return policy apply flags and profile scopes from AGENTS.md."""
    if not agents_path.exists():
        return {}
    parser = PolicyParser(agents_path)
    metadata: dict[str, dict[str, object]] = {}
    for policy in parser.parse_agents_md():
        if not policy.policy_id:
            continue
        scopes = _parse_profile_scopes(
            policy.raw_metadata.get("profile_scopes")
        )
        metadata[policy.policy_id] = {
            "apply": policy.apply,
            "profile_scopes": scopes,
        }
    return metadata


def _policy_profile_match(
    scopes: list[str], active_profiles: list[str]
) -> bool:
    """Return True if the policy scopes match any active profile."""
    if "global" in scopes:
        return True
    active = set(active_profiles)
    return any(scope in active for scope in scopes)


def _load_policy_assets(package_root: Path, target_root: Path) -> dict:
    """Load policy asset mappings from core/custom definitions."""
    assets: dict = {"global": [], "profiles": {}, "policies": {}}
    core_path = package_root / "core" / POLICY_ASSETS_FILE
    core_data = _load_yaml(core_path)
    for key in assets:
        if key in core_data:
            assets[key] = core_data[key]
    custom_path = package_root / "custom" / POLICY_ASSETS_FILE
    custom_data = _load_yaml(custom_path)
    for key, asset_value in (custom_data or {}).items():
        if key in {"global", "profiles", "policies"} and asset_value:
            assets[key] = asset_value
    target_custom = (
        target_root / DEV_COVENANT_DIR / "custom" / POLICY_ASSETS_FILE
    )
    if target_custom.exists():
        target_data = _load_yaml(target_custom)
        for key, asset_value in (target_data or {}).items():
            if key in {"global", "profiles", "policies"} and asset_value:
                assets[key] = asset_value
    return assets


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


def _apply_asset(
    template_path: Path,
    target_path: Path,
    mode: str,
) -> bool:
    """Apply a template asset to the target path."""
    if not template_path.exists():
        return False
    mode_text = (mode or "replace").lower()
    if target_path.exists():
        if mode_text == "skip":
            return False
        if mode_text == "merge":
            existing = target_path.read_text(encoding="utf-8")
            incoming = template_path.read_text(encoding="utf-8")
            merged = _merge_text_assets(existing, incoming)
            if merged != existing:
                _rename_existing_file(target_path)
                target_path.write_text(merged, encoding="utf-8")
                return True
            return False
        _rename_existing_file(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, target_path)
    return True


def _apply_profile_assets(
    package_root: Path,
    template_root: Path,
    target_root: Path,
    active_profiles: list[str],
    disabled_policies: set[str],
    policy_metadata: dict[str, dict[str, object]],
) -> list[str]:
    """Install profile and policy assets based on selection."""
    assets = _load_policy_assets(package_root, target_root)
    installed: list[str] = []
    for entry in _clean_asset_entries(assets.get("global", [])):
        template_path = _resolve_template_path(
            target_root,
            template_root,
            entry.get("template", ""),
        )
        target_path = target_root / entry.get("path", "")
        if _apply_asset(
            template_path, target_path, entry.get("mode", "replace")
        ):
            installed.append(str(target_path.relative_to(target_root)))
    profile_assets = assets.get("profiles", {}) or {}
    for profile in active_profiles:
        for entry in _clean_asset_entries(profile_assets.get(profile, [])):
            template_path = _resolve_template_path(
                target_root,
                template_root,
                entry.get("template", ""),
                profile=profile,
            )
            target_path = target_root / entry.get("path", "")
            if _apply_asset(
                template_path, target_path, entry.get("mode", "replace")
            ):
                installed.append(str(target_path.relative_to(target_root)))
    policy_assets = assets.get("policies", {}) or {}
    for policy_id, entries in policy_assets.items():
        if policy_id in disabled_policies:
            continue
        policy_info = policy_metadata.get(policy_id)
        if policy_info and not policy_info.get("apply", True):
            continue
        scopes = policy_info.get("profile_scopes") if policy_info else None
        if scopes and not _policy_profile_match(scopes, active_profiles):
            continue
        for entry in _clean_asset_entries(entries):
            template_path = _resolve_template_path(
                target_root,
                template_root,
                entry.get("template", ""),
                policy_id=policy_id,
            )
            target_path = target_root / entry.get("path", "")
            if _apply_asset(
                template_path, target_path, entry.get("mode", "replace")
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


def _render_gitignore(user_text: str) -> str:
    """Render a universal gitignore and append preserved user entries."""
    base_lines = [
        "# DevCovenant standard ignores",
        "",
        "# OS artifacts",
        ".DS_Store",
        ".AppleDouble",
        ".LSOverride",
        "Thumbs.db",
        "Desktop.ini",
        "ehthumbs.db",
        "Icon?",
        "*.lnk",
        "",
        "# Editor settings",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*.swn",
        "*.tmp",
        "*.bak",
        "",
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".tox/",
        ".nox/",
        ".venv/",
        "venv/",
        ".env",
        ".env.*",
        "!.env.example",
        ".coverage",
        ".coverage.*",
        "htmlcov/",
        "dist/",
        "build/",
        "*.egg-info/",
        ".eggs/",
        "",
        "# Node",
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "pnpm-debug.log*",
        "",
        "# Go",
        "bin/",
        "pkg/",
        "",
        "# Rust",
        "target/",
        "",
        "# Logs",
        "*.log",
        "",
        "# Misc",
        ".cache/",
        "tmp/",
        "temp/",
    ]
    base_text = "\n".join(base_lines).rstrip() + "\n"
    user_block = _extract_user_gitignore(user_text)
    return (
        f"{base_text}\n{GITIGNORE_USER_BEGIN}\n{user_block}\n"
        f"{GITIGNORE_USER_END}\n"
    )


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
    lines.extend(_build_doc_metadata_lines(doc_id, doc_type))
    if extra_lines:
        lines.append("")
        lines.extend(extra_lines)
    lines.append(BLOCK_END)
    return "\n".join(lines)


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
            "  devcovenant/core/policy_scripts/",
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
                "1. `python3 tools/run_pre_commit.py --phase start`",
                "2. `python3 tools/run_tests.py`",
                "3. `python3 tools/run_pre_commit.py --phase end`",
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


def _format_profile_list(active_profiles: list[str]) -> list[str]:
    """Return a normalized profile list for config storage."""
    if not active_profiles:
        return ["__none__"]
    return list(active_profiles)


def _format_profile_block(
    active_profiles: list[str],
    profile_catalog: dict[str, dict],
) -> list[str]:
    """Return the profiles block for config.yaml."""
    profiles = _format_profile_list(active_profiles)
    suffixes = resolve_profile_suffixes(profile_catalog, active_profiles)
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
    for profile in profiles:
        block.append(f"    - {profile}")
    block.append("  generated:")
    block.append("    file_suffixes:")
    for suffix in cleaned:
        block.append(f"      - {suffix}")
    return block


def _update_profile_config_text(
    text: str,
    active_profiles: list[str],
    profile_catalog: dict[str, dict],
) -> tuple[str, bool]:
    """Update profile selection inside config.yaml text."""
    lines = text.splitlines()
    profile_block = _format_profile_block(active_profiles, profile_catalog)
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


def _apply_profile_config(
    target_root: Path,
    active_profiles: list[str],
    profile_catalog: dict[str, dict],
) -> bool:
    """Ensure profile selection is recorded in config.yaml."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_profile_config_text(
        text, active_profiles, profile_catalog
    )
    if not changed:
        return False
    _rename_existing_file(config_path)
    config_path.write_text(updated, encoding="utf-8")
    return True


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
            "  devcovenant/core/policy_scripts/",
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


def _extract_policy_id(metadata: str) -> str:
    """Return the policy id from a metadata block."""
    for line in metadata.splitlines():
        stripped = line.strip()
        if stripped.startswith("id:"):
            return stripped.split(":", 1)[1].strip()


def _apply_policy_disables(
    agents_path: Path, disable_ids: list[str]
) -> list[str]:
    """Disable policies by setting apply: false in AGENTS.md."""
    if not disable_ids or not agents_path.exists():
        return []
    disable_set = {
        policy_id.strip() for policy_id in disable_ids if policy_id.strip()
    }
    if not disable_set:
        return []
    text = agents_path.read_text(encoding="utf-8")
    policy_pattern = re.compile(
        r"(##\s+Policy:\s+[^\n]+\n\n```policy-def\n)(.*?)(\n```\n\n)",
        re.DOTALL,
    )
    disabled: list[str] = []
    changed = False

    def _replace(match: re.Match[str]) -> str:
        """Apply the disable list to matching policy metadata."""
        nonlocal changed
        metadata = match.group(2)
        policy_id = _extract_policy_id(metadata)
        if policy_id not in disable_set:
            return match.group(0)
        keys, values = _parse_metadata_block(metadata)
        _ensure_key(keys, values, "apply")
        values["apply"] = ["false"]
        disabled.append(policy_id)
        changed = True
        rendered = _render_metadata_block(keys, values)
        return match.group(1) + rendered + match.group(3)

    updated = policy_pattern.sub(_replace, text)
    if changed:
        agents_path.write_text(updated, encoding="utf-8")
    missing = sorted(disable_set - set(disabled))
    if missing:
        missing_list = ", ".join(missing)
        print(f"Warning: policy ids not found for disable: {missing_list}")
    return disabled


def _extract_policy_sections(text: str) -> list[tuple[str, str]]:
    """Return policy ids with their full section text."""
    policy_pattern = re.compile(
        r"(##\s+Policy:\s+[^\n]+\n\n```policy-def\n(.*?)\n```\n\n"
        r".*?)(?=\n---\n|\n##|\Z)",
        re.DOTALL,
    )
    sections: list[tuple[str, str]] = []
    for match in policy_pattern.finditer(text):
        metadata = match.group(2)
        policy_id = ""
        for line in metadata.splitlines():
            stripped = line.strip()
            if stripped.startswith("id:"):
                policy_id = stripped.split(":", 1)[1].strip()
                break
        sections.append((policy_id, match.group(1).rstrip()))
    return sections


def _append_missing_policies(
    agents_path: Path, template_text: str
) -> list[str]:
    """Append missing policy sections from the template."""
    current = agents_path.read_text(encoding="utf-8")
    existing = _extract_policy_sections(current)
    existing_ids = {policy_id for policy_id, _section in existing if policy_id}
    template_sections = _extract_policy_sections(template_text)
    missing_sections = [
        section
        for policy_id, section in template_sections
        if policy_id and policy_id not in existing_ids
    ]
    if not missing_sections:
        return []
    tail = current.rstrip()
    separator = "\n\n---\n\n" if existing else "\n\n"
    tail = tail + separator + "\n\n---\n\n".join(missing_sections) + "\n"
    _rename_existing_file(agents_path)
    agents_path.write_text(tail, encoding="utf-8")
    return [
        policy_id
        for policy_id, _section in template_sections
        if policy_id and policy_id not in existing_ids
    ]


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

    disable_policies = _parse_policy_ids(args.disable_policy)

    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parent
    template_root = package_root / "core" / TEMPLATE_ROOT_NAME
    target_root = Path(args.target).resolve()
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
        auto_uninstall = args.auto_uninstall
        if not auto_uninstall and sys.stdin.isatty():
            auto_uninstall = _prompt_yes_no(
                "DevCovenant artifacts detected. Run uninstall first?",
                default=False,
            )
        if auto_uninstall:
            uninstall.main(["--target", str(target_root)])
            has_existing = False
            mode = "empty"
        else:
            raise SystemExit(
                "DevCovenant install detected. Use `devcovenant update` to "
                "refresh an existing repo, or `devcovenant uninstall` "
                "before a "
                "fresh install. Use --auto-uninstall to proceed "
                "automatically."
            )

    if args.allow_existing:
        mode = "existing"

    docs_mode = args.docs_mode
    config_mode = args.config_mode
    metadata_mode = args.metadata_mode
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

    spec_path = target_root / "SPEC.md"
    plan_path = target_root / "PLAN.md"
    include_spec = bool(args.include_spec) or spec_path.exists()
    include_plan = bool(args.include_plan) or plan_path.exists()
    if docs_include:
        include_spec = include_spec or ("SPEC" in docs_include)
        include_plan = include_plan or ("PLAN" in docs_include)

    required_docs = set(_DOC_NAME_MAP.keys())
    if not include_spec:
        required_docs.discard("SPEC")
    if not include_plan:
        required_docs.discard("PLAN")

    always_overwrite_docs = set()
    if mode != "existing":
        always_overwrite_docs = {"CHANGELOG", "CONTRIBUTING"}

    overwrite_targets = (
        set(docs_include) if docs_include is not None else set(required_docs)
    )
    overwrite_targets |= always_overwrite_docs
    overwrite_targets -= docs_exclude
    docs_exclude -= always_overwrite_docs
    if not include_spec:
        overwrite_targets.discard("SPEC")
    if not include_plan:
        overwrite_targets.discard("PLAN")

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
    if metadata_mode is None:
        metadata_mode = "overwrite" if mode == "empty" else "preserve"

    def _resolve_override(override_value: str) -> str:
        """Return the resolved metadata mode for a CLI override."""
        return metadata_mode if override_value == "inherit" else override_value

    license_mode = _resolve_override(args.license_mode)
    version_mode = _resolve_override(args.version_mode)
    pyproject_mode = _resolve_override(args.pyproject_mode)
    ci_mode = config_mode if args.ci_mode == "inherit" else args.ci_mode

    preserve_custom = args.preserve_custom
    if preserve_custom is None:
        preserve_custom = mode == "existing"

    last_updated = _utc_today()
    repo_name = target_root.name

    source_version_path = _resolve_source_path(
        target_root, template_root, "VERSION"
    )
    devcovenant_version = None
    if source_version_path.exists():
        devcovenant_version = source_version_path.read_text(
            encoding="utf-8"
        ).strip()
    else:
        devcovenant_version = "0.0.0"

    version_path = target_root / "VERSION"
    existing_version = None
    if version_path.exists():
        existing_version = version_path.read_text(encoding="utf-8").strip()

    requested_version = None
    if args.version_value:
        requested_version = _normalize_version(args.version_value)

    pyproject_version = _read_pyproject_version(target_root / "pyproject.toml")
    if pyproject_version:
        try:
            pyproject_version = _normalize_version(pyproject_version)
        except ValueError:
            pyproject_version = None

    detected_version = existing_version or pyproject_version
    if requested_version:
        detected_version = requested_version
    if not detected_version:
        if sys.stdin.isatty():
            detected_version = _prompt_version()
        if not detected_version:
            detected_version = DEFAULT_BOOTSTRAP_VERSION

    if version_mode == "preserve" and existing_version:
        target_version = existing_version
    else:
        target_version = detected_version

    profile_catalog = _load_profile_catalog(package_root, target_root)
    if mode == "existing":
        active_profiles = _load_active_profiles(target_root)
        if not active_profiles:
            active_profiles = _prompt_profiles(profile_catalog)
    else:
        active_profiles = _prompt_profiles(profile_catalog)

    installed: dict[str, list[str]] = {
        "core": [],
        "config": [],
        "docs": [],
        "assets": [],
    }
    doc_blocks: list[str] = []

    core_files = [path for path in CORE_PATHS if path != DEV_COVENANT_DIR]
    core_sources = {
        path: _resolve_source_path(target_root, template_root, path)
        for path in core_files
    }
    installed["core"].extend(
        _install_devcovenant_dir(
            repo_root,
            target_root,
            DEFAULT_PRESERVE_PATHS if preserve_custom else [],
            preserve_existing=preserve_custom,
        )
    )
    installed["core"].extend(
        _install_paths(
            repo_root,
            target_root,
            core_files,
            skip_existing=False,
            source_overrides=core_sources,
        )
    )

    if mode == "existing":
        _remove_legacy_paths(target_root, LEGACY_ROOT_PATHS)

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
    gitignore_text = _render_gitignore(existing_gitignore)
    if not gitignore_path.exists():
        installed["config"].append(".gitignore")
    gitignore_path.parent.mkdir(parents=True, exist_ok=True)
    if not gitignore_path.exists() or existing_gitignore != gitignore_text:
        if gitignore_path.exists():
            _rename_existing_file(gitignore_path)
        gitignore_path.write_text(gitignore_text, encoding="utf-8")

    include_core = target_root == repo_root
    _apply_core_config(target_root, include_core)
    _apply_profile_config(target_root, active_profiles, profile_catalog)

    version_existed = version_path.exists()
    if version_mode != "skip" and (
        version_mode == "overwrite" or not version_existed
    ):
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        if not version_existed:
            installed["docs"].append("VERSION")

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

        agents_template = _resolve_source_path(
            target_root, template_root, "AGENTS.md"
        )
    agents_existed = agents_path.exists()
    agents_text = ""
    if agents_template.exists():
        agents_text = agents_template.read_text(encoding="utf-8")
    if not agents_existed or policy_mode == "overwrite":
        if agents_text:
            agents_path.write_text(agents_text, encoding="utf-8")
            if not agents_existed:
                installed["docs"].append("AGENTS.md")
            _apply_standard_header(agents_path, last_updated, target_version)
            if existing_agents_text:
                _preserve_editable_section(agents_path, existing_agents_text)
    else:
        _apply_standard_header(agents_path, last_updated, target_version)
        if agents_text:
            _sync_blocks_from_template(agents_path, agents_text)
            if policy_mode == "append-missing":
                _append_missing_policies(agents_path, agents_text)

    disabled_policies = _apply_policy_disables(agents_path, disable_policies)
    policy_metadata = _load_policy_metadata(agents_path)
    installed["assets"].extend(
        _apply_profile_assets(
            package_root,
            template_root,
            target_root,
            active_profiles,
            set(disabled_policies),
            policy_metadata,
        )
    )

    readme_path = target_root / "README.md"
    if not readme_path.exists():
        base_readme = (
            f"# {repo_name}\n\n"
            "Replace this README content with a project-specific overview.\n"
        )
        base_readme = _ensure_standard_header(
            base_readme, last_updated, target_version, title=repo_name
        )
        readme_path.write_text(base_readme, encoding="utf-8")
        installed["docs"].append("README.md")

    readme_text = readme_path.read_text(encoding="utf-8")
    scan_text = _strip_devcov_block(readme_text)
    has_toc = _has_heading(scan_text, "Table of Contents")
    has_overview = _has_heading(scan_text, "Overview")
    has_workflow = _has_heading(scan_text, "Workflow")
    has_devcovenant = _has_heading(scan_text, "DevCovenant")
    readme_block = _build_readme_block(
        has_overview, has_workflow, has_toc, has_devcovenant
    )
    updated_readme = _ensure_standard_header(
        readme_text, last_updated, target_version, title=repo_name
    )
    readme_path.write_text(updated_readme, encoding="utf-8")
    _inject_block(readme_path, readme_block)
    if BLOCK_BEGIN in readme_path.read_text(encoding="utf-8"):
        doc_blocks.append("README.md")

    if include_spec:
        spec_path = target_root / "SPEC.md"
        if spec_path.exists() and not _should_overwrite("SPEC"):
            _apply_standard_header(spec_path, last_updated, target_version)
            _ensure_doc_block(spec_path, "SPEC", "specification")
        else:
            if spec_path.exists():
                _rename_existing_file(spec_path)
            spec_path.write_text(
                _render_spec_template(target_version, last_updated),
                encoding="utf-8",
            )
            installed["docs"].append("SPEC.md")
        if BLOCK_BEGIN in spec_path.read_text(encoding="utf-8"):
            doc_blocks.append("SPEC.md")

    if include_plan:
        plan_path = target_root / "PLAN.md"
        if plan_path.exists() and not _should_overwrite("PLAN"):
            _apply_standard_header(plan_path, last_updated, target_version)
            _ensure_doc_block(plan_path, "PLAN", "plan")
        else:
            if plan_path.exists():
                _rename_existing_file(plan_path)
            plan_path.write_text(
                _render_plan_template(target_version, last_updated),
                encoding="utf-8",
            )
            installed["docs"].append("PLAN.md")
        if BLOCK_BEGIN in plan_path.read_text(encoding="utf-8"):
            doc_blocks.append("PLAN.md")

    changelog_path = target_root / "CHANGELOG.md"
    if not changelog_path.exists():
        changelog_path.write_text(
            _render_changelog_template(target_version, last_updated),
            encoding="utf-8",
        )
        installed["docs"].append("CHANGELOG.md")
    elif _should_overwrite("CHANGELOG"):
        _rename_existing_file(changelog_path)
        changelog_path.write_text(
            _render_changelog_template(target_version, last_updated),
            encoding="utf-8",
        )
        installed["docs"].append("CHANGELOG.md")
    else:
        _ensure_changelog_block(changelog_path, last_updated, target_version)
    if BLOCK_BEGIN in changelog_path.read_text(encoding="utf-8"):
        doc_blocks.append("CHANGELOG.md")

    contributing_path = target_root / "CONTRIBUTING.md"
    contributing_template = _resolve_source_path(
        target_root, template_root, "CONTRIBUTING.md"
    )
    if contributing_template.exists():
        if contributing_path.exists() and not _should_overwrite(
            "CONTRIBUTING"
        ):
            _apply_standard_header(
                contributing_path, last_updated, target_version
            )
            template_block = _extract_block(
                contributing_template.read_text(encoding="utf-8")
            )
            _sync_block(contributing_path, template_block)
        else:
            if contributing_path.exists():
                _rename_existing_file(contributing_path)
            contributing_text = contributing_template.read_text(
                encoding="utf-8"
            )
            contributing_text = _ensure_standard_header(
                contributing_text, last_updated, target_version
            )
            contributing_path.write_text(contributing_text, encoding="utf-8")
            installed["docs"].append("CONTRIBUTING.md")
            if (
                BLOCK_BEGIN in contributing_text
                and BLOCK_END in contributing_text
            ):
                doc_blocks.append("CONTRIBUTING.md")

    internal_docs = [
        "devcovenant/README.md",
    ]
    for rel_path in internal_docs:
        _apply_standard_header(
            target_root / rel_path, last_updated, target_version
        )
    if devcovenant_version:
        _update_devcovenant_version(
            target_root / "devcovenant/README.md", devcovenant_version
        )

    manifest = manifest_module.build_manifest(
        options={
            "docs_mode": docs_mode,
            "config_mode": config_mode,
            "metadata_mode": metadata_mode,
            "license_mode": license_mode,
            "version_mode": version_mode,
            "target_version": target_version,
            "pyproject_mode": pyproject_mode,
            "ci_mode": ci_mode,
            "docs_include": sorted(docs_include or []),
            "docs_exclude": sorted(docs_exclude or []),
            "policy_mode": policy_mode,
            "include_spec": include_spec,
            "include_plan": include_plan,
            "preserve_custom": preserve_custom,
            "devcov_core_include": include_core,
            "disable_policies": sorted(disabled_policies),
            "auto_uninstall": bool(args.auto_uninstall),
        },
        installed=installed,
        doc_blocks=doc_blocks,
        mode="update" if mode == "existing" else "install",
    )
    manifest["profiles"]["active"] = list(active_profiles)
    manifest["profiles"]["catalog"] = sorted(profile_catalog.keys())
    manifest_module.write_manifest(target_root, manifest)

    backups = _backup_log()
    if backups:
        print("Backed up files before overwrite/merge:")
        for entry in backups:
            print(f"- {entry}")


if __name__ == "__main__":
    main()
