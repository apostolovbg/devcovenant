"""Mirrored tests for devcovenant.core.policy_runtime."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from devcovenant.core.policy_contract import (
    ChangeState,
    CheckContext,
    Violation,
)
from devcovenant.core.policy_metadata import PolicyDefinition
from devcovenant.core.policy_registry import PolicySyncIssue
from tests import MonkeyPatch

MODULE = "devcovenant.core.policy_runtime"
_GATE_STATUS_REL = "devcovenant/registry/runtime/gate_status.json"
_SESSION_SNAPSHOT_REL = "devcovenant/registry/runtime/session_snapshot.json"


def _write_gate_runtime_state(
    repo_root: Path,
    *,
    gate_status: dict[str, object],
    session_snapshot: dict[str, object] | None = None,
) -> None:
    """Write split gate runtime fixtures for context-builder tests."""
    status_path = repo_root / _GATE_STATUS_REL
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(gate_status)
    if session_snapshot is not None:
        payload["session_snapshot_file"] = _SESSION_SNAPSHOT_REL
        snapshot_path = repo_root / _SESSION_SNAPSHOT_REL
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(session_snapshot, indent=2) + "\n", encoding="utf-8"
        )
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _check_context_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _check_context_symbol_contract_is_stable() -> None:
    """Context-builder seam functions should remain callable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "build_change_state")
    assert hasattr(module, "build_check_context")
    assert callable(module.build_change_state)
    assert callable(module.build_check_context)


def _check_context_symbol_assertions_cover_context_seam() -> None:
    """Tests should assert the check-context helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.build_change_state
    assert module.build_check_context


def _change_state_start_stage_filters_ignored_paths() -> None:
    """Start-stage builder should capture current snapshot and mark valid."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with (
            mock.patch.dict(
                module.os.environ, {"DEVCOV_DEVFLOW_STAGE": "start"}
            ),
            mock.patch.object(
                module,
                "capture_current_snapshot_paths",
                return_value=["keep.py", "ignored.py"],
            ) as snapshot_paths,
            mock.patch.object(
                module, "capture_current_numstat_snapshot"
            ) as numstat,
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(
                    "devcovenant/registry/runtime/gate_status.json"
                ),
                is_ignored_path=lambda path: path.name == "ignored.py",
            )
        assert state.stage == "start"
        assert state.session_valid is True
        assert state.session_paths == []
        assert state.session_error == ""
        assert state.current_snapshot_numstat == {}
        assert state.current_snapshot_paths == [repo_root / "keep.py"]
        snapshot_paths.assert_called_once_with(repo_root)
        numstat.assert_not_called()


def _change_state_open_session_uses_baseline_and_filters() -> None:
    """Open-session builder should compute filtered session paths."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_runtime_state(
            repo_root,
            gate_status={"session_id": "open-ctx-1", "session_state": "open"},
            session_snapshot={
                "session_start_snapshot": {
                    "a.py": "old-a\ta.py",
                    "b.py": "old-b\tb.py",
                    "ignored.py": "old-ignored\tignored.py",
                },
                "session_baseline_snapshot": {
                    "a.py": "old-a\ta.py",
                    "b.py": "old-b\tb.py",
                    "ignored.py": "old-ignored\tignored.py",
                },
            },
        )
        with (
            mock.patch.dict(module.os.environ, {}, clear=True),
            mock.patch.object(
                module,
                "capture_current_numstat_snapshot",
                return_value={
                    "a.py": "new-a\ta.py",
                    "b.py": "new-b\tb.py",
                    "ignored.py": "new-ignored\tignored.py",
                },
            ),
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(_GATE_STATUS_REL),
                is_ignored_path=lambda path: path.name == "ignored.py",
            )
        assert state.stage == ""
        assert state.session_valid is True
        assert state.session_error == ""
        assert state.session_reason_code == "open_session"
        assert state.gate_status_payload["session_id"] == "open-ctx-1"
        assert state.session_snapshot_path == _SESSION_SNAPSHOT_REL
        assert state.current_snapshot_paths == [
            repo_root / "a.py",
            repo_root / "b.py",
        ]
        assert state.current_snapshot_numstat == {
            "a.py": "new-a\ta.py",
            "b.py": "new-b\tb.py",
        }
        assert state.session_paths == [repo_root / "a.py", repo_root / "b.py"]


def _change_state_closed_session_rejects_post_end_edits() -> None:
    """Closed-session builder should reject post-end edits."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_runtime_state(
            repo_root,
            gate_status={
                "session_id": "closed-ctx-1",
                "session_state": "closed",
            },
            session_snapshot={"session_end_snapshot": {"a.py": "old-a\ta.py"}},
        )
        with (
            mock.patch.dict(module.os.environ, {}, clear=True),
            mock.patch.object(
                module,
                "capture_current_numstat_snapshot",
                return_value={"a.py": "new-a\ta.py"},
            ),
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(_GATE_STATUS_REL),
                is_ignored_path=lambda _path: False,
            )
        assert state.session_valid is False
        assert state.session_reason_code == "unsessioned_edits_after_end"
        assert (
            "Detected edits after the previous `devcovenant gate --end`"
            in state.session_error
        )


def _change_state_open_session_rejects_legacy_snapshot() -> None:
    """Open-session builder should reject legacy snapshot payload rows."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_runtime_state(
            repo_root,
            gate_status={
                "session_id": "open-legacy-ctx",
                "session_state": "open",
            },
            session_snapshot={
                "session_start_snapshot": {"legacy.py": "1\t1\tlegacy.py"}
            },
        )
        with (
            mock.patch.dict(module.os.environ, {}, clear=True),
            mock.patch.object(
                module,
                "capture_current_numstat_snapshot",
                return_value={"legacy.py": "hash\tlegacy.py"},
            ),
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(_GATE_STATUS_REL),
                is_ignored_path=lambda _path: False,
            )
        assert state.session_valid is False
        assert state.session_reason_code == "unsupported_snapshot_style"
        assert "`session_start_snapshot`" in state.session_error
        assert "gate --start" in state.session_error


def _change_state_closed_session_rejects_legacy_snapshot() -> None:
    """Closed-session builder should reject legacy end snapshot rows."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_runtime_state(
            repo_root,
            gate_status={
                "session_id": "closed-legacy-ctx",
                "session_state": "closed",
            },
            session_snapshot={
                "session_end_snapshot": {"legacy.py": "1\t1\tlegacy.py"}
            },
        )
        with (
            mock.patch.dict(module.os.environ, {}, clear=True),
            mock.patch.object(
                module,
                "capture_current_numstat_snapshot",
                return_value={"legacy.py": "hash\tlegacy.py"},
            ),
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(_GATE_STATUS_REL),
                is_ignored_path=lambda _path: False,
            )
        assert state.session_valid is False
        assert state.session_reason_code == "unsupported_snapshot_style"
        assert "`session_end_snapshot`" in state.session_error
        assert "gate --start" in state.session_error


