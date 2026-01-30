"""Tests for policy descriptor helpers."""

from pathlib import Path

from devcovenant.core.policy_descriptor import load_policy_descriptor


def test_loads_changelog_descriptor():
    """Ensure the changelog coverage descriptor exposes expected metadata."""

    repo_root = Path(__file__).resolve().parents[3]
    descriptor = load_policy_descriptor(repo_root, "changelog-coverage")

    assert descriptor is not None
    assert descriptor.policy_id == "changelog-coverage"
    assert descriptor.metadata.get("severity") == "error"
    assert descriptor.metadata.get("main_changelog") == ["CHANGELOG.md"]
