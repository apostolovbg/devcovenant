"""Refresh policy metadata and grouping inside AGENTS.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

from devcovenant.core.generate_policy_metadata_schema import (
    write_schema as generate_policy_metadata_schema,
)
from devcovenant.core.policy_descriptor import (
    PolicyDescriptor,
    load_policy_descriptor,
)
from devcovenant.core.policy_schema import (
    POLICY_BLOCK_RE,
    PolicySchema,
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
    "updated",
    "enforcement",
    "apply",
    "custom",
    "freeze",
    "profile_scopes",
]

_COMMON_DEFAULTS: Dict[str, List[str]] = {
    "status": ["active"],
    "severity": ["warning"],
    "auto_fix": ["false"],
    "updated": ["false"],
    "enforcement": ["active"],
    "apply": ["true"],
    "custom": ["false"],
    "freeze": ["false"],
    "profile_scopes": ["global"],
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

_METADATA_MODES = ("preserve", "stock")

_GROUP_COMMENTS: Dict[int, str] = {}
POLICY_METADATA_SCHEMA_FILENAME = "policy_metadata_schema.yaml"


def policy_metadata_schema_path(repo_root: Path) -> Path:
    """Return the canonical metadata schema file path."""
    return (
        repo_root
        / "devcovenant"
        / "registry"
        / "local"
        / POLICY_METADATA_SCHEMA_FILENAME
    )


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


def _choose_schema_source(repo_root: Path, schema_path: Path | None) -> Path:
    """Resolve the schema source path, preferring the canonical file."""
    if schema_path and schema_path.exists():
        return schema_path
    canonical = policy_metadata_schema_path(repo_root)
    if canonical.exists():
        return canonical
    return _template_agents_path(repo_root)


@dataclass(frozen=True)
class RefreshResult:
    """Summary of refresh work."""

    changed_policies: Tuple[str, ...]
    skipped_policies: Tuple[str, ...]
    updated: bool
    metadata_mode: str


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


def _normalize_profile_name(raw: object) -> str:
    """Normalize a profile name for matching."""
    return str(raw or "").strip().lower()


def _load_active_profiles(repo_root: Path) -> List[str]:
    """Load active profiles from config.yaml, ensuring global is present."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return ["global"]
    try:
        config_data = (
            yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        )
    except Exception:
        return ["global"]
    profiles_block = (
        config_data.get("profiles", {})
        if isinstance(config_data, dict)
        else {}
    )
    active = profiles_block.get("active", [])
    if isinstance(active, str):
        candidates = [active]
    elif isinstance(active, list):
        candidates = active
    else:
        candidates = [active] if active else []
    normalized = []
    for entry in candidates:
        name = _normalize_profile_name(entry)
        if name and name != "__none__":
            normalized.append(name)
    if "global" not in normalized:
        normalized.append("global")
    return sorted(set(normalized))


def _scopes_match(scopes: List[str], active_profiles: List[str]) -> bool:
    """Return True when any scope matches the active profiles."""
    if not scopes:
        return True
    for scope in scopes:
        normalized = _normalize_profile_name(scope)
        if not normalized:
            continue
        if normalized == "global" or normalized in active_profiles:
            return True
    return False


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
    """Config-driven overrides for policy metadata."""

    autogen_do_not_apply: set[str]
    manual_force_apply: set[str]
    freeze_core: set[str]
    overrides: Dict[str, Dict[str, List[str]]]


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


