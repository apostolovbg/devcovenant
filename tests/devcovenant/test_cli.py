"""Tests for top-level DevCovenant CLI behavior and command layout."""

from __future__ import annotations

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace

from devcovenant import cli
from tests.devcovenant.support import MonkeyPatch

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_COMMAND_MODULES = (
    "check",
    "gate",
    "test",
    "install",
    "deploy",
    "upgrade",
    "refresh",
    "uninstall",
    "undeploy",
    "update_lock",
)
LEGACY_HELPER_MODULES = (
    "run_pre_commit",
    "run_tests",
    "update_test_status",
)
ASSET_SCRIPT_ROOT = (
    REPO_ROOT
    / "devcovenant"
    / "core"
    / "profiles"
    / "global"
    / "assets"
    / "devcovenant"
)


def _unit_test_cli_dispatches_command_and_args(monkeypatch) -> None:
    """CLI should dispatch to command module main with remaining args."""
    captured: dict[str, object] = {}

    def _fake_main(argv):
        """Capture forwarded argv for assertion."""
        captured["argv"] = list(argv)
        raise SystemExit(0)

    monkeypatch.setattr(
        cli,
        "_load_command_module",
        lambda command: (
            captured.update({"command": command})
            or SimpleNamespace(main=_fake_main)
        ),
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["command"] == "check"
    assert captured["argv"] == ["--nofix"]


def _unit_test_cli_unknown_command_fails(monkeypatch) -> None:
    """Unknown command should exit with parser error."""
    monkeypatch.setattr(sys, "argv", ["devcovenant", "does-not-exist"])
    stderr_buffer = io.StringIO()
    with redirect_stderr(stderr_buffer):
        try:
            cli.main()
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 2
    assert "invalid choice: 'does-not-exist'" in stderr_buffer.getvalue()


def _unit_test_test_help_is_command_scoped() -> None:
    """`test --help` should expose no extra lifecycle flags."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "test", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo" not in result.stdout
    assert "--install-mode" not in result.stdout
    assert "--docs-mode" not in result.stdout


def _unit_test_check_help_shows_check_only_options() -> None:
    """`check --help` should expose only check command options."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "check", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--nofix" in result.stdout
    assert "--norefresh" in result.stdout
    assert "--start" not in result.stdout
    assert "--end" not in result.stdout


def _unit_test_install_help_shows_command_scope() -> None:
    """`install --help` should expose only command-scoped defaults."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "install", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--mode" not in result.stdout
    assert "--target" not in result.stdout
    assert "--docs-mode" not in result.stdout
    assert "--nofix" not in result.stdout


def _unit_test_root_command_modules_exist() -> None:
    """All CLI command modules should exist at package root."""
    for module_name in ROOT_COMMAND_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        assert root_path.exists(), str(root_path)


def _unit_test_legacy_helper_modules_removed_from_root() -> None:
    """Legacy helper scripts should be removed from package root."""
    for module_name in LEGACY_HELPER_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        assert not root_path.exists(), str(root_path)


def _unit_test_command_modules_not_duplicated_as_profile_assets() -> None:
    """Root command modules should not be duplicated in profile assets."""
    for module_name in ROOT_COMMAND_MODULES + LEGACY_HELPER_MODULES:
        duplicate_path = ASSET_SCRIPT_ROOT / f"{module_name}.py"
        assert not duplicate_path.exists(), str(duplicate_path)


def _unit_test_command_modules_support_file_path_help() -> None:
    """File-path invocation should work without PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for module_name in ROOT_COMMAND_MODULES:
        result = subprocess.run(
            [sys.executable, f"devcovenant/{module_name}.py", "--help"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_cli_dispatches_command_and_args(self):
        """Run test_cli_dispatches_command_and_args."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_dispatches_command_and_args(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_cli_without_command_prints_help(self):
        """Run test_cli_without_command_prints_help."""
        result = subprocess.run(
            [sys.executable, "-m", "devcovenant"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "DevCovenant - Self-enforcing policy system",
            result.stdout,
        )

    def test_cli_unknown_command_fails(self):
        """Run test_cli_unknown_command_fails."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_unknown_command_fails(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_test_help_is_command_scoped(self):
        """Run test_test_help_is_command_scoped."""
        _unit_test_test_help_is_command_scoped()

    def test_check_help_shows_check_only_options(self):
        """Run test_check_help_shows_check_only_options."""
        _unit_test_check_help_shows_check_only_options()

    def test_install_help_shows_command_scope(self):
        """Run test_install_help_shows_command_scope."""
        _unit_test_install_help_shows_command_scope()

    def test_root_command_modules_exist(self):
        """Run test_root_command_modules_exist."""
        _unit_test_root_command_modules_exist()

    def test_legacy_helper_modules_removed_from_root(self):
        """Run test_legacy_helper_modules_removed_from_root."""
        _unit_test_legacy_helper_modules_removed_from_root()

    def test_command_modules_not_duplicated_as_profile_assets(self):
        """Run test_command_modules_not_duplicated_as_profile_assets."""
        _unit_test_command_modules_not_duplicated_as_profile_assets()

    def test_command_modules_support_file_path_help(self):
        """Run test_command_modules_support_file_path_help."""
        _unit_test_command_modules_support_file_path_help()
