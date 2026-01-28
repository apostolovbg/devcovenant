"""Refresh policy metadata and grouping inside AGENTS.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

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
                return {
                    str(key): str(value) for key, value in json_payload.items()
                }
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


def _build_schema(template_path: Path) -> Dict[str, PolicySchema]:
    """Build policy schema mapping from the template AGENTS file."""
    schema: Dict[str, PolicySchema] = {}
    if not template_path.exists():
        return schema
    content = template_path.read_text(encoding="utf-8")
    for match in POLICY_BLOCK_RE.finditer(content):
        metadata_block = match.group(2).strip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = ""
        if "id" in values and values["id"]:
            policy_id = values["id"][0]
        if not policy_id:
            continue
        schema[policy_id] = PolicySchema(tuple(order), values)
    return schema


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
        return ordered_keys, ordered_values

    ordered_keys = schema_keys + extras
    values: Dict[str, List[str]] = {}
    use_stock = metadata_mode == "stock"
    for key in ordered_keys:
        current = current_values.get(key, [])
        canonical = list(defaults.get(key, []))
        if use_stock and canonical:
            values[key] = list(canonical)
        elif current:
            values[key] = list(current)
        elif canonical:
            values[key] = list(canonical)
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
) -> RefreshResult:
    """Refresh the policy block metadata and ordering inside AGENTS.md."""
    if metadata_mode not in _METADATA_MODES:
        raise ValueError(f"Unsupported metadata mode: {metadata_mode}")
    if not agents_path.exists():
        return RefreshResult((), (), False, metadata_mode)

    repo_root = agents_path.parent
    schema = _build_schema(schema_path)
    stock_texts = _load_stock_texts(repo_root)
    discovered = _discover_policy_sources(repo_root)
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
        description = match.group(3).rstrip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0] if values.get("id") else ""
        if not policy_id:
            skipped.append("unknown")
            continue

        seen_ids.add(policy_id)
        custom_flag = (
            values.get("custom", ["false"])[0].strip().lower() == "true"
        )
        apply_flag = values.get("apply", ["true"])[0].strip().lower() == "true"
        normalized_order, normalized_values = _normalize_values(
            policy_id,
            order,
            values,
            schema,
            metadata_mode,
            custom_flag,
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
        base_values: Dict[str, List[str]] = {"id": [policy_id]}
        if source_flags.get("custom"):
            base_values["custom"] = ["true"]
        normalized_order, normalized_values = _normalize_values(
            policy_id,
            list(base_values.keys()),
            base_values,
            schema,
            metadata_mode,
            False,
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
        description = stock_texts.get(policy_id, "Policy description pending.")
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
                custom=bool(source_flags.get("custom")),
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
