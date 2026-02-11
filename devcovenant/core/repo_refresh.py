"""Full refresh orchestration for DevCovenant repositories."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

from devcovenant.core import manifest as manifest_module
from devcovenant.core import policy_freeze, profiles
from devcovenant.core.execution import print_step
from devcovenant.core.parser import PolicyDefinition
from devcovenant.core.policy_descriptor import (
    POLICY_BLOCK_RE,
    PolicyDescriptor,
    iter_script_locations,
    load_policy_descriptor,
    parse_metadata_block,
    resolve_script_location,
)
from devcovenant.core.registry import PolicyRegistry
from devcovenant.core.selector_helpers import _normalize_globs

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"

DEFAULT_MANAGED_DOCS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "devcovenant/README.md",
]


def _utc_today() -> str:
    """Return current UTC date."""
    return datetime.now(timezone.utc).date().isoformat()


def _read_version(repo_root: Path) -> str:
    """Read the target DevCovenant version."""
    version_path = repo_root / "devcovenant" / "VERSION"
    if not version_path.exists():
        return "0.0.0"
    version_text = version_path.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0"


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    """Write YAML mapping payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _normalize_doc_name(name: str) -> str:
    """Normalize configured doc names to canonical markdown paths."""
    raw = str(name or "").strip()
    if not raw:
        return ""
    mapping = {
        "AGENTS": "AGENTS.md",
        "README": "README.md",
        "CONTRIBUTING": "CONTRIBUTING.md",
        "SPEC": "SPEC.md",
        "PLAN": "PLAN.md",
        "CHANGELOG": "CHANGELOG.md",
    }
    upper = raw.upper()
    if upper in mapping:
        return mapping[upper]
    if upper.endswith(".MD") and upper[:-3] in mapping:
        return mapping[upper[:-3]]
    return raw


def _managed_docs_from_config(config: dict[str, object]) -> list[str]:
    """Resolve autogen managed docs from config doc_assets."""
    doc_assets = config.get("doc_assets")
    if not isinstance(doc_assets, dict):
        return list(DEFAULT_MANAGED_DOCS)

    raw_autogen = doc_assets.get("autogen")
    raw_user = doc_assets.get("user")

    autogen = []
    if isinstance(raw_autogen, list):
        autogen = [_normalize_doc_name(item) for item in raw_autogen]

    user_docs = set()
    if isinstance(raw_user, list):
        user_docs = {_normalize_doc_name(item) for item in raw_user if item}

    selected = [doc for doc in autogen if doc and doc not in user_docs]
    if not selected:
        selected = list(DEFAULT_MANAGED_DOCS)
    if "AGENTS.md" not in selected:
        selected.insert(0, "AGENTS.md")

    ordered: list[str] = []
    for doc in selected:
        if doc not in ordered:
            ordered.append(doc)
    return ordered


def _descriptor_path(repo_root: Path, doc_name: str) -> Path:
    """Resolve YAML descriptor path for a managed doc."""
    assets_root = (
        repo_root / "devcovenant" / "core" / "profiles" / "global" / "assets"
    )
    doc_path = Path(doc_name)
    if doc_path.parent != Path("."):
        return assets_root / doc_path.with_suffix(".yaml")
    return assets_root / f"{doc_path.stem}.yaml"


def _apply_header_overrides(
    header_lines: list[str],
    *,
    version: str,
    title: str | None = None,
) -> list[str]:
    """Inject standard header fields into descriptor header lines."""
    updated = []
    saw_title = False
    saw_date = False
    saw_version = False

    for line in header_lines:
        stripped = line.strip().lower()
        if title and line.lstrip().startswith("#") and not saw_title:
            updated.append(f"# {title}")
            saw_title = True
            continue
        if stripped.startswith("**last updated:**"):
            updated.append(f"**Last Updated:** {_utc_today()}")
            saw_date = True
            continue
        if stripped.startswith("**version:**"):
            updated.append(f"**Version:** {version}")
            saw_version = True
            continue
        updated.append(line.rstrip())

    if title and not saw_title:
        updated.insert(0, f"# {title}")

    insert_index = 1 if updated and updated[0].startswith("#") else 0
    if not saw_date:
        updated.insert(insert_index, f"**Last Updated:** {_utc_today()}")
        insert_index += 1
    if not saw_version:
        updated.insert(insert_index, f"**Version:** {version}")
    return updated


def _render_doc(repo_root: Path, doc_name: str, version: str) -> str | None:
    """Render managed doc text from YAML descriptor."""
    descriptor = _read_yaml(_descriptor_path(repo_root, doc_name))
    if not descriptor:
        return None

    headers_raw = descriptor.get("header_lines")
    if isinstance(headers_raw, list):
        header_lines = [str(item).rstrip() for item in headers_raw]
    else:
        header_lines = []

    title_override = repo_root.name if doc_name == "README.md" else None
    header_lines = _apply_header_overrides(
        header_lines,
        version=version,
        title=title_override,
    )

    block_body = str(descriptor.get("managed_block", "")).strip("\n")
    managed_block = ""
    if block_body:
        managed_block = "\n".join([BLOCK_BEGIN, block_body, BLOCK_END])

    body_value = descriptor.get("body")
    body_lines = []
    if isinstance(body_value, str):
        body_lines = [line.rstrip() for line in body_value.splitlines()]

    parts = []
    if header_lines:
        parts.append("\n".join(header_lines))
    if managed_block:
        parts.append(managed_block)
    if body_lines:
        parts.append("\n".join(body_lines))
    if not parts:
        return None
    return "\n\n".join(parts).rstrip() + "\n"


