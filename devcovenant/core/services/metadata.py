"""Metadata resolution runtime for policy refresh and execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import yaml

import devcovenant.core.services.profile_registry as profile_runtime
from devcovenant.core.lib.selectors import _normalize_globs
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.registry import PolicyDescriptor

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
_GLOB_SUFFIXES: Tuple[str, ...] = ("prefixes", "suffixes")
_SELECTOR_ROLE_TARGETS = {
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
_TRACE_LAYER_RUNTIME_DEFAULTS = "runtime_defaults"
_TRACE_LAYER_DESCRIPTOR = "descriptor"
_TRACE_LAYER_PROFILE_OVERLAYS = "profile_overlays"
_TRACE_LAYER_AUTOGEN_OVERLAYS = "autogen_overlays"
_TRACE_LAYER_USER_OVERLAYS = "user_overlays"
_TRACE_LAYER_AUTOGEN_OVERRIDES = "autogen_overrides"
_TRACE_LAYER_USER_OVERRIDES = "user_overrides"
_TRACE_LAYER_POLICY_STATE = "policy_state"
_TRACE_LAYER_DERIVED_SELECTORS = "derived_selectors"
_TRACE_LAYER_RUNTIME_IDENTITY = "runtime_identity"
_TRACE_LAYER_RUNTIME_CUSTOM = "runtime_custom_source"


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
    autogen_overlays: Dict[str, Dict[str, Tuple[List[str], bool]]]
    user_overlays: Dict[str, Dict[str, Tuple[List[str], bool]]]
    autogen_overrides: Dict[str, Dict[str, List[str]]]
    user_overrides: Dict[str, Dict[str, List[str]]]


@dataclass(frozen=True)
class ResolvedPolicyMetadata:
    """Canonical resolved metadata views for one policy."""

    order: List[str]
    list_map: Dict[str, List[str]]
    string_map: Dict[str, str]
    resolution_trace: Dict[str, Dict[str, Any]]
    warnings: List[Dict[str, Any]]

    def decode_options(
        self,
        *,
        reserved_keys: Iterable[str] = (),
    ) -> Dict[str, Any]:
        """Return a typed view of metadata suitable for policy options."""
        return decode_metadata_options_map(
            self.string_map,
            reserved_keys=reserved_keys,
        )

    def warning_messages(self) -> List[str]:
        """Return human-readable metadata warning messages."""
        messages: List[str] = []
        for warning in self.warnings:
            message = str(warning.get("message", "")).strip()
            if message:
                messages.append(message)
        return messages


def _load_config_payload(repo_root: Path) -> Dict[str, object]:
    """Load config.yaml into a dictionary."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        raise ValueError(f"Missing config file: {config_path}")
    try:
        payload = yaml_cache_service.load_yaml(config_path)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a YAML mapping: {config_path}")
    return payload


def _load_active_profiles(payload: Dict[str, object]) -> List[str]:
    """Return active profiles from config payload."""
    return profile_runtime.parse_active_profiles(payload, include_global=True)


