"""Contract checks for workflow-contract resolution helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.flow.workflow_contract"


def _tests_run_entry() -> dict[str, object]:
    """Return one minimal explicit tests run entry."""

    return {
        "id": "tests",
        "enabled": True,
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
            "event_adapter_group": "run_events",
            "write_runtime_profile": True,
        },
    }


def _unit_test_build_workflow_contract_supports_public_advanced_run_kinds():
    """Public runner and success-contract kinds should normalize cleanly."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {
                "python": {
                    "workflow_runs": [
                        _tests_run_entry(),
                        {
                            "id": "artifact-proof",
                            "runner": {
                                "kind": "command_group",
                                "commands": ["python3 -m build"],
                            },
                            "success_contract": {
                                "kind": "external_artifact_check",
                                "required_globs": ["dist/*.whl"],
                                "minimum_matches": 1,
                            },
                        },
                        {
                            "id": "runtime-proof",
                            "runner": {
                                "kind": "runtime_action",
                                "target": "demo:refresh",
                                "payload": {"mode": "fast"},
                            },
                            "success_contract": {
                                "kind": "runtime_action_success",
                            },
                        },
                        {
                            "id": "policy-proof",
                            "runner": {
                                "kind": "policy_command",
                                "target": "demo:refresh-all",
                                "args": ["--mode", "fast"],
                            },
                            "success_contract": {
                                "kind": "policy_command_success",
                            },
                        },
                        {
                            "id": "manual-proof",
                            "runner": {
                                "kind": "manual_attestation",
                                "attestation_key": "release-ready",
                            },
                            "success_contract": {
                                "kind": "manual_attested",
                            },
                        },
                    ]
                }
            },
            ["python"],
        )

    artifact_run = module.resolve_run(contract, "artifact-proof")
    runtime_run = module.resolve_run(contract, "runtime-proof")
    policy_run = module.resolve_run(contract, "policy-proof")
    manual_run = module.resolve_run(contract, "manual-proof")

    assert artifact_run is not None
    assert artifact_run["success_contract"]["kind"] == (
        "external_artifact_check"
    )
    assert artifact_run["success_contract"]["required_globs"] == ["dist/*.whl"]
    assert runtime_run is not None
    assert runtime_run["runner"]["kind"] == "runtime_action"
    assert runtime_run["runner"]["target"] == "demo:refresh"
    assert runtime_run["success_contract"]["kind"] == (
        "runtime_action_success"
    )
    assert policy_run is not None
    assert policy_run["runner"]["kind"] == "policy_command"
    assert policy_run["runner"]["args"] == ["--mode", "fast"]
    assert policy_run["success_contract"]["kind"] == ("policy_command_success")
    assert manual_run is not None
    assert manual_run["runner"]["kind"] == "manual_attestation"
    assert manual_run["runner"]["attestation_key"] == "release-ready"
    assert manual_run["success_contract"]["kind"] == "manual_attested"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""

    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_build_workflow_contract_uses_profile_declared_runs() -> None:
    """Explicit profile runs should define the active workflow contract."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {"python": {"workflow_runs": [_tests_run_entry()]}},
            ["python"],
        )

    assert contract["schema_version"] == module.SCHEMA_VERSION
    assert [anchor["id"] for anchor in contract["anchors"]] == [
        "start",
        "mid",
        "end",
    ]
    assert contract["run_ids"] == ["tests"]
    tests_run = module.resolve_run(contract, "tests")
    assert tests_run is not None
    assert tests_run["owner_id"] == "python"
    assert tests_run["source_field"] == "workflow_runs"
    assert tests_run["recording"]["output_mode_config_field"] == (
        "engine.tests_output_mode"
    )
    assert tests_run["recording"]["event_adapter_group"] == "run_events"
    assert tests_run["recording"]["write_runtime_profile"] is True
    assert tests_run["freshness"]["kind"] == "ignore_paths"
    assert tests_run["freshness"]["ignored_files"] == ["CHANGELOG.md"]
    assert tests_run["freshness"]["ignored_globs"] == []


def _unit_test_run_relevant_paths_changed_uses_freshness_contract():
    """Workflow-run invalidation should follow explicit freshness rules."""

    module = importlib.import_module(MODULE)
    tests_run = {
        "id": "tests",
        "runner": {"kind": "command_group"},
        "freshness": {
            "kind": "ignore_paths",
            "ignored_files": ["CHANGELOG.md"],
            "ignored_globs": [],
        },
    }
    default_run = {"id": "artifact-proof"}
    strict_run = {
        "id": "artifact-proof",
        "freshness": {"kind": "any_change"},
    }
    docs_run = {
        "id": "docs-proof",
        "freshness": {
            "kind": "ignore_paths",
            "ignored_files": [],
            "ignored_globs": ["docs/generated/**"],
        },
    }

    assert (
        module.run_relevant_paths_changed(tests_run, ["CHANGELOG.md"]) is False
    )
    assert (
        module.run_relevant_paths_changed(
            tests_run,
            ["CHANGELOG.md", "devcovenant/cli.py"],
        )
        is True
    )
    assert (
        module.run_relevant_paths_changed(default_run, ["CHANGELOG.md"])
        is False
    )
    assert (
        module.run_relevant_paths_changed(strict_run, ["CHANGELOG.md"]) is True
    )
    assert (
        module.run_relevant_paths_changed(
            docs_run,
            ["docs/generated/report.txt"],
        )
        is False
    )
    assert (
        module.run_relevant_paths_changed(
            docs_run,
            ["docs/generated/report.txt", "docs/workflow.md"],
        )
        is True
    )


def _unit_test_build_workflow_contract_orders_runs_with_positions() -> None:
    """
    Ordering should honor anchors, run refs, and deterministic tie-breaks.
    """

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {
                "python": {
                    "workflow_runs": [
                        {
                            **_tests_run_entry(),
                            "id": "alpha",
                            "order": 200,
                        },
                        {
                            **_tests_run_entry(),
                            "id": "beta",
                            "order": 50,
                            "before": "gamma",
                        },
                        {
                            **_tests_run_entry(),
                            "id": "gamma",
                            "order": 10,
                            "after": "beta",
                        },
                        {
                            **_tests_run_entry(),
                            "id": "delta",
                            "order": 0,
                        },
                    ]
                }
            },
            ["python"],
        )

    assert contract["run_ids"] == ["delta", "beta", "gamma", "alpha"]


def _unit_test_build_workflow_contract_rejects_unknown_position_targets():
    """Unknown anchor or run refs should fail contract resolution."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with unittest.TestCase().assertRaisesRegex(
            ValueError,
            "unknown `after` target `banana`",
        ):
            module.build_workflow_contract(
                repo_root,
                {
                    "python": {
                        "workflow_runs": [
                            {
                                **_tests_run_entry(),
                                "after": "banana",
                            }
                        ]
                    }
                },
                ["python"],
            )


