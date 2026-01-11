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


@dataclass(frozen=True)
class PolicyPatchLocation:
    """Resolved policy patch location."""

    kind: str
    path: Path


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
            devcov_dir / "custom" / "policy_scripts" / f"{script_name}.py",
            f"devcovenant.custom.policy_scripts.{script_name}",
        ),
        (
            "core",
            devcov_dir / "core" / "policy_scripts" / f"{script_name}.py",
            f"devcovenant.core.policy_scripts.{script_name}",
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
    """Return the default patch path for a policy id."""
    script_name = _script_name(policy_id)
    return (
        repo_root
        / "devcovenant"
        / "common_policy_patches"
        / f"{script_name}.py"
    )


def iter_patch_locations(
    repo_root: Path, policy_id: str
) -> Iterable[PolicyPatchLocation]:
    """Yield candidate patch locations in priority order."""
    script_name = _script_name(policy_id)
    patch_dir = repo_root / "devcovenant" / "common_policy_patches"
    candidates = [
        ("py", patch_dir / f"{script_name}.py"),
        ("yaml", patch_dir / f"{script_name}.yml"),
        ("yaml", patch_dir / f"{script_name}.yaml"),
        ("json", patch_dir / f"{script_name}.json"),
    ]
    for kind, path in candidates:
        yield PolicyPatchLocation(kind=kind, path=path)


def resolve_patch_location(
    repo_root: Path, policy_id: str
) -> PolicyPatchLocation | None:
    """Return the first existing patch location, if any."""
    for location in iter_patch_locations(repo_root, policy_id):
        if location.path.exists():
            return location
    return None
