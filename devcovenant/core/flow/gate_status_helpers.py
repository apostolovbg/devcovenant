"""Internal helpers for gate status payloads and read-only status output."""

from __future__ import annotations

import json
from pathlib import Path

import devcovenant.core.flow.gate_status_validation as status_validation
import devcovenant.core.runtime.execution as execution_runtime_module
import devcovenant.core.runtime.registry as registry_runtime_module
import devcovenant.core.runtime.workflow_session as workflow_session_runtime


def _load_status(path: Path) -> dict:
    """Load the current status payload."""
    return status_validation.load_gate_status_payload(path)


def _gate_status_summary_lines(repo_root: Path) -> list[str]:
    """Return short, deterministic status lines for `gate --status`."""
    repo_root = Path(repo_root)
    status_path = registry_runtime_module.gate_status_path(repo_root)
    status_rel = _repo_relative(repo_root, status_path)
    latest_pointer = _resolve_latest_relevant_run_pointer(repo_root)
    latest_line = _latest_pointer_summary_line(latest_pointer)
    if not status_path.exists():
        lines = [
            "Gate Status: missing",
            f"Status File: {status_rel}",
        ]
        if latest_line:
            lines.append(latest_line)
        return lines

    try:
        payload = _load_status(status_path)
    except ValueError as error:
        lines = [
            "Gate Status: malformed",
            f"Status File: {status_rel}",
            f"Error: {error}",
        ]
        if latest_line:
            lines.append(latest_line)
        return lines
    workflow_payload = _load_workflow_session_payload(repo_root)

    session_state = str(payload.get("session_state", "")).strip().lower()
    state_label = session_state or "unknown"
    lines = [f"Gate Status: {state_label}"]
    session_id = str(payload.get("session_id", "")).strip()
    if session_id:
        lines.append(f"Session ID: {session_id}")
    last_stage = _infer_last_gate_stage(payload, workflow_payload)
    if last_stage:
        lines.append(f"Last Stage: {last_stage}")

    session_start = _status_time_token(
        payload, "session_start_utc"
    ) or _status_time_token(payload, "pre_commit_start_utc")
    if session_start:
        lines.append(f"Session Start: {session_start}")
    session_end = _status_time_token(payload, "session_end_utc")
    if session_end:
        lines.append(f"Session End: {session_end}")
    last_workflow_run = _latest_workflow_run_utc(payload, workflow_payload)
    if last_workflow_run:
        lines.append(f"Last Workflow Run: {last_workflow_run}")
    if latest_line:
        lines.append(latest_line)
    return lines


def _infer_last_gate_stage(
    payload: dict[str, object],
    workflow_payload: dict[str, object] | None = None,
) -> str:
    """Infer the latest completed public workflow stage."""

    stage_epochs = _stage_epochs(payload, workflow_payload)
    resolved = [
        (index, stage, epoch)
        for index, (stage, epoch) in enumerate(stage_epochs)
        if epoch > 0.0
    ]
    if not resolved:
        return ""
    _, stage, _ = max(resolved, key=lambda item: (item[2], item[0]))
    return stage


def _load_workflow_session_payload(repo_root: Path) -> dict[str, object]:
    """Load workflow-session payload for status rendering when available."""

    try:
        return workflow_session_runtime.load_workflow_session(repo_root)
    except ValueError:
        return {}


def _anchor_epoch(
    workflow_payload: dict[str, object] | None,
    stage: str,
) -> float:
    """Return one workflow-session anchor epoch when present."""

    if not isinstance(workflow_payload, dict):
        return 0.0
    anchors = workflow_payload.get("anchors")
    if not isinstance(anchors, dict):
        return 0.0
    anchor = anchors.get(stage)
    if not isinstance(anchor, dict):
        return 0.0
    return _status_epoch(anchor, "last_run_epoch")


def _runs_epoch(workflow_payload: dict[str, object] | None) -> float:
    """Return the latest workflow-run epoch from session state."""

    if not isinstance(workflow_payload, dict):
        return 0.0
    runs = workflow_payload.get("runs")
    if not isinstance(runs, dict):
        return 0.0
    latest = 0.0
    for entry in runs.values():
        if not isinstance(entry, dict):
            continue
        latest = max(latest, _status_epoch(entry, "last_run_epoch"))
    return latest