def _unit_test_build_workflow_contract_rejects_cyclic_positions() -> None:
    """Cyclic run positioning should fail with a stable error."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with unittest.TestCase().assertRaisesRegex(
            ValueError,
            "cyclic ordering constraints",
        ):
            module.build_workflow_contract(
                repo_root,
                {
                    "python": {
                        "workflow_runs": [
                            {
                                **_tests_run_entry(),
                                "id": "alpha",
                                "after": "beta",
                            },
                            {
                                **_tests_run_entry(),
                                "id": "beta",
                                "after": "alpha",
                            },
                        ]
                    }
                },
                ["python"],
            )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for workflow-contract resolution checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""

        _unit_test_module_importable()

    def test_build_workflow_contract_uses_profile_declared_runs(self):
        """Run explicit workflow-run contract assertions."""

        _unit_test_build_workflow_contract_uses_profile_declared_runs()

    def test_build_workflow_contract_supports_public_advanced_run_kinds(
        self,
    ):
        """Run advanced workflow-run contract assertions."""

        _unit_test_build_workflow_contract_supports_public_advanced_run_kinds()

    def test_run_relevant_paths_changed_uses_freshness_contract(self):
        """Run workflow-run invalidation regression assertions."""

        _unit_test_run_relevant_paths_changed_uses_freshness_contract()

    def test_build_workflow_contract_orders_runs_with_positions(self):
        """Run workflow ordering assertions for anchors and run refs."""

        _unit_test_build_workflow_contract_orders_runs_with_positions()

    def test_build_workflow_contract_rejects_unknown_position_targets(self):
        """Run invalid workflow-position target assertions."""

        _unit_test_build_workflow_contract_rejects_unknown_position_targets()

    def test_build_workflow_contract_rejects_cyclic_positions(self):
        """Run cyclic workflow-position assertions."""

        _unit_test_build_workflow_contract_rejects_cyclic_positions()