def load_policy_control_config(repo_root: Path) -> PolicyControl:
    """Load the do-not-apply/freeze/override config for policies."""

    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return PolicyControl(set(), set(), set(), {})
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        payload = {}
    autogen_do_not_apply = _normalize_policy_list(
        payload.get("autogen_do_not_apply")
    )
    manual_force_apply = _normalize_policy_list(
        payload.get("manual_force_apply")
    )
    freeze_core = _normalize_policy_list(payload.get("freeze_core_policies"))
    overrides_block = payload.get("policy_overrides") or {}
    overrides: Dict[str, Dict[str, List[str]]] = {}
    if isinstance(overrides_block, dict):
        for policy_id, mapping in overrides_block.items():
            if not isinstance(mapping, dict):
                continue
            normalized: Dict[str, List[str]] = {}
            for key, raw_override in mapping.items():
                normalized[key] = metadata_value_list(raw_override)
            if normalized:
                overrides[str(policy_id)] = normalized
    return PolicyControl(
        autogen_do_not_apply, manual_force_apply, freeze_core, overrides
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


def apply_policy_control_overrides(
    order: List[str],
    values: Dict[str, List[str]],
    policy_id: str,
    control: PolicyControl,
    *,
    core_available: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Merge config-driven overrides into policy metadata values."""

    overrides = control.overrides.get(policy_id, {})
    for key, override_values in overrides.items():
        _ensure_metadata_key(order, values, key)
        existing = values.get(key, [])
        values[key] = _merge_values(existing, override_values)

    if policy_id in control.autogen_do_not_apply:
        _ensure_metadata_key(order, values, "apply")
        values["apply"] = ["false"]

    if policy_id in control.manual_force_apply:
        _ensure_metadata_key(order, values, "apply")
        values["apply"] = ["true"]

    if policy_id in control.freeze_core and core_available:
        custom_flag = (
            values.get("custom", ["false"])[0].strip().lower() == "true"
        )
        if not custom_flag:
            _ensure_metadata_key(order, values, "freeze")
            values["freeze"] = ["true"]

    return order, values


def _load_schema_from_yaml(schema_path: Path) -> Dict[str, PolicySchema]:
    """Load a metadata schema payload from the canonical YAML file."""
    schema: Dict[str, PolicySchema] = {}
    if not schema_path.exists():
        return schema
    try:
        payload = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except Exception:
        return schema
    if not isinstance(payload, dict):
        return schema
    policies = payload.get("policies")
    if not isinstance(policies, dict):
        return schema
    for policy_id, entry in policies.items():
        if not isinstance(entry, dict):
            continue
        keys = tuple(entry.get("keys", ()))
        defaults_block = entry.get("defaults", {})
        defaults: Dict[str, List[str]] = {}
        if isinstance(defaults_block, dict):
            for key in keys:
                defaults[key] = metadata_value_list(defaults_block.get(key))
        schema[policy_id] = PolicySchema(keys, defaults)
    return schema


def _descriptor_schema_map(
    descriptors: Dict[str, PolicyDescriptor],
) -> Dict[str, PolicySchema]:
    """Build schema entries for each policy descriptor."""
    schema: Dict[str, PolicySchema] = {}
    for policy_id, descriptor in descriptors.items():
        metadata = descriptor.metadata or {}
        keys = tuple(metadata.keys())
        defaults: Dict[str, List[str]] = {}
        for key in keys:
            defaults[key] = _dedupe(metadata_value_list(metadata.get(key)))
        schema[policy_id] = PolicySchema(keys, defaults)
    return schema


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
        first = entries[0]
        if first:
            lines.append(f"{key}: {first}")
        else:
            lines.append(f"{key}:")
        for extra in entries[1:]:
            lines.append(f"  {extra}")
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


def _build_schema(
    template_path: Path,
    descriptors: Dict[str, PolicyDescriptor],
) -> Dict[str, PolicySchema]:
    """Build policy schema mapping from descriptors with template fallback."""
    schema: Dict[str, PolicySchema] = {}
    descriptor_schemas = _descriptor_schema_map(descriptors)
    schema.update(descriptor_schemas)
    if template_path.exists() and template_path.suffix in {".yaml", ".yml"}:
        template_schema = _load_schema_from_yaml(template_path)
        for policy_id, entry in template_schema.items():
            if policy_id not in schema:
                schema[policy_id] = entry
    elif template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        for match in POLICY_BLOCK_RE.finditer(content):
            metadata_block = match.group(2).strip()
            order, values = parse_metadata_block(metadata_block)
            policy_id = ""
            if "id" in values and values["id"]:
                policy_id = values["id"][0]
            if not policy_id:
                continue
            if policy_id not in schema:
                schema[policy_id] = PolicySchema(tuple(order), values)
    return schema


def build_metadata_schema(repo_root: Path) -> Dict[str, PolicySchema]:
    """Return the metadata schema derived from AGENTS and descriptors."""

    template_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "AGENTS.md"
    )
    discovered = _discover_policy_sources(repo_root)
    descriptors = _load_descriptors(repo_root, discovered)
    return _build_schema(template_path, descriptors)


def export_metadata_schema(
    repo_root: Path,
    *,
    schema: Dict[str, PolicySchema] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write the metadata schema YAML under devcovenant/registry/global."""

    schema = schema or build_metadata_schema(repo_root)
    payload: Dict[str, object] = {"policies": {}}
    for policy_id in sorted(schema):
        entry = schema[policy_id]
        defaults: Dict[str, List[str]] = {}
        for key in entry.keys:
            raw_default = entry.defaults.get(key)
            defaults[key] = list(raw_default) if raw_default else []
        payload["policies"][policy_id] = {
            "keys": list(entry.keys),
            "defaults": defaults,
        }
    if output_path is None:
        output_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_metadata_schema.yaml"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return output_path


def load_metadata_schema(repo_root: Path) -> Dict[str, PolicySchema]:
    """Return the canonical metadata schema, loading the YAML if available."""
    schema_path = policy_metadata_schema_path(repo_root)
    discovered = _discover_policy_sources(repo_root)
    descriptors = _load_descriptors(repo_root, discovered)
    if schema_path.exists():
        return _build_schema(schema_path, descriptors)
    return build_metadata_schema(repo_root)


def _normalize_values(
    policy_id: str,
    current_order: List[str],
    current_values: Dict[str, List[str]],
    schema: Dict[str, PolicySchema],
    metadata_mode: str,
    is_custom: bool,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return normalized metadata order and values for a policy."""
    if policy_id in schema:
        schema_keys = list(schema[policy_id].keys)
        defaults = schema[policy_id].defaults
    else:
        schema_keys = list(_COMMON_KEYS)
        defaults = _COMMON_DEFAULTS

    extras = [key for key in current_order if key not in schema_keys]
    if is_custom:
        ordered_keys = [
            key for key in schema_keys if key in current_values
        ] + extras
        ordered_values = {
            key: list(current_values[key])
            for key in ordered_keys
            if key in current_values
        }
        for key in ordered_values:
            ordered_values[key] = _dedupe(ordered_values[key])
        return ordered_keys, ordered_values

    ordered_keys = schema_keys + extras
    values: Dict[str, List[str]] = {}
    use_stock = metadata_mode == "stock"
    for key in ordered_keys:
        current = current_values.get(key, [])
        canonical = list(defaults.get(key, []))
        if use_stock and canonical:
            values[key] = _dedupe(list(canonical))
        elif current:
            values[key] = _dedupe(list(current))
        elif canonical:
            values[key] = _dedupe(list(canonical))
        else:
            values[key] = []
    return _apply_selector_roles(ordered_keys, values)


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
    schema_path: Path,
    *,
    metadata_mode: str = "preserve",
    set_updated: bool = True,
    repo_root: Path | None = None,
) -> RefreshResult:
    """Refresh the policy block metadata and ordering inside AGENTS.md."""
    if metadata_mode not in _METADATA_MODES:
        raise ValueError(f"Unsupported metadata mode: {metadata_mode}")
    if not agents_path.exists():
        return RefreshResult((), (), False, metadata_mode)

    repo_root = repo_root or agents_path.parent
    # Keep the canonical schema in sync with current descriptors before use.
    generate_policy_metadata_schema(repo_root)
    discovered = _discover_policy_sources(repo_root)
    descriptors = _load_descriptors(repo_root, discovered)
    control = load_policy_control_config(repo_root)
    schema_source = _choose_schema_source(repo_root, schema_path)
    schema = _build_schema(schema_source, descriptors)
    stock_texts = _load_stock_texts(repo_root)
    active_profiles = _load_active_profiles(repo_root)
    content = agents_path.read_text(encoding="utf-8")
    try:
        block_start, block_end, block_text = _locate_policy_block(content)
    except ValueError:
        return RefreshResult((), (), False, metadata_mode)

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
        core_available = bool(source_flags.get("core"))
        if descriptor:
            base_order, base_values = descriptor_metadata_order_values(
                descriptor
            )
        else:
            base_order, base_values = order, values
        base_order = list(base_order)
        base_values = {key: list(vals) for key, vals in base_values.items()}
        order, values = apply_policy_control_overrides(
            base_order,
            base_values,
            policy_id,
            control,
            core_available=core_available,
        )
        custom_for_norm = (
            values.get("custom", ["false"])[0].strip().lower() == "true"
        )
        normalized_order, normalized_values = _normalize_values(
            policy_id,
            order,
            values,
            schema,
            metadata_mode,
            custom_for_norm,
        )
        apply_flag = (
            normalized_values.get("apply", ["true"])[0].strip().lower()
            == "true"
        )
        custom_flag = (
            normalized_values.get("custom", ["false"])[0].strip().lower()
            == "true"
        )
        scopes = _split_values(normalized_values.get("profile_scopes", []))
        if not scopes:
            scopes = ["global"]
        if not _scopes_match(scopes, active_profiles):
            skipped.append(policy_id)
            continue
        rendered = _render_metadata_block(normalized_order, normalized_values)
        metadata_changed = rendered != metadata_block
        if metadata_changed and set_updated and apply_flag and not custom_flag:
            normalized_values["updated"] = ["true"]
            rendered = _render_metadata_block(
                normalized_order, normalized_values
            )
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
        descriptor = descriptors.get(policy_id)
        if descriptor:
            base_order, base_values = descriptor_metadata_order_values(
                descriptor
            )
        else:
            base_order = ["id"]
            base_values = {"id": [policy_id]}
            if source_flags.get("custom"):
                base_values["custom"] = ["true"]
        base_order = list(base_order)
        base_values = {key: list(vals) for key, vals in base_values.items()}
        override_order, override_values = apply_policy_control_overrides(
            base_order,
            base_values,
            policy_id,
            control,
            core_available=core_available,
        )
        custom_override_flag = (
            override_values.get("custom", ["false"])[0].strip().lower()
            == "true"
        )
        normalized_order, normalized_values = _normalize_values(
            policy_id,
            override_order,
            override_values,
            schema,
            metadata_mode,
            custom_override_flag,
        )
        if source_flags.get("custom"):
            normalized_values["custom"] = ["true"]
            if "custom" not in normalized_order:
                normalized_order.append("custom")
        normalized_values.setdefault("id", [policy_id])
        scopes = _split_values(normalized_values.get("profile_scopes", []))
        if not scopes:
            scopes = ["global"]
        if not _scopes_match(scopes, active_profiles):
            skipped.append(policy_id)
            continue
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
        return RefreshResult((), tuple(skipped), False, metadata_mode)

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
    return RefreshResult(
        tuple(changed), tuple(skipped), updated, metadata_mode
    )