def _runs_last_run_utc(workflow_payload: dict[str, object] | None) -> str:
    """Return the latest workflow-run UTC token from session state."""

    if not isinstance(workflow_payload, dict):
        return ""
    runs = workflow_payload.get("runs")
    if not isinstance(runs, dict):
        return ""
    latest_epoch = 0.0
    latest_token = ""
    for entry in runs.values():
        if not isinstance(entry, dict):
            continue
        epoch = _status_epoch(entry, "last_run_epoch")
        token = _status_time_token(entry, "last_run_utc")
        if epoch > latest_epoch and token:
            latest_epoch = epoch
            latest_token = token
    return latest_token


def _stage_epochs(
    payload: dict[str, object],
    workflow_payload: dict[str, object] | None = None,
) -> list[tuple[str, float]]:
    """Return ordered public workflow stages with their latest epochs."""

    return [
        (
            "start",
            max(
                _status_epoch(payload, "pre_commit_start_epoch"),
                _anchor_epoch(workflow_payload, "start"),
            ),
        ),
        ("mid", _anchor_epoch(workflow_payload, "mid")),
        (
            "run",
            max(
                _status_epoch(payload, "last_run_epoch"),
                _runs_epoch(workflow_payload),
            ),
        ),
        (
            "end",
            max(
                _status_epoch(payload, "pre_commit_end_epoch"),
                _anchor_epoch(workflow_payload, "end"),
            ),
        ),
    ]


def _latest_workflow_run_utc(
    payload: dict[str, object],
    workflow_payload: dict[str, object] | None = None,
) -> str:
    """Return the latest workflow-run UTC token across both ledgers."""

    gate_epoch = _status_epoch(payload, "last_run_epoch")
    gate_token = _status_time_token(payload, "last_run_utc")
    session_epoch = _runs_epoch(workflow_payload)
    session_token = _runs_last_run_utc(workflow_payload)
    if session_epoch > gate_epoch and session_token:
        return session_token
    return gate_token


def _status_epoch(payload: dict[str, object], key: str) -> float:
    """Return one epoch-like numeric field from status payload or `0.0`."""
    try:
        value = float(payload.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if value < 0.0:
        return 0.0
    return value


def _status_time_token(payload: dict[str, object], key: str) -> str:
    """Return one trimmed time field from status payload when present."""
    return str(payload.get(key, "")).strip()


def _resolve_latest_relevant_run_pointer(
    repo_root: Path,
) -> dict[str, str] | None:
    """Return the latest relevant run pointer for status output."""
    run_logging = execution_runtime_module.run_logging_runtime_module
    pointer_path = run_logging.latest_run_pointer_path(repo_root)
    pointer_payload = _load_json_mapping(pointer_path)
    active_context = execution_runtime_module.get_active_run_log_context()
    active_run_id = active_context.run_id if active_context is not None else ""
    pointer_run_id = str(pointer_payload.get("run_id", "")).strip()
    if pointer_payload and pointer_run_id and pointer_run_id != active_run_id:
        return _normalize_latest_pointer_payload(pointer_payload)
    return None


def _normalize_latest_pointer_payload(
    payload: dict[str, object],
) -> dict[str, str]:
    """Normalize `latest.json` payload fields used by status output."""
    return {
        "run_id": str(payload.get("run_id", "")).strip(),
        "command_name": str(payload.get("command_name", "")).strip(),
        "status": str(payload.get("status", "")).strip(),
        "run_dir": str(payload.get("run_dir", "")).strip(),
        "summary_txt": str(payload.get("summary_txt", "")).strip(),
        "summary_json": str(payload.get("summary_json", "")).strip(),
    }


def _latest_pointer_summary_line(
    pointer: dict[str, str] | None,
) -> str:
    """Render one short latest-run line for `gate --status` output."""
    if not pointer:
        return ""
    run_dir = str(pointer.get("run_dir", "")).strip()
    summary_txt = str(pointer.get("summary_txt", "")).strip()
    command_name = str(pointer.get("command_name", "")).strip()
    status = str(pointer.get("status", "")).strip()
    if not run_dir:
        return ""
    suffix_parts = []
    if command_name:
        suffix_parts.append(f"command: {command_name}")
    if status:
        suffix_parts.append(f"status: {status}")
    if summary_txt:
        suffix_parts.append(f"summary: {summary_txt}")
    suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
    return f"Latest Relevant Logs: {run_dir}{suffix}"


def _load_json_mapping(path: Path) -> dict[str, object]:
    """Read one JSON file into a mapping, returning empty mapping on errors."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _repo_relative(repo_root: Path, path: Path) -> str:
    """Return repo-relative path text when possible."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)
