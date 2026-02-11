"""Unit tests for refresh command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant import install, refresh


def _unit_test_refresh_builds_local_registries_and_agents() -> None:
    """refresh_repo should build local registries and render AGENTS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        profile_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "profile_registry.yaml"
        )
        agents_path = repo_root / "AGENTS.md"

        assert policy_registry.exists()
        assert profile_registry.exists()
        assert agents_path.exists()


def _unit_test_refresh_updates_managed_block_only() -> None:
    """refresh_repo should update managed block without replacing full doc."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        readme = repo_root / "README.md"
        readme.write_text(
            "# User README\n\n"
            "<!-- DEVCOV:BEGIN -->\nold\n<!-- DEVCOV:END -->\n\n"
            "User body\n",
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = readme.read_text(encoding="utf-8")
        assert "User body" in updated
        assert "Doc ID:" in updated


def _unit_test_refresh_updates_all_managed_blocks() -> None:
    """refresh_repo should update every managed block in AGENTS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        agents.write_text(
            "# AGENTS\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old top block\n"
            "<!-- DEVCOV:END -->\n\n"
            "# EDITABLE SECTION\n\n"
            "keep me\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old secondary block\n"
            "<!-- DEVCOV:END -->\n\n"
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "<!-- DEVCOV-POLICIES:END -->\n",
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = agents.read_text(encoding="utf-8")
        assert "old top block" not in updated
        assert "old secondary block" not in updated
        assert "keep me" in updated
        assert "## THE DEV COVENANT" in updated


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_refresh_builds_local_registries_and_agents(self):
        """Run test_refresh_builds_local_registries_and_agents."""
        _unit_test_refresh_builds_local_registries_and_agents()

    def test_refresh_updates_managed_block_only(self):
        """Run test_refresh_updates_managed_block_only."""
        _unit_test_refresh_updates_managed_block_only()

    def test_refresh_updates_all_managed_blocks(self):
        """Run test_refresh_updates_all_managed_blocks."""
        _unit_test_refresh_updates_all_managed_blocks()
