"""Helpers for locating policy scripts and patches."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PolicyScriptLocation:
    """Resolved policy script location."""

    kind: str
    path: Path
    module: str


def _script_name(policy_id: str) -> str:
    """Return the Python module name for a policy id."""
    return policy_id.replace("-", "_")


def iter_script_locations(
    repo_root: Path,
    policy_id: str,
) -> Iterable[PolicyScriptLocation]:
    """Yield candidate script locations in priority order."""
    script_name = _script_name(policy_id)
    devcov_dir = repo_root / "devcovenant"
    candidates = [
        (
            "custom",
            devcov_dir / "custom_policy_scripts" / f"{script_name}.py",
            f"devcovenant.custom_policy_scripts.{script_name}",
        ),
        (
            "common",
            devcov_dir / "common_policy_scripts" / f"{script_name}.py",
            f"devcovenant.common_policy_scripts.{script_name}",
        ),
        (
            "compat",
            devcov_dir / "policy_scripts" / f"{script_name}.py",
            f"devcovenant.policy_scripts.{script_name}",
        ),
    ]
    for kind, path, module in candidates:
        yield PolicyScriptLocation(kind=kind, path=path, module=module)


def resolve_script_location(
    repo_root: Path, policy_id: str
) -> PolicyScriptLocation | None:
    """Return the first existing policy script location, if any."""
    for location in iter_script_locations(repo_root, policy_id):
        if location.path.exists():
            return location
    return None


def patch_path(repo_root: Path, policy_id: str) -> Path:
    """Return the patch path for a policy id."""
    script_name = _script_name(policy_id)
    return (
        repo_root
        / "devcovenant"
        / "common_policy_patches"
        / f"{script_name}.yml"
    )
