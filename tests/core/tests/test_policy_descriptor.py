"""Tests for policy descriptor helpers."""

from pathlib import Path

import yaml

from devcovenant.core.policy_descriptor import load_policy_descriptor


def test_loads_changelog_descriptor():
    """Ensure the changelog coverage descriptor exposes expected metadata."""

    repo_root = Path(__file__).resolve().parents[3]
    descriptor = load_policy_descriptor(repo_root, "changelog-coverage")

    assert descriptor is not None
    assert descriptor.policy_id == "changelog-coverage"
    assert descriptor.metadata.get("severity") == "error"
    assert descriptor.metadata.get("main_changelog") == ["CHANGELOG.md"]


def test_descriptors_do_not_define_activation_scope_keys() -> None:
    """Policy descriptors must not carry retired activation scope keys."""
    repo_root = Path(__file__).resolve().parents[3]
    forbidden = {"profile_scopes", "policy_scopes"}
    for policy_root in (
        repo_root / "devcovenant" / "core" / "policies",
        repo_root / "devcovenant" / "custom" / "policies",
    ):
        for policy_dir in policy_root.iterdir():
            if not policy_dir.is_dir() or policy_dir.name.startswith("_"):
                continue
            descriptor_path = policy_dir / f"{policy_dir.name}.yaml"
            payload = yaml.safe_load(
                descriptor_path.read_text(encoding="utf-8")
            )
            metadata = payload.get("metadata", {})
            present = forbidden.intersection(metadata.keys())
            assert not present, (
                f"{descriptor_path} contains retired scope keys: "
                f"{sorted(present)}"
            )
