"""Mirrored tests for devcovenant.core.workflow_support."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

import devcovenant.core.workflow_support as workflow_validation
from devcovenant.core.policy_contract import ChangeState, CheckContext
from tests import MonkeyPatch

MODULE = "devcovenant.core.workflow_support"


def _contract_tests_run_entry() -> dict[str, object]:
    """Return one minimal explicit tests run entry."""
    return {
        "id": "tests",
        "enabled": True,
        "after": "verify",
        "before": "close",
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


def _contract_build_workflow_contract_supports_public_advanced_run_kinds():
    """Public runner and success-contract kinds should normalize cleanly."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {
                "python": {
                    "workflow_runs": [
                        _contract_tests_run_entry(),
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
                                "kind": "runtime_action_success"
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
                                "kind": "policy_command_success"
                            },
                        },
                        {
                            "id": "manual-proof",
                            "runner": {
                                "kind": "manual_attestation",
                                "attestation_key": "release-ready",
                            },
                            "success_contract": {"kind": "manual_attested"},
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
    assert (
        artifact_run["success_contract"]["kind"] == "external_artifact_check"
    )
    assert artifact_run["success_contract"]["required_globs"] == ["dist/*.whl"]
    assert runtime_run is not None
    assert runtime_run["runner"]["kind"] == "runtime_action"
    assert runtime_run["runner"]["target"] == "demo:refresh"
    assert runtime_run["success_contract"]["kind"] == "runtime_action_success"
    assert policy_run is not None
    assert policy_run["runner"]["kind"] == "policy_command"
    assert policy_run["runner"]["args"] == ["--mode", "fast"]
    assert policy_run["success_contract"]["kind"] == "policy_command_success"
    assert manual_run is not None
    assert manual_run["runner"]["kind"] == "manual_attestation"
    assert manual_run["runner"]["attestation_key"] == "release-ready"
    assert manual_run["success_contract"]["kind"] == "manual_attested"


def _contract_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _contract_build_workflow_contract_uses_profile_declared_runs() -> None:
    """Explicit profile runs should define the active workflow contract."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        contract = module.build_workflow_contract(
            repo_root,
            {"python": {"workflow_runs": [_contract_tests_run_entry()]}},
            ["python"],
        )
    assert contract["schema_version"] == module.SCHEMA_VERSION
    assert [anchor["id"] for anchor in contract["anchors"]] == [
        "open",
        "verify",
        "close",
    ]
    assert contract["run_ids"] == ["tests"]
    tests_run = module.resolve_run(contract, "tests")
    assert tests_run is not None
    assert tests_run["owner_id"] == "python"
    assert tests_run["source_field"] == "workflow_runs"
    assert (
        tests_run["recording"]["output_mode_config_field"]
        == "engine.tests_output_mode"
    )
    assert tests_run["recording"]["event_adapter_group"] == "run_events"
    assert tests_run["recording"]["write_runtime_profile"] is True
    assert tests_run["freshness"]["kind"] == "ignore_paths"
    assert tests_run["freshness"]["ignored_files"] == ["CHANGELOG.md"]
    assert tests_run["freshness"]["ignored_globs"] == []


def _contract_run_relevant_paths_changed_uses_freshness_contract():
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
    strict_run = {"id": "artifact-proof", "freshness": {"kind": "any_change"}}
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
            tests_run, ["CHANGELOG.md", "devcovenant/cli.py"]
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
            docs_run, ["docs/generated/report.txt"]
        )
        is False
    )
    assert (
        module.run_relevant_paths_changed(
            docs_run, ["docs/generated/report.txt", "docs/workflow.md"]
        )
        is True
    )


def _contract_build_workflow_contract_orders_runs_with_positions() -> None:
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
                            **_contract_tests_run_entry(),
                            "id": "alpha",
                            "order": 200,
                        },
                        {
                            **_contract_tests_run_entry(),
                            "id": "beta",
                            "order": 50,
                            "before": "gamma",
                        },
                        {
                            **_contract_tests_run_entry(),
                            "id": "gamma",
                            "order": 10,
                            "after": "beta",
                        },
                        {
                            **_contract_tests_run_entry(),
                            "id": "delta",
                            "order": 0,
                        },
                    ]
                }
            },
            ["python"],
        )
    assert contract["run_ids"] == ["delta", "beta", "gamma", "alpha"]


def _contract_build_workflow_contract_rejects_unknown_position_targets():
    """Unknown anchor or run refs should fail contract resolution."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with unittest.TestCase().assertRaisesRegex(
            ValueError, "unknown `after` target `banana`"
        ):
            module.build_workflow_contract(
                repo_root,
                {
                    "python": {
                        "workflow_runs": [
                            {
                                **_contract_tests_run_entry(),
                                "after": "banana",
                            }
                        ]
                    }
                },
                ["python"],
            )


