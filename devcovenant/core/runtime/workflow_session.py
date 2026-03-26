"""Runtime helpers for persisted workflow-session state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from devcovenant.core.runtime import (
    session_snapshot as session_snapshot_runtime,
)
from devcovenant.core.services import registry as registry_runtime

SCHEMA_VERSION = 1
_PHASE_SNAPSHOTS_KEY = "workflow_phase_snapshots"


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
        "phases": {},
        "required_phase_ids": [],
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
    anchors = payload.get("anchors")
    normalized["anchors"] = dict(anchors) if isinstance(anchors, dict) else {}
    phases = payload.get("phases")
    normalized["phases"] = dict(phases) if isinstance(phases, dict) else {}
    required_phase_ids = payload.get("required_phase_ids")
    normalized["required_phase_ids"] = (
        list(required_phase_ids)
        if isinstance(required_phase_ids, list)
        else []
    )
    return normalized


def write_workflow_session(
    repo_root: Path,
    payload: Mapping[str, object],
) -> Path:
    """Persist workflow-session payload to the runtime registry."""

    path = workflow_session_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def resolve_phase_snapshot(
    repo_root: Path,
    payload: Mapping[str, object],
    phase_id: str,
) -> dict[str, str] | None:
    """Return the stored verification snapshot for one workflow phase."""

    snapshot_payload = session_snapshot_runtime.load_session_snapshot_payload(
        repo_root,
        payload,
    )
    raw_snapshots = snapshot_payload.get(_PHASE_SNAPSHOTS_KEY)
    if not isinstance(raw_snapshots, dict):
        return None
    raw_snapshot = raw_snapshots.get(str(phase_id or "").strip())
    if not isinstance(raw_snapshot, dict):
        return None
    return session_snapshot_runtime.normalize_snapshot_rows(
        raw_snapshot,
        field_name=f"{_PHASE_SNAPSHOTS_KEY}.{phase_id}",
    )


def merge_phase_snapshot(
    repo_root: Path,
    payload: Mapping[str, object],
    phase_id: str,
    snapshot: Mapping[str, str],
) -> tuple[str, dict[str, object]]:
    """Merge one phase snapshot into the shared session-snapshot file."""

    snapshot_payload = session_snapshot_runtime.load_session_snapshot_payload(
        repo_root,
        payload,
    )
    phase_snapshots = snapshot_payload.get(_PHASE_SNAPSHOTS_KEY)
    normalized_snapshots = (
        dict(phase_snapshots) if isinstance(phase_snapshots, dict) else {}
    )
    normalized_snapshots[str(phase_id or "").strip()] = dict(snapshot)
    return session_snapshot_runtime.merge_session_snapshot_payload(
        repo_root,
        dict(payload),
        updates={_PHASE_SNAPSHOTS_KEY: normalized_snapshots},
    )
