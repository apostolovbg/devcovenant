"""Refresh policies, registry, and profile catalog in one command."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from devcovenant.core import manifest as manifest_module
from devcovenant.core import profiles
from devcovenant.core.refresh_policies import refresh_policies, RefreshResult
from devcovenant.core.update_policy_registry import update_policy_registry


def _schema_path(repo_root: Path) -> Path:
    return (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "AGENTS.md"
    )


def refresh_all(
    repo_root: Path | None = None,
    *,
    metadata_mode: str = "preserve",
    schema_path: Path | None = None,
) -> int:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    agents_path = repo_root / "AGENTS.md"
    schema = schema_path or _schema_path(repo_root)
    result = refresh_policies(
        agents_path,
        schema,
        metadata_mode=metadata_mode,
        set_updated=True,
    )
    if result.changed_policies:
        joined = ", ".join(result.changed_policies)
        print(
            f"refresh-policies updated metadata for: {joined}"
            f" ({result.metadata_mode} mode)"
        )
    if result.skipped_policies:
        print("Skipped policies with missing ids:")
        for policy_id in result.skipped_policies:
            print(f"- {policy_id}")
    policy_result = update_policy_registry(repo_root)
    if policy_result != 0:
        return policy_result
    catalog = profiles.build_profile_catalog(repo_root)
    profiles.write_profile_catalog(repo_root, catalog)
    print("Rebuilt profile catalog at", profiles.REGISTRY_CATALOG)
    return 0


def main() -> int:
    return refresh_all()


if __name__ == "__main__":
    raise SystemExit(main())
