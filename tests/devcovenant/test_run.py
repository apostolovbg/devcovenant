"""Unit tests for workflow-run command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import run as run_command


def _unit_test_run_module_symbol_contract_is_stable() -> None:
    """run module should expose its public command entrypoints."""

    assert run_command._build_parser
    assert run_command.run
    assert run_command.main


def _unit_test_run_executes_required_workflow_runs() -> None:
    """run() should bootstrap and delegate the run set."""

    repo_root = Path("/repo")
    args = SimpleNamespace()

    with patch("devcovenant.run.resolve_repo_root", return_value=repo_root):
        with patch(
            "devcovenant.run.run_bootstrap_registry_refresh"
        ) as refresh:
            with patch("devcovenant.run.warn_version_mismatch") as mismatch:
                with patch("devcovenant.run.print_banner"):
                    with patch("devcovenant.run.print_step"):
                        with patch(
                            "devcovenant.run.run_workflow_runs",
                            return_value=0,
                        ) as run_runs:
                            exit_code = run_command.run(args)

    assert exit_code == 0
    refresh.assert_called_once_with(repo_root)
    mismatch.assert_called_once_with(repo_root)
    run_runs.assert_called_once_with(repo_root, notes="")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for workflow-run command checks."""

    def test_run_module_symbol_contract_is_stable(self):
        """Run workflow-run module symbol assertions."""

        _unit_test_run_module_symbol_contract_is_stable()

    def test_run_executes_required_workflow_runs(self):
        """Run workflow-run command delegation assertions."""

        _unit_test_run_executes_required_workflow_runs()
