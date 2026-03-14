"""Session gate contract: start -> test -> end for every work sequence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)

_DEFAULT_STATUS = (
    Path("devcovenant") / "registry" / "local" / "gate_status.json"
)
_DEFAULT_PRE_COMMIT_COMMAND = "python3 -m pre_commit run --all-files"
_DEFAULT_PRE_COMMIT_START_KEY = "pre_commit_start_epoch"
_DEFAULT_PRE_COMMIT_END_KEY = "pre_commit_end_epoch"
_DEFAULT_PRE_COMMIT_START_COMMAND_KEY = "pre_commit_start_command"
_DEFAULT_PRE_COMMIT_END_COMMAND_KEY = "pre_commit_end_command"
_OUTPUT_MODE_ALLOWED = frozenset({"normal", "verbose"})
_OUTPUT_MODE_DEFAULT = "verbose"


def _resolve_status_path(policy: "DevflowRunGates") -> Path:
    """Return the configured gate status path relative to the repository."""
    raw = policy.get_option("gate_status_file", str(_DEFAULT_STATUS))
    return Path(raw)


def _normalize_output_mode(raw_value: object) -> str:
    """Return one allowed output mode token with default fallback."""
    token = str(raw_value or "").strip().lower()
    if token in _OUTPUT_MODE_ALLOWED:
        return token
    return _OUTPUT_MODE_DEFAULT


def _tests_output_mode(policy: "DevflowRunGates", ctx: CheckContext) -> str:
    """Resolve tests output mode from CheckContext config."""
    config_map = ctx.config if isinstance(ctx.config, dict) else {}
    engine_map = config_map.get("engine")
    if not isinstance(engine_map, dict):
        return _OUTPUT_MODE_DEFAULT
    tests_mode = str(engine_map.get("tests_output_mode", "")).strip()
    if tests_mode:
        return _normalize_output_mode(tests_mode)
    # Backward compatibility: when tests mode is unset, reuse output_mode.
    return _normalize_output_mode(engine_map.get("output_mode"))


def _status_tests_output_mode(status: dict) -> str | None:
    """Return recorded tests output mode when gate status provides one."""
    token = str(status.get("tests_output_mode", "")).strip().lower()
    if token in _OUTPUT_MODE_ALLOWED:
        return token
    return None


def _required_commands_for_mode(
    policy: "DevflowRunGates",
    tests_mode: str,
) -> tuple[list[str], str]:
    """Return ordered required commands for one tests output mode."""
    primary_key = f"required_commands_{tests_mode}"
    commands_option = policy.get_option(primary_key, None)
    source_key = primary_key
    if commands_option is None:
        source_key = "required_commands"
        commands_option = policy.get_option(source_key, [])
    if isinstance(commands_option, str):
        commands = [commands_option]
    else:
        commands = list(commands_option or [])
    cleaned = [
        command.strip()
        for command in commands
        if isinstance(command, str) and command.strip()
    ]
    return [command.lower() for command in cleaned], source_key


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


def _require_pre_commit(policy: "DevflowRunGates", key: str) -> bool:
    """Return whether the specified pre-commit requirement is enabled."""
    return bool(policy.get_option(key, True))


def _pre_commit_command(policy: "DevflowRunGates") -> str:
    """Return the required pre-commit command string."""
    command = policy.get_option(
        "pre_commit_command", _DEFAULT_PRE_COMMIT_COMMAND
    )
    return str(command).strip().lower()


def _pre_commit_key(policy: "DevflowRunGates", key: str, default: str) -> str:
    """Return the configured gate-status key name."""
    option_value = policy.get_option(key, default)
    return str(option_value).strip() or default


def _as_epoch(raw: object) -> float:
    """Parse one epoch field, returning 0 when missing/invalid."""
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


class DevflowRunGates(PolicyCheck):
    """Validate that all work is bound to one recorded gate session."""

    @property
    def policy_id(self) -> str:
        """Return the policy identifier."""

        return "devflow-run-gates"

    def check(self, ctx: CheckContext) -> List[Violation]:
        """Enforce start->test->end sequencing from gate-status ledger."""
        violations: List[Violation] = []
        status_rel = _resolve_status_path(self)
        status_path = ctx.repo_root / status_rel
        phase = os.environ.get("DEVCOV_DEVFLOW_PHASE", "").strip().lower()
        in_pre_commit = bool(str(os.environ.get("PRE_COMMIT", "")).strip())

        if in_pre_commit and not phase:
            return violations
        if phase == "start":
            return violations

        configured_mode = _tests_output_mode(self, ctx)
        required_commands, source_key = _required_commands_for_mode(
            self,
            configured_mode,
        )
        if not required_commands:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "No required test commands are configured for "
                        "devflow-run-gates. Set "
                        f"`{source_key}` (or fallback `required_commands`) "
                        "via active profile overlays."
                    ),
                )
            ]

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
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Gate status is missing. Run "
                        "`devcovenant gate --start`, then `devcovenant test`, "
                        "then `devcovenant gate --end`."
                    ),
                )
            ]

        status_mode = _status_tests_output_mode(status)
        if status_mode and status_mode != configured_mode:
            required_commands, source_key = _required_commands_for_mode(
                self,
                status_mode,
            )
            if not required_commands:
                return [
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "No required test commands are configured for "
                            "devflow-run-gates. Set "
                            f"`{source_key}` (or fallback "
                            "`required_commands`) via active profile "
                            "overlays."
                        ),
                    )
                ]

        session_id = str(status.get("session_id", "")).strip()
        session_state = str(status.get("session_state", "")).strip().lower()
        session_error = str(ctx.change_state.session_error or "").strip()
        has_unsessioned_edits = (
            not ctx.change_state.session_valid
            and "Detected edits after the previous `devcovenant gate --end`"
            in session_error
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
        last_ts = _as_epoch(status.get("last_run_epoch"))
        last_run = str(status.get("last_run_utc") or "").strip()

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

        commands_raw = status.get("commands")
        if not isinstance(commands_raw, list):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message="Gate status field `commands` must be a list.",
                )
            )
            return violations
        commands_lower = " ".join(str(entry) for entry in commands_raw).lower()
        missing_commands = [
            command
            for command in required_commands
            if command not in commands_lower
        ]
        if missing_commands:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Latest recorded gate status is missing required "
                        f"commands: {', '.join(missing_commands)}. Run "
                        "`devcovenant test`."
                    ),
                )
            )

        if last_ts <= 0.0:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "No recorded test run for the active session. "
                        "Run `devcovenant test`."
                    ),
                )
            )
        elif start_ts > 0.0 and last_ts < start_ts:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Recorded tests predate session start "
                        f"({last_run or 'unknown'}). Run `devcovenant test` "
                        "after `devcovenant gate --start`."
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
            elif last_ts > 0.0 and end_ts < last_ts:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session end pre-commit run predates the latest "
                            "recorded tests. Re-run `devcovenant gate --end` "
                            "after tests."
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