def _build_context_assembles_context_with_helper_state() -> None:
    """Check-context builder should preserve helper and engine inputs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        expected_state = ChangeState(
            stage="mid",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[repo_root / "changed.py"],
        )
        calls: dict[str, object] = {}

        def _build_change_state_stub(
            repo_root_arg, *, gate_status_path, is_ignored_path
        ):
            """Capture helper arguments and return a prepared change state."""
            calls["repo_root"] = repo_root_arg
            calls["gate_status_path"] = gate_status_path
            calls["ignore_fn"] = is_ignored_path
            return expected_state

        with mock.patch.object(
            module, "build_change_state", side_effect=_build_change_state_stub
        ):
            context = module.build_check_context(
                repo_root,
                config={"ignore": {"patterns": []}},
                translator_runtime="translator-runtime",
                gate_status_path=Path(
                    "devcovenant/registry/runtime/gate_status.json"
                ),
                autofix_enabled=True,
                autofix_requested=False,
                is_ignored_path=lambda path: path.name == "ignored.py",
                resolve_file_suffixes=lambda: [".py"],
                collect_all_files=lambda suffixes: [repo_root / "all.py"],
            )
        assert calls["repo_root"] == repo_root
        assert calls["gate_status_path"] == Path(
            "devcovenant/registry/runtime/gate_status.json"
        )
        assert context.repo_root == repo_root
        assert context.translator_runtime == "translator-runtime"
        assert context.changed_files == [repo_root / "changed.py"]
        assert context.all_files == [repo_root / "all.py"]
        assert context.change_state is expected_state
        assert context.autofix_enabled is True
        assert context.autofix_requested is False


def _build_context_prefers_snapshot_paths_for_all_files() -> None:
    """Check-context builder should reuse snapshot paths before rescanning."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        expected_state = ChangeState(
            stage="mid",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[repo_root / "changed.py"],
            current_snapshot_paths=[
                repo_root / "all.py",
                repo_root / "notes.txt",
            ],
        )
        with mock.patch.object(
            module, "build_change_state", return_value=expected_state
        ):
            context = module.build_check_context(
                repo_root,
                config={"ignore": {"patterns": []}},
                translator_runtime="translator-runtime",
                gate_status_path=Path(
                    "devcovenant/registry/runtime/gate_status.json"
                ),
                autofix_enabled=False,
                autofix_requested=False,
                is_ignored_path=lambda _path: False,
                resolve_file_suffixes=lambda: [".py"],
                collect_all_files=lambda _suffixes: [
                    repo_root / "fallback.py"
                ],
            )
        assert context.all_files == [repo_root / "all.py"]


class PolicyRuntimeCheckContextTests(unittest.TestCase):
    """unittest wrappers for policy-check-context helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _check_context_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run policy-check-context symbol contract assertions."""
        _check_context_symbol_contract_is_stable()

    def test_symbol_assertions_cover_context_seam(self):
        """Run explicit policy-check-context symbol assertions."""
        _check_context_symbol_assertions_cover_context_seam()

    def test_build_change_state_start_stage_filters_ignored_paths(self):
        """Run start-stage change-state builder assertions."""
        _change_state_start_stage_filters_ignored_paths()

    def test_build_change_state_open_session_uses_baseline_and_filters(self):
        """Run open-session baseline/filter change-state assertions."""
        _change_state_open_session_uses_baseline_and_filters()

    def test_build_change_state_closed_session_rejects_post_end_edits(self):
        """Run closed-session post-end edit rejection assertions."""
        _change_state_closed_session_rejects_post_end_edits()

    def test_build_change_state_open_session_rejects_legacy_snapshot(self):
        """Run open-session legacy-snapshot rejection assertions."""
        _change_state_open_session_rejects_legacy_snapshot()

    def test_build_change_state_closed_session_rejects_legacy_snapshot(self):
        """Run closed-session legacy-snapshot rejection assertions."""
        _change_state_closed_session_rejects_legacy_snapshot()

    def test_build_check_context_assembles_context_with_helper_state(self):
        """Run check-context builder assembly assertions."""
        _build_context_assembles_context_with_helper_state()

    def test_build_check_context_prefers_snapshot_paths_for_all_files(self):
        """Run snapshot-path check-context fast-path assertions."""
        _build_context_prefers_snapshot_paths_for_all_files()


MODULE = "devcovenant.core.policy_runtime"


def _build_runner_policy(
    policy_id: str,
    *,
    severity: str = "warning",
    enabled: bool = True,
    custom: bool = False,
    raw_metadata: dict[str, str] | None = None,
) -> PolicyDefinition:
    """Build a small policy definition fixture for helper tests."""
    return PolicyDefinition(
        policy_id=policy_id,
        name=policy_id,
        severity=severity,
        auto_fix=False,
        enabled=enabled,
        custom=custom,
        description="demo",
        raw_metadata=dict(raw_metadata or {}),
    )


