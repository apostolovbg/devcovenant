"""Unit tests for check command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import check


def _unit_test_run_refreshes_by_default() -> None:
    """run() should refresh before invoking engine checks by default."""
    events: list[str] = []
    repo_root = Path("/repo")

    def _fake_refresh(_: Path) -> int:
        """Track refresh call order for assertion."""
        events.append("refresh")
        return 0

    args = SimpleNamespace(nofix=False, norefresh=False)
    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch(
            "devcovenant.check.refresh_repo", side_effect=_fake_refresh
        ):
            with patch("devcovenant.check.warn_version_mismatch"):
                with patch("devcovenant.check.print_banner"):
                    with patch("devcovenant.check.print_step"):
                        with patch(
                            "devcovenant.check.DevCovenantEngine"
                        ) as engine:
                            engine.return_value.check.return_value = (
                                SimpleNamespace(
                                    should_block=False,
                                    has_sync_issues=lambda: False,
                                )
                            )
                            exit_code = check.run(args)

    assert exit_code == 0
    assert events == ["refresh"]


def _unit_test_run_skips_refresh_with_norefresh() -> None:
    """run() should skip refresh when --norefresh is selected."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=True)
    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check.refresh_repo") as refresh_mock:
            with patch("devcovenant.check.warn_version_mismatch"):
                with patch("devcovenant.check.print_banner"):
                    with patch("devcovenant.check.print_step"):
                        with patch(
                            "devcovenant.check.DevCovenantEngine"
                        ) as engine:
                            engine.return_value.check.return_value = (
                                SimpleNamespace(
                                    should_block=False,
                                    has_sync_issues=lambda: False,
                                )
                            )
                            exit_code = check.run(args)
    assert exit_code == 0
    refresh_mock.assert_not_called()


def _unit_test_run_stops_when_refresh_fails() -> None:
    """run() should abort when refresh fails."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=False)

    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check.refresh_repo", return_value=9):
            with patch("devcovenant.check.warn_version_mismatch"):
                with patch("devcovenant.check.print_banner"):
                    with patch("devcovenant.check.print_step"):
                        with patch(
                            "devcovenant.check.DevCovenantEngine"
                        ) as engine:
                            exit_code = check.run(args)
    assert exit_code == 9
    engine.assert_not_called()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_run_refreshes_by_default(self):
        """Run test_run_refreshes_by_default."""
        _unit_test_run_refreshes_by_default()

    def test_run_skips_refresh_with_norefresh(self):
        """Run test_run_skips_refresh_with_norefresh."""
        _unit_test_run_skips_refresh_with_norefresh()

    def test_run_stops_when_refresh_fails(self):
        """Run test_run_stops_when_refresh_fails."""
        _unit_test_run_stops_when_refresh_fails()
