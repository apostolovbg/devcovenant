"""Unit tests for the managed doc assets policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core.base import CheckContext
from devcovenant.core.repo_refresh import refresh_repo
from devcovenant.custom.policies.managed_doc_assets.managed_doc_assets import (
    ManagedDocAssetsCheck,
)


def _load_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _dump_yaml(path: Path, payload: dict[str, object]) -> None:
    """Write YAML mapping payload to disk."""
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _policy_violations(repo_root: Path) -> list[str]:
    """Run managed doc policy and return violation messages."""
    check = ManagedDocAssetsCheck()
    context = CheckContext(repo_root=repo_root)
    return [violation.message for violation in check.check(context)]


def _unit_test_generated_metadata_managed_blocks_pass() -> None:
    """Policy should pass after refresh with generated metadata lines."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        assert refresh_repo(repo_root) == 0

        messages = _policy_violations(repo_root)
        assert not any("Managed block for " in message for message in messages)
        assert not any(
            "must not duplicate Doc ID/Doc Type/Managed By lines" in message
            for message in messages
        )


def _unit_test_descriptor_metadata_duplication_is_rejected() -> None:
    """Policy should reject descriptors that duplicate generated metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        assert refresh_repo(repo_root) == 0

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "global"
            / "assets"
            / "CONTRIBUTING.yaml"
        )
        descriptor = _load_yaml(descriptor_path)
        managed_block = str(descriptor.get("managed_block", "")).strip("\n")
        descriptor["managed_block"] = "\n".join(
            [
                "**Doc ID:** CONTRIBUTING",
                managed_block,
            ]
        )
        _dump_yaml(descriptor_path, descriptor)

        messages = _policy_violations(repo_root)
        assert any(
            "must not duplicate Doc ID/Doc Type/Managed By lines" in message
            for message in messages
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_generated_metadata_managed_blocks_pass(self):
        """Run test_generated_metadata_managed_blocks_pass."""
        _unit_test_generated_metadata_managed_blocks_pass()

    def test_descriptor_metadata_duplication_is_rejected(self):
        """Run test_descriptor_metadata_duplication_is_rejected."""
        _unit_test_descriptor_metadata_duplication_is_rejected()
