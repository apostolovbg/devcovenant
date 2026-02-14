"""Metadata resolution runtime for policy refresh and execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

from devcovenant.core import profile_runtime
from devcovenant.core.registry_runtime import PolicyDescriptor
from devcovenant.core.selector_runtime import _normalize_globs

_COMMON_KEYS = [
    "id",
    "severity",
    "auto_fix",
    "enforcement",
    "enabled",
    "custom",
]
_COMMON_DEFAULTS: Dict[str, List[str]] = {
    "severity": ["warning"],
    "auto_fix": ["false"],
    "enforcement": ["active"],
    "enabled": ["true"],
    "custom": ["false"],
}
_ROLE_SUFFIXES: Tuple[str, ...] = ("globs", "files", "dirs")
_LEGACY_SUFFIXES: Tuple[str, ...] = ("prefixes", "suffixes")
_LEGACY_ROLE_KEY = {
    "include_globs": ("include", "globs"),
    "exclude_globs": ("exclude", "globs"),
    "force_include_globs": ("force_include", "globs"),
    "include_files": ("include", "files"),
    "exclude_files": ("exclude", "files"),
    "force_include_files": ("force_include", "files"),
    "include_dirs": ("include", "dirs"),
    "exclude_dirs": ("exclude", "dirs"),
    "force_include_dirs": ("force_include", "dirs"),
    "watch_globs": ("watch", "globs"),
    "watch_files_files": ("watch_files", "files"),
    "watch_files_globs": ("watch_files", "globs"),
    "watch_files_dirs": ("watch_files", "dirs"),
    "tests_watch_globs": ("tests_watch", "globs"),
    "tests_watch_files": ("tests_watch", "files"),
    "tests_watch_dirs": ("tests_watch", "dirs"),
}
_DERIVED_VALUE_KEYS = {"updated"}
_ORDER_EXCLUDE_KEYS = {"updated"}
_RETIRED_METADATA_KEYS = {"status"}


def metadata_value_list(raw_value: object) -> List[str]:
    """Return metadata values as a string list."""
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item)]
    return [str(raw_value)]


@dataclass(frozen=True)
class PolicyControl:
    """Config-driven policy control flags."""

    policy_state: Dict[str, bool]


@dataclass(frozen=True)
class MetadataContext:
    """Resolved metadata context for policy normalization."""

    control: PolicyControl
    profile_overlays: Dict[str, Dict[str, Tuple[List[str], bool]]]
    autogen_overrides: Dict[str, Dict[str, List[str]]]
    user_overrides: Dict[str, Dict[str, List[str]]]


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
    """Return active profiles from config payload."""
    return profile_runtime.parse_active_profiles(payload, include_global=True)


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
    """Normalize policy override maps into list-valued metadata entries."""
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


def _load_metadata_overrides(
    payload: Dict[str, object],
) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, Dict[str, List[str]]]]:
    """Return autogen/user metadata overrides from config payload."""
    autogen = _normalize_override_map(
        payload.get("autogen_metadata_overrides")
    )
    user = _normalize_override_map(payload.get("user_metadata_overrides"))
    return autogen, user


def _merge_values(existing: List[str], incoming: List[str]) -> List[str]:
    """Merge values with de-duplication preserving order."""
    return _dedupe(existing + incoming)


def _collect_profile_overlays(
    repo_root: Path, active_profiles: List[str]
) -> Dict[str, Dict[str, Tuple[List[str], bool]]]:
    """Collect policy overlays from the profile registry."""
    registry = profile_runtime.load_profile_registry(repo_root)
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
                    continue
                policy_map[key_name] = (list(values), False)
    return overlays


def collect_profile_overlays(
    repo_root: Path, active_profiles: List[str]
) -> Dict[str, Dict[str, Tuple[List[str], bool]]]:
    """Public wrapper for resolved profile policy overlays."""
    return _collect_profile_overlays(repo_root, active_profiles)


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


def normalize_policy_state(raw_value: object) -> Dict[str, bool]:
    """Public wrapper for policy_state normalization."""
    return _normalize_policy_state(raw_value)


def load_policy_control_config(payload: Dict[str, object]) -> PolicyControl:
    """Load policy control values for policies."""
    policy_state = _normalize_policy_state(payload.get("policy_state"))
    return PolicyControl(policy_state)


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
    """Ensure a metadata key exists in order and values."""
    if key not in values:
        values[key] = []
    if key not in order:
        order.append(key)


def apply_policy_control(
    order: List[str],
    values: Dict[str, List[str]],
    policy_id: str,
    control: PolicyControl,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Apply enabled controls to metadata values."""
    if policy_id in control.policy_state:
        _ensure_metadata_key(order, values, "enabled")
        values["enabled"] = [
            "true" if control.policy_state[policy_id] else "false"
        ]
    return order, values


