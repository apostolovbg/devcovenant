"""Unit tests for gate command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import gate


def _unit_test_run_dispatches_start_phase() -> None:
    """run() should dispatch --start through run_pre_commit_gate."""
    args = SimpleNamespace(start=True, end=False)
    repo_root = Path("/repo")
    with patch("devcovenant.gate.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.gate.print_banner"):
            with patch("devcovenant.gate.print_step"):
                with patch(
                    "devcovenant.gate.run_pre_commit_gate",
                    return_value=0,
                ) as gate_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    gate_mock.assert_called_once_with(repo_root, "start")


def _unit_test_run_dispatches_end_phase() -> None:
    """run() should dispatch --end through run_pre_commit_gate."""
    args = SimpleNamespace(start=False, end=True)
    repo_root = Path("/repo")
    with patch("devcovenant.gate.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.gate.print_banner"):
            with patch("devcovenant.gate.print_step"):
                with patch(
                    "devcovenant.gate.run_pre_commit_gate",
                    return_value=0,
                ) as gate_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    gate_mock.assert_called_once_with(repo_root, "end")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_run_dispatches_start_phase(self):
        """Run test_run_dispatches_start_phase."""
        _unit_test_run_dispatches_start_phase()

    def test_run_dispatches_end_phase(self):
        """Run test_run_dispatches_end_phase."""
        _unit_test_run_dispatches_end_phase()
