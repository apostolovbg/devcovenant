"""Refresh policy metadata and grouping inside AGENTS.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

from devcovenant.core import profiles
from devcovenant.core.policy_descriptor import (
    PolicyDescriptor,
    load_policy_descriptor,
)
from devcovenant.core.policy_schema import (
    POLICY_BLOCK_RE,
    parse_metadata_block,
)
from devcovenant.core.selector_helpers import _normalize_globs

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


def _template_agents_path(repo_root: Path) -> Path:
    """Return the global template AGENTS file inside the core assets."""
    return (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "AGENTS.md"
    )


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


def _policy_id_from_dir(dir_name: str) -> str:
    """Convert a policy directory name into a policy id."""
    return dir_name.replace("_", "-").strip()


def _discover_policy_sources(repo_root: Path) -> Dict[str, Dict[str, bool]]:
    """Return discovered policy ids and whether custom overrides exist."""
    policies: Dict[str, Dict[str, bool]] = {}
    for source in ("core", "custom"):
        root = repo_root / "devcovenant" / source / "policies"
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            script = entry / f"{entry.name}.py"
            if not script.exists():
                continue
            policy_id = _policy_id_from_dir(entry.name)
            record = policies.setdefault(
                policy_id, {"custom": False, "core": False}
            )
            if source == "custom":
                record["custom"] = True
            else:
                record["core"] = True
    return policies


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
    template_defaults: Dict[str, Dict[str, List[str]]]


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
    template_defaults = _load_template_metadata(
        _template_agents_path(repo_root)
    )
    return MetadataContext(
        control=control,
        profile_overlays=profile_overlays,
        autogen_overrides=autogen_overrides,
        user_overrides=user_overrides,
        template_defaults=template_defaults,
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


def _load_stock_texts(repo_root: Path) -> Dict[str, str]:
    """Load stock policy text from YAML or JSON assets."""
    yaml_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "global"
        / "stock_policy_texts.yaml"
    )
    if yaml_path.exists():
        try:
            yaml_payload = yaml.safe_load(
                yaml_path.read_text(encoding="utf-8")
            )
            if isinstance(yaml_payload, dict):
                return {
                    str(key): str(value) for key, value in yaml_payload.items()
                }
        except Exception:
            pass
    json_path = repo_root / "devcovenant" / "core" / "stock_policy_texts.json"
    if json_path.exists():
        try:
            import json

            json_payload = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(json_payload, dict):
                normalized: Dict[str, str] = {}
                for key, payload_value in json_payload.items():
                    if isinstance(payload_value, list):
                        normalized[key] = "\n".join(
                            str(item) for item in payload_value
                        )
                    else:
                        normalized[key] = str(payload_value)
                return normalized
        except Exception:
            pass
    return {}


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


def _load_template_metadata(
    template_path: Path,
) -> Dict[str, Dict[str, List[str]]]:
    """Parse a template AGENTS policy block into metadata defaults."""
    if not template_path.exists():
        return {}
    content = template_path.read_text(encoding="utf-8")
    parsed: Dict[str, Dict[str, List[str]]] = {}
    for match in POLICY_BLOCK_RE.finditer(content):
        metadata_block = match.group(2).strip()
        _order, values = parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0] if values.get("id") else ""
        if not policy_id:
            continue
        parsed[policy_id] = values
    return parsed


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

    template_values = context.template_defaults.get(policy_id)
    if not descriptor and template_values:
        for key, defaults in template_values.items():
            if key in _ORDER_EXCLUDE_KEYS:
                continue
            values.setdefault(key, list(defaults))
            if not values[key] and defaults:
                values[key] = list(defaults)

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
    if template_values and not descriptor:
        for key in template_values.keys():
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


def refresh_policies(
    agents_path: Path,
    schema_path: Path | None,
    *,
    repo_root: Path | None = None,
) -> RefreshResult:
    """Refresh the policy block metadata and ordering inside AGENTS.md."""
    if not agents_path.exists():
        return RefreshResult((), (), False)

    repo_root = repo_root or agents_path.parent
    context = build_metadata_context(repo_root)
    discovered = _discover_policy_sources(repo_root)
    descriptors = _load_descriptors(repo_root, discovered)
    del schema_path
    stock_texts = _load_stock_texts(repo_root)
    content = agents_path.read_text(encoding="utf-8")
    try:
        block_start, block_end, block_text = _locate_policy_block(content)
    except ValueError:
        return RefreshResult((), (), False)

    changed: List[str] = []
    skipped: List[str] = []
    entries: List[_PolicyEntry] = []
    seen_ids: set[str] = set()

    for match in POLICY_BLOCK_RE.finditer(block_text):
        heading = match.group(1)
        metadata_block = match.group(2).strip()
        existing_description = match.group(3).rstrip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0] if values.get("id") else ""
        if not policy_id:
            skipped.append("unknown")
            continue
        descriptor = descriptors.get(policy_id)
        description = (
            descriptor.text.strip()
            if descriptor and descriptor.text
            else existing_description
        )

        seen_ids.add(policy_id)
        source_flags = discovered.get(policy_id, {})
        if not source_flags:
            skipped.append(policy_id)
            continue
        core_available = bool(source_flags.get("core"))
        custom_policy = bool(
            source_flags.get("custom") and not source_flags.get("core")
        )
        normalized_order, normalized_values = _resolve_metadata(
            policy_id,
            order,
            values,
            descriptor,
            context,
            core_available=core_available,
            custom_policy=custom_policy,
        )
        custom_flag = (
            normalized_values.get("custom", ["false"])[0].strip().lower()
            == "true"
        )
        rendered = _render_metadata_block(normalized_order, normalized_values)
        metadata_changed = rendered != metadata_block
        final_text = (
            f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        )
        entries.append(
            _PolicyEntry(
                policy_id=policy_id,
                text=final_text,
                group=0,
                changed=metadata_changed,
                custom=custom_flag,
            )
        )
        if metadata_changed:
            changed.append(policy_id)

    for policy_id, source_flags in sorted(discovered.items()):
        if policy_id in seen_ids:
            continue
        core_available = bool(source_flags.get("core"))
        custom_policy = bool(
            source_flags.get("custom") and not source_flags.get("core")
        )
        descriptor = descriptors.get(policy_id)
        base_order = ["id"]
        base_values = {"id": [policy_id]}
        normalized_order, normalized_values = _resolve_metadata(
            policy_id,
            base_order,
            base_values,
            descriptor,
            context,
            core_available=core_available,
            custom_policy=custom_policy,
        )
        normalized_values.setdefault("id", [policy_id])
        rendered = _render_metadata_block(normalized_order, normalized_values)
        if descriptor and descriptor.text:
            description = descriptor.text.strip()
        else:
            description = stock_texts.get(
                policy_id, "Policy description pending."
            )
        heading = f"## Policy: {policy_id.replace('-', ' ').title()}\n\n"
        final_text = (
            f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        )
        entries.append(
            _PolicyEntry(
                policy_id=policy_id,
                text=final_text,
                group=0,
                changed=True,
                custom=(
                    normalized_values.get("custom", ["false"])[0]
                    .strip()
                    .lower()
                    == "true"
                ),
            )
        )
        changed.append(policy_id)

    if not entries:
        return RefreshResult((), tuple(skipped), False)

    new_block = _assemble_sections(entries)
    block_clean = block_text.strip()
    new_block_clean = new_block.strip()
    prefix = content[:block_start]
    suffix = content[block_end:]
    rebuilt = (
        f"{prefix}\n{new_block.rstrip()}\n{suffix}"
        if not prefix.endswith("\n")
        else f"{prefix}{new_block.rstrip()}\n{suffix}"
    )
    agents_path.write_text(rebuilt, encoding="utf-8")
    updated = new_block_clean != block_clean
    return RefreshResult(tuple(changed), tuple(skipped), updated)
