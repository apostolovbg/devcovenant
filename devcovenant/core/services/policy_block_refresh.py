"""AGENTS policy-block refresh helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

import devcovenant.core.services.metadata as metadata_runtime
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.registry import (
    POLICY_BLOCK_RE,
    PolicyDescriptor,
    load_policy_descriptor,
    parse_metadata_block,
    policy_registry_path,
)

_POLICIES_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
_POLICIES_END = "<!-- DEVCOV-POLICIES:END -->"


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        raise ValueError(f"Missing YAML file: {path}")
    try:
        payload = yaml_cache_service.load_yaml(path)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read {path}: {exc}") from exc
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"YAML file must contain a mapping: {path}")


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
            normalized = metadata_runtime.split_metadata_values(
                [str(raw_value)]
            )
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
        rendered = metadata_runtime.render_metadata_block(order, values)
        section = f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        sections[policy_id] = section
    return sections


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
    if text:
        return text
    raise ValueError(
        f"Missing descriptor text for `{policy_id}`."
        " Set the `text` field in the policy descriptor YAML."
    )


def refresh_agents_policy_block(
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

    registry_path = policy_registry_path(repo_root)
    if not registry_path.exists():
        return RefreshResult((), (), scaffolded)
    payload = _read_yaml(registry_path)
    policies = payload.get("policies", {})
    if not isinstance(policies, dict) or not policies:
        raise ValueError(
            "Policy registry payload is invalid; expected non-empty "
            f"`policies` mapping in {registry_path}."
        )

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
        rendered = metadata_runtime.render_metadata_block(order, values)
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
