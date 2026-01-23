"""Normalize policy metadata blocks against a canonical schema."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from devcovenant.core.selectors import _normalize_globs

_POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)

_COMMON_KEYS = [
    "id",
    "status",
    "severity",
    "auto_fix",
    "updated",
    "applies_to",
    "enforcement",
    "apply",
    "custom",
]

_COMMON_DEFAULTS: Dict[str, List[str]] = {
    "status": ["active"],
    "severity": ["warning"],
    "auto_fix": ["false"],
    "updated": ["false"],
    "applies_to": ["*"],
    "enforcement": ["active"],
    "apply": ["true"],
    "custom": ["false"],
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


@dataclass(frozen=True)
class PolicySchema:
    """Schema for a policy metadata block."""

    keys: Tuple[str, ...]
    defaults: Dict[str, List[str]]


@dataclass(frozen=True)
class NormalizeResult:
    """Summary of normalization changes."""

    changed_policies: Tuple[str, ...]
    skipped_policies: Tuple[str, ...]
    updated: bool


def _parse_metadata_block(
    block: str,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered keys and per-key line values from a policy-def block."""
    order: List[str] = []
    values: Dict[str, List[str]] = {}
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
    for match in _POLICY_BLOCK_RE.finditer(content):
        metadata_block = match.group(2).strip()
        order, values = _parse_metadata_block(metadata_block)
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
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return normalized metadata order and values for a policy."""
    if policy_id in schema:
        schema_keys = list(schema[policy_id].keys)
        defaults = schema[policy_id].defaults
    else:
        schema_keys = list(_COMMON_KEYS)
        defaults = _COMMON_DEFAULTS

    extras = [key for key in current_order if key not in schema_keys]
    ordered_keys = schema_keys + extras
    values: Dict[str, List[str]] = {}
    for key in ordered_keys:
        if key in current_values:
            values[key] = current_values[key]
        elif key in defaults:
            values[key] = list(defaults[key])
        else:
            values[key] = []
    return _apply_selector_roles(ordered_keys, values)


def normalize_agents_metadata(
    agents_path: Path,
    schema_path: Path,
    *,
    set_updated: bool = True,
) -> NormalizeResult:
    """Normalize policy metadata blocks in AGENTS.md against schema."""
    if not agents_path.exists():
        return NormalizeResult((), (), False)

    schema = _build_schema(schema_path)
    content = agents_path.read_text(encoding="utf-8")
    changed: List[str] = []
    skipped: List[str] = []

    def _replace(match: re.Match[str]) -> str:
        """Return the updated policy block."""
        heading = match.group(1)
        metadata_block = match.group(2).strip()
        description = match.group(3)
        order, values = _parse_metadata_block(metadata_block)
        policy_id = ""
        if "id" in values and values["id"]:
            policy_id = values["id"][0]
        if not policy_id:
            skipped.append("unknown")
            return match.group(0)

        normalized_order, normalized_values = _normalize_values(
            policy_id, order, values, schema
        )
        rendered = _render_metadata_block(normalized_order, normalized_values)
        if rendered != metadata_block and set_updated:
            normalized_values["updated"] = ["true"]
            rendered = _render_metadata_block(
                normalized_order, normalized_values
            )
        if rendered != metadata_block:
            changed.append(policy_id)
        return f"{heading}```policy-def\n{rendered}\n```\n\n{description}"

    updated = False
    updated_content, count = _POLICY_BLOCK_RE.subn(_replace, content)
    if count and updated_content != content:
        agents_path.write_text(updated_content, encoding="utf-8")
        updated = True

    return NormalizeResult(tuple(changed), tuple(skipped), updated)