def descriptor_metadata_order_values(
    descriptor: PolicyDescriptor,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered keys and list values from a descriptor."""
    order = list(descriptor.metadata.keys())
    values: Dict[str, List[str]] = {}
    for key in order:
        values[key] = metadata_value_list(descriptor.metadata.get(key))
    return order, values


def _split_values(raw_values: Sequence[str]) -> List[str]:
    """Return a flattened list of comma-separated values."""
    items: List[str] = []
    for entry in raw_values:
        for part in entry.split(","):
            token = part.strip()
            if token:
                items.append(token)
    return items


def split_metadata_values(raw_values: Sequence[str]) -> List[str]:
    """Public wrapper for metadata value splitting."""
    return _split_values(raw_values)


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
            continue
        globs.append(f"*.{cleaned}")
    return globs


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
    if "selector_roles" in new_order:
        insert_at = new_order.index("selector_roles") + 1
    else:
        insert_at = len(new_order)
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
        if key in _RETIRED_METADATA_KEYS:
            continue
        values[key] = list(override_values)


def _apply_profile_overlays(
    values: Dict[str, List[str]],
    overlays: Dict[str, Tuple[List[str], bool]],
) -> None:
    """Apply profile overlays, merging list values and replacing scalars."""
    for key, (overlay_values, merge_lists) in overlays.items():
        if key in _RETIRED_METADATA_KEYS:
            continue
        if merge_lists:
            values[key] = _merge_values(values.get(key, []), overlay_values)
            continue
        values[key] = list(overlay_values)


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
    custom_policy: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Resolve metadata using defaults, overlays, and config overrides."""
    if descriptor:
        base_order, base_values = descriptor_metadata_order_values(descriptor)
        base_order = [
            key
            for key in base_order
            if key not in _ORDER_EXCLUDE_KEYS
            and key not in _RETIRED_METADATA_KEYS
        ]
        values = {
            key: list(entries)
            for key, entries in base_values.items()
            if key not in _RETIRED_METADATA_KEYS
        }
    else:
        base_order = [
            key
            for key in current_order
            if key not in _ORDER_EXCLUDE_KEYS
            and key not in _RETIRED_METADATA_KEYS
        ]
        values = {
            key: list(entries)
            for key, entries in current_values.items()
            if key not in _RETIRED_METADATA_KEYS
        }
    if not descriptor:
        for key in current_order:
            if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
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
        if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in overlays.keys():
        if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in autogen_overrides.keys():
        if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in user_overrides.keys():
        if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    if not descriptor:
        for key in current_order:
            if key in _ORDER_EXCLUDE_KEYS or key in _RETIRED_METADATA_KEYS:
                continue
            _ensure_metadata_key(ordered_keys, values, key)

    values["id"] = [policy_id]
    if custom_policy:
        values["custom"] = ["true"]

    for key in ordered_keys:
        current = values.get(key, [])
        if current:
            values[key] = _dedupe(list(current))
            continue
        if key in _COMMON_DEFAULTS:
            values[key] = _dedupe(list(_COMMON_DEFAULTS[key]))
            continue
        values[key] = []

    ordered_keys, values = apply_policy_control(
        ordered_keys,
        values,
        policy_id,
        context.control,
    )
    return _apply_selector_roles(ordered_keys, values)


def resolve_policy_metadata_map(
    policy_id: str,
    current_order: List[str],
    current_values: Dict[str, List[str]],
    descriptor: PolicyDescriptor | None,
    context: MetadataContext,
    *,
    custom_policy: bool = False,
) -> Tuple[List[str], Dict[str, str]]:
    """Return resolved metadata order and string map for a policy."""
    order, values = _resolve_metadata(
        policy_id,
        current_order,
        current_values,
        descriptor,
        context,
        custom_policy=custom_policy,
    )
    resolved: Dict[str, str] = {}
    for key in order:
        entries = values.get(key, [])
        resolved[key] = ", ".join(entry for entry in entries if entry)
    return order, resolved


def render_metadata_block(
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
