"""Check-context and change-state builders extracted from `policy_engine`."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from devcovenant.core.contracts.policy import ChangeState, CheckContext
from devcovenant.core.runtime.execution import (
    capture_current_numstat_snapshot,
    changed_numstat_paths,
    diff_snapshot_paths,
    normalize_snapshot_rows,
    snapshot_row_style,
)


def build_check_context(
    repo_root: Path,
    *,
    config: dict[str, Any] | None,
    translator_runtime: Any,
    gate_status_path: Path,
    is_ignored_path: Callable[[Path], bool],
    resolve_file_suffixes: Callable[[], list[str]],
    collect_all_files: Callable[[set[str]], list[Path]],
) -> CheckContext:
    """Build the `CheckContext` used by policy checks."""
    change_state = build_change_state(
        repo_root,
        gate_status_path=gate_status_path,
        is_ignored_path=is_ignored_path,
    )
    suffixes = set(resolve_file_suffixes())
    all_files = [
        path
        for path in collect_all_files(suffixes)
        if not is_ignored_path(path)
    ]
    changed_files = (
        list(change_state.session_paths) if change_state.session_valid else []
    )
    return CheckContext(
        repo_root=repo_root,
        changed_files=changed_files,
        all_files=all_files,
        config=config or {},
        translator_runtime=translator_runtime,
        change_state=change_state,
    )


def build_change_state(
    repo_root: Path,
    *,
    gate_status_path: Path,
    is_ignored_path: Callable[[Path], bool],
) -> ChangeState:
    """Build current-snapshot and session scopes for policy checks."""
    phase = os.environ.get("DEVCOV_DEVFLOW_PHASE", "").strip().lower()
    state = ChangeState(
        phase=phase,
        gate_status_path=gate_status_path.as_posix(),
    )

    def _set_invalid(reason_code: str, message: str) -> ChangeState:
        """Populate one explicit invalid-session reason and message."""
        state.session_valid = False
        state.session_reason_code = reason_code
        state.session_error = message
        return state

    try:
        current_snapshot = capture_current_numstat_snapshot(repo_root)
    except ValueError as error:
        _set_invalid("snapshot_error", str(error))
        return state
    current_snapshot = {
        path: row
        for path, row in current_snapshot.items()
        if not is_ignored_path(repo_root / path)
    }
    state.current_snapshot_numstat = dict(current_snapshot)
    state.current_snapshot_paths = [
        repo_root / path for path in sorted(current_snapshot)
    ]

    def _current_snapshot_for_style(style: str) -> dict[str, str]:
        """
        Return the current snapshot rendered in a target row style.

        Legacy-session compatibility: older gate snapshots may store
        `mtime<TAB>size<TAB>path` rows. We render current files in that same
        style for deterministic row-level comparisons without git history.
        """
        if style != "legacy_numstat":
            return dict(current_snapshot)
        legacy_rows: dict[str, str] = {}
        for path in sorted(current_snapshot):
            file_path = repo_root / path
            try:
                stat = file_path.stat()
            except OSError as error:
                _set_invalid(
                    "snapshot_error",
                    f"Unable to stat snapshot file {file_path}: {error}",
                )
                return {}
            legacy_rows[path] = f"{stat.st_mtime_ns}\t{stat.st_size}\t{path}"
        return legacy_rows

    if phase == "start":
        state.session_valid = True
        state.session_reason_code = "start_phase"
        state.session_paths = []
        state.session_error = ""
        return state

    status_path = repo_root / gate_status_path
    if not status_path.exists():
        return _set_invalid(
            "missing_gate_status",
            f"Gate status file is missing: {gate_status_path.as_posix()}. "
            "Run `devcovenant gate --start` first.",
        )

    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return _set_invalid(
            "invalid_gate_status_json",
            f"Invalid gate status JSON in {gate_status_path.as_posix()}: "
            f"{error}",
        )
    if not isinstance(payload, dict):
        return _set_invalid(
            "invalid_gate_status_payload",
            "Invalid gate status payload: expected a mapping.",
        )
    state.gate_status_payload = payload

    session_id = str(payload.get("session_id", "")).strip()
    if not session_id:
        return _set_invalid(
            "missing_session_id",
            "Gate status payload is missing `session_id`. "
            "Run `devcovenant gate --start` first.",
        )

    session_state = str(payload.get("session_state", "")).strip().lower()
    if session_state not in {"open", "closed"}:
        return _set_invalid(
            "invalid_session_state",
            "Invalid gate status payload: `session_state` must be "
            "`open` or `closed`.",
        )

    def _load_snapshot_field(
        field_name: str,
        *,
        missing_reason_code: str,
    ) -> dict[str, str] | None:
        """Load one snapshot mapping field from gate status."""
        if field_name not in payload:
            _set_invalid(
                missing_reason_code,
                "Invalid gate status payload: "
                f"`{field_name}` is required for session checks.",
            )
            return None
        try:
            snapshot = normalize_snapshot_rows(
                payload.get(field_name),
                field_name=field_name,
            )
        except ValueError as error:
            _set_invalid("invalid_snapshot_payload", str(error))
            return None
        return {
            path: row
            for path, row in snapshot.items()
            if not is_ignored_path(repo_root / path)
        }

    if session_state == "closed":
        end_snapshot = _load_snapshot_field(
            "session_end_snapshot",
            missing_reason_code="missing_session_end_snapshot",
        )
        if end_snapshot is None:
            return state
        end_style = snapshot_row_style(end_snapshot)
        post_end_paths = diff_snapshot_paths(
            end_snapshot,
            _current_snapshot_for_style(end_style),
        )
        if not state.session_reason_code and end_style == "legacy_numstat":
            state.session_reason_code = "legacy_snapshot_compat"
        if post_end_paths:
            _set_invalid(
                "unsessioned_edits_after_end",
                "Detected edits after the previous `devcovenant gate "
                "--end`. Run `devcovenant gate --start` to open a new "
                "session.",
            )
            return state
        state.session_valid = True
        state.session_reason_code = "closed_clean"
        state.session_paths = []
        state.session_error = ""
        return state

    start_snapshot = _load_snapshot_field(
        "session_start_snapshot",
        missing_reason_code="missing_session_start_snapshot",
    )
    if start_snapshot is None:
        return state

    baseline_snapshot = start_snapshot
    if "session_baseline_snapshot" in payload:
        loaded_baseline = _load_snapshot_field(
            "session_baseline_snapshot",
            missing_reason_code="missing_session_baseline_snapshot",
        )
        if loaded_baseline is None:
            return state
        baseline_snapshot = loaded_baseline
    baseline_style = snapshot_row_style(baseline_snapshot)
    session_rel_paths = changed_numstat_paths(
        baseline_snapshot,
        _current_snapshot_for_style(baseline_style),
    )
    if not state.session_reason_code and baseline_style == "legacy_numstat":
        state.session_reason_code = "legacy_snapshot_compat"
    state.session_paths = sorted(
        [repo_root / path for path in session_rel_paths]
    )
    state.session_valid = True
    if not state.session_reason_code:
        state.session_reason_code = "open_session"
    state.session_error = ""
    return state
