"""Tests for top-level DevCovenant CLI dispatch."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import pytest

from devcovenant import cli

REPO_ROOT = Path(__file__).resolve().parents[3]


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
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check", "--nofix"],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert captured["command"] == "check"
    assert captured["argv"] == ["--nofix"]


def _unit_test_cli_unknown_command_fails(monkeypatch) -> None:
    """Unknown command should exit with parser error."""
    monkeypatch.setattr(sys, "argv", ["devcovenant", "does-not-exist"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2


def _unit_test_test_help_is_command_scoped() -> None:
    """`test --help` should expose no extra command flags."""
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


def _unit_test_install_help_shows_lifecycle_options() -> None:
    """`install --help` should expose no lifecycle override options."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "install", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--install-mode" not in result.stdout
    assert "--target" not in result.stdout
    assert "--docs-mode" not in result.stdout
    assert "--nofix" not in result.stdout


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_cli_dispatches_command_and_args(self):
        """Run test_cli_dispatches_command_and_args."""
        monkeypatch = pytest.MonkeyPatch()
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
            "DevCovenant - Self-enforcing policy system", result.stdout
        )

    def test_cli_unknown_command_fails(self):
        """Run test_cli_unknown_command_fails."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            _unit_test_cli_unknown_command_fails(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_test_help_is_command_scoped(self):
        """Run test_test_help_is_command_scoped."""
        _unit_test_test_help_is_command_scoped()

    def test_install_help_shows_lifecycle_options(self):
        """Run test_install_help_shows_lifecycle_options."""
        _unit_test_install_help_shows_lifecycle_options()