def _doc_is_placeholder(text: str) -> bool:
    """Return True for empty or effectively one-line docs."""
    lines = [line for line in text.splitlines() if line.strip()]
    return len(lines) <= 1


def _extract_managed_block(text: str) -> str | None:
    """Extract first managed block from text."""
    if BLOCK_BEGIN not in text or BLOCK_END not in text:
        return None
    start = text.index(BLOCK_BEGIN)
    end = text.index(BLOCK_END, start) + len(BLOCK_END)
    return text[start:end]


def _replace_managed_block(current: str, template: str) -> tuple[str, bool]:
    """Replace current first managed block with template managed block."""
    current_block = _extract_managed_block(current)
    template_block = _extract_managed_block(template)
    if current_block is None or template_block is None:
        return current, False

    start = current.index(BLOCK_BEGIN)
    end = current.index(BLOCK_END, start) + len(BLOCK_END)
    updated = current[:start] + template_block + current[end:]
    return updated, updated != current


def _sync_doc(repo_root: Path, doc_name: str, version: str) -> bool:
    """Synchronize one managed doc from descriptor content."""
    rendered = _render_doc(repo_root, doc_name, version)
    if rendered is None:
        return False

    target = repo_root / doc_name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        return True

    current = target.read_text(encoding="utf-8")
    if _doc_is_placeholder(current):
        target.write_text(rendered, encoding="utf-8")
        return True

    updated, changed = _replace_managed_block(current, rendered)
    if not changed:
        return False

    target.write_text(updated, encoding="utf-8")
    return True


def _active_profiles(config: dict[str, object]) -> list[str]:
    """Resolve active profiles from config, always including global."""
    profiles_block = config.get("profiles")
    if not isinstance(profiles_block, dict):
        return ["global"]

    active = profiles_block.get("active")
    if not isinstance(active, list):
        return ["global"]

    names = [str(item).strip().lower() for item in active if str(item).strip()]
    if "global" not in names:
        names.insert(0, "global")

    ordered = []
    for name in names:
        if name not in ordered:
            ordered.append(name)
    return ordered


def _refresh_profile_registry(
    repo_root: Path, active_profiles: list[str]
) -> dict[str, dict]:
    """Rebuild and persist profile registry."""
    registry = profiles.build_profile_registry(repo_root, active_profiles)
    profiles.write_profile_registry(repo_root, registry)
    return registry


def _refresh_config_generated(
    config_path: Path,
    config: dict[str, object],
    registry: dict[str, dict],
    active_profiles: list[str],
) -> bool:
    """Refresh generated config sections from active profile metadata."""
    if not config:
        return False

    profile_suffixes = profiles.resolve_profile_suffixes(
        registry, active_profiles
    )
    suffixes = sorted({str(item) for item in profile_suffixes if str(item)})

    profiles_block = config.get("profiles")
    if not isinstance(profiles_block, dict):
        profiles_block = {}

    generated = profiles_block.get("generated")
    if not isinstance(generated, dict):
        generated = {}

    changed = False
    if profiles_block.get("active") != active_profiles:
        profiles_block["active"] = active_profiles
        changed = True
    if generated.get("file_suffixes") != suffixes:
        generated["file_suffixes"] = suffixes
        changed = True

    profiles_block["generated"] = generated
    config["profiles"] = profiles_block

    if changed:
        _write_yaml(config_path, config)
    return changed


