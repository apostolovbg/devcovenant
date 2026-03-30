"""Workflow-contract validation for start, mid, run, and end."""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

import yaml

from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.flow import workflow_contract as workflow_contract_module
from devcovenant.core.runtime import registry as runtime_registry_module
from devcovenant.core.services import yaml_cache as yaml_cache_service

CHECK_ID = "workflow-contract"
_DEFAULT_PRE_COMMIT_COMMAND = (
    workflow_contract_module.DEFAULT_PRE_COMMIT_COMMAND
)
_PRE_COMMIT_EXECUTABLE_TOKENS = frozenset(
    {"pre-commit", "pre-commit.exe", "pre_commit", "pre_commit.exe"}
)


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


def _merged_section(
    repo_root: Path,
    context_config: dict[str, object],
    section_name: str,
) -> dict[str, object]:
    """Return one config section merged with in-context overrides."""
    merged: dict[str, object] = {}
    repo_payload = _load_config_payload_or_empty(repo_root)
    repo_section = repo_payload.get(section_name)
    if isinstance(repo_section, dict):
        merged.update(repo_section)
    context_section = context_config.get(section_name)
    if isinstance(context_section, dict):
        merged.update(context_section)
    return merged


def _resolve_status_path(context: CheckContext) -> Path:
    """Return the configured gate-status path for one repository."""
    paths = _merged_section(context.repo_root, context.config, "paths")
    return runtime_registry_module.gate_status_path_from_option(
        context.repo_root,
        paths.get("gate_status_file"),
    )


def _resolve_workflow_session_path(context: CheckContext) -> Path:
    """Return the configured workflow-session path for one repository."""
    paths = _merged_section(context.repo_root, context.config, "paths")
    return runtime_registry_module.workflow_session_path_from_option(
        context.repo_root,
        paths.get("workflow_session_file"),
    )


def _format_run_rerun_instructions(run_ids: list[str]) -> str:
    """Render the canonical rerun instruction."""
    del run_ids
    return "`devcovenant run`"


def _normalize_pre_commit_command(raw_value: object) -> str:
    """Normalize canonical pre-commit launchers for exact validation."""
    raw = str(raw_value or "").strip()
    if not raw:
        return ""
    try:
        tokens = shlex.split(raw)
    except ValueError:
        return raw.lower()
    if not tokens:
        return ""
    first = Path(tokens[0]).name.lower()
    normalized = [str(token).strip().lower() for token in tokens]
    if first in _PRE_COMMIT_EXECUTABLE_TOKENS:
        normalized[0] = "pre-commit"
        return shlex.join(normalized)
    return shlex.join(normalized)


def _required_pre_commit_command(context: CheckContext) -> str:
    """Return the workflow-owned canonical pre-commit command."""
    workflow = _merged_section(context.repo_root, context.config, "workflow")
    raw = str(workflow.get("pre_commit_command", "") or "").strip()
    if not raw:
        raw = _DEFAULT_PRE_COMMIT_COMMAND
    return _normalize_pre_commit_command(raw)


