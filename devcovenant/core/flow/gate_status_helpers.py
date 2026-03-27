"""Internal helpers for gate status payloads and read-only status output."""

from __future__ import annotations

import json
from pathlib import Path

import devcovenant.core.flow.gate_status_validation as status_validation
import devcovenant.core.runtime.execution as execution_runtime_module
import devcovenant.core.runtime.registry as registry_runtime_module


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

    session_state = str(payload.get("session_state", "")).strip().lower()
    state_label = session_state or "unknown"
    lines = [f"Gate Status: {state_label}"]
    session_id = str(payload.get("session_id", "")).strip()
    if session_id:
        lines.append(f"Session ID: {session_id}")
    last_phase = _infer_last_gate_phase(payload)
    if last_phase:
        lines.append(f"Last Phase: {last_phase}")

    session_start = _status_time_token(
        payload, "session_start_utc"
    ) or _status_time_token(payload, "pre_commit_start_utc")
    if session_start:
        lines.append(f"Session Start: {session_start}")
    session_end = _status_time_token(payload, "session_end_utc")
    if session_end:
        lines.append(f"Session End: {session_end}")
    last_workflow_run = _status_time_token(payload, "last_run_utc")
    if last_workflow_run:
        lines.append(f"Last Workflow Run: {last_workflow_run}")
    if latest_line:
        lines.append(latest_line)
    return lines


def _infer_last_gate_phase(payload: dict[str, object]) -> str:
    """Infer the latest completed lifecycle phase from gate-status fields."""
    pre_commit_end = _status_epoch(payload, "pre_commit_end_epoch")
    if pre_commit_end > 0.0:
        return "end"
    pre_commit_start = _status_epoch(payload, "pre_commit_start_epoch")
    last_run_epoch = _status_epoch(payload, "last_run_epoch")
    if pre_commit_start > 0.0 and last_run_epoch >= pre_commit_start:
        return "run"
    if pre_commit_start > 0.0:
        return "start"
    return ""


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
