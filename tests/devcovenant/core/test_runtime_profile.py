"""Tests for devcovenant.core.runtime_profile."""

from __future__ import annotations

import datetime as _dt
import importlib
import unittest

MODULE = "devcovenant.core.run_logs"


def _runtime_profile_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _runtime_profile_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _runtime_profile_symbol_contract_is_stable() -> None:
    """Profiling service should preserve expected helper symbols."""
    module = importlib.import_module(MODULE)
    assert module.build_workflow_runtime_profile_payload
    assert module.render_workflow_runtime_profile_text
    assert module.infer_workflow_run_command_group
    assert module.infer_workflow_run_command_module


def _runtime_profile_profile_payload_supports_arbitrary_command_count() -> (
    None
):
    """Payload builder should support command chains beyond two runners."""
    module = importlib.import_module(MODULE)
    started = _dt.datetime(2026, 2, 27, 12, 0, 0, tzinfo=_dt.timezone.utc)
    finished = _dt.datetime(2026, 2, 27, 12, 0, 30, tzinfo=_dt.timezone.utc)
    payload = module.build_workflow_runtime_profile_payload(
        run_id="tests",
        commands=[
            ("python3 -m unittest discover -v", ["python3", "-m", "unittest"]),
            ("pytest", ["pytest"]),
            ("ruff check .", ["ruff", "check", "."]),
        ],
        events=[
            {
                "command": ["python3", "-m", "unittest", "discover", "-v"],
                "duration_seconds": 10.0,
                "status": "success",
                "metadata": {"exit_code": 0},
            },
            {
                "command": ["pytest"],
                "duration_seconds": 12.5,
                "status": "success",
                "metadata": {"exit_code": 0},
            },
            {
                "command": ["ruff", "check", "."],
                "duration_seconds": 3.25,
                "status": "success",
                "metadata": {"exit_code": 0},
            },
        ],
        workflow_run_output_mode="normal",
        source_field="workflow_runs",
        started=started,
        finished=finished,
    )
    assert payload["total_configured_commands"] == 3
    assert payload["recorded_events"] == 3
    assert len(payload["commands"]) == 3
    assert payload["duration_seconds"] == 30.0
    assert payload["slowest_commands"][0]["raw_command"] == "pytest"
    modules = {row["module"] for row in payload["commands"]}
    assert "unittest" in modules
    assert "pytest" in modules
    groups = {row["group"] for row in payload["commands"]}
    assert "unittest" in groups
    assert "pytest" in groups


def _runtime_profile_render_profile_text_includes_breakdowns() -> None:
    """Rendered profile text should include summary and breakdown sections."""
    module = importlib.import_module(MODULE)
    payload = {
        "schema_version": "1.0",
        "run_id": "tests",
        "workflow_run_output_mode": "normal",
        "workflow_run_source_field": "workflow_runs",
        "started_at": "2026-02-27T12:00:00+00:00",
        "finished_at": "2026-02-27T12:00:30+00:00",
        "duration_seconds": 30.0,
        "total_configured_commands": 3,
        "recorded_events": 3,
        "group_breakdown": [
            {"group": "pytest", "duration_seconds": 12.5, "commands": 1}
        ],
        "module_breakdown": [
            {"module": "pytest", "duration_seconds": 12.5, "commands": 1}
        ],
        "slowest_commands": [
            {
                "raw_command": "pytest",
                "duration_seconds": 12.5,
                "group": "pytest",
                "module": "pytest",
            }
        ],
    }
    rendered = module.render_workflow_runtime_profile_text(payload)
    assert "Workflow Run Profile (informational)" in rendered
    assert "Run Id: tests" in rendered
    assert "Group Breakdown:" in rendered
    assert "Module Breakdown:" in rendered
    assert "Slowest Commands:" in rendered
    assert "pytest: duration=12.5" in rendered


class RuntimeProfileTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _runtime_profile_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _runtime_profile_module_has_public_symbols()

    def test_symbol_contract_is_stable(self):
        """Run profiling service symbol contract assertions."""
        _runtime_profile_symbol_contract_is_stable()

    def test_profile_payload_supports_arbitrary_command_count(self):
        """Run arbitrary command-count profiling payload assertions."""
        _runtime_profile_profile_payload_supports_arbitrary_command_count()

    def test_render_profile_text_includes_breakdowns(self):
        """Run profile text rendering section assertions."""
        _runtime_profile_render_profile_text_includes_breakdowns()
