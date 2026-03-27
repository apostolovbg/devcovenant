"""Contract checks for workflow-contract resolution helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.flow.workflow_contract"


def _tests_phase_entry() -> dict[str, object]:
    """Return one minimal explicit tests phase entry."""

    return {
        "id": "tests",
        "enabled": True,
        "required": True,
        "after": "mid",
        "before": "end",
        "order": 100,
        "runner": {
            "kind": "command_group",
            "commands": ["python3 -m unittest discover -v", "pytest"],
        },
        "success_contract": {"kind": "all_commands_exit_zero"},
        "recording": {
            "record_in_session": True,
            "summary_label": "Tests",
            "output_mode_config_field": "engine.tests_output_mode",
            "event_adapter_group": "test_events",
            "write_runtime_profile": True,
        },
    }


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""

    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_build_workflow_contract_uses_profile_declared_phases() -> None:
    """Explicit profile phases should define the active workflow contract."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {"python": {"workflow_phases": [_tests_phase_entry()]}},
            ["python"],
        )

    assert contract["schema_version"] == module.SCHEMA_VERSION
    assert [anchor["id"] for anchor in contract["anchors"]] == [
        "start",
        "mid",
        "end",
    ]
    assert contract["required_phase_ids"] == ["tests"]
    tests_phase = module.resolve_phase(contract, "tests")
    assert tests_phase is not None
    assert tests_phase["owner_id"] == "python"
    assert tests_phase["source_field"] == "workflow_phases"
    assert tests_phase["recording"]["output_mode_config_field"] == (
        "engine.tests_output_mode"
    )
    assert tests_phase["recording"]["event_adapter_group"] == "test_events"
    assert tests_phase["recording"]["write_runtime_profile"] is True
    assert tests_phase["freshness"]["kind"] == "ignore_paths"
    assert tests_phase["freshness"]["ignored_files"] == ["CHANGELOG.md"]
    assert tests_phase["freshness"]["ignored_globs"] == []


def _unit_test_phase_relevant_paths_changed_uses_freshness_contract():
    """Workflow-phase invalidation should follow explicit freshness rules."""

    module = importlib.import_module(MODULE)
    tests_phase = {
        "id": "tests",
        "runner": {"kind": "command_group"},
        "freshness": {
            "kind": "ignore_paths",
            "ignored_files": ["CHANGELOG.md"],
            "ignored_globs": [],
        },
    }
    default_phase = {"id": "artifact-proof"}
    strict_phase = {
        "id": "artifact-proof",
        "freshness": {"kind": "any_change"},
    }
    docs_phase = {
        "id": "docs-proof",
        "freshness": {
            "kind": "ignore_paths",
            "ignored_files": [],
            "ignored_globs": ["docs/generated/**"],
        },
    }

    assert (
        module.phase_relevant_paths_changed(tests_phase, ["CHANGELOG.md"])
        is False
    )
    assert (
        module.phase_relevant_paths_changed(
            tests_phase,
            ["CHANGELOG.md", "devcovenant/cli.py"],
        )
        is True
    )
    assert (
        module.phase_relevant_paths_changed(default_phase, ["CHANGELOG.md"])
        is False
    )
    assert (
        module.phase_relevant_paths_changed(strict_phase, ["CHANGELOG.md"])
        is True
    )
    assert (
        module.phase_relevant_paths_changed(
            docs_phase,
            ["docs/generated/report.txt"],
        )
        is False
    )
    assert (
        module.phase_relevant_paths_changed(
            docs_phase,
            ["docs/generated/report.txt", "docs/workflow.md"],
        )
        is True
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for workflow-contract resolution checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""

        _unit_test_module_importable()

    def test_build_workflow_contract_uses_profile_declared_phases(self):
        """Run explicit workflow-phase contract assertions."""

        _unit_test_build_workflow_contract_uses_profile_declared_phases()

    def test_phase_relevant_paths_changed_uses_freshness_contract(self):
        """Run workflow-phase invalidation regression assertions."""

        _unit_test_phase_relevant_paths_changed_uses_freshness_contract()
