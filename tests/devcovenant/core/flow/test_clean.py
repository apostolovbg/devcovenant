"""Unit tests for cleanup flow orchestration."""

from __future__ import annotations

import importlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.devcovenant import repo_seed_cache

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
        include_runtime_registry=False,
        include_logs=False,
    )
    result = module.cleanup_runtime.CleanResult(
        selection=selection,
        removed_paths=("build",),
        skipped_protected_paths=(),
        skipped_protected_match_count=0,
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
                patch.object(
                    module,
                    "_gate_session_is_open",
                    return_value=False,
                ),
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
                    include_registry=False,
                    include_logs=False,
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


def _unit_test_clean_flow_rejects_open_gate_session() -> None:
    """Clean flow should fail explicitly during an open gate session."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps({"session_state": "open"}, indent=2) + "\n",
            encoding="utf-8",
        )
        output = io.StringIO()
        with redirect_stderr(output):
            exit_code = module.clean_repo(
                repo_root,
                include_all=False,
                include_build=True,
                include_cache=False,
                include_registry=False,
                include_logs=False,
            )

    assert exit_code == 1
    assert (
        "Cannot run `clean` while a gate session is open" in output.getvalue()
    )


def _unit_test_clean_flow_protects_active_run_log_directory() -> None:
    """Clean flow should protect the active run directory during cleanup."""
    module = importlib.import_module(MODULE)
    selection = module.cleanup_runtime.CleanSelection(
        include_build=False,
        include_cache=False,
        include_runtime_registry=False,
        include_logs=True,
    )
    result = module.cleanup_runtime.CleanResult(
        selection=selection,
        removed_paths=(),
        skipped_protected_paths=("devcovenant/logs/active-run",),
        skipped_protected_match_count=1,
    )
    active_run_dir = Path("devcovenant/logs/active-run")
    active_context = SimpleNamespace(
        require_paths=lambda: SimpleNamespace(run_dir=active_run_dir)
    )
    with patch.object(
        module.cleanup_runtime,
        "resolve_clean_selection",
        return_value=selection,
    ):
        with patch.object(
            module.cleanup_runtime,
            "execute_cleanup",
            return_value=result,
        ) as execute_mock:
            with (
                patch.object(
                    module,
                    "_gate_session_is_open",
                    return_value=False,
                ),
                patch.object(
                    module,
                    "get_active_run_log_context",
                    return_value=active_context,
                ),
                patch.object(module, "print_step"),
                patch.object(module, "merge_active_run_log_metadata"),
            ):
                flow_result = module.clean_repo(
                    Path("."),
                    include_all=False,
                    include_build=False,
                    include_cache=False,
                    include_registry=False,
                    include_logs=True,
                )

    assert flow_result == 0
    execute_mock.assert_called_once_with(
        Path("."),
        selection,
        extra_protected_paths=(active_run_dir,),
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for cleanup flow regression coverage."""

    def test_clean_flow_module_symbol_contract_is_stable(self):
        """Run clean flow symbol contract coverage."""
        _unit_test_clean_flow_module_symbol_contract_is_stable()

    def test_clean_flow_reports_scope_and_removed_targets(self):
        """Run clean flow reporting coverage."""
        _unit_test_clean_flow_reports_scope_and_removed_targets()

    def test_clean_flow_rejects_open_gate_session(self):
        """Run open-session cleanup rejection coverage."""
        _unit_test_clean_flow_rejects_open_gate_session()

    def test_clean_flow_protects_active_run_log_directory(self):
        """Run active-run cleanup protection coverage."""
        _unit_test_clean_flow_protects_active_run_log_directory()