def _contract_build_workflow_contract_rejects_cyclic_positions() -> None:
    """Cyclic run positioning should fail with a stable error."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with unittest.TestCase().assertRaisesRegex(
            ValueError, "cyclic ordering constraints"
        ):
            module.build_workflow_contract(
                repo_root,
                {
                    "python": {
                        "workflow_runs": [
                            {
                                **_contract_tests_run_entry(),
                                "id": "alpha",
                                "after": "beta",
                            },
                            {
                                **_contract_tests_run_entry(),
                                "id": "beta",
                                "after": "alpha",
                            },
                        ]
                    }
                },
                ["python"],
            )


class WorkflowSupportContractTests(unittest.TestCase):
    """unittest wrappers for workflow-contract resolution checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _contract_module_importable()

    def test_build_workflow_contract_uses_profile_declared_runs(self):
        """Run explicit workflow-run contract assertions."""
        _contract_build_workflow_contract_uses_profile_declared_runs()

    def test_build_workflow_contract_supports_public_advanced_run_kinds(self):
        """Run advanced workflow-run contract assertions."""
        _contract_build_workflow_contract_supports_public_advanced_run_kinds()

    def test_run_relevant_paths_changed_uses_freshness_contract(self):
        """Run workflow-run invalidation regression assertions."""
        _contract_run_relevant_paths_changed_uses_freshness_contract()

    def test_build_workflow_contract_orders_runs_with_positions(self):
        """Run workflow ordering assertions for anchors and run refs."""
        _contract_build_workflow_contract_orders_runs_with_positions()

    def test_build_workflow_contract_rejects_unknown_position_targets(self):
        """Run invalid workflow-position target assertions."""
        _contract_build_workflow_contract_rejects_unknown_position_targets()

    def test_build_workflow_contract_rejects_cyclic_positions(self):
        """Run cyclic workflow-position assertions."""
        _contract_build_workflow_contract_rejects_cyclic_positions()


MODULE = "devcovenant.core.workflow_support"


def _registry_module_importable() -> None:
    """Runtime registry module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _registry_public_symbol_contract_is_stable() -> None:
    """Runtime registry should expose the runtime path-helper surface."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "RUNTIME_REGISTRY_DIR",
        "GATE_STATUS_FILENAME",
        "WORKFLOW_SESSION_FILENAME",
        "LATEST_RUNTIME_FILENAME",
        "SESSION_SNAPSHOT_FILENAME",
        "runtime_registry_root",
        "latest_runtime_path",
        "session_snapshot_path",
        "gate_status_path",
        "gate_status_path_from_option",
        "workflow_session_path",
        "workflow_session_path_from_option",
    ]:
        assert hasattr(module, symbol)


def _registry_path_helpers_resolve_runtime_locations() -> None:
    """Runtime registry helpers should resolve runtime evidence paths."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        runtime_root = repo_root / "devcovenant" / "registry" / "runtime"
        assert module.runtime_registry_root(repo_root) == runtime_root
        assert (
            module.latest_runtime_path(repo_root)
            == runtime_root / "latest.json"
        )
        assert (
            module.session_snapshot_path(repo_root)
            == runtime_root / "session_snapshot.json"
        )
        assert (
            module.gate_status_path(repo_root)
            == runtime_root / "gate_status.json"
        )
        assert (
            module.workflow_session_path(repo_root)
            == runtime_root / "workflow_session.json"
        )


def _registry_path_helpers_honor_runtime_evidence_overrides() -> None:
    """Runtime evidence helpers should honor dedicated config path keys."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "paths:",
                    (
                        "  gate_status_file: "
                        "devcovenant/registry/runtime/evidence/status.json"
                    ),
                    (
                        "  workflow_session_file: "
                        "devcovenant/registry/runtime/evidence/workflow.json"
                    ),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        assert (
            module.gate_status_path(repo_root)
            == repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "evidence"
            / "status.json"
        )
        assert (
            module.workflow_session_path(repo_root)
            == repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "evidence"
            / "workflow.json"
        )