def _normalize_metadata_values(raw_value: object) -> List[str]:
    """Normalize a metadata value into a list of strings."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text:
            return []
        return [text]
    if isinstance(raw_value, list):
        cleaned: List[str] = []
        for entry in raw_value:
            token = str(entry or "").strip()
            if token:
                cleaned.append(token)
        return cleaned
    text = str(raw_value).strip()
    if not text:
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


def _normalize_overlay_map(
    raw_value: object,
) -> Dict[str, Dict[str, Tuple[List[str], bool]]]:
    """Normalize metadata overlays into merge/replace-aware entries."""
    if not isinstance(raw_value, dict):
        return {}
    normalized: Dict[str, Dict[str, Tuple[List[str], bool]]] = {}
    for policy_id, mapping in raw_value.items():
        if not isinstance(mapping, dict):
            continue
        policy_key = str(policy_id).strip()
        if not policy_key:
            continue
        entries: Dict[str, Tuple[List[str], bool]] = {}
        for key, metadata_value in mapping.items():
            key_name = str(key).strip()
            if not key_name:
                continue
            merge_values = isinstance(metadata_value, list)
            values = _normalize_metadata_values(metadata_value)
            entries[key_name] = (values, merge_values)
        if entries:
            normalized[policy_key] = entries
    return normalized


def _load_metadata_layers(
    payload: Dict[str, object],
) -> Tuple[
    Dict[str, Dict[str, Tuple[List[str], bool]]],
    Dict[str, Dict[str, Tuple[List[str], bool]]],
    Dict[str, Dict[str, List[str]]],
    Dict[str, Dict[str, List[str]]],
]:
    """Return autogen/user metadata overlays and overrides from config."""
    autogen_overlays = _normalize_overlay_map(
        payload.get("autogen_metadata_overlays")
    )
    user_overlays = _normalize_overlay_map(
        payload.get("user_metadata_overlays")
    )
    autogen = _normalize_override_map(
        payload.get("autogen_metadata_overrides")
    )
    user = _normalize_override_map(payload.get("user_metadata_overrides"))
    return autogen_overlays, user_overlays, autogen, user


def _merge_values(existing: List[str], incoming: List[str]) -> List[str]:
    """Merge values with de-duplication preserving order."""
    return _dedupe(existing + incoming)


def _collect_profile_overlays(
    repo_root: Path, active_profiles: List[str]
) -> Dict[str, Dict[str, Tuple[List[str], bool]]]:
    """Collect policy and core-invariant overlays from the profile registry."""
    registry = profile_runtime.load_profile_registry(repo_root)
    overlays: Dict[str, Dict[str, Tuple[List[str], bool]]] = {}
    for profile in active_profiles:
        meta = registry.get(profile)
        if not isinstance(meta, dict):
            continue
        for section_name in ("policy_overlays", "core_invariant_overlays"):
            raw_overlays = meta.get(section_name) or {}
            if not isinstance(raw_overlays, dict):
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
                        current_values = policy_map.get(key_name, ([], True))[
                            0
                        ]
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
    return build_metadata_context_from_payload(repo_root, payload)


def build_metadata_context_from_payload(
    repo_root: Path,
    payload: Dict[str, object],
) -> MetadataContext:
    """Return the metadata resolution context for an in-memory config."""
    active_profiles = _load_active_profiles(payload)
    profile_overlays = _collect_profile_overlays(repo_root, active_profiles)
    (
        autogen_overlays,
        user_overlays,
        autogen_overrides,
        user_overrides,
    ) = _load_metadata_layers(payload)
    control = load_policy_control_config(payload)
    return MetadataContext(
        control=control,
        profile_overlays=profile_overlays,
        autogen_overlays=autogen_overlays,
        user_overlays=user_overlays,
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


def _first_metadata_token(
    values: Dict[str, List[str]],
    key: str,
) -> str:
    """Return the first normalized metadata token for a key."""
    entries = values.get(key, [])
    if not isinstance(entries, list) or not entries:
        return ""
    return str(entries[0] or "").strip().lower()


def apply_policy_control(
    order: List[str],
    values: Dict[str, List[str]],
    policy_id: str,
    control: PolicyControl,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Apply enabled controls to metadata values."""
    if policy_id in control.policy_state:
        requested_enabled = bool(control.policy_state[policy_id])
        severity_token = _first_metadata_token(values, "severity")
        if severity_token == "critical" and not requested_enabled:
            requested_enabled = True
        _ensure_metadata_key(order, values, "enabled")
        values["enabled"] = ["true" if requested_enabled else "false"]
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


