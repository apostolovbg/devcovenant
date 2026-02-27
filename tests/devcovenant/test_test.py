"""Unit tests for test command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import test as test_command


def _unit_test_run_executes_metadata_driven_test_chain() -> None:
    """run() should execute bootstrap refresh and required tests."""
    repo_root = Path("/repo")
    args = SimpleNamespace()

    with patch("devcovenant.test.resolve_repo_root", return_value=repo_root):
        with patch(
            "devcovenant.test.run_bootstrap_registry_refresh"
        ) as refresh:
            with patch("devcovenant.test.warn_version_mismatch") as mismatch:
                with patch("devcovenant.test.print_banner"):
                    with patch("devcovenant.test.print_step"):
                        with patch(
                            "devcovenant.test.run_and_record_tests",
                            return_value=0,
                        ) as run_tests:
                            exit_code = test_command.run(args)

    assert exit_code == 0
    refresh.assert_called_once_with(repo_root)
    mismatch.assert_called_once_with(repo_root)
    run_tests.assert_called_once_with(repo_root, notes="")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_run_executes_metadata_driven_test_chain(self):
        """Run test_run_executes_metadata_driven_test_chain."""
        _unit_test_run_executes_metadata_driven_test_chain()
