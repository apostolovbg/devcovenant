"""Unit tests for check command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import check


def _unit_test_gate_runs_full_refresh_before_start_phase() -> None:
    """_run_gate should refresh before executing start gate."""
    events: list[str] = []
    repo_root = Path("/repo")

    # Mock refresh callback for execution-order assertions.
    def _fake_refresh(_: Path) -> int:
        events.append("refresh")
        return 0

    # Mock gate callback for execution-order assertions.
    def _fake_gate(_: Path, phase: str) -> int:
        events.append(f"gate:{phase}")
        return 0

    with patch("devcovenant.check.refresh_repo", side_effect=_fake_refresh):
        with patch(
            "devcovenant.check.run_pre_commit_gate",
            side_effect=_fake_gate,
        ):
            exit_code = check._run_gate(repo_root, "start")

    assert exit_code == 0
    assert events == ["refresh", "gate:start"]


def _unit_test_gate_runs_full_refresh_before_end_phase() -> None:
    """_run_gate should refresh before executing end gate."""
    events: list[str] = []
    repo_root = Path("/repo")

    # Mock refresh callback for execution-order assertions.
    def _fake_refresh(_: Path) -> int:
        events.append("refresh")
        return 0

    # Mock gate callback for execution-order assertions.
    def _fake_gate(_: Path, phase: str) -> int:
        events.append(f"gate:{phase}")
        return 0

    with patch("devcovenant.check.refresh_repo", side_effect=_fake_refresh):
        with patch(
            "devcovenant.check.run_pre_commit_gate",
            side_effect=_fake_gate,
        ):
            exit_code = check._run_gate(repo_root, "end")

    assert exit_code == 0
    assert events == ["refresh", "gate:end"]


def _unit_test_gate_stops_when_refresh_fails() -> None:
    """_run_gate should abort without pre-commit when refresh fails."""
    repo_root = Path("/repo")

    with patch("devcovenant.check.refresh_repo", return_value=9):
        with patch("devcovenant.check.run_pre_commit_gate") as gate_mock:
            exit_code = check._run_gate(repo_root, "start")

    assert exit_code == 9
    gate_mock.assert_not_called()


def _unit_test_run_dispatches_start_and_end_to_gate() -> None:
    """run() should dispatch --start/--end through _run_gate."""
    start_args = SimpleNamespace(start=True, end=False, nofix=False)
    end_args = SimpleNamespace(start=False, end=True, nofix=False)
    repo_root = Path("/repo")

    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check._run_gate", return_value=0) as gate_mock:
            start_exit = check.run(start_args)
            end_exit = check.run(end_args)

    assert start_exit == 0
    assert end_exit == 0
    assert gate_mock.call_count == 2
    gate_mock.assert_any_call(repo_root, "start")
    gate_mock.assert_any_call(repo_root, "end")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_gate_runs_full_refresh_before_start_phase(self):
        """Run test_gate_runs_full_refresh_before_start_phase."""
        _unit_test_gate_runs_full_refresh_before_start_phase()

    def test_gate_runs_full_refresh_before_end_phase(self):
        """Run test_gate_runs_full_refresh_before_end_phase."""
        _unit_test_gate_runs_full_refresh_before_end_phase()

    def test_gate_stops_when_refresh_fails(self):
        """Run test_gate_stops_when_refresh_fails."""
        _unit_test_gate_stops_when_refresh_fails()

    def test_run_dispatches_start_and_end_to_gate(self):
        """Run test_run_dispatches_start_and_end_to_gate."""
        _unit_test_run_dispatches_start_and_end_to_gate()
