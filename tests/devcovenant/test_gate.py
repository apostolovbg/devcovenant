"""Unit tests for gate command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from devcovenant import gate


def _unit_test_run_dispatches_start_stage() -> None:
    """run() should dispatch --start through run_pre_commit_gate."""
    args = SimpleNamespace(start=True, end=False)
    repo_root = Path("/repo")
    with patch(
        "devcovenant.core.execution.resolve_repo_root",
        return_value=repo_root,
    ):
        with patch("devcovenant.core.execution.print_banner"):
            with patch("devcovenant.core.execution.print_step") as step_mock:
                with patch(
                    "devcovenant.core.gate_runtime.run_pre_commit_gate",
                    return_value=0,
                ) as gate_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    gate_mock.assert_called_once_with(repo_root, "start")
    step_mock.assert_has_calls(
        [
            call("Running `start` pre-commit gate", "▶️"),
            call(gate.START_GATE_REMINDER_MESSAGE, "•"),
        ]
    )
    assert step_mock.call_count == 2


def _unit_test_run_dispatches_end_stage() -> None:
    """run() should dispatch --end through run_pre_commit_gate."""
    args = SimpleNamespace(start=False, end=True)
    repo_root = Path("/repo")
    with patch(
        "devcovenant.core.execution.resolve_repo_root",
        return_value=repo_root,
    ):
        with patch("devcovenant.core.execution.print_banner"):
            with patch("devcovenant.core.execution.print_step"):
                with patch(
                    "devcovenant.core.gate_runtime.run_pre_commit_gate",
                    return_value=0,
                ) as gate_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    gate_mock.assert_called_once_with(repo_root, "end")


def _unit_test_run_dispatches_mid_stage() -> None:
    """run() should dispatch --mid through run_pre_commit_gate."""
    args = SimpleNamespace(start=False, mid=True, end=False, status=False)
    repo_root = Path("/repo")
    with patch(
        "devcovenant.core.execution.resolve_repo_root",
        return_value=repo_root,
    ):
        with patch("devcovenant.core.execution.print_banner"):
            with patch("devcovenant.core.execution.print_step"):
                with patch(
                    "devcovenant.core.gate_runtime.run_pre_commit_gate",
                    return_value=0,
                ) as gate_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    gate_mock.assert_called_once_with(repo_root, "mid")


def _unit_test_run_dispatches_status_read_only() -> None:
    """run() should dispatch --status through the read-only status path."""
    args = SimpleNamespace(start=False, end=False, status=True)
    repo_root = Path("/repo")
    with patch(
        "devcovenant.core.execution.resolve_repo_root",
        return_value=repo_root,
    ):
        with patch("devcovenant.core.execution.print_banner") as banner_mock:
            with patch("devcovenant.core.execution.print_step") as step_mock:
                with patch(
                    "devcovenant.core.gate_runtime.show_gate_status",
                    return_value=0,
                ) as status_mock:
                    exit_code = gate.run(args)
    assert exit_code == 0
    status_mock.assert_called_once_with(repo_root)
    banner_mock.assert_not_called()
    step_mock.assert_not_called()


def _unit_test_main_exits_with_run_exit_code() -> None:
    """main() should parse args and exit with run() return code."""
    args = SimpleNamespace(start=False, end=False, status=True)
    with patch("devcovenant.gate._build_parser") as parser_factory:
        parser = parser_factory.return_value
        parser.parse_args.return_value = args
        with patch("devcovenant.gate.run", return_value=7) as run_mock:
            with unittest.TestCase().assertRaises(SystemExit) as ctx:
                gate.main(["--status"])
    parser.parse_args.assert_called_once_with(["--status"])
    run_mock.assert_called_once_with(args)
    assert ctx.exception.code == 7


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_run_dispatches_start_stage(self):
        """Run test_run_dispatches_start_stage."""
        _unit_test_run_dispatches_start_stage()

    def test_run_dispatches_end_stage(self):
        """Run test_run_dispatches_end_stage."""
        _unit_test_run_dispatches_end_stage()

    def test_run_dispatches_mid_stage(self):
        """Run test_run_dispatches_mid_stage."""
        _unit_test_run_dispatches_mid_stage()

    def test_run_dispatches_status_read_only(self):
        """Run test_run_dispatches_status_read_only."""
        _unit_test_run_dispatches_status_read_only()

    def test_main_exits_with_run_exit_code(self):
        """Run test_main_exits_with_run_exit_code."""
        _unit_test_main_exits_with_run_exit_code()