def decode_metadata_option_value(raw_value: object) -> Any:
    """Decode one metadata value into a common scalar/list representation."""
    if raw_value is None:
        return ""
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, float):
        return raw_value
    if isinstance(raw_value, (list, tuple, set)):
        items: List[str] = []
        for entry in raw_value:
            text = str(entry or "").strip()
            if not text:
                continue
            if "," in text:
                items.extend(_split_values([text]))
                continue
            items.append(text)
        return items

    text = str(raw_value).strip()
    if not text:
        return ""

    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    if "," in text:
        return _split_values([text])

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    return text


def decode_metadata_options_map(
    raw_metadata: Mapping[str, object] | None,
    *,
    reserved_keys: Iterable[str] = (),
) -> Dict[str, Any]:
    """Decode a metadata map into typed policy/runtime options."""
    if not isinstance(raw_metadata, Mapping):
        return {}
    reserved = {
        str(key).strip().lower() for key in reserved_keys if str(key).strip()
    }
    decoded: Dict[str, Any] = {}
    for raw_key, raw_value in raw_metadata.items():
        key = str(raw_key or "").strip()
        if not key:
            continue
        if key.lower() in reserved:
            continue
        decoded[key] = decode_metadata_option_value(raw_value)
    return decoded


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


def _trace_bucket(
    trace: Dict[str, Dict[str, Any]],
    key: str,
) -> Dict[str, Any]:
    """Return the trace bucket for one metadata key."""
    return trace.setdefault(key, {})


def _record_trace_layer(
    trace: Dict[str, Dict[str, Any]],
    key: str,
    *,
    layer: str,
    values: Sequence[str],
    behavior: str,
    replaced_inherited_values: Sequence[str] = (),
    note: str = "",
) -> None:
    """Record one resolution-layer contribution for a metadata key."""
    bucket = _trace_bucket(trace, key)
    payload: Dict[str, Any] = {
        "values": [str(entry) for entry in values if str(entry)],
        "behavior": behavior,
    }
    replaced = [
        str(entry) for entry in replaced_inherited_values if str(entry)
    ]
    if replaced:
        payload["replaced_inherited_values"] = replaced
    if note.strip():
        payload["note"] = note.strip()
    bucket[layer] = payload


def _record_effective_trace(
    trace: Dict[str, Dict[str, Any]],
    key: str,
    values: Sequence[str],
) -> None:
    """Record the final effective values for one metadata key."""
    bucket = _trace_bucket(trace, key)
    bucket["effective"] = {
        "values": [str(entry) for entry in values if str(entry)]
    }


def _build_override_warning(
    policy_id: str,
    key: str,
    *,
    layer: str,
    inherited_values: Sequence[str],
    replacement_values: Sequence[str],
) -> Dict[str, Any]:
    """Build one structured override-replacement warning payload."""
    inherited = [str(entry) for entry in inherited_values if str(entry)]
    replacement = [str(entry) for entry in replacement_values if str(entry)]
    return {
        "policy_id": policy_id,
        "key": key,
        "layer": layer,
        "inherited_values": inherited,
        "replacement_values": replacement,
        "message": (
            f"{layer} replaces inherited metadata for "
            f"`{policy_id}.{key}`; use overlays if you intended additive "
            "behavior."
        ),
    }


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
    if key in _SELECTOR_ROLE_TARGETS:
        return _SELECTOR_ROLE_TARGETS[key]
    for suffix in _ROLE_SUFFIXES:
        marker = f"_{suffix}"
        if key.endswith(marker):
            return key[: -len(marker)], suffix
    for suffix in _GLOB_SUFFIXES:
        marker = f"_{suffix}"
        if key.endswith(marker):
            return key[: -len(marker)], "globs"
    return None


