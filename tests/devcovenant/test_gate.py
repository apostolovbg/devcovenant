"""Unit tests for gate command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from devcovenant import gate


def _unit_test_run_dispatches_open_stage() -> None:
    """run() should dispatch --open through run_pre_commit_gate."""
    args = SimpleNamespace(open=True, close=False)
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
    gate_mock.assert_called_once_with(repo_root, "open")
    step_mock.assert_has_calls(
        [
            call("Running `open` pre-commit gate", "▶️"),
            call(gate.OPEN_GATE_REMINDER_MESSAGE, "•"),
        ]
    )


def _unit_test_run_dispatches_close_stage() -> None:
    """run() should dispatch --close through run_pre_commit_gate."""
    args = SimpleNamespace(open=False, close=True)
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
    gate_mock.assert_called_once_with(repo_root, "close")


def _unit_test_run_dispatches_verify_stage() -> None:
    """run() should dispatch --verify through run_pre_commit_gate."""
    args = SimpleNamespace(open=False, verify=True, close=False, status=False)
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
    gate_mock.assert_called_once_with(repo_root, "verify")


def _unit_test_run_dispatches_status_read_only() -> None:
    """run() should dispatch --status through the read-only status path."""
    args = SimpleNamespace(open=False, close=False, status=True)
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
    args = SimpleNamespace(open=False, close=False, status=True)
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

    def test_run_dispatches_open_stage(self):
        """Run test_run_dispatches_open_stage."""
        _unit_test_run_dispatches_open_stage()

    def test_run_dispatches_close_stage(self):
        """Run test_run_dispatches_close_stage."""
        _unit_test_run_dispatches_close_stage()

    def test_run_dispatches_verify_stage(self):
        """Run test_run_dispatches_verify_stage."""
        _unit_test_run_dispatches_verify_stage()

    def test_run_dispatches_status_read_only(self):
        """Run test_run_dispatches_status_read_only."""
        _unit_test_run_dispatches_status_read_only()

    def test_main_exits_with_run_exit_code(self):
        """Run test_main_exits_with_run_exit_code."""
        _unit_test_main_exits_with_run_exit_code()