def _runner_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _runner_symbol_contract_is_stable() -> None:
    """Policy-check runner seam functions should remain importable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "PolicyCheckRunResult",
        "critical_disable_attempted",
        "critical_disable_attempt_violation",
        "extract_policy_options",
        "run_policy_checks",
    ]:
        assert hasattr(module, symbol)


def _runner_symbol_assertions_cover_runner_seam() -> None:
    """Tests should assert the policy-check runner seam directly."""
    module = importlib.import_module(MODULE)
    assert module.PolicyCheckRunResult
    assert module.critical_disable_attempted
    assert module.critical_disable_attempt_violation
    assert module.extract_policy_options
    assert module.run_policy_checks


def _runner_critical_disable_attempted_uses_state_and_default_config() -> None:
    """Critical-disable helper should honor state and config defaults."""
    module = importlib.import_module(MODULE)
    critical_policy = _build_runner_policy(
        "critical-demo", severity="critical"
    )
    warning_policy = _build_runner_policy("warning-demo", severity="warning")
    assert (
        module.critical_disable_attempted(
            warning_policy,
            normalized_policy_state={"warning-demo": False},
            config={},
        )
        is False
    )
    assert (
        module.critical_disable_attempted(
            critical_policy,
            normalized_policy_state={"critical-demo": False},
            config={},
        )
        is True
    )
    assert (
        module.critical_disable_attempted(
            critical_policy,
            normalized_policy_state=None,
            config={"policy_state": {"critical-demo": False}},
        )
        is True
    )


def _runner_critical_disable_attempt_violation_messages_are_stable() -> None:
    """Critical-disable violation helper should preserve remediation text."""
    module = importlib.import_module(MODULE)
    builtin_violation = module.critical_disable_attempt_violation(
        _build_runner_policy(
            "critical-demo", severity="critical", custom=False
        ),
        config_path=Path("devcovenant/config.yaml"),
    )
    custom_violation = module.critical_disable_attempt_violation(
        _build_runner_policy(
            "critical-demo", severity="critical", custom=True
        ),
        config_path=Path("devcovenant/config.yaml"),
    )
    assert builtin_violation.severity == "critical"
    assert "remain enforced" in builtin_violation.message
    assert "copy the builtin policy" in str(builtin_violation.suggestion)
    assert "custom policy metadata" in str(custom_violation.suggestion)


def _runner_extract_policy_options_preserves_severity() -> None:
    """Option extractor should decode metadata while keeping severity."""
    module = importlib.import_module(MODULE)
    policy = _build_runner_policy(
        "demo-policy",
        severity="error",
        raw_metadata={
            "header_scan_lines": "4",
            "required_globs": "README.md, AGENTS.md",
            "severity": "warning",
        },
    )
    options = module.extract_policy_options(
        policy, reserved_metadata_keys={"severity"}
    )
    assert options["severity"] == "error"
    assert options["header_scan_lines"] == 4
    assert options["required_globs"] == ["README.md", "AGENTS.md"]


def _runner_run_policy_checks_tracks_counts_for_forced_and_successful() -> (
    None
):
    """Runner helper should count forced-critical and successful checks."""
    module = importlib.import_module(MODULE)
    critical_policy = _build_runner_policy(
        "critical-demo", severity="critical", enabled=False
    )
    passing_policy = _build_runner_policy(
        "pass-demo", severity="warning", enabled=True
    )
    skipped_policy = _build_runner_policy(
        "skip-demo", severity="warning", enabled=False
    )
    calls: list[str] = []

    class _Checker:
        """Minimal checker stub for runner helper tests."""

        def __init__(self, policy_id: str) -> None:
            """Store policy id for assertions."""
            self.policy_id = policy_id
            self.options = ({}, {})

        def set_options(self, metadata_options, config_overrides) -> None:
            """Capture passed options."""
            self.options = (dict(metadata_options), dict(config_overrides))

        def check(self, context):
            """Return no violations and record execution order."""
            assert isinstance(context, CheckContext)
            calls.append(self.policy_id)
            return []

    def _load_policy_script(policy_id: str):
        """Return stubs for policies that should execute."""
        if policy_id == "skip-demo":
            raise AssertionError(
                "Disabled non-critical policy should not load."
            )
        return _Checker(policy_id)

    context = CheckContext(
        repo_root=Path("/tmp/devcovenant"),
        config={"user_metadata_overrides": {}},
    )
    result = module.run_policy_checks(
        [critical_policy, passing_policy, skipped_policy],
        context=context,
        load_policy_script=_load_policy_script,
        extract_policy_options_fn=lambda policy: {"severity": policy.severity},
        critical_disable_attempted_fn=lambda policy: policy.policy_id
        == "critical-demo",
        critical_disable_attempt_violation_fn=lambda policy: Violation(
            policy_id=policy.policy_id,
            severity="critical",
            message="forced critical",
        ),
    )
    assert calls == ["critical-demo", "pass-demo"]
    assert result.passed_count == 1
    assert result.failed_count == 1
    assert len(result.violations) == 1
    assert result.violations[0].policy_id == "critical-demo"


def _runner_run_policy_checks_captures_checker_exceptions() -> None:
    """Runner helper should convert checker exceptions into violations."""
    module = importlib.import_module(MODULE)
    exploding_policy = _build_runner_policy("explode-demo")
    context = CheckContext(repo_root=Path("/tmp/devcovenant"))

    def _load_policy_script(_policy_id: str):
        """Return a checker that raises when executed."""

        class _ExplodingChecker:
            """Minimal exploding checker."""

            def set_options(self, metadata_options, config_overrides) -> None:
                """Accept options before raising in check."""
                del metadata_options, config_overrides

            def check(self, _context):
                """Raise to exercise error-to-violation conversion."""
                raise RuntimeError("boom")

        return _ExplodingChecker()

    result = module.run_policy_checks(
        [exploding_policy],
        context=context,
        load_policy_script=_load_policy_script,
        extract_policy_options_fn=lambda policy: {"severity": policy.severity},
        critical_disable_attempted_fn=lambda _policy: False,
        critical_disable_attempt_violation_fn=lambda _policy: Violation(
            policy_id="unused", severity="critical", message="unused"
        ),
    )
    assert result.passed_count == 0
    assert result.failed_count == 1
    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.policy_id == "explode-demo"
    assert violation.severity == "error"
    assert "Policy execution failed: boom" in violation.message


class PolicyRuntimeCheckRunnerTests(unittest.TestCase):
    """unittest wrappers for policy-check-runner helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _runner_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run policy-check-runner symbol contract assertions."""
        _runner_symbol_contract_is_stable()

    def test_symbol_assertions_cover_runner_seam(self):
        """Run explicit policy-check-runner symbol assertions."""
        _runner_symbol_assertions_cover_runner_seam()

    def test_critical_disable_attempted_uses_state_and_default_config(self):
        """Run critical-disable state/default assertions."""
        _runner_critical_disable_attempted_uses_state_and_default_config()

    def test_critical_disable_attempt_violation_messages_are_stable(self):
        """Run critical-disable violation message assertions."""
        _runner_critical_disable_attempt_violation_messages_are_stable()

    def test_extract_policy_options_decodes_metadata_and_preserves_severity(
        self,
    ):
        """Run policy-option extraction/decoding assertions."""
        _runner_extract_policy_options_preserves_severity()

    def test_run_policy_checks_tracks_counts_for_forced_and_successful(self):
        """Run runner helper count/forced-policy assertions."""
        _runner_run_policy_checks_tracks_counts_for_forced_and_successful()

    def test_run_policy_checks_captures_checker_exceptions(self):
        """Run runner helper exception-to-violation assertions."""
        _runner_run_policy_checks_captures_checker_exceptions()


MODULE = "devcovenant.core.policy_runtime"


def _engine_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _engine_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _engine_engine_surface_contract_is_stable() -> None:
    """Policy-engine classes and methods should stay discoverable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "DevCovenantEngine")
    assert hasattr(module, "CheckResult")
    assert hasattr(module, "load_policy_check_instance")
    assert hasattr(module, "run_policy_runtime_action")
    engine_cls = module.DevCovenantEngine
    assert hasattr(engine_cls, "check")
    assert hasattr(engine_cls, "run_policy_checks")
    assert hasattr(engine_cls, "apply_auto_fixes")
    assert hasattr(engine_cls, "report_violations")
    assert hasattr(engine_cls, "report_sync_issues")
    assert hasattr(engine_cls, "should_block")


def _engine_checkresult_helpers_return_expected_flags() -> None:
    """CheckResult helper methods should reflect list-backed state."""
    module = importlib.import_module(MODULE)
    result_with_items = module.CheckResult(
        violations=[object()], should_block=True, sync_issues=[object()]
    )
    assert result_with_items.has_violations() is True
    assert result_with_items.has_sync_issues() is True
    empty_result = module.CheckResult(
        violations=[], should_block=False, sync_issues=[]
    )
    assert empty_result.has_violations() is False
    assert empty_result.has_sync_issues() is False


def _engine_run_policy_runtime_action_invokes_policy_action(
    monkeypatch: MonkeyPatch,
) -> None:
    """Runtime action dispatcher should call the loaded policy checker."""
    module = importlib.import_module(MODULE)

    class _FakeChecker:
        """Simple checker stub for runtime action dispatch tests."""

        def __init__(self) -> None:
            """Store received options for assertions."""
            self.options = ({}, {})

        def set_options(self, metadata_options, config_overrides) -> None:
            """Capture options passed by runtime dispatcher."""
            self.options = (
                dict(metadata_options or {}),
                dict(config_overrides or {}),
            )

        def run_runtime_action(
            self, action: str, *, repo_root: Path, payload=None
        ):
            """Return the received runtime-action payload for assertions."""
            return {
                "action": action,
                "repo_root": str(repo_root),
                "payload": payload,
                "metadata": self.options[0],
                "config": self.options[1],
            }

    class _Descriptor:
        """Descriptor stub exposing metadata for option wiring tests."""

        metadata = {"alpha": "beta"}

    def _fake_runtime_action_dispatch(
        repo_root,
        *,
        policy_id,
        action,
        payload,
        checker_loader,
        metadata_loader,
        config_loader,
    ):
        """Apply resolved options to a checker and run one runtime action."""
        checker = checker_loader(repo_root, policy_id)
        checker.set_options(
            metadata_loader(repo_root, policy_id),
            config_loader(repo_root, policy_id),
        )
        return checker.run_runtime_action(
            action, repo_root=repo_root.resolve(), payload=payload
        )

    monkeypatch.setattr(
        module,
        "load_policy_check_instance",
        lambda repo_root, policy_id: _FakeChecker(),
    )
    monkeypatch.setattr(
        module,
        "load_policy_descriptor",
        lambda repo_root, policy_id: _Descriptor(),
    )
    monkeypatch.setattr(
        module,
        "_runtime_policy_config_overrides",
        lambda repo_root, policy_id: {"gamma": "delta"},
    )
    monkeypatch.setattr(
        module.runtime_actions,
        "run_policy_runtime_action",
        _fake_runtime_action_dispatch,
    )
    result = module.run_policy_runtime_action(
        Path("/tmp/devcovenant"),
        policy_id="dependency-management",
        action="refresh-all",
        payload={"scope": "full"},
    )
    assert result["action"] == "refresh-all"
    assert result["repo_root"] == str(Path("/tmp/devcovenant").resolve())
    assert result["payload"] == {"scope": "full"}
    assert result["metadata"] == {"alpha": "beta"}
    assert result["config"] == {"gamma": "delta"}


