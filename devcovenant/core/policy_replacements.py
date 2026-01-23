"""Helpers for policy replacement metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml

_DEFAULT_REPLACEMENTS = Path("devcovenant/core/policy_replacements.yaml")


@dataclass(frozen=True)
class PolicyReplacement:
    """Replacement metadata for a policy."""

    policy_id: str
    replaced_by: str
    note: str | None = None


def load_policy_replacements(repo_root: Path) -> Dict[str, PolicyReplacement]:
    """Load policy replacement mappings from YAML."""
    path = repo_root / _DEFAULT_REPLACEMENTS
    if not path.exists():
        return {}
    replacements_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = (
        replacements_data.get("replacements", {})
        if isinstance(replacements_data, dict)
        else {}
    )
    replacements: Dict[str, PolicyReplacement] = {}
    for policy_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        replaced_by = str(payload.get("replaced_by", "")).strip()
        if not replaced_by:
            continue
        note = payload.get("note")
        replacements[policy_id] = PolicyReplacement(
            policy_id=policy_id,
            replaced_by=replaced_by,
            note=note,
        )
    return replacements
