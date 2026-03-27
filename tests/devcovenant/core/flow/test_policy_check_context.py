"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from devcovenant.core.contracts.policy import ChangeState

MODULE = "devcovenant.core.flow.policy_check_context"
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
            json.dumps(session_snapshot, indent=2) + "\n",
            encoding="utf-8",
        )
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Context-builder seam functions should remain callable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "build_change_state")
    assert hasattr(module, "build_check_context")
    assert callable(module.build_change_state)
    assert callable(module.build_check_context)


def _unit_test_symbol_assertions_cover_context_seam() -> None:
    """Tests should assert the check-context helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.build_change_state
    assert module.build_check_context


def _unit_test_build_change_state_start_phase_filters_ignored_paths() -> None:
    """Start-phase builder should capture current snapshot and mark valid."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        with (
            mock.patch.dict(
                module.os.environ,
                {"DEVCOV_DEVFLOW_PHASE": "start"},
            ),
            mock.patch.object(
                module,
                "capture_current_numstat_snapshot",
                return_value={
                    "keep.py": "hash-keep\tkeep.py",
                    "ignored.py": "hash-ignored\tignored.py",
                },
            ),
        ):
            state = module.build_change_state(
                repo_root,
                gate_status_path=Path(
                    "devcovenant/registry/runtime/gate_status.json"
                ),
                is_ignored_path=lambda path: path.name == "ignored.py",
            )

        assert state.phase == "start"
        assert state.session_valid is True
        assert state.session_paths == []
        assert state.session_error == ""
        assert state.current_snapshot_numstat == {
            "keep.py": "hash-keep\tkeep.py"
        }
        assert state.current_snapshot_paths == [repo_root / "keep.py"]


def _unit_test_build_change_state_open_session_uses_baseline_and_filters() -> (
    None
):
    """Open-session builder should compute filtered session paths."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_runtime_state(
            repo_root,
            gate_status={
                "session_id": "open-ctx-1",
                "session_state": "open",
            },
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

        assert state.phase == ""
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


def _unit_test_build_change_state_closed_session_rejects_post_end_edits() -> (
    None
):
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
            session_snapshot={
                "session_end_snapshot": {
                    "a.py": "old-a\ta.py",
                },
            },
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


def _unit_test_build_change_state_open_session_rejects_legacy_snapshot() -> (
    None
):
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
                "session_start_snapshot": {
                    "legacy.py": "1\t1\tlegacy.py",
                },
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


def _unit_test_build_change_state_closed_session_rejects_legacy_snapshot() -> (
    None
):
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
                "session_end_snapshot": {
                    "legacy.py": "1\t1\tlegacy.py",
                },
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


def _unit_test_build_check_context_assembles_context_with_helper_state() -> (
    None
):
    """Check-context builder should preserve helper and engine inputs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        expected_state = ChangeState(
            phase="mid",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[repo_root / "changed.py"],
        )
        calls: dict[str, object] = {}

        def _build_change_state_stub(
            repo_root_arg,
            *,
            gate_status_path,
            is_ignored_path,
        ):
            """Capture helper arguments and return a prepared change state."""
            calls["repo_root"] = repo_root_arg
            calls["gate_status_path"] = gate_status_path
            calls["ignore_fn"] = is_ignored_path
            return expected_state

        with mock.patch.object(
            module,
            "build_change_state",
            side_effect=_build_change_state_stub,
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
                collect_all_files=lambda suffixes: [
                    repo_root / "all.py",
                    repo_root / "ignored.py",
                ],
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy-check-context helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run policy-check-context symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_context_seam(self):
        """Run explicit policy-check-context symbol assertions."""
        _unit_test_symbol_assertions_cover_context_seam()

    def test_build_change_state_start_phase_filters_ignored_paths(self):
        """Run start-phase change-state builder assertions."""
        _unit_test_build_change_state_start_phase_filters_ignored_paths()

    def test_build_change_state_open_session_uses_baseline_and_filters(self):
        """Run open-session baseline/filter change-state assertions."""
        _unit_test_build_change_state_open_session_uses_baseline_and_filters()

    def test_build_change_state_closed_session_rejects_post_end_edits(self):
        """Run closed-session post-end edit rejection assertions."""
        _unit_test_build_change_state_closed_session_rejects_post_end_edits()

    def test_build_change_state_open_session_rejects_legacy_snapshot(self):
        """Run open-session legacy-snapshot rejection assertions."""
        _unit_test_build_change_state_open_session_rejects_legacy_snapshot()

    def test_build_change_state_closed_session_rejects_legacy_snapshot(self):
        """Run closed-session legacy-snapshot rejection assertions."""
        _unit_test_build_change_state_closed_session_rejects_legacy_snapshot()

    def test_build_check_context_assembles_context_with_helper_state(self):
        """Run check-context builder assembly assertions."""
        _unit_test_build_check_context_assembles_context_with_helper_state()
