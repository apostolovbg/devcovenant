"""Unit tests for devcovenant.core.repo_refresh orchestration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant import install
from devcovenant.core import repo_refresh as core_refresh


def _unit_test_refresh_repo_builds_policy_registry() -> None:
    """core refresh should materialize local policy registry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        assert registry_path.exists()


def _unit_test_refresh_repo_updates_agents_policy_block() -> None:
    """core refresh should keep AGENTS policy block populated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        agents_path = repo_root / "AGENTS.md"
        content = agents_path.read_text(encoding="utf-8")
        assert "<!-- DEVCOV-POLICIES:BEGIN -->" in content
        assert "## Policy:" in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for core refresh coverage."""

    def test_refresh_repo_builds_policy_registry(self):
        """Run test_refresh_repo_builds_policy_registry."""
        _unit_test_refresh_repo_builds_policy_registry()

    def test_refresh_repo_updates_agents_policy_block(self):
        """Run test_refresh_repo_updates_agents_policy_block."""
        _unit_test_refresh_repo_updates_agents_policy_block()
