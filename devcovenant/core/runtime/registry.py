"""Runtime registry path helpers owned by the runtime layer."""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.services import (
    core_invariants as core_invariants_service,
)
from devcovenant.core.services import tracked_registry

RUNTIME_REGISTRY_DIR = f"{tracked_registry.REGISTRY_DIR}/runtime"
GATE_STATUS_FILENAME = "gate_status.json"
WORKFLOW_SESSION_FILENAME = "workflow_session.json"
LATEST_RUNTIME_FILENAME = "latest.json"
SESSION_SNAPSHOT_FILENAME = "session_snapshot.json"
_DEVFLOW_INVARIANT_ID = "devflow-run-gates"


def runtime_registry_root(repo_root: Path) -> Path:
    """Return the path to the runtime registry directory."""
    return repo_root / RUNTIME_REGISTRY_DIR


def _default_runtime_evidence_relative_path(filename: str) -> Path:
    """Return the canonical repo-relative runtime evidence path."""

    return Path(RUNTIME_REGISTRY_DIR) / str(filename or "").strip()


def _resolve_runtime_evidence_path(
    repo_root: Path,
    *,
    option_name: str,
    default_filename: str,
    override_value: object | None = None,
) -> Path:
    """
    Resolve one configurable runtime evidence path under the runtime root.
    """

    default_relative = _default_runtime_evidence_relative_path(
        default_filename
    )
    if override_value is None:
        metadata = (
            core_invariants_service.runtime_core_invariant_metadata_options(
                repo_root,
                _DEVFLOW_INVARIANT_ID,
            )
        )
        overrides = (
            core_invariants_service.runtime_core_invariant_config_overrides(
                repo_root,
                _DEVFLOW_INVARIANT_ID,
            )
        )
        raw_value = overrides.get(option_name, metadata.get(option_name, ""))
    else:
        raw_value = override_value
    token = str(raw_value or "").strip()
    relative_path = Path(token) if token else default_relative
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(
            f"`{option_name}` must be a repo-relative path inside "
            "`devcovenant/registry/runtime/`."
        )
    candidate = repo_root / relative_path
    runtime_root = runtime_registry_root(repo_root).resolve()
    resolved = candidate.resolve()
    if resolved != runtime_root and runtime_root not in resolved.parents:
        raise ValueError(
            f"`{option_name}` must stay inside "
            "`devcovenant/registry/runtime/`."
        )
    return candidate


def latest_runtime_path(repo_root: Path) -> Path:
    """Return the runtime latest-run pointer path."""
    return runtime_registry_root(repo_root) / LATEST_RUNTIME_FILENAME


def session_snapshot_path(repo_root: Path) -> Path:
    """Return the runtime session snapshot companion path."""
    return runtime_registry_root(repo_root) / SESSION_SNAPSHOT_FILENAME


def gate_status_path(repo_root: Path) -> Path:
    """Return the configured gate-status file path."""

    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="gate_status_file",
        default_filename=GATE_STATUS_FILENAME,
    )


def gate_status_path_from_option(
    repo_root: Path,
    raw_value: object | None,
) -> Path:
    """Resolve one gate-status path from an explicit option value."""

    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="gate_status_file",
        default_filename=GATE_STATUS_FILENAME,
        override_value=raw_value,
    )


def workflow_session_path(repo_root: Path) -> Path:
    """Return the configured workflow-session file path."""

    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="workflow_session_file",
        default_filename=WORKFLOW_SESSION_FILENAME,
    )


def workflow_session_path_from_option(
    repo_root: Path,
    raw_value: object | None,
) -> Path:
    """Resolve one workflow-session path from an explicit option value."""

    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="workflow_session_file",
        default_filename=WORKFLOW_SESSION_FILENAME,
        override_value=raw_value,
    )
