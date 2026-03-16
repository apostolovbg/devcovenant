"""Tests for the DevFlow gate-session policy."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.devflow_run_gates import devflow_run_gates
from devcovenant.core.contracts.policy import ChangeState, CheckContext
from tests.devcovenant.support import MonkeyPatch

DevflowRunGates = devflow_run_gates.DevflowRunGates

_DEFAULT_REQUIRED_COMMANDS = [
    "run suite-a",
    "run suite-b",
]


def _make_ctx(
    tmp_path: Path,
    changed: list[str],
    *,
    working_numstat: dict[str, str] | None = None,
    session_valid: bool = False,
    session_error: str = "",
    session_reason_code: str = "",
    config: dict | None = None,
) -> CheckContext:
    """Build test context with changed files and optional working snapshot."""
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


def _write_status(tmp_path: Path, payload: dict) -> None:
    """Write one test gate-status payload."""
    path = _status_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configured_check(
    *,
    required_commands: list[str] | None = None,
    extra_options: dict | None = None,
) -> DevflowRunGates:
    """Return policy instance with required command metadata."""
    options = {
        "required_commands": (
            list(required_commands)
            if required_commands is not None
            else list(_DEFAULT_REQUIRED_COMMANDS)
        )
    }
    options.update(dict(extra_options or {}))
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
        """Closed session with valid command evidence should pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _write_status(tmp_path, _closed_session_payload())
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check().check(ctx)
            self.assertEqual(violations, [])

    def test_policy_id_contract(self):
        """Policy id should remain stable for runtime wiring."""
        devflowrungates = DevflowRunGates()
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

    def test_end_phase_accepts_open_session(self):
        """End-phase run should validate open session without end evidence."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _write_status(tmp_path, _open_session_payload())
                ctx = _make_ctx(
                    tmp_path,
                    ["src/example.py"],
                    working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
                )
                monkeypatch.setenv("DEVCOV_DEVFLOW_PHASE", "end")
                violations = _configured_check().check(ctx)
                self.assertEqual(violations, [])
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

    def test_closed_audit_allows_stale_end_vs_test_order(self):
        """Closed no-change audits should ignore stale end/test ordering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            payload = _closed_session_payload()
            payload["pre_commit_end_epoch"] = 12.0
            payload["last_run_epoch"] = 15.0
            _write_status(tmp_path, payload)
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                session_valid=True,
            )
            violations = _configured_check().check(ctx)
            self.assertEqual(violations, [])

    def test_closed_session_with_unsessioned_edits_still_blocks(self):
        """Closed sessions with post-end edits must still block."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            payload = _closed_session_payload()
            payload["pre_commit_end_epoch"] = 12.0
            payload["last_run_epoch"] = 15.0
            _write_status(tmp_path, payload)
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

    def test_requires_tests_after_start(self):
        """Test evidence must post-date the session start timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            payload = _closed_session_payload()
            payload["last_run_epoch"] = 5.0
            _write_status(tmp_path, payload)
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check().check(ctx)
            self.assertTrue(
                any("predate session start" in v.message for v in violations)
            )

    def test_missing_required_commands_configuration(self):
        """Missing required_commands should produce config violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={"src/example.py": "1\t1\tsrc/example.py"},
            )
            check = _configured_check(required_commands=[])
            violations = check.check(ctx)
            self.assertTrue(violations)
            self.assertIn("No required test commands", violations[0].message)

    def test_required_commands_use_exact_matching(self):
        """Recorded commands should satisfy requirements by exact match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            payload = _closed_session_payload()
            payload["commands"] = ["pytest-custom"]
            _write_status(tmp_path, payload)
            ctx = _make_ctx(tmp_path, ["src/example.py"], working_numstat={})
            violations = _configured_check(required_commands=["pytest"]).check(
                ctx
            )
            self.assertTrue(violations)
            self.assertIn(
                "missing required commands: pytest", violations[0].message
            )

    def test_custom_status_path(self):
        """Custom status path from config overrides should be honored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            status_path = tmp_path / "alt" / "status.json"
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                json.dumps(_closed_session_payload()), encoding="utf-8"
            )
            ctx = _make_ctx(
                tmp_path,
                ["src/example.py"],
                working_numstat={},
                config={
                    "user_metadata_overrides": {
                        "devflow-run-gates": {
                            "gate_status_file": "alt/status.json",
                            "required_commands": list(
                                _DEFAULT_REQUIRED_COMMANDS
                            ),
                        }
                    }
                },
            )
            check = DevflowRunGates()
            check.set_options({}, ctx.get_policy_config("devflow-run-gates"))
            violations = check.check(ctx)
            self.assertEqual(violations, [])

    def test_runtime_action_resolves_required_commands(self):
        """Runtime action should return required command payload."""
        check = _configured_check(
            required_commands=["python3 -m unittest discover -v", "pytest"]
        )
        result = check.run_runtime_action(
            devflow_run_gates.RUNTIME_ACTION_RESOLVE_REQUIRED_COMMANDS,
            repo_root=Path("/tmp/repo"),
            payload={},
        )
        self.assertEqual(
            result["commands"],
            ["python3 -m unittest discover -v", "pytest"],
        )
        self.assertEqual(result["source_field"], "required_commands")

    def test_runtime_action_rejects_unsupported_action(self):
        """Unsupported runtime action should raise ValueError."""
        check = _configured_check()
        with self.assertRaises(ValueError):
            check.run_runtime_action(
                "unknown-action",
                repo_root=Path("/tmp/repo"),
                payload={},
            )
