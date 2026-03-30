"""Runtime helpers for persisted workflow-session state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from devcovenant.core.runtime import registry as registry_runtime
from devcovenant.core.runtime import (
    session_snapshot as session_snapshot_runtime,
)

SCHEMA_VERSION = 1
_RUN_SNAPSHOTS_KEY = "workflow_run_snapshots"


def _normalize_commands(raw_value: object) -> list[str]:
    """Normalize workflow entry commands into a trimmed ordered list."""

    if isinstance(raw_value, list):
        values = raw_value
    elif isinstance(raw_value, str):
        values = [part.strip() for part in raw_value.split("&&")]
    else:
        values = []
    commands: list[str] = []
    for entry in values:
        token = str(entry or "").strip()
        if token and token not in commands:
            commands.append(token)
    return commands


def _normalize_entry_payload(entry_raw: object) -> dict[str, object]:
    """Normalize one anchor/run payload into the current session shape."""

    entry = dict(entry_raw) if isinstance(entry_raw, Mapping) else {}
    last_run_utc = str(entry.get("last_run_utc") or "").strip()
    if last_run_utc:
        entry["last_run_utc"] = last_run_utc
    else:
        entry.pop("last_run_utc", None)
    entry.pop("last_run", None)
    commands = _normalize_commands(entry.get("commands"))
    if commands:
        entry["commands"] = commands
    else:
        entry.pop("commands", None)
    entry.pop("command", None)
    return entry


def _normalize_entry_mapping(raw_entries: object) -> dict[str, object]:
    """Normalize stored anchor/run entry mappings."""

    if not isinstance(raw_entries, dict):
        return {}
    normalized: dict[str, object] = {}
    for key, value in raw_entries.items():
        token = str(key or "").strip()
        if not token:
            continue
        normalized[token] = _normalize_entry_payload(value)
    return normalized


def workflow_session_path(repo_root: Path) -> Path:
    """Return the runtime workflow-session path for a repository."""

    return registry_runtime.workflow_session_path(repo_root)


def _base_payload() -> dict[str, object]:
    """Return an empty workflow-session payload."""

    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": "",
        "session_state": "",
        "anchors": {},
        "runs": {},
        "run_ids": [],
    }


def load_workflow_session(repo_root: Path) -> dict[str, object]:
    """Load workflow-session payload, defaulting to an empty structure."""

    path = workflow_session_path(repo_root)
    if not path.exists():
        return _base_payload()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid workflow session JSON in {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Workflow session payload must be a mapping: {path}")
    normalized = _base_payload()
    normalized.update(payload)
    normalized.pop("required_run_ids", None)
    anchors = payload.get("anchors")
    normalized["anchors"] = _normalize_entry_mapping(anchors)
    runs = payload.get("runs")
    normalized["runs"] = _normalize_entry_mapping(runs)
    run_ids = payload.get("run_ids")
    normalized["run_ids"] = list(run_ids) if isinstance(run_ids, list) else []
    return normalized


def write_workflow_session(
    repo_root: Path,
    payload: Mapping[str, object],
) -> Path:
    """Persist workflow-session payload to the runtime registry."""

    path = workflow_session_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _base_payload()
    normalized.update(dict(payload))
    normalized.pop("required_run_ids", None)
    normalized["anchors"] = _normalize_entry_mapping(normalized.get("anchors"))
    normalized["runs"] = _normalize_entry_mapping(normalized.get("runs"))
    path.write_text(
        json.dumps(normalized, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def resolve_run_snapshot(
    repo_root: Path,
    payload: Mapping[str, object],
    run_id: str,
) -> dict[str, str] | None:
    """Return the stored verification snapshot for one workflow run."""

    snapshot_payload = session_snapshot_runtime.load_session_snapshot_payload(
        repo_root,
        payload,
    )
    raw_snapshots = snapshot_payload.get(_RUN_SNAPSHOTS_KEY)
    if not isinstance(raw_snapshots, dict):
        return None
    raw_snapshot = raw_snapshots.get(str(run_id or "").strip())
    if not isinstance(raw_snapshot, dict):
        return None
    return session_snapshot_runtime.normalize_snapshot_rows(
        raw_snapshot,
        field_name=f"{_RUN_SNAPSHOTS_KEY}.{run_id}",
    )


def merge_run_snapshot(
    repo_root: Path,
    payload: Mapping[str, object],
    run_id: str,
    snapshot: Mapping[str, str],
) -> tuple[str, dict[str, object]]:
    """Merge one run snapshot into the shared session-snapshot file."""

    snapshot_payload = session_snapshot_runtime.load_session_snapshot_payload(
        repo_root,
        payload,
    )
    run_snapshots = snapshot_payload.get(_RUN_SNAPSHOTS_KEY)
    normalized_snapshots = (
        dict(run_snapshots) if isinstance(run_snapshots, dict) else {}
    )
    normalized_snapshots[str(run_id or "").strip()] = dict(snapshot)
    return session_snapshot_runtime.merge_session_snapshot_payload(
        repo_root,
        dict(payload),
        updates={_RUN_SNAPSHOTS_KEY: normalized_snapshots},
    )