def _registry_runtime_evidence_paths_must_stay_under_runtime_root() -> None:
    """
    Configured evidence paths should reject escapes from the runtime root.
    """
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        try:
            module.gate_status_path_from_option(repo_root, "alt/status.json")
        except ValueError as exc:
            assert "devcovenant/registry/runtime/" in str(exc)
        else:
            raise AssertionError(
                "Expected ValueError for escaped status path."
            )


class WorkflowSupportRegistryTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run runtime-registry importability assertions."""
        _registry_module_importable()

    def test_public_symbol_contract_is_stable(self):
        """Run runtime-registry public symbol assertions."""
        _registry_public_symbol_contract_is_stable()

    def test_path_helpers_resolve_runtime_locations(self):
        """Run runtime-registry path resolution assertions."""
        _registry_path_helpers_resolve_runtime_locations()

    def test_path_helpers_honor_runtime_evidence_overrides(self):
        """Run runtime-evidence override assertions."""
        _registry_path_helpers_honor_runtime_evidence_overrides()

    def test_runtime_evidence_paths_must_stay_under_runtime_root(self):
        """Run runtime-evidence containment assertions."""
        _registry_runtime_evidence_paths_must_stay_under_runtime_root()


_DEFAULT_REQUIRED_COMMANDS = ["run suite-a", "run suite-b"]


def _write_workflow_contract_fixture(
    tmp_path: Path, *, workflow_runs: list[str] | None = None
) -> None:
    """Write minimal config and registry surfaces for workflow-contract use."""
    commands = (
        list(workflow_runs)
        if workflow_runs is not None
        else list(_DEFAULT_REQUIRED_COMMANDS)
    )
    config_path = tmp_path / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "project-governance:",
                "  stage: stable",
                "  maintenance_stance: active",
                "  compatibility_policy: forward-only",
                "  versioning_mode: versioned",
                "profiles:",
                "  active:",
                "    - python",
                "workflow:",
                "  pre_commit_command: pre-commit run --all-files",
                "",
            ]
        ),
        encoding="utf-8",
    )
    workflow_run_lines = [
        "    workflow_runs:",
        "      - id: tests",
        "        enabled: true",
        "        after: verify",
        "        before: close",
        "        order: 100",
        "        runner:",
        "          kind: command_group",
        "          commands:",
    ]
    for command in commands:
        workflow_run_lines.append(f"            - {command}")
    workflow_run_lines.extend(
        [
            "        success_contract:",
            "          kind: all_commands_exit_zero",
            "        recording:",
            "          record_in_session: true",
            "          summary_label: Tests",
        ]
    )
    registry_lines = [
        "metadata:",
        "  schema_version: 1",
        "  registry_layout: single-root",
        "profiles:",
        "  global:",
        "    category: system",
        "  python:",
        "    category: language",
    ]
    if commands:
        registry_lines.extend(workflow_run_lines)
    registry_lines.extend(["inventory: {}", ""])
    registry_path = tmp_path / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("\n".join(registry_lines), encoding="utf-8")


def _make_workflow_check_context(
    tmp_path: Path,
    changed: list[str],
    *,
    working_numstat: dict[str, str] | None = None,
    session_valid: bool = False,
    session_reason_code: str = "",
    config: dict | None = None,
    workflow_runs: list[str] | None = None,
) -> CheckContext:
    """Build test context with changed files and optional working snapshot."""
    _write_workflow_contract_fixture(tmp_path, workflow_runs=workflow_runs)
    files = [tmp_path / path for path in changed]
    for file_path in files:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# code\n", encoding="utf-8")
    return CheckContext(
        repo_root=tmp_path,
        changed_files=files,
        all_files=files,
        config=config or {},
        change_state=ChangeState(
            current_snapshot_numstat=dict(working_numstat or {}),
            session_valid=session_valid,
            session_reason_code=session_reason_code,
        ),
    )


def _workflow_status_path(tmp_path: Path) -> Path:
    """Return default gate status path for tests."""
    return (
        tmp_path / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )


def _workflow_session_path(
    tmp_path: Path,
) -> Path:
    """Return default workflow-session path for tests."""
    return (
        tmp_path
        / "devcovenant"
        / "registry"
        / "runtime"
        / "workflow_session.json"
    )


def _workflow_run_entry(
    *, session_id: str, status: str = "passed"
) -> dict[str, object]:
    """Return one minimal recorded workflow run entry."""
    return {
        "id": "tests",
        "enabled": True,
        "status": status,
        "summary_label": "Tests",
        "runner_kind": "command_group",
        "success_contract_kind": "all_commands_exit_zero",
        "last_run_session_id": session_id,
        "commands": list(_DEFAULT_REQUIRED_COMMANDS),
        "command_name": "run",
    }


def _write_workflow_session_payload(
    tmp_path: Path,
    payload: dict[str, object],
    *,
    custom_path: Path | None = None,
) -> None:
    """Write one workflow-session payload for workflow-contract checks."""
    path = custom_path or _workflow_session_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_workflow_status_payload(
    tmp_path: Path,
    payload: dict[str, object],
    *,
    workflow_runs: list[str] | None = None,
    tests_run_present: bool = True,
    tests_run_status: str = "passed",
    tests_run_session_id: str | None = None,
    custom_status_path: Path | None = None,
    custom_workflow_session_path: Path | None = None,
) -> None:
    """Write gate status and aligned workflow-session payloads."""
    _write_workflow_contract_fixture(tmp_path, workflow_runs=workflow_runs)
    path = custom_status_path or _workflow_status_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    session_id = str(payload.get("session_id", "")).strip()
    commands = (
        list(workflow_runs)
        if workflow_runs is not None
        else list(_DEFAULT_REQUIRED_COMMANDS)
    )
    runs: dict[str, object] = {}
    if commands and tests_run_present:
        runs["tests"] = _workflow_run_entry(
            session_id=tests_run_session_id or session_id,
            status=tests_run_status,
        )
    _write_workflow_session_payload(
        tmp_path,
        {
            "schema_version": 1,
            "workflow_contract_schema_version": 1,
            "session_id": session_id,
            "session_state": str(payload.get("session_state", "")).strip(),
            "run_ids": ["tests"] if commands else [],
            "anchors": {},
            "runs": runs,
        },
        custom_path=custom_workflow_session_path,
    )


def _closed_session_payload() -> dict[str, object]:
    """Return a fully valid closed-session status payload."""
    return {
        "session_id": "123",
        "session_state": "closed",
        "pre_commit_open_epoch": 10.0,
        "pre_commit_open_command": "pre-commit run --all-files",
        "pre_commit_close_epoch": 20.0,
        "pre_commit_close_command": "pre-commit run --all-files",
        "last_run_epoch": 15.0,
        "last_run_utc": "2026-02-18T00:00:15+00:00",
        "commands": list(_DEFAULT_REQUIRED_COMMANDS),
    }


def _open_session_payload() -> dict[str, object]:
    """Return a fully valid open-session status payload."""
    payload = _closed_session_payload()
    payload["session_state"] = "open"
    payload.pop("pre_commit_close_epoch", None)
    payload.pop("pre_commit_close_command", None)
    return payload


class WorkflowSupportValidationTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_open_stage_skips_checks(self):
        """Open-stage pre-commit should skip workflow enforcement."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                ctx = _make_workflow_check_context(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                )
                monkeypatch.setenv("DEVCOV_DEVFLOW_STAGE", "open")
                violations = workflow_validation.check_workflow_contract(ctx)
                self.assertEqual(violations, [])
        finally:
            monkeypatch.undo()

    def test_missing_status_with_edits_requires_full_flow(self):
        """Edits without status should require the full gate flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            ctx = _make_workflow_check_context(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_close",
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertTrue(violations)
            self.assertIn("gate --open", violations[0].message)
            self.assertIn("gate --verify", violations[0].message)
            self.assertIn("devcovenant run", violations[0].message)
            self.assertIn("gate --close", violations[0].message)

    def test_missing_status_allows_read_only_check_bootstrap(self):
        """Read-only check should not fail before the first gate session."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                ctx = _make_workflow_check_context(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                    session_reason_code="missing_gate_status",
                )
                monkeypatch.setenv("DEVCOV_TOP_COMMAND", "check")
                violations = workflow_validation.check_workflow_contract(ctx)
                self.assertEqual(violations, [])
        finally:
            monkeypatch.undo()

    def test_closed_session_without_edits_passes(self):
        """Closed session with matching workflow-run evidence should pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_workflow_status_payload(
                tmp_path,
                _closed_session_payload(),
            )
            ctx = _make_workflow_check_context(
                tmp_path, ["src/example.py"], working_numstat={}
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertEqual(violations, [])

    def test_python_module_pre_commit_record_is_rejected(self):
        """Recorded launcher drift should fail exact validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            payload = _closed_session_payload()
            payload["pre_commit_open_command"] = (
                "python3 -m pre_commit run --all-files"
            )
            payload["pre_commit_close_command"] = (
                "/tmp/.venv/bin/python -m pre_commit run --all-files"
            )
            _write_workflow_status_payload(tmp_path, payload)
            ctx = _make_workflow_check_context(
                tmp_path, ["src/example.py"], working_numstat={}
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertEqual(len(violations), 2)
            self.assertTrue(
                all(
                    (
                        "pre-commit run --all-files" in violation.message
                        for violation in violations
                    )
                )
            )

    def test_open_session_requires_close(self):
        """Non-close stage should fail while session remains open."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_workflow_status_payload(
                tmp_path,
                _open_session_payload(),
            )
            ctx = _make_workflow_check_context(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_close",
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertTrue(
                any(("Session is still open" in v.message for v in violations))
            )

    def test_missing_required_run_configuration(self):
        """Missing workflow runs should produce a config violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_workflow_status_payload(
                tmp_path,
                _closed_session_payload(),
                workflow_runs=[],
                tests_run_present=False,
            )
            ctx = _make_workflow_check_context(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                workflow_runs=[],
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertTrue(violations)
            self.assertIn("No workflow runs", violations[0].message)

    def test_missing_required_run_for_current_session_is_reported(self):
        """Required run evidence must belong to the active session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_workflow_status_payload(
                tmp_path,
                _closed_session_payload(),
                tests_run_session_id="older-session",
            )
            ctx = _make_workflow_check_context(
                tmp_path, ["src/example.py"], working_numstat={}
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertTrue(violations)
            self.assertIn("missing runs: tests", violations[0].message)
            self.assertIn("Run `devcovenant run`.", violations[0].message)

    def test_missing_workflow_session_mentions_mid_gate(self):
        """Missing workflow-session guidance should teach the full flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            status_path = _workflow_status_path(tmp_path)
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                json.dumps(_closed_session_payload()),
                encoding="utf-8",
            )
            ctx = _make_workflow_check_context(
                tmp_path, ["src/example.py"], working_numstat={}
            )
            session_path = _workflow_session_path(tmp_path)
            if session_path.exists():
                session_path.unlink()
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertTrue(violations)
            self.assertIn("gate --open", violations[0].message)
            self.assertIn("gate --verify", violations[0].message)
            self.assertIn("devcovenant run", violations[0].message)
            self.assertIn("gate --close", violations[0].message)

    def test_custom_runtime_paths_are_honored(self):
        """Custom evidence paths from config should be honored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            custom_status_path = (
                tmp_path
                / "devcovenant"
                / "registry"
                / "runtime"
                / "evidence"
                / "status.json"
            )
            custom_workflow_path = (
                tmp_path
                / "devcovenant"
                / "registry"
                / "runtime"
                / "evidence"
                / "workflow.json"
            )
            _write_workflow_status_payload(
                tmp_path,
                _closed_session_payload(),
                custom_status_path=custom_status_path,
                custom_workflow_session_path=custom_workflow_path,
            )
            ctx = _make_workflow_check_context(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                config={
                    "paths": {
                        "gate_status_file": (
                            "devcovenant/registry/runtime/evidence/"
                            "status.json"
                        ),
                        "workflow_session_file": (
                            "devcovenant/registry/runtime/evidence/"
                            "workflow.json"
                        ),
                    }
                },
            )
            violations = workflow_validation.check_workflow_contract(ctx)
            self.assertEqual(violations, [])


MODULE = "devcovenant.core.workflow_support"


class WorkflowSupportTests(unittest.TestCase):
    """unittest wrappers for mirrored collector tests."""

    def test_module_importable(self) -> None:
        """Collector module should still point at the mirrored source."""
        assert importlib.import_module(MODULE) is not None