def _apply_selector_roles(
    order: List[str],
    values: Dict[str, List[str]],
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Insert selector role keys and normalize selector values."""
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
        if key in _SELECTOR_ROLE_TARGETS:
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
    *,
    policy_id: str,
    layer_name: str,
    trace: Dict[str, Dict[str, Any]],
    warnings: List[Dict[str, Any]],
) -> None:
    """Apply override values by replacing existing entries."""
    for key, override_values in overrides.items():
        inherited_values = list(values.get(key, []))
        values[key] = list(override_values)
        _record_trace_layer(
            trace,
            key,
            layer=layer_name,
            values=override_values,
            behavior="replace",
            replaced_inherited_values=inherited_values,
        )
        if inherited_values and inherited_values != list(override_values):
            warnings.append(
                _build_override_warning(
                    policy_id,
                    key,
                    layer=layer_name,
                    inherited_values=inherited_values,
                    replacement_values=override_values,
                )
            )


def _apply_profile_overlays(
    values: Dict[str, List[str]],
    overlays: Dict[str, Tuple[List[str], bool]],
    *,
    layer_name: str,
    trace: Dict[str, Dict[str, Any]],
) -> None:
    """Apply profile overlays, merging list values and replacing scalars."""
    for key, (overlay_values, merge_lists) in overlays.items():
        inherited_values = list(values.get(key, []))
        if merge_lists:
            values[key] = _merge_values(values.get(key, []), overlay_values)
            _record_trace_layer(
                trace,
                key,
                layer=layer_name,
                values=overlay_values,
                behavior="append",
            )
            continue
        values[key] = list(overlay_values)
        _record_trace_layer(
            trace,
            key,
            layer=layer_name,
            values=overlay_values,
            behavior="replace",
            replaced_inherited_values=inherited_values,
        )


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
) -> Tuple[
    List[str],
    Dict[str, List[str]],
    Dict[str, Dict[str, Any]],
    List[Dict[str, Any]],
]:
    """Resolve metadata using defaults, overlays, and config overrides."""
    trace: Dict[str, Dict[str, Any]] = {}
    warnings: List[Dict[str, Any]] = []
    if descriptor:
        base_order, base_values = descriptor_metadata_order_values(descriptor)
        base_order = [
            key for key in base_order if key not in _ORDER_EXCLUDE_KEYS
        ]
        values = {key: list(entries) for key, entries in base_values.items()}
        for key in base_order:
            _record_trace_layer(
                trace,
                key,
                layer=_TRACE_LAYER_DESCRIPTOR,
                values=values.get(key, []),
                behavior="base",
            )
    else:
        base_order = [
            key for key in current_order if key not in _ORDER_EXCLUDE_KEYS
        ]
        values = {
            key: list(entries) for key, entries in current_values.items()
        }
        for key in base_order:
            _record_trace_layer(
                trace,
                key,
                layer=_TRACE_LAYER_DESCRIPTOR,
                values=values.get(key, []),
                behavior="base",
            )
    if not descriptor:
        for key in current_order:
            if key in _ORDER_EXCLUDE_KEYS:
                continue
            values.setdefault(key, list(current_values.get(key, [])))

    overlays = context.profile_overlays.get(policy_id, {})
    _apply_profile_overlays(
        values,
        overlays,
        layer_name=_TRACE_LAYER_PROFILE_OVERLAYS,
        trace=trace,
    )
    autogen_overlays = context.autogen_overlays.get(policy_id, {})
    _apply_profile_overlays(
        values,
        autogen_overlays,
        layer_name=_TRACE_LAYER_AUTOGEN_OVERLAYS,
        trace=trace,
    )
    user_overlays = context.user_overlays.get(policy_id, {})
    _apply_profile_overlays(
        values,
        user_overlays,
        layer_name=_TRACE_LAYER_USER_OVERLAYS,
        trace=trace,
    )
    autogen_overrides = context.autogen_overrides.get(policy_id, {})
    _apply_overrides_replace(
        values,
        autogen_overrides,
        policy_id=policy_id,
        layer_name=_TRACE_LAYER_AUTOGEN_OVERRIDES,
        trace=trace,
        warnings=warnings,
    )
    user_overrides = context.user_overrides.get(policy_id, {})
    _apply_overrides_replace(
        values,
        user_overrides,
        policy_id=policy_id,
        layer_name=_TRACE_LAYER_USER_OVERRIDES,
        trace=trace,
        warnings=warnings,
    )
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
    for key in autogen_overlays.keys():
        if key in _ORDER_EXCLUDE_KEYS:
            continue
        _ensure_metadata_key(ordered_keys, values, key)
    for key in user_overlays.keys():
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
    _record_trace_layer(
        trace,
        "id",
        layer=_TRACE_LAYER_RUNTIME_IDENTITY,
        values=[policy_id],
        behavior="replace",
    )
    if custom_policy:
        values["custom"] = ["true"]
        _record_trace_layer(
            trace,
            "custom",
            layer=_TRACE_LAYER_RUNTIME_CUSTOM,
            values=["true"],
            behavior="replace",
            note="Resolved from active custom policy script.",
        )

    for key in ordered_keys:
        current = values.get(key, [])
        if current:
            values[key] = _dedupe(list(current))
            continue
        if key in _COMMON_DEFAULTS:
            values[key] = _dedupe(list(_COMMON_DEFAULTS[key]))
            _record_trace_layer(
                trace,
                key,
                layer=_TRACE_LAYER_RUNTIME_DEFAULTS,
                values=values[key],
                behavior="default",
            )
            continue
        values[key] = []

    control_requested = context.control.policy_state.get(policy_id)
    pre_control_enabled = list(values.get("enabled", []))
    severity_token = _first_metadata_token(values, "severity")
    ordered_keys, values = apply_policy_control(
        ordered_keys,
        values,
        policy_id,
        context.control,
    )
    if control_requested is not None:
        control_note = ""
        if severity_token == "critical" and not bool(control_requested):
            control_note = (
                "Critical policy disable attempt preserved enforcement."
            )
        _record_trace_layer(
            trace,
            "enabled",
            layer=_TRACE_LAYER_POLICY_STATE,
            values=["true" if bool(control_requested) else "false"],
            behavior="replace",
            replaced_inherited_values=pre_control_enabled,
            note=control_note,
        )

    pre_selector_values = {
        key: list(entries) for key, entries in values.items()
    }
    ordered_keys, values = _apply_selector_roles(ordered_keys, values)
    for key, resolved_values in values.items():
        previous_values = pre_selector_values.get(key, [])
        if resolved_values == previous_values:
            continue
        derived_values = [
            entry for entry in resolved_values if entry not in previous_values
        ]
        _record_trace_layer(
            trace,
            key,
            layer=_TRACE_LAYER_DERIVED_SELECTORS,
            values=derived_values or resolved_values,
            behavior="derive",
        )
    for key in ordered_keys:
        _record_effective_trace(trace, key, values.get(key, []))
    return ordered_keys, values, trace, warnings


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
    bundle = resolve_policy_metadata_bundle(
        policy_id,
        current_order,
        current_values,
        descriptor,
        context,
        custom_policy=custom_policy,
    )
    return bundle.order, bundle.string_map


def resolve_policy_metadata_bundle(
    policy_id: str,
    current_order: List[str],
    current_values: Dict[str, List[str]],
    descriptor: PolicyDescriptor | None,
    context: MetadataContext,
    *,
    custom_policy: bool = False,
) -> ResolvedPolicyMetadata:
    """Return resolved metadata in list and string forms."""
    order, values, trace, warnings = _resolve_metadata(
        policy_id,
        current_order,
        current_values,
        descriptor,
        context,
        custom_policy=custom_policy,
    )
    list_map: Dict[str, List[str]] = {}
    string_map: Dict[str, str] = {}
    for key in order:
        entries = list(values.get(key, []))
        list_map[key] = entries
        string_map[key] = ", ".join(entry for entry in entries if entry)
    return ResolvedPolicyMetadata(
        order=list(order),
        list_map=list_map,
        string_map=string_map,
        resolution_trace=trace,
        warnings=warnings,
    )


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
