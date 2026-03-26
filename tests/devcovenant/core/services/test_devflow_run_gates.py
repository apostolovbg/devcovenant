"""Tests for the DevFlow gate-session core invariant."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import ChangeState, CheckContext
from devcovenant.core.services import devflow_run_gates
from tests.devcovenant.support import MonkeyPatch

DevflowRunGates = devflow_run_gates.DevflowRunGates

_DEFAULT_REQUIRED_COMMANDS = [
    "run suite-a",
    "run suite-b",
]


def _write_workflow_contract(
    tmp_path: Path,
    *,
    workflow_phases: list[str] | None = None,
) -> None:
    """Write minimal config and registry surfaces for workflow-contract use."""
    commands = (
        list(workflow_phases)
        if workflow_phases is not None
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
                "  compatibility_policy: breaking-allowed",
                "  versioning_mode: versioned",
                "profiles:",
                "  active:",
                "    - python",
                "",
            ]
        ),
        encoding="utf-8",
    )
    workflow_phase_lines = [
        "    workflow_phases:",
        "      - id: tests",
        "        enabled: true",
        "        required: true",
        "        after: mid",
        "        before: end",
        "        order: 100",
        "        runner:",
        "          kind: command_group",
        "          commands:",
    ]
    for command in commands:
        workflow_phase_lines.append(f"            - {command}")
    workflow_phase_lines.extend(
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
        registry_lines.extend(workflow_phase_lines)
    registry_lines.extend(["inventory: {}", ""])
    registry_path = tmp_path / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("\n".join(registry_lines), encoding="utf-8")


def _make_ctx(
    tmp_path: Path,
    changed: list[str],
    *,
    working_numstat: dict[str, str] | None = None,
    session_valid: bool = False,
    session_error: str = "",
    session_reason_code: str = "",
    config: dict | None = None,
    workflow_phases: list[str] | None = None,
) -> CheckContext:
    """Build test context with changed files and optional working snapshot."""
    _write_workflow_contract(tmp_path, workflow_phases=workflow_phases)
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
            session_error=session_error,
            session_reason_code=session_reason_code,
        ),
    )


def _status_path(tmp_path: Path) -> Path:
    """Return default gate status path for tests."""
    return (
        tmp_path / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )


def _workflow_session_path(tmp_path: Path) -> Path:
    """Return default workflow-session path for tests."""
    return (
        tmp_path
        / "devcovenant"
        / "registry"
        / "runtime"
        / "workflow_session.json"
    )


def _phase_entry(
    *,
    session_id: str,
    status: str = "passed",
) -> dict[str, object]:
    """Return one minimal recorded workflow phase entry."""
    return {
        "id": "tests",
        "required": True,
        "enabled": True,
        "status": status,
        "summary_label": "Tests",
        "runner_kind": "command_group",
        "success_contract_kind": "all_commands_exit_zero",
        "last_run_session_id": session_id,
        "command": " && ".join(_DEFAULT_REQUIRED_COMMANDS),
        "commands": list(_DEFAULT_REQUIRED_COMMANDS),
        "command_name": "run",
    }


def _write_workflow_session(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    """Write one workflow-session payload for invariant checks."""
    path = _workflow_session_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_status(
    tmp_path: Path,
    payload: dict[str, object],
    *,
    workflow_phases: list[str] | None = None,
    tests_phase_present: bool = True,
    tests_phase_status: str = "passed",
    tests_phase_session_id: str | None = None,
) -> None:
    """Write gate status and aligned workflow-session payloads."""
    _write_workflow_contract(tmp_path, workflow_phases=workflow_phases)
    path = _status_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    session_id = str(payload.get("session_id", "")).strip()
    commands = (
        list(workflow_phases)
        if workflow_phases is not None
        else list(_DEFAULT_REQUIRED_COMMANDS)
    )
    phases: dict[str, object] = {}
    if commands and tests_phase_present:
        phases["tests"] = _phase_entry(
            session_id=tests_phase_session_id or session_id,
            status=tests_phase_status,
        )
    _write_workflow_session(
        tmp_path,
        {
            "schema_version": 1,
            "workflow_contract_schema_version": 1,
            "session_id": session_id,
            "session_state": str(payload.get("session_state", "")).strip(),
            "required_phase_ids": ["tests"] if commands else [],
            "anchors": {},
            "phases": phases,
        },
    )


def _configured_check(
    *,
    extra_options: dict | None = None,
) -> DevflowRunGates:
    """Return invariant instance with optional metadata overrides."""
    options = dict(extra_options or {})
    check = DevflowRunGates()
    check.set_options(options, {})
    return check


def _closed_session_payload() -> dict:
    """Return a fully valid closed-session status payload."""
    return {
        "session_id": "123",
        "session_state": "closed",
        "pre_commit_start_epoch": 10.0,
        "pre_commit_start_command": "python3 -m pre_commit run --all-files",
        "pre_commit_end_epoch": 20.0,
        "pre_commit_end_command": "python3 -m pre_commit run --all-files",
        "last_run_epoch": 15.0,
        "last_run_utc": "2026-02-18T00:00:15+00:00",
        "commands": list(_DEFAULT_REQUIRED_COMMANDS),
    }


def _open_session_payload() -> dict:
    """Return a fully valid open-session status payload."""
    payload = _closed_session_payload()
    payload["session_state"] = "open"
    payload.pop("pre_commit_end_epoch", None)
    payload.pop("pre_commit_end_command", None)
    return payload


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_start_phase_skips_checks(self):
        """Start-phase pre-commit should skip session enforcement."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                ctx = _make_ctx(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                )
                monkeypatch.setenv("DEVCOV_DEVFLOW_PHASE", "start")
                violations = _configured_check().check(ctx)
                self.assertEqual(violations, [])
        finally:
            monkeypatch.undo()

    def test_missing_status_with_edits_requires_start(self):
        """Edits without status should require opening a session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_end",
            )
            violations = _configured_check().check(ctx)
            self.assertTrue(violations)
            self.assertIn("gate --start", violations[0].message)

    def test_missing_status_allows_read_only_check_bootstrap(self):
        """Read-only check should not fail before first gate session."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                ctx = _make_ctx(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                    session_reason_code="missing_gate_status",
                )
                monkeypatch.setenv("DEVCOV_TOP_COMMAND", "check")
                violations = _configured_check().check(ctx)
                self.assertEqual(violations, [])
        finally:
            monkeypatch.undo()

    def test_closed_session_without_edits_passes(self):
        """Closed session with matching workflow-phase evidence should pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check().check(ctx)
            self.assertEqual(violations, [])

    def test_list_valued_pre_commit_command_is_normalized(self):
        """List-valued command metadata should still match gate status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check(
                extra_options={
                    "pre_commit_command": [
                        "python3 -m pre_commit run --all-files"
                    ]
                }
            ).check(ctx)
            self.assertEqual(violations, [])

    def test_invariant_id_contract(self):
        """Invariant id should remain stable for runtime wiring."""
        devflowrungates = DevflowRunGates()
        self.assertEqual(devflowrungates.invariant_id, "devflow-run-gates")
        self.assertEqual(devflowrungates.policy_id, "devflow-run-gates")

    def test_open_session_requires_end(self):
        """Non-end phase should fail while session remains open."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _open_session_payload())
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_end",
            )
            violations = _configured_check().check(ctx)
            self.assertTrue(
                any("Session is still open" in v.message for v in violations)
            )

    def test_end_phase_requires_missing_required_phase(self):
        """End-phase checks should require recorded required phases."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _write_status(
                    tmp_path,
                    _open_session_payload(),
                    tests_phase_present=False,
                )
                ctx = _make_ctx(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                )
                monkeypatch.setenv("DEVCOV_DEVFLOW_PHASE", "end")
                violations = _configured_check().check(ctx)
                self.assertTrue(
                    any(
                        "missing required phases: tests" in v.message
                        for v in violations
                    )
                )
        finally:
            monkeypatch.undo()

    def test_closed_session_with_unsessioned_edits_requires_start(self):
        """Edits against a closed session require a new start gate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_end",
            )
            violations = _configured_check().check(ctx)
            self.assertTrue(
                any(
                    "outside an active session" in v.message
                    for v in violations
                )
            )

    def test_closed_session_with_matching_end_snapshot_passes(self):
        """Closed-session edits pass when runtime marks the session valid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_valid=True,
            )
            violations = _configured_check().check(ctx)
            self.assertEqual(violations, [])

    def test_closed_session_with_unsessioned_edits_still_blocks(self):
        """Closed sessions with post-end edits must still block."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                session_reason_code="unsessioned_edits_after_end",
            )
            violations = _configured_check().check(ctx)
            self.assertTrue(
                any(
                    "outside an active session" in violation.message
                    for violation in violations
                )
            )

    def test_missing_required_phase_configuration(self):
        """Missing workflow phases should produce config violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(
                tmp_path,
                _closed_session_payload(),
                workflow_phases=[],
                tests_phase_present=False,
            )
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                workflow_phases=[],
            )
            violations = _configured_check().check(ctx)
            self.assertTrue(violations)
            self.assertIn("No required workflow phases", violations[0].message)

    def test_missing_required_phase_for_current_session_is_reported(self):
        """Required phase evidence must belong to the active session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(
                tmp_path,
                _closed_session_payload(),
                tests_phase_session_id="older-session",
            )
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check().check(ctx)
            self.assertTrue(violations)
            self.assertIn(
                "missing required phases: tests", violations[0].message
            )

    def test_custom_status_path(self):
        """Custom status path from config overrides should be honored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_workflow_contract(tmp_path)
            status_path = tmp_path / "alt" / "status.json"
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                json.dumps(_closed_session_payload()), encoding="utf-8"
            )
            _write_workflow_session(
                tmp_path,
                {
                    "schema_version": 1,
                    "workflow_contract_schema_version": 1,
                    "session_id": "123",
                    "session_state": "closed",
                    "required_phase_ids": ["tests"],
                    "anchors": {},
                    "phases": {"tests": _phase_entry(session_id="123")},
                },
            )
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                config={
                    "user_metadata_overrides": {
                        "devflow-run-gates": {
                            "gate_status_file": "alt/status.json",
                        }
                    }
                },
            )
            check = DevflowRunGates()
            check.set_options({}, ctx.get_policy_config("devflow-run-gates"))
            violations = check.check(ctx)
            self.assertEqual(violations, [])