def _engine_run_policy_runtime_action_fails_when_policy_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    """Runtime action dispatcher should fail cleanly for missing policies."""
    module = importlib.import_module(MODULE)

    def _fake_runtime_action_dispatch(
        repo_root,
        *,
        policy_id,
        action,
        payload,
        checker_loader,
        metadata_loader,
        config_loader,
    ):
        """Raise the runtime-action missing-policy error deterministically."""
        del action, payload, metadata_loader, config_loader
        if checker_loader(repo_root, policy_id) is None:
            raise ValueError(
                f"Policy script not found for runtime action: `{policy_id}`."
            )
        return None

    monkeypatch.setattr(
        module, "load_policy_check_instance", lambda repo_root, policy_id: None
    )
    monkeypatch.setattr(
        module.runtime_actions,
        "run_policy_runtime_action",
        _fake_runtime_action_dispatch,
    )
    try:
        module.run_policy_runtime_action(
            Path("/tmp/devcovenant"),
            policy_id="missing-policy",
            action="refresh-all",
            payload={},
        )
    except ValueError as error:
        assert "Policy script not found" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for missing runtime-action policy."
        )


def _engine_engine_autofix_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine autofix wrappers should delegate to `policy_autofix`."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine._custom_policy_overrides = {"demo-policy"}
    engine.fixers = ["loaded-fixer"]
    calls: dict[str, object] = {}

    def _fake_load_fixers(repo_root, custom_policy_overrides=None):
        """Capture wrapper loader args and return a sentinel payload."""
        calls["load_repo_root"] = repo_root
        calls["load_overrides"] = set(custom_policy_overrides or set())
        return ["delegated-fixer"]

    def _fake_apply_auto_fixes(violations, fixers, *, print_fn):
        """Capture wrapper apply args and return a sentinel bool."""
        calls["apply_violations"] = list(violations)
        calls["apply_fixers"] = list(fixers)
        calls["apply_print_fn"] = print_fn
        return True

    monkeypatch.setattr(
        module.policy_autofix, "load_fixers", _fake_load_fixers
    )
    monkeypatch.setattr(
        module.policy_autofix, "apply_auto_fixes", _fake_apply_auto_fixes
    )
    loaded_fixers = module.DevCovenantEngine._load_fixers(engine)
    applied = module.DevCovenantEngine.apply_auto_fixes(
        engine,
        [
            module.Violation(
                policy_id="demo-policy",
                severity="warning",
                message="demo",
                can_auto_fix=True,
            )
        ],
    )
    assert loaded_fixers == ["delegated-fixer"]
    assert calls["load_repo_root"] == engine.repo_root
    assert calls["load_overrides"] == {"demo-policy"}
    assert applied is True
    assert calls["apply_fixers"] == ["loaded-fixer"]
    assert calls["apply_print_fn"] is module.runtime_print


def _engine_engine_context_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine context builders should delegate to flat context helpers."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine.config = {"ignore": {"patterns": []}}
    engine.translator_runtime = object()
    engine._DEFAULT_GATE_STATUS_PATH = Path(
        "devcovenant/registry/runtime/gate_status.json"
    )
    engine._is_ignored_path = lambda path: False
    engine._resolve_file_suffixes = lambda: [".py"]
    engine._collect_all_files = lambda suffixes: [engine.repo_root / "a.py"]
    calls: dict[str, object] = {}
    fake_change_state = module.ChangeState(session_valid=True)
    fake_context = module.CheckContext(repo_root=engine.repo_root)

    def _fake_build_change_state(
        repo_root, *, gate_status_path, is_ignored_path
    ):
        """Capture args and return a sentinel change state."""
        calls["change_repo_root"] = repo_root
        calls["change_gate_status_path"] = gate_status_path
        calls["change_ignore_fn"] = is_ignored_path
        return fake_change_state

    def _fake_build_check_context(
        repo_root,
        *,
        config,
        translator_runtime,
        autofix_enabled,
        autofix_requested,
        gate_status_path,
        is_ignored_path,
        resolve_file_suffixes,
        collect_all_files,
    ):
        """Capture args and return a sentinel check context."""
        calls["context_repo_root"] = repo_root
        calls["context_config"] = config
        calls["context_translator_runtime"] = translator_runtime
        calls["context_autofix_enabled"] = autofix_enabled
        calls["context_autofix_requested"] = autofix_requested
        calls["context_gate_status_path"] = gate_status_path
        calls["context_ignore_fn"] = is_ignored_path
        calls["context_resolve_fn"] = resolve_file_suffixes
        calls["context_collect_fn"] = collect_all_files
        return fake_context

    monkeypatch.setattr(module, "build_change_state", _fake_build_change_state)
    monkeypatch.setattr(
        module, "build_check_context", _fake_build_check_context
    )
    change_state = module.DevCovenantEngine._build_change_state(engine)
    context = module.DevCovenantEngine._build_check_context(engine)
    assert change_state is fake_change_state
    assert context is fake_context
    assert calls["change_repo_root"] == engine.repo_root
    assert calls["change_gate_status_path"] == engine._DEFAULT_GATE_STATUS_PATH
    assert calls["context_repo_root"] == engine.repo_root
    assert calls["context_config"] is engine.config
    assert calls["context_translator_runtime"] is engine.translator_runtime
    assert calls["context_autofix_enabled"] is False
    assert calls["context_autofix_requested"] is False
    assert (
        calls["context_gate_status_path"] == engine._DEFAULT_GATE_STATUS_PATH
    )
    assert calls["context_resolve_fn"] is engine._resolve_file_suffixes
    assert calls["context_collect_fn"] is engine._collect_all_files


