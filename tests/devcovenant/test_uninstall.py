"""Unit tests for uninstall command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import uninstall
from tests import copy_installed_repo, copy_refreshed_repo


def _unit_test_uninstall_removes_devcovenant_package() -> None:
    """uninstall_repo should remove the repository devcovenant directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        package_dir = repo_root / "devcovenant"
        assert package_dir.exists()

        result = uninstall.uninstall_repo(repo_root)
        assert result == 0
        assert not package_dir.exists()


def _unit_test_uninstall_recovers_when_config_is_invalid() -> None:
    """uninstall_repo should remove package even with invalid config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.write_text(":\n", encoding="utf-8")

        package_dir = repo_root / "devcovenant"
        assert package_dir.exists()

        result = uninstall.uninstall_repo(repo_root)
        assert result == 0
        assert not package_dir.exists()


def _unit_test_uninstall_run_calls_uninstall_repo() -> None:
    """run() should resolve repo root and delegate to uninstall_repo."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with patch(
            "devcovenant.core.execution.resolve_repo_root",
            return_value=repo_root,
        ):
            with patch(
                "devcovenant.uninstall.uninstall_repo",
                return_value=0,
            ) as mock:
                result = uninstall.run(SimpleNamespace())
    assert result == 0
    mock.assert_called_once_with(repo_root)


def _unit_test_uninstall_main_exits_with_run_code() -> None:
    """main() should parse args, call run, and exit with its code."""
    captured: dict[str, object] = {}
    original_run = uninstall.run

    def _fake_run(args):
        """Capture parsed args and return a stable exit code."""
        captured["args"] = args
        return 0

    uninstall.run = _fake_run
    try:
        try:
            uninstall.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from main().")
    finally:
        uninstall.run = original_run

    assert code == 0
    assert hasattr(captured["args"], "__dict__")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_uninstall_removes_devcovenant_package(self):
        """Run test_uninstall_removes_devcovenant_package."""
        _unit_test_uninstall_removes_devcovenant_package()

    def test_uninstall_recovers_when_config_is_invalid(self):
        """Run test_uninstall_recovers_when_config_is_invalid."""
        _unit_test_uninstall_recovers_when_config_is_invalid()

    def test_uninstall_run_calls_uninstall_repo(self):
        """Run test_uninstall_run_calls_uninstall_repo."""
        _unit_test_uninstall_run_calls_uninstall_repo()

    def test_uninstall_main_exits_with_run_code(self):
        """Run test_uninstall_main_exits_with_run_code."""
        _unit_test_uninstall_main_exits_with_run_code()
