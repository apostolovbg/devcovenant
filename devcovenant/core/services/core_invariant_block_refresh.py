"""AGENTS core-invariant block refresh helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import yaml

from devcovenant.core.services import (
    core_invariants as core_invariants_service,
)
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.tracked_registry import policy_registry_path


@dataclass(frozen=True)
class RefreshResult:
    """Summary of core-invariant block refresh work."""

    changed_invariants: Tuple[str, ...]
    updated: bool


def _read_yaml(path: Path) -> dict[str, object]:
    """Load a YAML mapping payload from disk."""
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


def _locate_block(text: str) -> tuple[int, int, str]:
    """Return the span and content for the AGENTS core-invariant block."""
    begin_marker = core_invariants_service.CORE_INVARIANTS_BEGIN
    end_marker = core_invariants_service.CORE_INVARIANTS_END
    try:
        start = text.index(begin_marker)
        end = text.index(end_marker, start + len(begin_marker))
    except ValueError as exc:
        raise ValueError(
            "Core-invariant block markers not found in AGENTS.md"
        ) from exc
    block_start = start
    block_end = end + len(end_marker)
    return block_start, block_end, text[block_start:block_end]


def _ensure_block_scaffold(
    agents_path: Path, content: str
) -> tuple[str, bool]:
    """Ensure AGENTS contains one empty core-invariant block scaffold."""
    begin_marker = core_invariants_service.CORE_INVARIANTS_BEGIN
    end_marker = core_invariants_service.CORE_INVARIANTS_END
    has_begin = begin_marker in content
    has_end = end_marker in content
    if has_begin and has_end:
        return content, False
    policy_marker = "<!-- DEVCOV-POLICIES:BEGIN -->"
    scaffold = f"{begin_marker}\n{end_marker}\n"
    if policy_marker in content:
        rebuilt = content.replace(
            policy_marker, scaffold + "\n" + policy_marker, 1
        )
    else:
        rebuilt = content.rstrip() + "\n\n" + scaffold
    agents_path.write_text(rebuilt, encoding="utf-8")
    return rebuilt, True


def refresh_agents_core_invariant_block(
    agents_path: Path,
    schema_path: Path | None,
    *,
    repo_root: Path | None = None,
) -> RefreshResult:
    """Refresh the AGENTS core-invariant block from registry data."""
    del schema_path
    if not agents_path.exists():
        return RefreshResult((), False)
    repo_root = repo_root or agents_path.parent
    content = agents_path.read_text(encoding="utf-8")
    scaffolded = False
    try:
        block_start, block_end, block_text = _locate_block(content)
    except ValueError:
        content, scaffolded = _ensure_block_scaffold(agents_path, content)
        block_start, block_end, block_text = _locate_block(content)

    registry_path = policy_registry_path(repo_root)
    if not registry_path.exists():
        return RefreshResult((), scaffolded)
    payload = _read_yaml(registry_path)
    invariants = payload.get("core-invariants", {})
    if not isinstance(invariants, dict):
        raise ValueError(
            "Registry payload is invalid; expected "
            f"`core-invariants` mapping in {registry_path}."
        )
    new_block = core_invariants_service.render_core_invariants_block(
        invariants
    )
    if not new_block:
        return RefreshResult((), scaffolded)
    updated = new_block.strip() != block_text.strip()
    if updated:
        rebuilt = content[:block_start] + new_block + content[block_end:]
        agents_path.write_text(rebuilt, encoding="utf-8")
    changed_ids = tuple(sorted(invariants)) if updated or scaffolded else ()
    return RefreshResult(changed_ids, updated or scaffolded)