def _engine_engine_policy_runner_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine policy-runner wrappers should delegate to flat helpers."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.config = {"policy_state": {"critical-demo": False}}
    engine.config_path = Path("/tmp/devcovenant/config.yaml")
    engine._normalized_policy_state = {"critical-demo": False}
    engine._RESERVED_METADATA_KEYS = {"severity", "enabled"}
    engine.passed_count = 10
    engine.failed_count = 20
    calls: dict[str, object] = {}
    policy = module.PolicyDefinition(
        policy_id="critical-demo",
        name="Critical Demo",
        severity="critical",
        auto_fix=False,
        enabled=False,
        custom=False,
        description="demo",
        raw_metadata={"header_scan_lines": "4"},
    )
    fake_context = module.CheckContext(repo_root=Path("/tmp/devcovenant"))
    engine._build_check_context = lambda: fake_context
    engine._load_policy_script = lambda policy_id: None

    def _capture_critical_attempted(*args, **kwargs):
        """Capture args for critical-disable check wrapper."""
        calls["critical_attempted_args"] = args
        calls["critical_attempted_kwargs"] = kwargs
        return True

    def _capture_critical_violation(*args, **kwargs):
        """Capture args for critical-disable violation wrapper."""
        calls["critical_violation_args"] = args
        calls["critical_violation_kwargs"] = kwargs
        return module.Violation(
            policy_id="critical-demo", severity="critical", message="forced"
        )

    def _capture_extract(*args, **kwargs):
        """Capture args for policy-option extraction wrapper."""
        calls["extract_args"] = args
        calls["extract_kwargs"] = kwargs
        return {"severity": "critical"}

    def _capture_run_policy_checks(*args, **kwargs):
        """Capture args for run-policy-checks wrapper."""
        calls["run_args"] = args
        calls["run_kwargs"] = kwargs
        return module.PolicyCheckRunResult(
            violations=[
                module.Violation(
                    policy_id="demo", severity="warning", message="demo"
                )
            ],
            passed_count=2,
            failed_count=3,
        )

    monkeypatch.setattr(
        module, "critical_disable_attempted", _capture_critical_attempted
    )
    monkeypatch.setattr(
        module,
        "critical_disable_attempt_violation",
        _capture_critical_violation,
    )
    monkeypatch.setattr(module, "extract_policy_options", _capture_extract)
    monkeypatch.setattr(
        module, "run_policy_checks", _capture_run_policy_checks
    )
    attempted = module.DevCovenantEngine._critical_disable_attempted(
        engine, policy
    )
    violation = module.DevCovenantEngine._critical_disable_attempt_violation(
        engine, policy
    )
    options = module.DevCovenantEngine._extract_policy_options(engine, policy)
    run_violations = module.DevCovenantEngine.run_policy_checks(
        engine, [policy], context=None
    )
    assert attempted is True
    assert violation.policy_id == "critical-demo"
    assert options == {"severity": "critical"}
    assert len(run_violations) == 1
    assert engine.passed_count == 12
    assert engine.failed_count == 23
    assert calls["critical_attempted_args"] == (policy,)
    assert calls["critical_attempted_kwargs"]["normalized_policy_state"] == {
        "critical-demo": False
    }
    assert calls["critical_attempted_kwargs"]["config"] is engine.config
    assert calls["critical_violation_args"] == (policy,)
    assert (
        calls["critical_violation_kwargs"]["config_path"] == engine.config_path
    )
    assert calls["extract_args"] == (policy,)
    assert calls["extract_kwargs"]["reserved_metadata_keys"] == {
        "severity",
        "enabled",
    }
    assert calls["run_args"] == ([policy],)
    assert calls["run_kwargs"]["context"] is fake_context
    assert (
        calls["run_kwargs"]["load_policy_script"] is engine._load_policy_script
    )
    extract_fn = calls["run_kwargs"]["extract_policy_options_fn"]
    assert extract_fn.__self__ is engine
    assert (
        extract_fn.__func__ is module.DevCovenantEngine._extract_policy_options
    )
    attempted_fn = calls["run_kwargs"]["critical_disable_attempted_fn"]
    assert attempted_fn.__self__ is engine
    assert (
        attempted_fn.__func__
        is module.DevCovenantEngine._critical_disable_attempted
    )
    violation_fn = calls["run_kwargs"]["critical_disable_attempt_violation_fn"]
    assert violation_fn.__self__ is engine
    assert (
        violation_fn.__func__
        is module.DevCovenantEngine._critical_disable_attempt_violation
    )


def _engine_run_check_cycle_rechecks_after_autofix(
    monkeypatch: MonkeyPatch,
) -> None:
    """Check cycle should rebuild context after a successful autofix."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.passed_count = 0
    engine.failed_count = 0
    contexts = ["first-context", "second-context"]
    calls: list[str] = []
    monkeypatch.setattr(
        engine, "_build_check_context", lambda **_kwargs: contexts.pop(0)
    )
    monkeypatch.setattr(engine, "apply_auto_fixes", lambda violations: True)

    def _fake_run_checks_for_context(_policies, *, context):
        """Return different violations across the two check passes."""
        calls.append(context)
        if context == "first-context":
            engine.passed_count = 1
            engine.failed_count = 1
            return [
                module.Violation(
                    policy_id="demo",
                    severity="warning",
                    message="needs autofix",
                    can_auto_fix=True,
                )
            ]
        engine.passed_count = 4
        engine.failed_count = 0
        return []

    monkeypatch.setattr(
        engine, "_run_checks_for_context", _fake_run_checks_for_context
    )
    violations = module.DevCovenantEngine._run_check_cycle(
        engine, [], apply_fixes=True, auto_fix_enabled=True
    )
    assert violations == []
    assert calls == ["first-context", "second-context"]
    assert engine.passed_count == 4
    assert engine.failed_count == 0


def _engine_runtime_policy_metadata_options_decodes_registry_strings() -> None:
    """Runtime metadata loader should decode registry strings.

    It should expose typed values to policy runtime callers.
    """
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "policies": {
                        "demo-policy": {
                            "metadata": {
                                "enabled": "true",
                                "header_scan_lines": "4",
                                "required_globs": "README.md, AGENTS.md",
                            }
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        options = module._runtime_policy_metadata_options(
            repo_root, "demo-policy"
        )
        assert options["enabled"] is True
        assert options["header_scan_lines"] == 4
        assert options["required_globs"] == ["README.md", "AGENTS.md"]


def _write_engine_minimal_config(
    repo_root: Path, *, include_core: bool, core_paths: list[str]
) -> None:
    """Write a minimal config payload for core exclusion tests."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                f"developer_mode: {('true' if include_core else 'false')}",
                "profiles:",
                "  active: []",
                "  generated:",
                "    devcov_core_paths:",
            ]
            + [f"      - {entry}" for entry in core_paths]
        )
        + "\n",
        encoding="utf-8",
    )


def _engine_core_exclusions_ignore_builtin_when_disabled() -> None:
    """Core exclusions should ignore builtin paths when disabled."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_engine_minimal_config(
            repo_root,
            include_core=False,
            core_paths=["devcovenant/core", "devcovenant/builtin"],
        )
        monkeypatch = MonkeyPatch()
        try:
            monkeypatch.setattr(module, "load_profile_registry", lambda _: {})
            engine = module.DevCovenantEngine(repo_root=repo_root)
        finally:
            monkeypatch.undo()
        builtin_path = (
            engine.repo_root / "devcovenant" / "builtin" / "policies"
        )
        core_path = engine.repo_root / "devcovenant" / "core" / "flow"
        custom_path = engine.repo_root / "devcovenant" / "custom" / "policies"
        assert engine._is_ignored_path(builtin_path) is True
        assert engine._is_ignored_path(core_path) is True
        assert engine._is_ignored_path(custom_path) is False


def _engine_core_exclusions_respected_when_enabled() -> None:
    """Core exclusions should allow builtin paths when enabled."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_engine_minimal_config(
            repo_root,
            include_core=True,
            core_paths=["devcovenant/core", "devcovenant/builtin"],
        )
        monkeypatch = MonkeyPatch()
        try:
            monkeypatch.setattr(module, "load_profile_registry", lambda _: {})
            engine = module.DevCovenantEngine(repo_root=repo_root)
        finally:
            monkeypatch.undo()
        builtin_path = (
            engine.repo_root / "devcovenant" / "builtin" / "policies"
        )
        core_path = engine.repo_root / "devcovenant" / "core" / "flow"
        assert engine._is_ignored_path(builtin_path) is False
        assert engine._is_ignored_path(core_path) is False


