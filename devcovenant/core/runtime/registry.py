"""Runtime registry path helpers owned by the runtime layer."""

from __future__ import annotations

from pathlib import Path

import yaml

from devcovenant.core.services import tracked_registry
from devcovenant.core.services import yaml_cache as yaml_cache_service

RUNTIME_REGISTRY_DIR = f"{tracked_registry.REGISTRY_DIR}/runtime"
GATE_STATUS_FILENAME = "gate_status.json"
WORKFLOW_SESSION_FILENAME = "workflow_session.json"
LATEST_RUNTIME_FILENAME = "latest.json"
SESSION_SNAPSHOT_FILENAME = "session_snapshot.json"


def runtime_registry_root(repo_root: Path) -> Path:
    """Return the path to the runtime registry directory."""
    return repo_root / RUNTIME_REGISTRY_DIR


def _default_runtime_evidence_relative_path(filename: str) -> Path:
    """Return the canonical repo-relative runtime evidence path."""
    return Path(RUNTIME_REGISTRY_DIR) / str(filename or "").strip()


def _load_config_payload_or_empty(repo_root: Path) -> dict[str, object]:
    """Load config when present, otherwise return an empty payload."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml_cache_service.load_yaml(config_path)
    except (OSError, yaml.YAMLError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _config_runtime_path_override(
    repo_root: Path,
    *,
    option_name: str,
    config_payload: dict[str, object] | None = None,
) -> object | None:
    """Return one configured runtime evidence override when available."""
    payload = config_payload
    if not isinstance(payload, dict):
        payload = _load_config_payload_or_empty(repo_root)
    paths = payload.get("paths") if isinstance(payload, dict) else None
    if not isinstance(paths, dict):
        return None
    return paths.get(option_name)


def _resolve_runtime_evidence_path(
    repo_root: Path,
    *,
    option_name: str,
    default_filename: str,
    override_value: object | None = None,
    config_payload: dict[str, object] | None = None,
) -> Path:
    """Resolve one configurable runtime path under the runtime root."""
    default_relative = _default_runtime_evidence_relative_path(
        default_filename
    )
    raw_value = override_value
    if raw_value is None:
        raw_value = _config_runtime_path_override(
            repo_root,
            option_name=option_name,
            config_payload=config_payload,
        )
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


def gate_status_path(
    repo_root: Path,
    config_payload: dict[str, object] | None = None,
) -> Path:
    """Return the configured gate-status file path."""
    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="gate_status_file",
        default_filename=GATE_STATUS_FILENAME,
        config_payload=config_payload,
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


def workflow_session_path(
    repo_root: Path,
    config_payload: dict[str, object] | None = None,
) -> Path:
    """Return the configured workflow-session file path."""
    return _resolve_runtime_evidence_path(
        repo_root,
        option_name="workflow_session_file",
        default_filename=WORKFLOW_SESSION_FILENAME,
        config_payload=config_payload,
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