def refresh_repo(repo_root: Path) -> int:
    """Run full refresh for the repository."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config = _read_yaml(config_path)
    version = _read_version(repo_root)

    _sync_doc(repo_root, "AGENTS.md", version)

    registry_result = refresh_registry(repo_root, skip_freeze=False)
    if registry_result != 0:
        return registry_result

    agents_path = repo_root / "AGENTS.md"
    refresh_policies(agents_path, None, repo_root=repo_root)

    active_profiles = _active_profiles(config)
    profile_registry = _refresh_profile_registry(repo_root, active_profiles)

    if _refresh_config_generated(
        config_path, config, profile_registry, active_profiles
    ):
        print_step("Refreshed config generated profile metadata", "✅")

    docs = _managed_docs_from_config(config)
    synced = [doc for doc in docs if _sync_doc(repo_root, doc, version)]
    if synced:
        print_step(f"Synchronized managed docs: {', '.join(synced)}", "✅")

    manifest_module.ensure_manifest(repo_root)
    return 0


# ---- Inlined from core/refresh_policies.py ----
_POLICIES_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
_POLICIES_END = "<!-- DEVCOV-POLICIES:END -->"

_COMMON_KEYS = [
    "id",
    "status",
    "severity",
    "auto_fix",
    "enforcement",
    "enabled",
    "custom",
    "freeze",
]

_COMMON_DEFAULTS: Dict[str, List[str]] = {
    "severity": ["warning"],
    "auto_fix": ["false"],
    "enforcement": ["active"],
    "enabled": ["true"],
    "custom": ["false"],
    "freeze": ["false"],
    "status": ["active"],
}

_ROLE_SUFFIXES: Tuple[str, ...] = ("globs", "files", "dirs")
_LEGACY_SUFFIXES: Tuple[str, ...] = ("prefixes", "suffixes")
_LEGACY_ROLE_KEY = {
    "guarded_paths": ("guarded", "globs"),
    "user_visible_files": ("user_visible", "files"),
    "user_visible_prefixes": ("user_visible", "dirs"),
    "user_visible_globs": ("user_visible", "globs"),
    "user_visible_dirs": ("user_visible", "dirs"),
    "user_facing_files": ("user_facing", "files"),
    "user_facing_prefixes": ("user_facing", "dirs"),
    "user_facing_globs": ("user_facing", "globs"),
    "user_facing_dirs": ("user_facing", "dirs"),
    "user_facing_suffixes": ("user_facing", "globs"),
    "user_facing_exclude_prefixes": ("user_facing_exclude", "dirs"),
    "user_facing_exclude_globs": ("user_facing_exclude", "globs"),
    "user_facing_exclude_suffixes": ("user_facing_exclude", "globs"),
    "doc_quality_files": ("doc_quality", "files"),
    "doc_quality_globs": ("doc_quality", "globs"),
    "doc_quality_dirs": ("doc_quality", "dirs"),
}

_GROUP_COMMENTS: Dict[int, str] = {}
# Keep policy-defined defaults authoritative; only strip transient keys.
_DERIVED_VALUE_KEYS = {"updated"}
_ORDER_EXCLUDE_KEYS = {"updated"}
_STATUS_OVERRIDE_VALUES = {"deprecated", "fiducial", "new", "deleted"}


@dataclass(frozen=True)
class RefreshResult:
    """Summary of refresh work."""

    changed_policies: Tuple[str, ...]
    skipped_policies: Tuple[str, ...]
    updated: bool


@dataclass
class _PolicyEntry:
    """Track a policy block's key attributes during refresh."""

    policy_id: str
    text: str
    group: int
    changed: bool
    custom: bool


def metadata_value_list(raw_value: object) -> List[str]:
    """Return the metadata value as a list of strings."""
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item)]
    return [str(raw_value)]


@dataclass(frozen=True)
class PolicyControl:
    """Config-driven policy control flags."""

    policy_state: Dict[str, bool]
    freeze_core: set[str]


@dataclass(frozen=True)
class MetadataContext:
    """Resolved metadata context for policy normalization."""

    control: PolicyControl
    profile_overlays: Dict[str, Dict[str, Tuple[List[str], bool]]]
    autogen_overrides: Dict[str, Dict[str, List[str]]]
    user_overrides: Dict[str, Dict[str, List[str]]]


def _normalize_policy_list(raw_value: object | None) -> set[str]:
    """Normalize a config list/string into a set of policy ids."""
    if raw_value is None:
        return set()
    if isinstance(raw_value, str):
        candidate = raw_value.strip()
        return {candidate} if candidate else set()
    if isinstance(raw_value, Iterable):
        normalized: set[str] = set()
        for entry in raw_value:
            token = str(entry or "").strip()
            if token:
                normalized.add(token)
        return normalized
    return set()


def _load_config_payload(repo_root: Path) -> Dict[str, object]:
    """Load config.yaml into a dictionary."""

    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _load_active_profiles(payload: Dict[str, object]) -> List[str]:
    """Return the active profiles from config payload."""

    profiles_block = (
        payload.get("profiles", {}) if isinstance(payload, dict) else {}
    )
    active = (
        profiles_block.get("active", [])
        if isinstance(profiles_block, dict)
        else []
    )
    if isinstance(active, str):
        candidates = [active]
    elif isinstance(active, list):
        candidates = active
    else:
        candidates = [active] if active else []
    normalized: List[str] = []
    for entry in candidates:
        token = str(entry or "").strip().lower()
        if token and token != "__none__":
            normalized.append(token)
    if "global" not in normalized:
        normalized.insert(0, "global")
    return normalized


def _normalize_metadata_values(raw_value: object) -> List[str]:
    """Normalize a metadata value into a list of strings."""

    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text or text == "__none__":
            return []
        return [text]
    if isinstance(raw_value, list):
        cleaned: List[str] = []
        for entry in raw_value:
            token = str(entry or "").strip()
            if token and token != "__none__":
                cleaned.append(token)
        return cleaned
    text = str(raw_value).strip()
    if not text or text == "__none__":
        return []
    return [text]


def _normalize_override_map(
    raw_value: object,
) -> Dict[str, Dict[str, List[str]]]:
    """Normalize a policy override map into list-valued metadata entries."""

    if not isinstance(raw_value, dict):
        return {}
    normalized: Dict[str, Dict[str, List[str]]] = {}
    for policy_id, mapping in raw_value.items():
        if not isinstance(mapping, dict):
            continue
        policy_key = str(policy_id).strip()
        if not policy_key:
            continue
        entries: Dict[str, List[str]] = {}
        for key, metadata_value in mapping.items():
            key_name = str(key).strip()
            if not key_name:
                continue
            entries[key_name] = _normalize_metadata_values(metadata_value)
        if entries:
            normalized[policy_key] = entries
    return normalized


def _merge_override_maps(
    base: Dict[str, Dict[str, List[str]]],
    incoming: Dict[str, Dict[str, List[str]]],
) -> Dict[str, Dict[str, List[str]]]:
    """Merge override maps with incoming values taking precedence."""

    merged = {policy_id: dict(values) for policy_id, values in base.items()}
    for policy_id, overrides in incoming.items():
        current = merged.setdefault(policy_id, {})
        for key, values in overrides.items():
            current[key] = list(values)
    return merged