def _engine_summary_status_respects_warning_fail_threshold() -> None:
    """Summary status text should match blocking threshold semantics."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"engine": {"fail_threshold": "warning"}}
    printed: list[str] = []
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "runtime_print",
            lambda *parts, **_kwargs: printed.append(
                " ".join((str(part) for part in parts))
            ),
        )
        engine._report_summary({"warning": [object(), object()]})
    finally:
        monkeypatch.undo()
    joined = "\n".join(printed)
    assert "Status: 🚫 BLOCKED (violations >= warning threshold)" in joined
    assert "Status: ✅ PASSED" not in joined


def _engine_quiet_mode_reports_violations_to_stderr(
    monkeypatch: MonkeyPatch,
) -> None:
    """Quiet-mode violation reporting should route output to stderr."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine.config = {"engine": {"fail_threshold": "warning"}}
    engine.passed_count = 0
    engine.failed_count = 1
    printed: list[dict[str, object]] = []

    def _fake_runtime_print(message="", **kwargs):
        """Capture runtime_print invocations for quiet-mode assertions."""
        printed.append({"message": str(message), **kwargs})

    monkeypatch.setattr(module, "runtime_print", _fake_runtime_print)
    monkeypatch.setattr(module, "get_output_mode", lambda: "quiet")
    engine.report_violations(
        [
            module.Violation(
                policy_id="demo-policy",
                severity="warning",
                message="demo warning",
            )
        ]
    )
    assert printed
    assert all((entry.get("file") is sys.stderr for entry in printed))


def _engine_quiet_mode_skips_success_banners(
    monkeypatch: MonkeyPatch,
) -> None:
    """Quiet mode should suppress success-only policy output."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine.config = {"engine": {"fail_threshold": "warning"}}
    engine.passed_count = 1
    engine.failed_count = 0
    printed: list[dict[str, object]] = []

    def _fake_runtime_print(message="", **kwargs):
        """Capture runtime_print invocations for quiet-mode assertions."""
        printed.append({"message": str(message), **kwargs})

    monkeypatch.setattr(module, "runtime_print", _fake_runtime_print)
    monkeypatch.setattr(module, "get_output_mode", lambda: "quiet")
    engine.report_violations([])
    assert printed == []


def _engine_critical_disable_attempt_enforced(
    monkeypatch: MonkeyPatch, *, custom_policy: bool
) -> None:
    """Critical disable attempts should emit diagnostics and still execute."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"policy_state": {"critical-demo": False}}
    engine.config_path = Path("/tmp/devcovenant/config.yaml")
    engine.passed_count = 0
    engine.failed_count = 0
    engine._normalized_policy_state = {"critical-demo": False}
    calls: list[str] = []

    class _FakeChecker:
        """Minimal checker stub that records execution."""

        def set_options(self, metadata_options, config_overrides):
            """Accept runtime options without modifying test state."""
            del metadata_options, config_overrides

        def check(self, context):
            """Record execution and return no policy-script violations."""
            del context
            calls.append("ran")
            return []

    class _FakeContext:
        """Minimal context stub for `run_policy_checks` unit tests."""

        @staticmethod
        def get_policy_config(_policy_id):
            """Return no config overrides for the fake checker."""
            return {}

    monkeypatch.setattr(
        engine, "_load_policy_script", lambda _policy_id: _FakeChecker()
    )
    monkeypatch.setattr(engine, "_extract_policy_options", lambda _policy: {})
    policy = module.PolicyDefinition(
        policy_id="critical-demo",
        name="Critical Demo",
        severity="critical",
        auto_fix=False,
        enabled=False,
        custom=custom_policy,
        description="test",
    )
    violations = engine.run_policy_checks([policy], context=_FakeContext())
    assert calls == ["ran"]
    assert engine.passed_count == 0
    assert engine.failed_count == 1
    assert len(violations) == 1
    violation = violations[0]
    assert violation.severity == "critical"
    assert "policy_state" in violation.message
    assert "remain enforced" in violation.message
    if custom_policy:
        assert "custom policy metadata" in str(violation.suggestion)
    else:
        assert "copy the builtin policy" in str(violation.suggestion)


class PolicyRuntimeEngineTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _engine_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _engine_module_has_public_symbols()

    def test_engine_surface_contract_is_stable(self):
        """Run engine surface contract assertions."""
        _engine_engine_surface_contract_is_stable()

    def test_checkresult_helpers_return_expected_flags(self):
        """Run CheckResult helper behavior assertions."""
        _engine_checkresult_helpers_return_expected_flags()

    def test_run_policy_runtime_action_invokes_policy_action(self):
        """Run runtime-action dispatch happy-path assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_run_policy_runtime_action_invokes_policy_action(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_policy_runtime_action_fails_when_policy_missing(self):
        """Run runtime-action dispatch missing-policy assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_run_policy_runtime_action_fails_when_policy_missing(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_runtime_policy_metadata_options_decodes_registry_strings(self):
        """Run runtime metadata typed-decoding assertions."""
        _engine_runtime_policy_metadata_options_decodes_registry_strings()

    def test_engine_autofix_wrappers_delegate_to_helper(self):
        """Run autofix-wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_engine_autofix_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_engine_context_wrappers_delegate_to_helper(self):
        """Run context-wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_engine_context_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_engine_policy_runner_wrappers_delegate_to_helper(self):
        """Run policy-runner wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_engine_policy_runner_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_check_cycle_rechecks_after_autofix(self):
        """Run the autofix-rerun regression for the policy-engine cycle."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_run_check_cycle_rechecks_after_autofix(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_core_exclusions_ignore_builtin_when_disabled(self):
        """Run core-exclusion ignore check for builtin paths."""
        _engine_core_exclusions_ignore_builtin_when_disabled()

    def test_core_exclusions_respected_when_enabled(self):
        """Run core-exclusion allow check for enabled mode."""
        _engine_core_exclusions_respected_when_enabled()

    def test_summary_status_respects_warning_fail_threshold(self):
        """Run fail-threshold-aware summary status assertions."""
        _engine_summary_status_respects_warning_fail_threshold()

    def test_quiet_mode_reports_violations_to_stderr(self):
        """Run quiet-mode stderr routing assertions for violations."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_quiet_mode_reports_violations_to_stderr(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_quiet_mode_skips_success_banners(self):
        """Run quiet-mode suppression assertions for success output."""
        monkeypatch = MonkeyPatch()
        try:
            _engine_quiet_mode_skips_success_banners(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_critical_builtin_disable_attempt_is_reported_and_enforced(self):
        """Run builtin critical-disable immunity assertions."""
        monkeypatch = MonkeyPatch()
        try:
            test_case = globals()["_engine_critical_disable_attempt_enforced"]
            test_case(monkeypatch=monkeypatch, custom_policy=False)
        finally:
            monkeypatch.undo()

    def test_critical_custom_disable_attempt_is_reported_and_enforced(self):
        """Run custom critical-disable immunity assertions."""
        monkeypatch = MonkeyPatch()
        try:
            test_case = globals()["_engine_critical_disable_attempt_enforced"]
            test_case(monkeypatch=monkeypatch, custom_policy=True)
        finally:
            monkeypatch.undo()


MODULE = "devcovenant.core.policy_runtime"


def _file_scope_module_importable() -> None:
    """Module should import without engine wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _file_scope_symbol_contract_is_stable() -> None:
    """File-scope helper seam symbols should remain callable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "collect_all_files",
        "config_ignore_patterns",
        "configured_ignore_dir_names",
        "core_exclusion_paths",
        "discover_custom_policy_overrides",
        "is_ignored_path",
        "matches_config_ignore_pattern",
        "profile_ignored_dir_names",
        "resolve_engine_file_suffixes",
        "should_descend_dir",
    ]:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))


def _file_scope_symbol_assertions_cover_file_scope_seam() -> None:
    """Tests should assert each file-scope helper seam symbol directly."""
    module = importlib.import_module(MODULE)
    assert module.collect_all_files
    assert module.config_ignore_patterns
    assert module.configured_ignore_dir_names
    assert module.core_exclusion_paths
    assert module.discover_custom_policy_overrides
    assert module.is_ignored_path
    assert module.matches_config_ignore_pattern
    assert module.profile_ignored_dir_names
    assert module.resolve_engine_file_suffixes
    assert module.should_descend_dir


def _file_scope_config_ignore_patterns_normalize_comments_and_dirs() -> None:
    """Config ignore patterns should normalize separators and dir markers."""
    module = importlib.import_module(MODULE)
    config = {
        "ignore": {
            "patterns": [
                " docs/generated/ ",
                "#comment",
                r"tmp\cache\\",
                "",
            ]
        }
    }
    assert module.config_ignore_patterns(config) == [
        "docs/generated/**",
        "tmp/cache/**",
    ]


def _file_scope_matches_config_ignore_pattern_matches_dir_token() -> None:
    """Pattern matcher should treat `foo/**` as matching `foo` too."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    patterns = ["docs/generated/**"]
    assert (
        module.matches_config_ignore_pattern(
            repo_root, repo_root / "docs" / "generated", patterns
        )
        is True
    )
    assert (
        module.matches_config_ignore_pattern(
            repo_root, repo_root / "docs" / "generated" / "page.md", patterns
        )
        is True
    )
    assert (
        module.matches_config_ignore_pattern(
            repo_root, repo_root / "docs" / "guide.md", patterns
        )
        is False
    )


def _file_scope_core_exclusion_paths_respect_include_toggle() -> None:
    """Core exclusion helper should honor `developer_mode`."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    disabled = module.core_exclusion_paths(
        repo_root,
        {
            "developer_mode": False,
            "profiles": {
                "generated": {
                    "devcov_core_paths": [
                        "devcovenant/core",
                        "devcovenant/builtin",
                    ]
                }
            },
        },
    )
    enabled = module.core_exclusion_paths(repo_root, {"developer_mode": True})
    assert disabled == [
        repo_root / "devcovenant/core",
        repo_root / "devcovenant/builtin",
    ]
    assert enabled == []


def _file_scope_core_exclusion_paths_fallback_matches_manifest() -> None:
    """Fallback core exclusions should stay aligned with manifest helpers."""
    module = importlib.import_module(MODULE)
    manifest_module = importlib.import_module(
        "devcovenant.core.repository_validation"
    )
    repo_root = Path("/tmp/devcovenant")
    actual = module.core_exclusion_paths(repo_root, {"developer_mode": False})
    expected = [
        repo_root / entry
        for entry in manifest_module.default_scan_excluded_core_paths()
    ]
    assert actual == expected


def _file_scope_discover_custom_policy_overrides_finds_script_dirs() -> None:
    """Custom policy override discovery should require matching script file."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        custom_root = repo_root / "devcovenant" / "custom" / "policies"
        demo_dir = custom_root / "demo_policy"
        empty_dir = custom_root / "empty_policy"
        demo_dir.mkdir(parents=True)
        empty_dir.mkdir(parents=True)
        (demo_dir / "demo_policy.py").write_text("# demo\n", encoding="utf-8")
        overrides = module.discover_custom_policy_overrides(repo_root)
    assert overrides == {"demo-policy"}


def _file_scope_is_ignored_path_checks_patterns_names_and_prefixes() -> None:
    """Ignore helper should apply pattern/name/prefix ignore rules."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    ignored_dirs = {"node_modules"}
    ignored_paths = [repo_root / "build"]
    patterns = ["docs/generated/**"]
    assert (
        module.is_ignored_path(
            repo_root / "docs" / "generated" / "out.md",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "site" / "node_modules" / "x.js",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "build" / "artifact.py",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "src" / "main.py",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is False
    )


def _file_scope_profile_ignored_dir_names_normalize_entries() -> None:
    """Profile ignore-dir helper should normalize resolver output."""
    module = importlib.import_module(MODULE)
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "resolve_profile_ignore_dirs",
            lambda _registry, _profiles: [" build ", "", "tmp"],
        )
        result = module.profile_ignored_dir_names({}, ["global"])
    finally:
        monkeypatch.undo()
    assert result == ["build", "tmp"]


def _file_scope_resolve_engine_file_suffixes_merges_and_cleans() -> None:
    """Suffix helper should merge configured and profile suffixes."""
    module = importlib.import_module(MODULE)
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "resolve_profile_suffixes",
            lambda _registry, _profiles: [".json", "  ", ".toml"],
        )
        suffixes = module.resolve_engine_file_suffixes(
            {"engine": {"file_suffixes": [".py", " .md ", ""]}}, {}, ["global"]
        )
    finally:
        monkeypatch.undo()
    assert suffixes == [".py", ".md", ".json", ".toml"]


def _file_scope_should_descend_dir_skips_ignored_and_pycache() -> None:
    """Walk helper should skip ignored names, patterns, and pycache dirs."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    common_kwargs = {
        "repo_root": repo_root,
        "ignored_dirs": {"node_modules"},
        "ignored_paths": [repo_root / "build"],
        "config_ignore_patterns": ["docs/generated/**"],
    }
    assert (
        module.should_descend_dir(repo_root / "node_modules", **common_kwargs)
        is False
    )
    assert (
        module.should_descend_dir(
            repo_root / "docs" / "generated", **common_kwargs
        )
        is False
    )
    assert (
        module.should_descend_dir(repo_root / "__pycache__", **common_kwargs)
        is False
    )
    assert (
        module.should_descend_dir(repo_root / "src", **common_kwargs) is True
    )


def _file_scope_collect_all_files_honors_ignore_rules() -> None:
    """File collection should honor suffix filters and ignore helpers."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / "build").mkdir()
        (repo_root / "tmp").mkdir()
        (repo_root / "node_modules").mkdir()
        (repo_root / "pkg" / "__pycache__").mkdir(parents=True)
        (repo_root / "src" / "main.py").write_text("x=1\n", encoding="utf-8")
        (repo_root / "docs" / "guide.md").write_text(
            "# guide\n", encoding="utf-8"
        )
        (repo_root / "build" / "skip.py").write_text("x=1\n", encoding="utf-8")
        (repo_root / "tmp" / "skip.yml").write_text("a: 1\n", encoding="utf-8")
        (repo_root / "node_modules" / "skip.py").write_text(
            "x=1\n", encoding="utf-8"
        )
        (repo_root / "pkg" / "__pycache__" / "skip.py").write_text(
            "x=1\n", encoding="utf-8"
        )
        matched = module.collect_all_files(
            repo_root,
            {".py", ".md", ".yml"},
            ignored_dirs={"node_modules"},
            ignored_paths=[repo_root / "build"],
            config_ignore_patterns=["tmp/**"],
        )
    rel = sorted((path.relative_to(repo_root).as_posix() for path in matched))
    assert rel == ["docs/guide.md", "src/main.py"]


class PolicyRuntimeFileScopeTests(unittest.TestCase):
    """unittest wrappers for policy file-scope helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _file_scope_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run file-scope helper symbol contract assertions."""
        _file_scope_symbol_contract_is_stable()

    def test_symbol_assertions_cover_file_scope_seam(self):
        """Run explicit file-scope helper symbol assertions."""
        _file_scope_symbol_assertions_cover_file_scope_seam()

    def test_config_ignore_patterns_normalize_comments_and_dirs(self):
        """Run config-ignore normalization assertions."""
        _file_scope_config_ignore_patterns_normalize_comments_and_dirs()

    def test_matches_config_ignore_pattern_matches_dir_token(self):
        """Run config-ignore pattern matching assertions."""
        _file_scope_matches_config_ignore_pattern_matches_dir_token()

    def test_core_exclusion_paths_respect_include_toggle(self):
        """Run core-exclusion path toggle assertions."""
        _file_scope_core_exclusion_paths_respect_include_toggle()

    def test_core_exclusion_paths_fallback_matches_manifest(self):
        """Run fallback core-exclusion alignment assertions."""
        _file_scope_core_exclusion_paths_fallback_matches_manifest()

    def test_discover_custom_policy_overrides_finds_script_dirs(self):
        """Run custom-policy override discovery assertions."""
        _file_scope_discover_custom_policy_overrides_finds_script_dirs()

    def test_is_ignored_path_checks_patterns_names_and_prefixes(self):
        """Run ignore-path helper rule assertions."""
        _file_scope_is_ignored_path_checks_patterns_names_and_prefixes()

    def test_profile_ignored_dir_names_normalize_entries(self):
        """Run profile ignore-dir normalization assertions."""
        _file_scope_profile_ignored_dir_names_normalize_entries()

    def test_resolve_engine_file_suffixes_merges_and_cleans(self):
        """Run suffix merge/cleanup helper assertions."""
        _file_scope_resolve_engine_file_suffixes_merges_and_cleans()

    def test_should_descend_dir_skips_ignored_and_pycache(self):
        """Run directory-walk decision helper assertions."""
        _file_scope_should_descend_dir_skips_ignored_and_pycache()

    def test_collect_all_files_honors_ignore_rules(self):
        """Run file collection helper ignore/suffix assertions."""
        _file_scope_collect_all_files_honors_ignore_rules()


MODULE = "devcovenant.core.policy_runtime"


def _capture_reporting_lines():
    """Return a print sink and collected output buffer."""
    lines: list[str] = []

    def _print(*parts, **_kwargs):
        """Collect printed parts as one line."""
        lines.append(" ".join((str(part) for part in parts)))

    return (_print, lines)


def _reporting_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _reporting_symbol_contract_is_stable() -> None:
    """Reporting helper seam functions should remain callable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "config_auto_fix_enabled",
        "config_fail_threshold",
        "report_single_violation",
        "report_summary",
        "report_sync_issues",
        "report_violations",
        "should_block",
        "violations_by_severity",
    ]:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))


def _reporting_symbol_assertions_cover_reporting_seam() -> None:
    """Tests should assert the reporting helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.config_auto_fix_enabled
    assert module.config_fail_threshold
    assert module.report_single_violation
    assert module.report_summary
    assert module.report_sync_issues
    assert module.report_violations
    assert module.should_block
    assert module.violations_by_severity


def _reporting_should_block_respects_threshold() -> None:
    """Blocking helper should honor the configured fail threshold."""
    module = importlib.import_module(MODULE)
    warning_violation = Violation(
        policy_id="line-length-limit",
        severity="warning",
        message="demo warning",
    )
    assert module.should_block([], fail_threshold="error") is False
    assert (
        module.should_block([warning_violation], fail_threshold="error")
        is False
    )
    assert (
        module.should_block([warning_violation], fail_threshold="warning")
        is True
    )


def _reporting_report_summary_emits_threshold_status() -> None:
    """Summary helper should print blocked status at warning threshold."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_reporting_lines()
    by_severity = {"warning": [object(), object()]}
    module.report_summary(
        by_severity,
        print_fn=print_fn,
        fail_threshold="warning",
        auto_fix_enabled=True,
    )
    joined = "\n".join(lines)
    assert "Summary: 0 critical, 0 errors, 2 warnings, 0 info" in joined
    assert "Status: 🚫 BLOCKED (violations >= warning threshold)" in joined
    assert "devcovenant check" in joined


def _reporting_report_single_violation_includes_location_and_policy() -> None:
    """Single-violation helper should print location and policy anchor."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_reporting_lines()
    module.report_single_violation(
        Violation(
            policy_id="line-length-limit",
            severity="warning",
            file_path=Path("README.md"),
            line_number=10,
            message="Line exceeds limit",
            suggestion="Wrap the line",
            can_auto_fix=True,
        ),
        print_fn=print_fn,
    )
    joined = "\n".join(lines)
    assert "WARNING: line-length-limit" in joined
    assert "📍 README.md:10" in joined
    assert "Policy: AGENTS.md#line-length-limit" in joined
    assert "Auto-fix: Available in gate workflow" in joined


def _reporting_report_sync_issues_suggests_test_paths() -> None:
    """Sync-issue helper should suggest deterministic test file paths."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_reporting_lines()
    issues = [
        PolicySyncIssue(
            policy_id="demo-policy",
            policy_text="x" * 520,
            policy_hash="",
            script_path=Path(
                "devcovenant/builtin/policies/demo_policy/demo_policy.py"
            ),
            script_exists=False,
            issue_type="script_missing",
        )
    ]
    module.report_sync_issues(issues, print_fn=print_fn)
    joined = "\n".join(lines)
    assert "POLICY SYNC REQUIRED" in joined
    assert (
        "Create: devcovenant/builtin/policies/demo_policy/demo_policy.py"
        in joined
    )
    assert (
        "tests/devcovenant/builtin/policies/demo_policy/test_demo_policy.py"
        in joined
    )
    assert "..." in joined


def _reporting_report_violations_groups_and_summarizes() -> None:
    """Violation report helper should print grouped details and summary."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_reporting_lines()
    violations = [
        Violation(policy_id="warn-demo", severity="warning", message="warn"),
        Violation(policy_id="err-demo", severity="error", message="err"),
    ]
    module.report_violations(
        violations,
        passed_count=4,
        failed_count=2,
        print_fn=print_fn,
        fail_threshold="error",
        auto_fix_enabled=False,
    )
    joined = "\n".join(lines)
    assert "✅ Passed: 4 policies" in joined
    assert "⚠️  Violations: 2 issues found" in joined
    assert joined.index("ERROR: err-demo") < joined.index("WARNING: warn-demo")
    assert "Status: 🚫 BLOCKED (violations >= error threshold)" in joined


def _reporting_config_helpers_normalize_engine_values() -> None:
    """Config helpers should normalize fail threshold and auto-fix flag."""
    module = importlib.import_module(MODULE)
    config = {"engine": {"fail_threshold": " Warning ", "auto_fix_enabled": 1}}
    assert module.config_fail_threshold(config) == "warning"
    assert module.config_auto_fix_enabled(config) is True
    assert module.config_fail_threshold({}) == "error"
    assert module.config_auto_fix_enabled({}) is False


class PolicyRuntimeReportingTests(unittest.TestCase):
    """unittest wrappers for policy-reporting helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _reporting_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run reporting helper symbol contract assertions."""
        _reporting_symbol_contract_is_stable()

    def test_symbol_assertions_cover_reporting_seam(self):
        """Run explicit reporting helper symbol assertions."""
        _reporting_symbol_assertions_cover_reporting_seam()

    def test_should_block_respects_threshold(self):
        """Run fail-threshold blocking helper assertions."""
        _reporting_should_block_respects_threshold()

    def test_report_summary_emits_threshold_status(self):
        """Run summary helper threshold-status assertions."""
        _reporting_report_summary_emits_threshold_status()

    def test_report_single_violation_includes_location_and_policy(self):
        """Run single-violation output assertions."""
        _reporting_report_single_violation_includes_location_and_policy()

    def test_report_sync_issues_suggests_test_paths(self):
        """Run sync-issue output path assertions."""
        _reporting_report_sync_issues_suggests_test_paths()

    def test_report_violations_groups_and_summarizes(self):
        """Run grouped violation report output assertions."""
        _reporting_report_violations_groups_and_summarizes()

    def test_config_helpers_normalize_engine_values(self):
        """Run reporting config-helper normalization assertions."""
        _reporting_config_helpers_normalize_engine_values()


MODULE = "devcovenant.core.policy_runtime"


class PolicyRuntimeTests(unittest.TestCase):
    """unittest wrappers for mirrored collector tests."""

    def test_module_importable(self) -> None:
        """Collector module should still point at the mirrored source."""
        assert importlib.import_module(MODULE) is not None
