"""Unit tests for cleanup flow orchestration."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = "devcovenant.core.flow.clean"


def _unit_test_clean_flow_module_symbol_contract_is_stable() -> None:
    """Clean flow module should expose its orchestration entrypoint."""
    module = importlib.import_module(MODULE)
    assert module.clean_repo


def _unit_test_clean_flow_reports_scope_and_removed_targets() -> None:
    """Clean flow should report selection scope and removal counts."""
    module = importlib.import_module(MODULE)
    selection = module.cleanup_runtime.CleanSelection(
        include_build=True,
        include_cache=False,
    )
    result = module.cleanup_runtime.CleanResult(
        selection=selection,
        removed_paths=("build",),
        skipped_protected_paths=(),
    )
    with patch.object(
        module.cleanup_runtime,
        "resolve_clean_selection",
        return_value=selection,
    ) as resolve_mock:
        with patch.object(
            module.cleanup_runtime,
            "execute_cleanup",
            return_value=result,
        ) as execute_mock:
            with (
                patch.object(module, "print_step") as print_mock,
                patch.object(
                    module,
                    "merge_active_run_log_metadata",
                ) as metadata_mock,
            ):
                flow_result = module.clean_repo(
                    Path("."),
                    include_all=False,
                    include_build=True,
                    include_cache=False,
                )

    assert flow_result == 0
    resolve_mock.assert_called_once()
    execute_mock.assert_called_once()
    messages = [call.args[0] for call in print_mock.call_args_list]
    assert "Cleanup scope: build" in messages
    assert "Removed 1 cleanup target(s)" in messages
    metadata_mock.assert_called_once()
    payload = metadata_mock.call_args.args[0]
    assert payload["clean_summary"]["selected_scopes"] == ["build"]
    assert payload["clean_summary"]["removed_count"] == 1


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for cleanup flow regression coverage."""

    def test_clean_flow_module_symbol_contract_is_stable(self):
        """Run clean flow symbol contract coverage."""
        _unit_test_clean_flow_module_symbol_contract_is_stable()

    def test_clean_flow_reports_scope_and_removed_targets(self):
        """Run clean flow reporting coverage."""
        _unit_test_clean_flow_reports_scope_and_removed_targets()
