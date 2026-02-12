"""Unit tests for undeploy command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant import install, refresh, undeploy


def _unit_test_undeploy_removes_registry_local_and_managed_blocks() -> None:
    """undeploy_repo should remove local registry and managed doc blocks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        refresh.refresh_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        assert "<!-- DEVCOV:BEGIN -->" in agents.read_text(encoding="utf-8")
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" in agents.read_text(
            encoding="utf-8"
        )

        result = undeploy.undeploy_repo(repo_root)
        assert result == 0

        registry_local = repo_root / "devcovenant" / "registry" / "local"
        assert not registry_local.exists()

        updated_agents = agents.read_text(encoding="utf-8")
        assert "<!-- DEVCOV:BEGIN -->" not in updated_agents
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" not in updated_agents


def _unit_test_undeploy_removes_generated_gitignore_fragments() -> None:
    """undeploy_repo should keep user gitignore entries only."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        refresh.refresh_repo(repo_root)

        gitignore_path = repo_root / ".gitignore"
        existing = gitignore_path.read_text(encoding="utf-8")
        marker = "# --- User entries (preserved) ---\n\n"
        assert marker in existing
        updated = existing.replace(
            marker,
            marker + "# keep-me\nlocal-only/\n\n",
            1,
        )
        gitignore_path.write_text(updated, encoding="utf-8")

        result = undeploy.undeploy_repo(repo_root)
        assert result == 0

        post = gitignore_path.read_text(encoding="utf-8")
        assert "# keep-me" in post
        assert "local-only/" in post
        assert "# DevCovenant base ignores" not in post
        assert "# Profile: data" not in post
        assert "# --- User entries (preserved) ---" not in post
        assert "# --- End user entries ---" not in post


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_undeploy_removes_registry_local_and_managed_blocks(self):
        """Run test_undeploy_removes_registry_local_and_managed_blocks."""
        _unit_test_undeploy_removes_registry_local_and_managed_blocks()

    def test_undeploy_removes_generated_gitignore_fragments(self):
        """Run test_undeploy_removes_generated_gitignore_fragments."""
        _unit_test_undeploy_removes_generated_gitignore_fragments()
