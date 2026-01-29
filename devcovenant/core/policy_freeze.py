"""Helpers for policy freeze overrides."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

from devcovenant.core.parser import PolicyDefinition


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
