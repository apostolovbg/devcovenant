"""Helpers for policy freeze and replacement metadata handling."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml

from devcovenant.core.parser import PolicyDefinition

_DEFAULT_REPLACEMENTS = (
    Path("devcovenant") / "registry" / "global" / "policy_replacements.yaml"
)


@dataclass(frozen=True)
class PolicyReplacement:
    """Replacement metadata for a policy."""

    policy_id: str
    replaced_by: str
    note: str | None = None


def _script_name(policy_id: str) -> str:
    """Return the Python module name for a policy id."""
    return policy_id.replace("-", "_")


def _core_policy_dir(repo_root: Path, policy_id: str) -> Path:
    """Return the core policy directory for the given policy."""
    script_name = _script_name(policy_id)
    return repo_root / "devcovenant" / "core" / "policies" / script_name


def _custom_policy_dir(repo_root: Path, policy_id: str) -> Path:
    """Return the custom override directory for the given policy."""
    script_name = _script_name(policy_id)
    return repo_root / "devcovenant" / "custom" / "policies" / script_name


def _copy_policy_dir(core_dir: Path, custom_dir: Path) -> bool:
    """Mirror the core policy directory inside the custom overrides."""
    if not core_dir.exists():
        return False
    if custom_dir.exists():
        shutil.rmtree(custom_dir)
    shutil.copytree(core_dir, custom_dir)
    return True


def _remove_policy_dir(custom_dir: Path) -> bool:
    """Delete the custom override directory, if present."""
    if not custom_dir.exists():
        return False
    shutil.rmtree(custom_dir)
    return True


def apply_policy_freeze(
    repo_root: Path,
    policies: Iterable[PolicyDefinition],
) -> Tuple[bool, List[str]]:
    """Apply policy freeze overrides for policies with `freeze: true`."""
    changed = False
    messages: List[str] = []
    for policy in policies:
        if getattr(policy, "custom", False):
            continue
        freeze_flag = getattr(policy, "freeze", False)
        core_dir = _core_policy_dir(repo_root, policy.policy_id)
        custom_dir = _custom_policy_dir(repo_root, policy.policy_id)
        if freeze_flag:
            copied = _copy_policy_dir(core_dir, custom_dir)
            if copied:
                changed = True
                messages.append(
                    (
                        f"Policy '{policy.policy_id}' frozen into custom "
                        "overrides."
                    )
                )
        else:
            removed = _remove_policy_dir(custom_dir)
            if removed:
                changed = True
                messages.append(
                    (
                        f"Policy '{policy.policy_id}' unfrozen; custom "
                        "overrides removed."
                    )
                )
    return changed, messages


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
