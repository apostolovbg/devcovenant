"""Refresh policies, registry, and profile catalog in one command."""

from __future__ import annotations

from pathlib import Path

import yaml

from devcovenant.core import manifest as manifest_module
from devcovenant.core import profiles
from devcovenant.core.install import (
    _ensure_custom_tree,
    _ensure_tests_mirror,
    _prune_devcovrepo_overrides,
    apply_autogen_metadata_overrides,
)
from devcovenant.core.refresh_policies import (
    export_metadata_schema,
    policy_metadata_schema_path,
    refresh_policies,
)
from devcovenant.core.update_policy_registry import update_policy_registry


def _schema_path(repo_root: Path) -> Path:
    """Return the schema path used for refresh-policies runs."""
    canonical = policy_metadata_schema_path(repo_root)
    if canonical.exists():
        return canonical
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
    registry_only: bool = False,
) -> int:
    """Refresh policies, registry, and profile catalog."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    agents_path = repo_root / "AGENTS.md"
    schema = schema_path or _schema_path(repo_root)
    if registry_only:
        return refresh_registry(repo_root, schema_path=schema)
    result = refresh_policies(
        agents_path,
        schema,
        metadata_mode=metadata_mode,
        set_updated=True,
    )
    export_metadata_schema(repo_root)
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
    if apply_autogen_metadata_overrides(repo_root):
        print("Updated autogen metadata overrides in config.yaml")
    include_core = _load_devcov_core_include(repo_root)
    _ensure_custom_tree(repo_root)
    _ensure_tests_mirror(repo_root, include_core)
    removed_overrides = _prune_devcovrepo_overrides(repo_root, include_core)
    if removed_overrides:
        manifest_module.append_notifications(
            repo_root,
            [
                (
                    "Removed devcovrepo-prefixed overrides:"
                    f" {', '.join(removed_overrides)}"
                )
            ],
        )
    return 0


def refresh_registry(
    repo_root: Path | None = None,
    *,
    schema_path: Path | None = None,
) -> int:
    """Refresh only registry assets without touching AGENTS or docs."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    # Regenerate schema to keep descriptors aligned.
    export_metadata_schema(repo_root)
    # Update registry hashes/metadata without toggling AGENTS updated flags.
    result = update_policy_registry(
        repo_root, skip_freeze=True, reset_updated_flags=False
    )
    if result != 0:
        return result
    # Rebuild profile catalog (lives under registry/local/, gitignored).
    catalog = profiles.build_profile_catalog(repo_root)
    profiles.write_profile_catalog(repo_root, catalog)
    print("Registry-only refresh completed (schema, hashes, profile catalog).")
    return 0


def _load_devcov_core_include(repo_root: Path) -> bool:
    """Return devcov_core_include from config.yaml when present."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return False
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("devcov_core_include", False))


def main() -> int:
    """CLI entry point."""
    return refresh_all()


if __name__ == "__main__":
    raise SystemExit(main())
