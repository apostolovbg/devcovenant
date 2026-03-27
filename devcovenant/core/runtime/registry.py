"""Runtime registry path helpers owned by the runtime layer."""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.services import tracked_registry

RUNTIME_REGISTRY_DIR = f"{tracked_registry.REGISTRY_DIR}/runtime"
GATE_STATUS_FILENAME = "gate_status.json"
WORKFLOW_SESSION_FILENAME = "workflow_session.json"
LATEST_RUNTIME_FILENAME = "latest.json"
SESSION_SNAPSHOT_FILENAME = "session_snapshot.json"


def runtime_registry_root(repo_root: Path) -> Path:
    """Return the path to the runtime registry directory."""
    return repo_root / RUNTIME_REGISTRY_DIR


def latest_runtime_path(repo_root: Path) -> Path:
    """Return the runtime latest-run pointer path."""
    return runtime_registry_root(repo_root) / LATEST_RUNTIME_FILENAME


def session_snapshot_path(repo_root: Path) -> Path:
    """Return the runtime session snapshot companion path."""
    return runtime_registry_root(repo_root) / SESSION_SNAPSHOT_FILENAME


def gate_status_path(repo_root: Path) -> Path:
    """Return the gate status file path inside the runtime registry."""
    return runtime_registry_root(repo_root) / GATE_STATUS_FILENAME


def workflow_session_path(repo_root: Path) -> Path:
    """Return the workflow-session file path inside the runtime registry."""
    return runtime_registry_root(repo_root) / WORKFLOW_SESSION_FILENAME
