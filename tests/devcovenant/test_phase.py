"""Unit tests for workflow-phase command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import phase as phase_command


def _unit_test_phase_module_symbol_contract_is_stable() -> None:
    """phase module should expose its public command entrypoints."""

    assert phase_command._build_parser
    assert phase_command.run
    assert phase_command.main


def _unit_test_run_executes_one_declared_workflow_phase() -> None:
    """run() should bootstrap and delegate one requested workflow phase."""

    repo_root = Path("/repo")
    args = SimpleNamespace(phase_command="run", phase_id="tests")

    with patch("devcovenant.phase.resolve_repo_root", return_value=repo_root):
        with patch(
            "devcovenant.phase.run_bootstrap_registry_refresh"
        ) as refresh:
            with patch("devcovenant.phase.warn_version_mismatch") as mismatch:
                with patch("devcovenant.phase.print_banner"):
                    with patch("devcovenant.phase.print_step"):
                        with patch(
                            "devcovenant.phase.run_and_record_workflow_phase",
                            return_value=0,
                        ) as run_phase:
                            exit_code = phase_command.run(args)

    assert exit_code == 0
    refresh.assert_called_once_with(repo_root)
    mismatch.assert_called_once_with(repo_root)
    run_phase.assert_called_once_with(repo_root, "tests")


def _unit_test_run_requires_non_empty_phase_id() -> None:
    """run() should reject empty workflow phase ids."""

    args = SimpleNamespace(phase_command="run", phase_id="")
    with patch(
        "devcovenant.phase.resolve_repo_root",
        return_value=Path("/repo"),
    ):
        with patch("devcovenant.phase.run_bootstrap_registry_refresh"):
            with patch("devcovenant.phase.warn_version_mismatch"):
                with patch("devcovenant.phase.print_banner"):
                    with patch("devcovenant.phase.print_step"):
                        try:
                            phase_command.run(args)
                        except SystemExit as exc:
                            assert str(exc) == "Workflow phase id is required."
                        else:
                            raise AssertionError(
                                "Expected empty workflow phase ids to fail."
                            )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for phase command module checks."""

    def test_phase_module_symbol_contract_is_stable(self):
        """Run workflow-phase module symbol assertions."""

        _unit_test_phase_module_symbol_contract_is_stable()

    def test_run_executes_one_declared_workflow_phase(self):
        """Run workflow-phase command delegation assertions."""

        _unit_test_run_executes_one_declared_workflow_phase()

    def test_run_requires_non_empty_phase_id(self):
        """Run workflow-phase command validation assertions."""

        _unit_test_run_requires_non_empty_phase_id()