def _load_metadata_overrides(
    payload: Dict[str, object],
) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, Dict[str, List[str]]]]:
    """Return autogen/user metadata overrides from config payload."""

    autogen = _normalize_override_map(
        payload.get("autogen_metadata_overrides")
    )
    user = _normalize_override_map(payload.get("user_metadata_overrides"))
    legacy = _normalize_override_map(payload.get("policy_overrides"))
    merged_user = _merge_override_maps(legacy, user)
    return autogen, merged_user


def _collect_profile_overlays(
    repo_root: Path, active_profiles: List[str]
) -> Dict[str, Dict[str, Tuple[List[str], bool]]]:
    """Collect policy overlays from the profile registry."""

    registry = profiles.discover_profiles(repo_root)
    overlays: Dict[str, Dict[str, Tuple[List[str], bool]]] = {}
    for profile in active_profiles:
        meta = registry.get(profile)
        if not isinstance(meta, dict):
            continue
        raw_overlays = meta.get("policy_overlays") or {}
        if raw_overlays == "__none__" or not isinstance(raw_overlays, dict):
            continue
        for policy_id, overlay in raw_overlays.items():
            if not isinstance(overlay, dict):
                continue
            policy_key = str(policy_id).strip()
            if not policy_key:
                continue
            policy_map = overlays.setdefault(policy_key, {})
            for key, raw_value in overlay.items():
                key_name = str(key).strip()
                if not key_name:
                    continue
                merge_values = isinstance(raw_value, list)
                values = _normalize_metadata_values(raw_value)
                if merge_values:
                    current_values = policy_map.get(key_name, ([], True))[0]
                    merged = _merge_values(current_values, values)
                    policy_map[key_name] = (merged, True)
                else:
                    policy_map[key_name] = (list(values), False)
    return overlays


def _normalize_policy_state(raw_value: object) -> Dict[str, bool]:
    """Normalize policy_state config into a boolean map."""
    if not isinstance(raw_value, dict):
        return {}
    normalized: Dict[str, bool] = {}
    for policy_id, enabled_value in raw_value.items():
        key = str(policy_id or "").strip()
        if not key:
            continue
        if isinstance(enabled_value, bool):
            normalized[key] = enabled_value
            continue
        token = str(enabled_value).strip().lower()
        if token in {"true", "1", "yes", "y", "on"}:
            normalized[key] = True
        elif token in {"false", "0", "no", "n", "off"}:
            normalized[key] = False
    return normalized


def load_policy_control_config(payload: Dict[str, object]) -> PolicyControl:
    """Load enabled/freeze control values for policies."""

    policy_state = _normalize_policy_state(payload.get("policy_state"))
    freeze_core = _normalize_policy_list(payload.get("freeze_core_policies"))
    return PolicyControl(policy_state, freeze_core)


def build_metadata_context(repo_root: Path) -> MetadataContext:
    """Return the metadata resolution context for a repo."""

    payload = _load_config_payload(repo_root)
    active_profiles = _load_active_profiles(payload)
    profile_overlays = _collect_profile_overlays(repo_root, active_profiles)
    autogen_overrides, user_overrides = _load_metadata_overrides(payload)
    control = load_policy_control_config(payload)
    return MetadataContext(
        control=control,
        profile_overlays=profile_overlays,
        autogen_overrides=autogen_overrides,
        user_overrides=user_overrides,
    )


def _ensure_metadata_key(
    order: List[str],
    values: Dict[str, List[str]],
    key: str,
) -> None:
    """Ensure a metadata key exists in the ordered key list."""

    if key not in values:
        values[key] = []
    if key not in order:
        order.append(key)


