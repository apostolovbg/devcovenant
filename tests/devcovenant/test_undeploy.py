"""Unit tests for undeploy command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import undeploy
from tests.devcovenant import repo_seed_cache


def _unit_test_undeploy_removes_registry_state_and_managed_blocks() -> None:
    """undeploy_repo should remove registry state and managed doc blocks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        assert "<!-- DEVCOV:BEGIN -->" in agents.read_text(encoding="utf-8")
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" in agents.read_text(
            encoding="utf-8"
        )

        result = undeploy.undeploy_repo(repo_root)
        assert result == 0

        runtime_registry = repo_root / "devcovenant" / "registry" / "runtime"
        tracked_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        assert not runtime_registry.exists()
        assert not tracked_registry.exists()

        updated_agents = agents.read_text(encoding="utf-8")
        assert "<!-- DEVCOV:BEGIN -->" not in updated_agents
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" not in updated_agents


def _unit_test_undeploy_removes_generated_gitignore_fragments() -> None:
    """undeploy_repo should keep user gitignore entries only."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

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


def _unit_test_undeploy_recovers_when_config_is_invalid() -> None:
    """undeploy_repo should still clean managed blocks with broken config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        assert "<!-- DEVCOV:BEGIN -->" in agents.read_text(encoding="utf-8")
        script_path = repo_root / "example.py"
        script_path.write_text(
            'MARKER = "<!-- DEVCOV:BEGIN --> literal"\n',
            encoding="utf-8",
        )

        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.write_text(":\n", encoding="utf-8")

        result = undeploy.undeploy_repo(repo_root)
        assert result == 0
        assert "<!-- DEVCOV:BEGIN -->" not in agents.read_text(
            encoding="utf-8"
        )
        assert script_path.read_text(encoding="utf-8").strip() == (
            'MARKER = "<!-- DEVCOV:BEGIN --> literal"'
        )


def _unit_test_undeploy_run_calls_undeploy_repo() -> None:
    """run() should resolve repo root and delegate to undeploy_repo."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with patch(
            "devcovenant.undeploy.resolve_repo_root",
            return_value=repo_root,
        ):
            with patch(
                "devcovenant.undeploy.undeploy_repo",
                return_value=0,
            ) as mock:
                result = undeploy.run(SimpleNamespace())
    assert result == 0
    mock.assert_called_once_with(repo_root)


def _unit_test_undeploy_main_exits_with_run_code() -> None:
    """main() should parse args, call run, and exit with its code."""
    captured: dict[str, object] = {}
    original_run = undeploy.run

    def _fake_run(args):
        """Capture parsed args and return a stable exit code."""
        captured["args"] = args
        return 0

    undeploy.run = _fake_run
    try:
        try:
            undeploy.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from main().")
    finally:
        undeploy.run = original_run

    assert code == 0
    assert hasattr(captured["args"], "__dict__")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_undeploy_removes_registry_state_and_managed_blocks(self):
        """Run test_undeploy_removes_registry_state_and_managed_blocks."""
        _unit_test_undeploy_removes_registry_state_and_managed_blocks()

    def test_undeploy_removes_generated_gitignore_fragments(self):
        """Run test_undeploy_removes_generated_gitignore_fragments."""
        _unit_test_undeploy_removes_generated_gitignore_fragments()

    def test_undeploy_recovers_when_config_is_invalid(self):
        """Run test_undeploy_recovers_when_config_is_invalid."""
        _unit_test_undeploy_recovers_when_config_is_invalid()

    def test_undeploy_run_calls_undeploy_repo(self):
        """Run test_undeploy_run_calls_undeploy_repo."""
        _unit_test_undeploy_run_calls_undeploy_repo()

    def test_undeploy_main_exits_with_run_code(self):
        """Run test_undeploy_main_exits_with_run_code."""
        _unit_test_undeploy_main_exits_with_run_code()