def _load_gate_status(status_file: Path) -> dict | None:
    """Return parsed gate status, or None when file is missing."""
    if not status_file.is_file():
        return None
    try:
        payload = json.loads(status_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid gate status JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Gate status payload must be a JSON object.")
    return payload


def _load_workflow_session(session_file: Path) -> dict | None:
    """Return parsed workflow-session payload, or None when file is missing."""
    if not session_file.is_file():
        return None
    try:
        payload = json.loads(session_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid workflow session JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Workflow session payload must be a JSON object.")
    return payload


def _as_epoch(raw: object) -> float:
    """Parse one epoch field, returning 0 when missing or invalid."""
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


def check_workflow_contract(
    context: CheckContext,
) -> list[Violation]:
    """Enforce the recorded start, mid, run, and end workflow contract."""
    violations: list[Violation] = []
    status_path = _resolve_status_path(context)
    status_rel = status_path.relative_to(context.repo_root)
    workflow_session_path = _resolve_workflow_session_path(context)
    workflow_session_rel = workflow_session_path.relative_to(context.repo_root)
    stage = os.environ.get("DEVCOV_DEVFLOW_STAGE", "").strip().lower()
    in_pre_commit = bool(str(os.environ.get("PRE_COMMIT", "")).strip())

    if in_pre_commit and not stage:
        return violations
    if stage == "start":
        return violations

    try:
        status = _load_gate_status(status_path)
    except ValueError as error:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_rel,
                message=str(error),
            )
        ]
    if not status:
        top_command = (
            str(os.environ.get("DEVCOV_TOP_COMMAND", "")).strip().lower()
        )
        reason = str(context.change_state.session_reason_code or "").strip()
        if (
            not stage
            and top_command == "check"
            and reason == "missing_gate_status"
        ):
            return violations
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_rel,
                message=(
                    "Gate status is missing. Run `devcovenant gate --start`, "
                    "then `devcovenant gate --mid`, then `devcovenant run`, "
                    "then `devcovenant gate --end`."
                ),
            )
        ]

    session_id = str(status.get("session_id", "")).strip()
    session_state = str(status.get("session_state", "")).strip().lower()
    session_reason_code = str(
        context.change_state.session_reason_code or ""
    ).strip()
    has_unsessioned_edits = (
        not context.change_state.session_valid
        and session_reason_code == "unsessioned_edits_after_end"
    )
    if not session_id:
        if has_unsessioned_edits:
            return [
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Changes exist without a recorded session. Run "
                        "`devcovenant gate --start` before edits."
                    ),
                )
            ]
        return violations

    if stage == "end":
        if session_state != "open":
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "End gate requires an active open session. Run "
                        "`devcovenant gate --start` first."
                    ),
                )
            )
            return violations
    else:
        if session_state == "open":
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Session is still open. Complete the workflow with "
                        "`devcovenant gate --end`."
                    ),
                )
            )
        elif has_unsessioned_edits:
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Detected edits outside an active session. Run "
                        "`devcovenant gate --start` before edits."
                    ),
                )
            )

    try:
        workflow_contract = workflow_contract_module.load_workflow_contract(
            context.repo_root
        )
    except ValueError as error:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=str(error),
            )
        ]
    run_ids = workflow_contract_module.run_ids(workflow_contract)
    if not run_ids:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=(
                    "No workflow runs are configured for the active "
                    "profiles. Declare `workflow_runs` before using "
                    "the workflow contract."
                ),
            )
        ]

    try:
        workflow_session = _load_workflow_session(workflow_session_path)
    except ValueError as error:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=str(error),
            )
        ]
    if not workflow_session:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=(
                    "Workflow session is missing. Run `devcovenant "
                    "gate --start`, then `devcovenant gate --mid`, then "
                    "execute workflow runs with `devcovenant run`, then "
                    "`devcovenant gate --end`."
                ),
            )
        ]

    pre_commit_command = _required_pre_commit_command(context)
    start_ts = _as_epoch(status.get("pre_commit_start_epoch"))
    end_ts = _as_epoch(status.get("pre_commit_end_epoch"))
    if start_ts <= 0.0:
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_rel,
                message=(
                    "Session start pre-commit run is missing. Run "
                    "`devcovenant gate --start` before edits."
                ),
            )
        )
    start_command = _normalize_pre_commit_command(
        status.get("pre_commit_start_command") or ""
    )
    if pre_commit_command and start_command != pre_commit_command:
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_rel,
                message=(
                    "Session start pre-commit command is missing or does "
                    f"not include `{pre_commit_command}`. Re-run "
                    "`devcovenant gate --start`."
                ),
            )
        )

    workflow_session_id = str(workflow_session.get("session_id", "")).strip()
    workflow_session_state = (
        str(workflow_session.get("session_state", "")).strip().lower()
    )
    if workflow_session_id and workflow_session_id != session_id:
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=(
                    "Workflow session id does not match gate status. "
                    "Re-run `devcovenant gate --start`."
                ),
            )
        )
        return violations
    if stage == "end":
        if workflow_session_state != "open":
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "Workflow session must be open during "
                        "`devcovenant gate --end`."
                    ),
                )
            )
            return violations
    elif workflow_session_state == "open":
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=(
                    "Workflow session is still open. Complete the "
                    "workflow with `devcovenant gate --end`."
                ),
            )
        )

    runs_raw = workflow_session.get("runs")
    run_map = dict(runs_raw) if isinstance(runs_raw, dict) else {}
    missing_runs: list[str] = []
    for run_id in run_ids:
        run_entry = run_map.get(run_id)
        if not isinstance(run_entry, dict):
            missing_runs.append(run_id)
            continue
        if str(run_entry.get("status", "")).strip().lower() != "passed":
            missing_runs.append(run_id)
            continue
        last_run_session_id = str(
            run_entry.get("last_run_session_id", "")
        ).strip()
        if session_id and last_run_session_id != session_id:
            missing_runs.append(run_id)
    if missing_runs:
        rerun_instructions = _format_run_rerun_instructions(missing_runs)
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=workflow_session_rel,
                message=(
                    "Latest recorded workflow session is missing runs: "
                    f"{', '.join(missing_runs)}. Run {rerun_instructions}."
                ),
            )
        )

    if stage != "end":
        if end_ts <= 0.0:
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Session end pre-commit run is missing. Run "
                        "`devcovenant gate --end`."
                    ),
                )
            )
        elif start_ts > 0.0 and end_ts < start_ts:
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Session end timestamp predates session start. "
                        "Re-run `devcovenant gate --end`."
                    ),
                )
            )
        end_command = _normalize_pre_commit_command(
            status.get("pre_commit_end_command") or ""
        )
        if pre_commit_command and end_command != pre_commit_command:
            violations.append(
                Violation(
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Session end pre-commit command is missing or does "
                        f"not include `{pre_commit_command}`. Re-run "
                        "`devcovenant gate --end`."
                    ),
                )
            )

    return violations