def apply_policy_control(
    order: List[str],
    values: Dict[str, List[str]],
    policy_id: str,
    control: PolicyControl,
    *,
    core_available: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Apply enabled/force/freeze controls to metadata values."""

    if policy_id in control.policy_state:
        _ensure_metadata_key(order, values, "enabled")
        values["enabled"] = [
            "true" if control.policy_state[policy_id] else "false"
        ]

    if policy_id in control.freeze_core and core_available:
        custom_flag = (
            values.get("custom", ["false"])[0].strip().lower() == "true"
        )
        if not custom_flag:
            _ensure_metadata_key(order, values, "freeze")
            values["freeze"] = ["true"]

    return order, values


def _load_descriptors(
    repo_root: Path, discovered: Dict[str, Dict[str, bool]]
) -> Dict[str, PolicyDescriptor]:
    """Load descriptors for every discovered policy script."""
    descriptors: Dict[str, PolicyDescriptor] = {}
    for policy_id in discovered:
        descriptor = load_policy_descriptor(repo_root, policy_id)
        if descriptor:
            descriptors[policy_id] = descriptor
    return descriptors


def descriptor_metadata_order_values(
    descriptor: PolicyDescriptor,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return the ordered keys and list values from a descriptor."""

    order = list(descriptor.metadata.keys())
    values: Dict[str, List[str]] = {}
    for key in order:
        values[key] = metadata_value_list(descriptor.metadata.get(key))
    return order, values


def _descriptor_text_or_error(
    descriptor: PolicyDescriptor | None,
    policy_id: str,
) -> str:
    """Return canonical descriptor text or raise when missing."""
    if descriptor is None:
        raise ValueError(
            f"Missing policy descriptor for `{policy_id}`."
            " Add a <policy>.yaml file with a non-empty `text` field."
        )
    text = str(descriptor.text or "").strip()
    if not text:
        raise ValueError(
            f"Missing descriptor text for `{policy_id}`."
            " Set the `text` field in the policy descriptor YAML."
        )
    return text


def _render_metadata_block(
    keys: Iterable[str], values: Dict[str, List[str]]
) -> str:
    """Render a policy-def block from ordered keys and values."""
    lines: List[str] = []
    for key in keys:
        entries = values.get(key, [])
        if not entries:
            lines.append(f"{key}:")
            continue
        non_empty = [entry for entry in entries if entry]
        if not non_empty:
            lines.append(f"{key}:")
            continue
        if len(non_empty) == 1:
            lines.append(f"{key}: {non_empty[0]}")
            continue
        lines.append(f"{key}: {non_empty[0]}")
        for entry in non_empty[1:]:
            lines.append(f"  {entry}")
    return "\n".join(lines)


def _split_values(raw_values: Sequence[str]) -> List[str]:
    """Return a flattened list of comma-separated values."""
    items: List[str] = []
    for entry in raw_values:
        for part in entry.split(","):
            token = part.strip()
            if token:
                items.append(token)
    return items


def _dedupe(values: Iterable[str]) -> List[str]:
    """Return unique values while preserving order."""
    seen: set[str] = set()
    ordered: List[str] = []
    for entry in values:
        if entry in seen:
            continue
        seen.add(entry)
        ordered.append(entry)
    return ordered


def _convert_prefixes(prefixes: Iterable[str]) -> List[str]:
    """Convert prefixes into glob patterns."""
    globs: List[str] = []
    for prefix in prefixes:
        cleaned = prefix.strip().strip("/")
        if cleaned:
            globs.append(f"{cleaned}/**")
    return globs


def _convert_suffixes(suffixes: Iterable[str]) -> List[str]:
    """Convert suffixes into glob patterns."""
    globs: List[str] = []
    for suffix in suffixes:
        cleaned = suffix.strip()
        if not cleaned:
            continue
        if cleaned.startswith("."):
            globs.append(f"*{cleaned}")
        else:
            globs.append(f"*.{cleaned}")
    return globs


def _merge_values(existing: List[str], incoming: List[str]) -> List[str]:
    """Merge values with de-duplication, preserving order."""
    return _dedupe(existing + incoming)


def _role_from_key(key: str) -> Tuple[str, str] | None:
    """Return (role, target) for selector-ish metadata keys."""
    if key in _LEGACY_ROLE_KEY:
        return _LEGACY_ROLE_KEY[key]
    for suffix in _ROLE_SUFFIXES:
        marker = f"_{suffix}"
        if key.endswith(marker):
            return key[: -len(marker)], suffix
    for legacy in _LEGACY_SUFFIXES:
        marker = f"_{legacy}"
        if key.endswith(marker):
            return key[: -len(marker)], "globs"
    return None


def _apply_selector_roles(
    order: List[str],
    values: Dict[str, List[str]],
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Insert selector role keys and migrate legacy selector values."""
    roles: List[str] = []
    if "selector_roles" in values:
        roles = _split_values(values["selector_roles"])

    role_values: Dict[str, Dict[str, List[str]]] = {}
    for key, raw_values in values.items():
        if key == "selector_roles":
            continue
        role_info = _role_from_key(key)
        if not role_info:
            continue
        role, target = role_info
        if role not in roles:
            roles.append(role)
        bucket = role_values.setdefault(
            role, {"globs": [], "files": [], "dirs": []}
        )
        items = _split_values(raw_values)
        if key.endswith("_prefixes"):
            items = _convert_prefixes(items)
        elif key.endswith("_suffixes"):
            items = _convert_suffixes(items)
        if key in _LEGACY_ROLE_KEY:
            items = _normalize_globs(items)
        bucket[target] = _merge_values(bucket[target], items)

    if roles and "selector_roles" not in values:
        values["selector_roles"] = [",".join(roles)]
        order.append("selector_roles")

    new_order = list(order)
    insert_at = (
        new_order.index("selector_roles") + 1
        if "selector_roles" in new_order
        else len(new_order)
    )
    for role in roles:
        for suffix in _ROLE_SUFFIXES:
            key = f"{role}_{suffix}"
            if key not in values:
                values[key] = []
            if role in role_values:
                values[key] = _merge_values(
                    values[key], role_values[role][suffix]
                )
            if key not in new_order:
                new_order.insert(insert_at, key)
                insert_at += 1
    return new_order, values


def _apply_overrides_replace(
    values: Dict[str, List[str]],
    overrides: Dict[str, List[str]],
) -> None:
    """Apply override values by replacing existing entries."""

    for key, override_values in overrides.items():
        values[key] = list(override_values)


def _apply_profile_overlays(
    values: Dict[str, List[str]],
    overlays: Dict[str, Tuple[List[str], bool]],
) -> None:
    """Apply profile overlays, merging list values and replacing scalars."""

    for key, (overlay_values, merge_lists) in overlays.items():
        if merge_lists:
            values[key] = _merge_values(values.get(key, []), overlay_values)
        else:
            values[key] = list(overlay_values)


def _status_override_value(
    current_values: Dict[str, List[str]],
) -> List[str] | None:
    """Return a non-default status override when present."""
    for entry in current_values.get("status", []):
        normalized = entry.strip().lower()
        if normalized in _STATUS_OVERRIDE_VALUES:
            return [normalized]
    return None


def _strip_derived_values(values: Dict[str, List[str]]) -> None:
    """Remove derived metadata values before recomputing."""
    for key in _DERIVED_VALUE_KEYS:
        values.pop(key, None)


def _resolve_metadata(
    policy_id: str,
    current_order: List[str],
    current_values: Dict[str, List[str]],
    descriptor: PolicyDescriptor | None,
    context: MetadataContext,
    *,
    core_available: bool = False,
    custom_policy: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Resolve metadata using defaults, overlays, and config overrides."""

    status_override = _status_override_value(current_values)

    if descriptor:
        base_order, base_values = descriptor_metadata_order_values(descriptor)
        base_order = [
            key for key in base_order if key not in _ORDER_EXCLUDE_KEYS
        ]
        values = {key: list(entries) for key, entries in base_values.items()}
    else:
        base_order = [
            key for key in current_order if key not in _ORDER_EXCLUDE_KEYS
        ]
        values = {
            key: list(entries) for key, entries in current_values.items()
        }

    if not descriptor:
        for key in current_order:
            if key in _ORDER_EXCLUDE_KEYS:
                continue
            values.setdefault(key, list(current_values.get(key, [])))

    overlays = context.profile_overlays.get(policy_id, {})
    _apply_profile_overlays(values, overlays)

    autogen_overrides = context.autogen_overrides.get(policy_id, {})
    _apply_overrides_replace(values, autogen_overrides)

    user_overrides = context.user_overrides.get(policy_id, {})
    _apply_overrides_replace(values, user_overrides)

    _strip_derived_values(values)

    ordered_keys: List[str] = []
    for key in _COMMON_KEYS:
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in base_order:
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in overlays.keys():
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in autogen_overrides.keys():
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in user_overrides.keys():
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    if not descriptor:
        for key in current_order:
            if key in _ORDER_EXCLUDE_KEYS:
                continue
            _ensure_metadata_key(ordered_keys, values, key)

    values["id"] = [policy_id]
    if status_override:
        values["status"] = list(status_override)
    if custom_policy:
        values["custom"] = ["true"]

    for key in ordered_keys:
        current = values.get(key, [])
        if current:
            values[key] = _dedupe(list(current))
            continue
        if key in _COMMON_DEFAULTS:
            values[key] = _dedupe(list(_COMMON_DEFAULTS[key]))
        else:
            values[key] = []

    ordered_keys, values = apply_policy_control(
        ordered_keys,
        values,
        policy_id,
        context.control,
        core_available=core_available,
    )

    return _apply_selector_roles(ordered_keys, values)


def resolve_policy_metadata_map(
    policy_id: str,
    current_order: List[str],
    current_values: Dict[str, List[str]],
    descriptor: PolicyDescriptor | None,
    context: MetadataContext,
    *,
    core_available: bool = False,
    custom_policy: bool = False,
) -> Tuple[List[str], Dict[str, str]]:
    """Return the resolved metadata order and string map for a policy."""

    order, values = _resolve_metadata(
        policy_id,
        current_order,
        current_values,
        descriptor,
        context,
        core_available=core_available,
        custom_policy=custom_policy,
    )
    resolved: Dict[str, str] = {}
    for key in order:
        entries = values.get(key, [])
        resolved[key] = ", ".join(entry for entry in entries if entry)
    return order, resolved


def _assemble_sections(entries: List[_PolicyEntry]) -> str:
    """Build a policy block ordered alphabetically."""
    if not entries:
        return ""

    sorted_entries = sorted(entries, key=lambda item: item.policy_id)
    sections_text: List[str] = []
    for idx, entry in enumerate(sorted_entries):
        if idx > 0:
            sections_text.append("\n\n---\n\n")
        sections_text.append(entry.text)
    final = "".join(sections_text)
    if not final.endswith("\n"):
        final += "\n"
    return final


def _locate_policy_block(text: str) -> Tuple[int, int, str]:
    """Return the start/end spans and content of the policy block."""
    try:
        start = text.index(_POLICIES_BEGIN)
        end = text.index(_POLICIES_END, start + len(_POLICIES_BEGIN))
    except ValueError:
        raise ValueError("Policy block markers not found in AGENTS.md")
    block_start = start + len(_POLICIES_BEGIN)
    block_text = text[block_start:end]
    return block_start, end, block_text


def _ensure_policy_block_scaffold(
    agents_path: Path, content: str
) -> Tuple[str, bool]:
    """Ensure AGENTS has exactly one policy marker block scaffold."""
    has_begin = _POLICIES_BEGIN in content
    has_end = _POLICIES_END in content
    if has_begin and has_end:
        return content, False

    stripped = (
        content.replace(_POLICIES_BEGIN, "")
        .replace(_POLICIES_END, "")
        .rstrip()
    )
    scaffold = f"{_POLICIES_BEGIN}\n{_POLICIES_END}\n"
    rebuilt = f"{stripped}\n\n{scaffold}"
    agents_path.write_text(rebuilt, encoding="utf-8")
    return rebuilt, True


def _metadata_from_registry(
    policy_id: str,
    metadata_map: object,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered metadata keys/values sourced from registry entries."""
    if not isinstance(metadata_map, dict):
        return ["id"], {"id": [policy_id]}

    order: List[str] = []
    values: Dict[str, List[str]] = {}
    for key, raw_value in metadata_map.items():
        key_name = str(key).strip()
        if not key_name:
            continue
        order.append(key_name)
        if isinstance(raw_value, list):
            normalized = [
                str(item).strip() for item in raw_value if str(item).strip()
            ]
        else:
            normalized = _split_values([str(raw_value)])
        values[key_name] = normalized
    if "id" not in values:
        values["id"] = [policy_id]
    else:
        values["id"] = [policy_id]
    if "id" not in order:
        order.insert(0, "id")
    return order, values


def _section_map(block_text: str) -> Dict[str, str]:
    """Return a map of policy id -> rendered section from a policy block."""
    sections: Dict[str, str] = {}
    for match in POLICY_BLOCK_RE.finditer(block_text):
        heading = match.group(1)
        metadata_block = match.group(2).strip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0] if values.get("id") else ""
        if not policy_id:
            continue
        description = match.group(3).strip()
        rendered = _render_metadata_block(order, values)
        section = f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        sections[policy_id] = section
    return sections


def refresh_policies(
    agents_path: Path,
    schema_path: Path | None,
    *,
    repo_root: Path | None = None,
) -> RefreshResult:
    """Refresh the AGENTS policy block from registry policy entries."""
    if not agents_path.exists():
        return RefreshResult((), (), False)

    repo_root = repo_root or agents_path.parent
    del schema_path
    content = agents_path.read_text(encoding="utf-8")
    scaffolded = False
    try:
        block_start, block_end, block_text = _locate_policy_block(content)
    except ValueError:
        content, scaffolded = _ensure_policy_block_scaffold(
            agents_path, content
        )
        try:
            block_start, block_end, block_text = _locate_policy_block(content)
        except ValueError:
            return RefreshResult((), (), scaffolded)

    registry_path = manifest_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        return RefreshResult((), (), scaffolded)
    try:
        payload = (
            yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        )
    except Exception:
        return RefreshResult((), (), scaffolded)
    policies = payload.get("policies", {})
    if not isinstance(policies, dict) or not policies:
        return RefreshResult((), (), scaffolded)

    previous_sections = _section_map(block_text)
    generated_sections: Dict[str, str] = {}
    skipped: List[str] = []
    entries: List[_PolicyEntry] = []
    for policy_id in sorted(policies):
        payload_entry = policies.get(policy_id, {})
        if not isinstance(payload_entry, dict):
            skipped.append(policy_id)
            continue
        order, values = _metadata_from_registry(
            policy_id, payload_entry.get("metadata")
        )
        rendered = _render_metadata_block(order, values)
        heading_name = (
            str(payload_entry.get("description", "")).strip()
            or policy_id.replace("-", " ").title()
        )
        heading = f"## Policy: {heading_name}\n\n"
        description = str(payload_entry.get("policy_text", "")).strip()
        if not description:
            descriptor = load_policy_descriptor(repo_root, policy_id)
            try:
                description = _descriptor_text_or_error(descriptor, policy_id)
            except ValueError:
                skipped.append(policy_id)
                continue
        final_text = (
            f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        )
        generated_sections[policy_id] = final_text
        custom_flag = (
            str(payload_entry.get("custom", False)).strip().lower() == "true"
        )
        entries.append(
            _PolicyEntry(
                policy_id=policy_id,
                text=final_text,
                group=0,
                changed=False,
                custom=custom_flag,
            )
        )

    if not entries:
        return RefreshResult((), tuple(skipped), scaffolded)

    new_block = _assemble_sections(entries)
    block_clean = block_text.strip()
    new_block_clean = new_block.strip()
    updated = new_block_clean != block_clean
    changed_file = scaffolded or updated
    if updated:
        prefix = content[:block_start]
        suffix = content[block_end:]
        rebuilt = (
            f"{prefix}\n{new_block.rstrip()}\n{suffix}"
            if not prefix.endswith("\n")
            else f"{prefix}{new_block.rstrip()}\n{suffix}"
        )
        agents_path.write_text(rebuilt, encoding="utf-8")
    changed = sorted(
        {
            *previous_sections.keys(),
            *generated_sections.keys(),
        }
        - {
            policy_id
            for policy_id in previous_sections.keys()
            & generated_sections.keys()
            if previous_sections.get(policy_id, "").strip()
            == generated_sections.get(policy_id, "").strip()
        }
    )
    return RefreshResult(tuple(changed), tuple(skipped), changed_file)


# ---- Inlined from core/refresh_registry.py ----
def _ensure_trailing_newline(path: Path) -> bool:
    """Ensure the given file ends with a newline."""
    if not path.exists():
        return False
    contents = path.read_bytes()
    if not contents:
        path.write_text("\n", encoding="utf-8")
        return True
    if contents.endswith(b"\n"):
        return False
    path.write_bytes(contents + b"\n")
    return True


def _discover_policy_sources(repo_root: Path) -> Dict[str, Dict[str, bool]]:
    """Return discovered policy ids and whether core/custom scripts exist."""

    discovered: Dict[str, Dict[str, bool]] = {}
    for source in ("core", "custom"):
        source_root = repo_root / "devcovenant" / source / "policies"
        if not source_root.exists():
            continue
        for entry in source_root.iterdir():
            if not entry.is_dir():
                continue
            script = entry / f"{entry.name}.py"
            if not script.exists():
                continue
            policy_id = entry.name.replace("_", "-").strip()
            record = discovered.setdefault(
                policy_id, {"core": False, "custom": False}
            )
            if source == "core":
                record["core"] = True
            else:
                record["custom"] = True
    return discovered


def _descriptor_values(raw_value: object | None) -> List[str]:
    """Normalize descriptor metadata values into a list of strings."""

    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    text = str(raw_value).strip()
    return [text] if text else []


def _as_bool(raw_value: str | None, *, default: bool) -> bool:
    """Interpret a resolved metadata value as a boolean."""

    if raw_value is None:
        return default
    token = raw_value.strip().lower()
    if token in {"true", "1", "yes", "on"}:
        return True
    if token in {"false", "0", "no", "off"}:
        return False
    return default


def refresh_registry(
    repo_root: Path | None = None,
    *,
    rerun: bool = False,
    skip_freeze: bool = False,
) -> int:
    """Refresh policy hashes.

    Writes devcovenant/registry/local/policy_registry.yaml.
    """

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = manifest_module.policy_registry_path(repo_root)

    if not agents_md_path.exists():
        print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    context = build_metadata_context(repo_root)
    discovered = _discover_policy_sources(repo_root)

    registry = PolicyRegistry(registry_path, repo_root)

    updated = 0
    policies: List[PolicyDefinition] = []
    seen_policy_ids: set[str] = set()
    for policy_id in sorted(discovered):
        location = resolve_script_location(repo_root, policy_id)
        core_available = any(
            loc.kind == "core" and loc.path.exists()
            for loc in iter_script_locations(repo_root, policy_id)
        )
        custom_available = any(
            loc.kind == "custom" and loc.path.exists()
            for loc in iter_script_locations(repo_root, policy_id)
        )
        if location is None:
            print(
                f"Notice: Policy script missing for {policy_id}. "
                "Entry will be updated without a hash.",
                file=sys.stderr,
            )
        else:
            updated += 1
        descriptor = load_policy_descriptor(repo_root, policy_id)
        if descriptor is None:
            print(
                (
                    f"Notice: Descriptor missing for {policy_id}. "
                    "Skipping registry entry."
                ),
                file=sys.stderr,
            )
            continue
        policy_text = str(descriptor.text or "").strip()
        if not policy_text:
            print(
                (
                    f"Notice: Descriptor text missing for {policy_id}. "
                    "Skipping registry entry."
                ),
                file=sys.stderr,
            )
            continue

        current_order = list(descriptor.metadata.keys())
        current_values = {
            key: _descriptor_values(descriptor.metadata.get(key))
            for key in current_order
        }
        resolved_order, resolved_metadata = resolve_policy_metadata_map(
            policy_id,
            current_order,
            current_values,
            descriptor,
            context,
            core_available=core_available,
            custom_policy=bool(custom_available and not core_available),
        )
        ordered_metadata = {
            key: str(resolved_metadata.get(key, "")).strip()
            for key in resolved_order
        }
        status = ordered_metadata.get("status") or "active"
        severity = ordered_metadata.get("severity") or "warning"
        enabled = _as_bool(ordered_metadata.get("enabled"), default=True)
        custom = _as_bool(ordered_metadata.get("custom"), default=False)
        auto_fix = _as_bool(ordered_metadata.get("auto_fix"), default=False)
        freeze = _as_bool(ordered_metadata.get("freeze"), default=False)
        policy_name = policy_id.replace("-", " ").title()
        policy = PolicyDefinition(
            policy_id=policy_id,
            name=policy_name,
            status=status,
            severity=severity,
            auto_fix=auto_fix,
            enabled=enabled,
            custom=custom,
            description=policy_text,
            freeze=freeze,
            raw_metadata=dict(ordered_metadata),
        )
        seen_policy_ids.add(policy_id)
        policies.append(policy)
        registry.update_policy_entry(
            policy,
            location,
            descriptor,
            resolved_metadata=ordered_metadata,
        )
        script_name = (
            location.path.name if location is not None else "<missing>"
        )
        print(f"Recorded {policy_id}: {script_name}")

    stale_ids = sorted(
        set(registry._data.get("policies", {}).keys()) - seen_policy_ids
    )
    for stale_id in stale_ids:
        registry._data["policies"].pop(stale_id, None)
        print(f"Removed stale policy entry: {stale_id}")
    if stale_ids:
        registry.save()

    if updated == 0:
        print("All policy hashes are up to date.")
    else:
        print("\nUpdated " f"{updated} policy hash(es) in {registry_path}")

    if _ensure_trailing_newline(registry_path):
        print(f"Ensured trailing newline in {registry_path}.")

    if not skip_freeze:
        freeze_changed, freeze_messages = policy_freeze.apply_policy_freeze(
            repo_root, policies
        )
        if freeze_messages:
            manifest_module.append_notifications(repo_root, freeze_messages)
            _print_freeze_messages(freeze_messages)
        if freeze_changed and not rerun:
            return refresh_registry(
                repo_root,
                rerun=True,
                skip_freeze=True,
            )

    return 0


def _print_freeze_messages(messages: Iterable[str]) -> None:
    """Print freeze-related notifications."""
    if not messages:
        return
    print("\nPolicy freeze notices:")
    for message in messages:
        print(f"- {message}")
