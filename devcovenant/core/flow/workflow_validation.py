"""Session gate contract for start, required phases, and end."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from devcovenant.core.contracts.invariant import CoreInvariantCheck
from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.runtime import registry as runtime_registry_module
from devcovenant.core.services import (
    core_invariants as core_invariants_service,
)
from devcovenant.core.services import (
    workflow_contract as workflow_contract_module,
)

_DEFAULT_STATUS = (
    Path("devcovenant") / "registry" / "runtime" / "gate_status.json"
)
_DEFAULT_WORKFLOW_SESSION = (
    Path("devcovenant") / "registry" / "runtime" / "workflow_session.json"
)
_DEFAULT_PRE_COMMIT_COMMAND = "python3 -m pre_commit run --all-files"
_DEFAULT_PRE_COMMIT_START_KEY = "pre_commit_start_epoch"
_DEFAULT_PRE_COMMIT_END_KEY = "pre_commit_end_epoch"
_DEFAULT_PRE_COMMIT_START_COMMAND_KEY = "pre_commit_start_command"
_DEFAULT_PRE_COMMIT_END_COMMAND_KEY = "pre_commit_end_command"


def _resolve_status_path(invariant: "DevflowRunGates") -> Path:
    """Return the configured gate status path relative to the repository."""
    raw = str(invariant.get_option("gate_status_file", str(_DEFAULT_STATUS)))
    token = raw.strip()
    if not token:
        return _DEFAULT_STATUS
    return Path(token)


def _phase_rerun_command(phase_id: str) -> str:
    """Return the canonical rerun command for one workflow phase."""
    token = str(phase_id or "").strip().lower()
    return f"devcovenant phase run {token}"


def _format_phase_rerun_instructions(
    phase_ids: list[str],
    *,
    required_phase_ids: list[str] | None = None,
) -> str:
    """Render one operator-facing rerun instruction chain."""
    phase_tokens = [
        str(phase_id or "").strip().lower()
        for phase_id in phase_ids
        if str(phase_id or "").strip()
    ]
    required_tokens = [
        str(phase_id or "").strip().lower()
        for phase_id in (required_phase_ids or [])
        if str(phase_id or "").strip()
    ]
    if phase_tokens and required_tokens and phase_tokens == required_tokens:
        return "`devcovenant run`"
    commands = [_phase_rerun_command(phase_id) for phase_id in phase_tokens]
    if not commands:
        return ""
    if len(commands) == 1:
        return f"`{commands[0]}`"
    return ", then ".join(f"`{command}`" for command in commands)


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


def _require_pre_commit(invariant: "DevflowRunGates", key: str) -> bool:
    """Return whether the specified pre-commit requirement is enabled."""
    return bool(invariant.get_option(key, True))


def _pre_commit_command(invariant: "DevflowRunGates") -> str:
    """Return the required pre-commit command string."""
    option = invariant.get_option("pre_commit_command", "")
    if isinstance(option, list):
        for entry in option:
            token = str(entry or "").strip()
            if token:
                return token.lower()
        return _DEFAULT_PRE_COMMIT_COMMAND.lower()
    raw = str(option or "").strip()
    if not raw:
        raw = _DEFAULT_PRE_COMMIT_COMMAND
    return raw.lower()


def _pre_commit_key(
    invariant: "DevflowRunGates", key: str, default: str
) -> str:
    """Return the configured gate-status key name."""
    option_value = invariant.get_option(key, default)
    return str(option_value).strip() or default


def _as_epoch(raw: object) -> float:
    """Parse one epoch field, returning 0 when missing/invalid."""
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_recorded_commands(commands_raw: list[object]) -> set[str]:
    """Normalize recorded command history into exact lowercase tokens."""
    return {
        str(entry).strip().lower()
        for entry in commands_raw
        if str(entry).strip()
    }


def _allow_closed_audit_end_order_relaxation(
    ctx: CheckContext,
    *,
    phase: str,
    session_state: str,
    has_unsessioned_edits: bool,
) -> bool:
    """Return True when stale end-vs-test ordering is audit-safe.

    This branch is intentionally narrow:
    - applies only to non-gate command checks (`phase` empty)
    - applies only to closed sessions
    - applies only when runtime reports no unsessioned edits since end
    """
    if phase:
        return False
    if session_state != "closed":
        return False
    if has_unsessioned_edits:
        return False
    return bool(ctx.change_state.session_valid)


def configured_invariant(repo_root: Path) -> DevflowRunGates:
    """Return the configured devflow invariant instance for one repo."""
    checker = core_invariants_service.load_core_invariant_check_instance(
        repo_root,
        "devflow-run-gates",
    )
    if checker is None or not isinstance(checker, DevflowRunGates):
        raise ValueError(
            "Core invariant `devflow-run-gates` could not be loaded."
        )
    checker.set_options(
        core_invariants_service.runtime_core_invariant_metadata_options(
            repo_root,
            "devflow-run-gates",
        ),
        core_invariants_service.runtime_core_invariant_config_overrides(
            repo_root,
            "devflow-run-gates",
        ),
    )
    return checker


class DevflowRunGates(CoreInvariantCheck):
    """Validate that all work is bound to one recorded gate session."""

    invariant_id = "devflow-run-gates"

    def check(self, ctx: CheckContext) -> List[Violation]:
        """Enforce start->required-phases->end sequencing from gate state."""
        violations: List[Violation] = []
        status_rel = _resolve_status_path(self)
        status_path = ctx.repo_root / status_rel
        phase = os.environ.get("DEVCOV_DEVFLOW_PHASE", "").strip().lower()
        in_pre_commit = bool(str(os.environ.get("PRE_COMMIT", "")).strip())

        if in_pre_commit and not phase:
            return violations
        if phase == "start":
            return violations

        try:
            status = _load_gate_status(status_path)
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=str(error),
                )
            ]
        if not status:
            top_command = (
                str(os.environ.get("DEVCOV_TOP_COMMAND", "")).strip().lower()
            )
            reason = str(ctx.change_state.session_reason_code or "").strip()
            if (
                not phase
                and top_command == "check"
                and reason == "missing_gate_status"
            ):
                # Read-only audit checks should stay usable before the first
                # gate session has been opened.
                return violations
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Gate status is missing. Run "
                        "`devcovenant gate --start`, then `devcovenant run`, "
                        "then `devcovenant gate --end`."
                    ),
                )
            ]

        workflow_session_path = runtime_registry_module.workflow_session_path(
            ctx.repo_root
        )
        try:
            workflow_session_rel = workflow_session_path.relative_to(
                ctx.repo_root
            )
        except ValueError:
            workflow_session_rel = workflow_session_path

        session_id = str(status.get("session_id", "")).strip()
        session_state = str(status.get("session_state", "")).strip().lower()
        session_reason_code = str(
            ctx.change_state.session_reason_code or ""
        ).strip()
        has_unsessioned_edits = (
            not ctx.change_state.session_valid
            and session_reason_code == "unsessioned_edits_after_end"
        )
        if not session_id:
            if has_unsessioned_edits:
                return [
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Changes exist without a recorded session. "
                            "Run `devcovenant gate --start` before edits."
                        ),
                    )
                ]
            return violations

        if phase == "end":
            if session_state != "open":
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "End gate requires an active open session. "
                            "Run `devcovenant gate --start` first."
                        ),
                    )
                )
                return violations
        else:
            if session_state == "open":
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session is still open. Complete the workflow "
                            "with `devcovenant gate --end`."
                        ),
                    )
                )
            elif has_unsessioned_edits:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Detected edits outside an active session. "
                            "Run `devcovenant gate --start` before edits."
                        ),
                    )
                )

        try:
            workflow_contract = (
                workflow_contract_module.load_workflow_contract(ctx.repo_root)
            )
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=str(error),
                )
            ]
        required_phase_ids = workflow_contract_module.required_phase_ids(
            workflow_contract
        )
        if not required_phase_ids:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "No required workflow phases are configured for "
                        "the active profiles. Declare `workflow_phases` "
                        "before relying on devflow-run-gates."
                    ),
                )
            ]
        try:
            workflow_session = _load_workflow_session(workflow_session_path)
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=str(error),
                )
            ]
        if not workflow_session:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "Workflow session is missing. Run "
                        "`devcovenant gate --start`, execute required "
                        "workflow phases, then `devcovenant gate --end`."
                    ),
                )
            ]

        pre_commit_command = _pre_commit_command(self)
        require_start = _require_pre_commit(self, "require_pre_commit_start")
        require_end = _require_pre_commit(self, "require_pre_commit_end")
        if phase == "end":
            require_end = False

        start_epoch_key = _pre_commit_key(
            self, "pre_commit_start_epoch_key", _DEFAULT_PRE_COMMIT_START_KEY
        )
        end_epoch_key = _pre_commit_key(
            self, "pre_commit_end_epoch_key", _DEFAULT_PRE_COMMIT_END_KEY
        )
        start_command_key = _pre_commit_key(
            self,
            "pre_commit_start_command_key",
            _DEFAULT_PRE_COMMIT_START_COMMAND_KEY,
        )
        end_command_key = _pre_commit_key(
            self,
            "pre_commit_end_command_key",
            _DEFAULT_PRE_COMMIT_END_COMMAND_KEY,
        )

        start_ts = _as_epoch(status.get(start_epoch_key))
        end_ts = _as_epoch(status.get(end_epoch_key))
        if require_start:
            if start_ts <= 0.0:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session start pre-commit run is missing. Run "
                            "`devcovenant gate --start` before edits."
                        ),
                    )
                )
            start_command = str(status.get(start_command_key) or "").lower()
            if pre_commit_command and pre_commit_command not in start_command:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session start pre-commit command is missing or "
                            f"does not include `{pre_commit_command}`. "
                            "Re-run `devcovenant gate --start`."
                        ),
                    )
                )
        workflow_session_id = str(
            workflow_session.get("session_id", "")
        ).strip()
        workflow_session_state = (
            str(workflow_session.get("session_state", "")).strip().lower()
        )
        if workflow_session_id and workflow_session_id != session_id:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "Workflow session id does not match gate status. "
                        "Re-run `devcovenant gate --start`."
                    ),
                )
            )
            return violations
        if phase == "end":
            if workflow_session_state != "open":
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
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
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "Workflow session is still open. Complete the "
                        "workflow with `devcovenant gate --end`."
                    ),
                )
            )

        phases_raw = workflow_session.get("phases")
        phase_map = dict(phases_raw) if isinstance(phases_raw, dict) else {}
        missing_required_phases: list[str] = []
        for phase_id in required_phase_ids:
            phase_entry = phase_map.get(phase_id)
            if not isinstance(phase_entry, dict):
                missing_required_phases.append(phase_id)
                continue
            if str(phase_entry.get("status", "")).strip().lower() != "passed":
                missing_required_phases.append(phase_id)
                continue
            last_run_session_id = str(
                phase_entry.get("last_run_session_id", "")
            ).strip()
            if session_id and last_run_session_id != session_id:
                missing_required_phases.append(phase_id)
                continue
        if missing_required_phases:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=workflow_session_rel,
                    message=(
                        "Latest recorded workflow session is missing "
                        "required phases: "
                        f"{', '.join(missing_required_phases)}. Run "
                        f"{_format_phase_rerun_instructions(
                            missing_required_phases,
                            required_phase_ids=required_phase_ids,
                        )}."
                    ),
                )
            )

        if require_end:
            if end_ts <= 0.0:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
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
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session end timestamp predates session start. "
                            "Re-run `devcovenant gate --end`."
                        ),
                    )
                )
            end_command = str(status.get(end_command_key) or "").lower()
            if pre_commit_command and pre_commit_command not in end_command:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session end pre-commit command is missing or "
                            f"does not include `{pre_commit_command}`. "
                            "Re-run `devcovenant gate --end`."
                        ),
                    )
                )

        return violations
