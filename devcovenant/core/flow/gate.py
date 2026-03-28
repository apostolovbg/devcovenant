"""Gate execution helpers for DevCovenant gate lifecycle and status flows."""

from __future__ import annotations

import datetime as _dt
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Mapping

import devcovenant.core.flow.workflow_contract as workflow_contract_module
import devcovenant.core.runtime.execution as execution_runtime_module
import devcovenant.core.runtime.registry as registry_runtime_module
from devcovenant.core.flow.gate_changelog_helpers import (
    _entry_fingerprint,
    _latest_changelog_entry,
    _resolve_doc_exemption_options,
)
from devcovenant.core.flow.gate_status_helpers import (
    _gate_status_summary_lines,
    _load_status,
)
from devcovenant.core.flow.gate_status_helpers import (
    _resolve_latest_relevant_run_pointer as _resolve_latest_pointer_impl,
)
from devcovenant.core.runtime import (
    workflow_session as workflow_session_runtime_module,
)

runtime_print = execution_runtime_module.runtime_print
normalize_snapshot_rows = execution_runtime_module.normalize_snapshot_rows
load_session_snapshot_payload = (
    execution_runtime_module.load_session_snapshot_payload
)
merge_session_snapshot_payload = (
    execution_runtime_module.merge_session_snapshot_payload
)
prune_inline_session_snapshot_fields = (
    execution_runtime_module.prune_inline_session_snapshot_fields
)
_CHECK_APPLY_FIXES_ENV = "DEVCOV_CHECK_APPLY_FIXES"
_CHECK_RUN_REFRESH_ENV = "DEVCOV_CHECK_RUN_REFRESH"
_CHECK_CLEAN_BYTECODE_ENV = "DEVCOV_CHECK_CLEAN_BYTECODE"
_PRE_COMMIT_EXECUTABLE_TOKENS = frozenset(
    {"pre-commit", "pre-commit.exe", "pre_commit", "pre_commit.exe"}
)


def _utc_now() -> _dt.datetime:
    """Return the current UTC time."""
    return _dt.datetime.now(tz=_dt.timezone.utc)


def show_gate_status(repo_root: Path) -> int:
    """Print a short, read-only gate status summary."""
    for line in _gate_status_summary_lines(repo_root):
        runtime_print(line)
    return 0


def _resolve_latest_relevant_run_pointer(
    repo_root: Path,
) -> dict[str, str] | None:
    """Compatibility wrapper for gate-status latest-run pointer lookup."""
    return _resolve_latest_pointer_impl(repo_root)


def _is_pre_commit_run_command(tokens: list[str]) -> bool:
    """Return True when tokens describe a `pre-commit run` invocation."""
    if not tokens or "run" not in tokens:
        return False
    first = Path(tokens[0]).name.lower()
    if first in _PRE_COMMIT_EXECUTABLE_TOKENS:
        return True
    for index, token in enumerate(tokens[:-1]):
        if token == "-m" and tokens[index + 1] == "pre_commit":
            return True
    return False


def _resolve_hook_command(repo_root: Path, command: str) -> str:
    """Resolve the effective pre-commit command for gate hook execution."""
    tokens = shlex.split(command)
    if not tokens:
        raise SystemExit("Pre-commit command is empty.")
    if "--all-files" not in tokens:
        return command
    if "--files" in tokens:
        return command
    if not _is_pre_commit_run_command(tokens):
        return command
    snapshot_paths = execution_runtime_module.capture_current_snapshot_paths(
        repo_root
    )
    if not snapshot_paths:
        return command
    resolved: list[str] = []
    replaced = False
    for token in tokens:
        if token == "--all-files" and not replaced:
            resolved.append("--files")
            resolved.extend(snapshot_paths)
            replaced = True
            continue
        if token == "--all-files":
            continue
        resolved.append(token)
    if not replaced:
        return command
    return shlex.join(resolved)


_TEST_IRRELEVANT_FILES = {"changelog.md"}
_DEVCOV_POLICY_HOOK_TOKEN = "enforce repository policies (DevCovenant)"
_DEVCOV_BLOCKING_MARKERS = (
    "Status: 🚫 BLOCKED",
    "Status: BLOCKED",
    "critical violations must be fixed",
    "violations >= error threshold",
)
_SUPPRESSED_FAILURE_TAIL_MAX_LINES = 40
_SUPPRESSED_FAILURE_TAIL_MAX_CHARS = 6000


def _emit_suppressed_failure_tail(command_output: str) -> None:
    """Emit a bounded tail when normal mode suppresses gate child output."""
    output = str(command_output or "").strip()
    if not output:
        return
    lines = output.splitlines()
    tail_lines = lines[-_SUPPRESSED_FAILURE_TAIL_MAX_LINES:]
    tail_text = "\n".join(tail_lines)
    if len(tail_text) > _SUPPRESSED_FAILURE_TAIL_MAX_CHARS:
        tail_text = tail_text[-_SUPPRESSED_FAILURE_TAIL_MAX_CHARS:]
    runtime_print(
        "Pre-commit output tail " "(normal mode child output suppressed):",
        file=sys.stderr,
    )
    for line in tail_text.splitlines():
        runtime_print(line, file=sys.stderr)


def _restore_status_file(path: Path, previous_bytes: bytes | None) -> None:
    """Restore gate status file from prior bytes, or remove when absent."""
    if previous_bytes is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(previous_bytes)


def _run_command(
    command: str,
    env: dict[str, str] | None = None,
    *,
    strict: bool = True,
) -> int:
    """Execute a shell command string and optionally fail on non-zero exit."""
    exit_code, _ = _run_command_with_output(command, env=env)
    if strict and exit_code != 0:
        parts = shlex.split(command)
        rendered = " ".join(parts) if parts else command
        runtime_print(
            f"Pre-commit command failed with exit code {exit_code}:"
            f" {rendered}",
            file=sys.stderr,
        )
        raise SystemExit(exit_code)
    return exit_code


def _run_command_with_output(
    command: str,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Execute a shell command string and return exit code with output."""
    parts = shlex.split(command)
    if not parts:
        raise SystemExit("Pre-commit command is empty.")
    result, combined_output = (
        execution_runtime_module.run_child_command_with_output_policy(
            parts,
            channel="gate_child",
            env=env,
            capture_combined_output=True,
        )
    )
    exit_code = int(result.returncode)
    output_plan = (
        execution_runtime_module.resolve_child_output_plan_for_channel(
            "gate_child"
        )
    )
    if exit_code != 0 and output_plan.child_output_suppressed:
        _emit_suppressed_failure_tail(combined_output)
    return exit_code, combined_output


def _is_blocking_devcov_failure(
    exit_code: int,
    command_output: str,
) -> bool:
    """Return whether command output reflects blocking DevCovenant failures."""
    if exit_code == 0:
        return False
    output = command_output.strip()
    if not output:
        return False
    if _DEVCOV_POLICY_HOOK_TOKEN not in output:
        return False
    return any(marker in output for marker in _DEVCOV_BLOCKING_MARKERS)


def _is_test_relevant_path(path: str) -> bool:
    """Return True when a changed path should trigger test reruns."""
    leaf = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return leaf not in _TEST_IRRELEVANT_FILES


def _format_run_rerun_instructions(
    run_ids: list[str],
    *,
    required_run_ids: list[str] | None = None,
) -> str:
    """Render the canonical rerun instruction."""
    del run_ids, required_run_ids
    return "`devcovenant run`"


def _stale_required_run_ids(
    repo_root: Path,
    contract: Mapping[str, object],
    workflow_payload: Mapping[str, object],
    current_snapshot: Mapping[str, str],
    *,
    session_id: str,
) -> list[str]:
    """Return required runs whose latest evidence is missing or stale."""
    runs_raw = workflow_payload.get("runs")
    run_map = dict(runs_raw) if isinstance(runs_raw, dict) else {}
    stale: list[str] = []
    for run_id in workflow_contract_module.required_run_ids(contract):
        run = workflow_contract_module.resolve_run(contract, run_id)
        if run is None:
            stale.append(run_id)
            continue
        entry = run_map.get(run_id)
        if not isinstance(entry, dict):
            stale.append(run_id)
            continue
        if session_id:
            last_run_session_id = str(
                entry.get("last_run_session_id", "")
            ).strip()
            if last_run_session_id != session_id:
                stale.append(run_id)
                continue
        try:
            run_snapshot = (
                workflow_session_runtime_module.resolve_run_snapshot(
                    repo_root,
                    workflow_payload,
                    run_id,
                )
            )
        except ValueError:
            stale.append(run_id)
            continue
        if not run_snapshot:
            stale.append(run_id)
            continue
        changed_paths = _changed_paths_between(run_snapshot, current_snapshot)
        if workflow_contract_module.run_relevant_paths_changed(
            run,
            sorted(changed_paths),
        ):
            stale.append(run_id)
    return stale


def _record_workflow_anchor(
    repo_root: Path,
    *,
    contract: Mapping[str, object],
    stage: str,
    command: str,
    notes: str,
    when: _dt.datetime,
    session_id: str,
    session_state: str,
    reset_runs: bool = False,
    session_snapshot_file: str = "",
    session_snapshot_updated_utc: str = "",
    session_snapshot_updated_epoch: float = 0.0,
) -> None:
    """Persist workflow-session anchor state for one gate stage."""
    try:
        workflow_payload = (
            workflow_session_runtime_module.load_workflow_session(repo_root)
        )
    except ValueError:
        workflow_payload = {
            "schema_version": workflow_session_runtime_module.SCHEMA_VERSION,
            "session_id": "",
            "session_state": "",
            "anchors": {},
            "runs": {},
            "required_run_ids": [],
        }
    anchors_raw = workflow_payload.get("anchors")
    anchors = dict(anchors_raw) if isinstance(anchors_raw, dict) else {}
    anchor_entry = dict(anchors.get(stage) or {})
    anchor_entry.update(
        {
            "id": stage,
            "status": "passed",
            "last_run_utc": when.isoformat(),
            "last_run_epoch": when.timestamp(),
            "commands": [command.strip()] if command.strip() else [],
            "command_name": f"gate --{stage}",
            "notes": notes.strip(),
        }
    )
    anchor_entry.pop("last_run", None)
    anchor_entry.pop("command", None)
    anchors[stage] = anchor_entry
    workflow_payload["schema_version"] = (
        workflow_session_runtime_module.SCHEMA_VERSION
    )
    workflow_payload["workflow_contract_schema_version"] = contract.get(
        "schema_version",
        workflow_contract_module.SCHEMA_VERSION,
    )
    workflow_payload["required_run_ids"] = (
        workflow_contract_module.required_run_ids(contract)
    )
    workflow_payload["session_id"] = session_id
    workflow_payload["session_state"] = session_state
    workflow_payload["anchors"] = anchors
    if reset_runs:
        workflow_payload["runs"] = {}
    if session_snapshot_file:
        workflow_payload["session_snapshot_file"] = session_snapshot_file
    if session_snapshot_updated_utc:
        workflow_payload["session_snapshot_updated_utc"] = (
            session_snapshot_updated_utc
        )
    if session_snapshot_updated_epoch > 0.0:
        workflow_payload["session_snapshot_updated_epoch"] = (
            session_snapshot_updated_epoch
        )
    workflow_session_runtime_module.write_workflow_session(
        repo_root,
        workflow_payload,
    )


def _current_numstat_snapshot(repo_root: Path) -> dict[str, str]:
    """Return deterministic filesystem-hash snapshot rows keyed by path."""
    return execution_runtime_module.capture_current_numstat_snapshot(repo_root)


def _changed_paths_between(
    before: dict[str, str], after: dict[str, str]
) -> set[str]:
    """Return changed paths across two snapshots, including deletions."""
    return execution_runtime_module.diff_snapshot_paths(before, after)


def run_pre_commit_gate(
    repo_root: Path,
    stage: str,
    *,
    command: str = "python3 -m pre_commit run --all-files",
    notes: str = "",
) -> int:
    """Run one gate pre-commit stage (`start`, `mid`, or `end`)."""
    if stage not in {"start", "mid", "end"}:
        raise SystemExit("stage must be 'start', 'mid', or 'end'.")
    is_start = stage == "start"
    is_mid = stage == "mid"
    is_end = stage == "end"

    status_path = registry_runtime_module.gate_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    if is_end or is_mid:
        try:
            pre_payload = _load_status(status_path)
        except ValueError as error:
            runtime_print(str(error), file=sys.stderr)
            return 1
        session_id = str(pre_payload.get("session_id", "")).strip()
        session_state = (
            str(pre_payload.get("session_state", "")).strip().lower()
        )
        if not session_id or session_state != "open":
            runtime_print(
                f"Cannot run {stage} gate without an active open session. "
                "Run `devcovenant gate --start` first.",
                file=sys.stderr,
            )
            return 1

    start_ts = _utc_now() if is_start else None
    required_run_ids_pending: list[str] = []
    recovery_required_run_ids: list[str] = []
    recovery_status_active = False
    recovery_status_previous: bytes | None = None
    managed_env_stage = "command" if is_mid else stage
    try:
        managed_env, managed_python = (
            execution_runtime_module.resolve_managed_environment_for_stage(
                repo_root,
                managed_env_stage,
            )
        )
    except ValueError as error:
        runtime_print(str(error), file=sys.stderr)
        return 1
    effective_command = (
        execution_runtime_module.rewrite_command_string_for_managed_python(
            command,
            managed_python,
        )
    )
    try:
        workflow_contract = workflow_contract_module.load_workflow_contract(
            repo_root
        )
    except ValueError as error:
        runtime_print(str(error), file=sys.stderr)
        return 1

    while True:
        env = dict(managed_env or os.environ)
        env["DEVCOV_DEVFLOW_STAGE"] = "" if is_mid else stage
        hook_env = dict(env)
        auto_fix_enabled = (
            execution_runtime_module.resolve_engine_auto_fix_enabled(repo_root)
        )
        # Gate owns refresh/autofix/lifecycle orchestration; the local
        # pre-commit `devcovenant check` hook reads these to enable mutating
        # behavior while public `check` stays read-only by default.
        hook_env[_CHECK_APPLY_FIXES_ENV] = "1" if auto_fix_enabled else "0"
        hook_env[_CHECK_RUN_REFRESH_ENV] = "1"
        hook_env[_CHECK_CLEAN_BYTECODE_ENV] = "1"
        hook_command = _resolve_hook_command(repo_root, effective_command)
        try:
            diff_before = _current_numstat_snapshot(repo_root)
        except ValueError as error:
            runtime_print(str(error), file=sys.stderr)
            return 1
        if is_end:
            session_id = str(pre_payload.get("session_id", "")).strip()
            try:
                workflow_payload = (
                    workflow_session_runtime_module.load_workflow_session(
                        repo_root
                    )
                )
            except ValueError as error:
                runtime_print(str(error), file=sys.stderr)
                return 1
            required_run_ids_pending = _stale_required_run_ids(
                repo_root,
                workflow_contract,
                workflow_payload,
                diff_before,
                session_id=session_id,
            )
        if is_start:
            status_exists = status_path.exists()
            status_payload: dict[str, object] = {}
            status_parse_error = ""
            status_snapshot_payload: dict[str, object] = {}
            status_snapshot_error = ""
            workflow_payload: dict[str, object] = {}
            workflow_status_error = ""
            if status_exists:
                try:
                    recovery_status_previous = status_path.read_bytes()
                except OSError as error:
                    runtime_print(str(error), file=sys.stderr)
                    return 1
                try:
                    status_payload = _load_status(status_path)
                except ValueError as error:
                    status_parse_error = str(error)
                else:
                    try:
                        status_snapshot_payload = (
                            load_session_snapshot_payload(
                                repo_root,
                                status_payload,
                            )
                        )
                    except ValueError as error:
                        status_snapshot_error = str(error)
            try:
                workflow_payload = (
                    workflow_session_runtime_module.load_workflow_session(
                        repo_root
                    )
                )
            except ValueError as error:
                workflow_status_error = str(error)

            session_state = (
                str(status_payload.get("session_state", "")).strip().lower()
            )
            recovery_reason = ""
            recovery_baseline_snapshot: dict[str, str] | None = None
            if status_parse_error:
                recovery_reason = (
                    "Gate status is malformed; opening a recovery session "
                    "from the current baseline."
                )
            elif session_state == "open":
                runtime_print(
                    "Cannot start a new session while another session is "
                    "open. Complete it with `devcovenant gate --end`.",
                    file=sys.stderr,
                )
                return 1
            elif session_state and session_state != "closed":
                recovery_reason = (
                    "Gate status has an invalid `session_state`; opening "
                    "a recovery session from the current baseline."
                )
            elif session_state == "closed":
                if status_snapshot_error:
                    recovery_reason = (
                        "Closed gate session snapshot is unusable; opening "
                        "a recovery session from the current baseline."
                    )
                raw_end_snapshot = status_snapshot_payload.get(
                    "session_end_snapshot"
                )
                if not isinstance(raw_end_snapshot, dict):
                    recovery_reason = (
                        "Closed gate status is missing "
                        "`session_end_snapshot`; "
                        "opening a recovery session from the current "
                        "baseline."
                    )
                else:
                    try:
                        end_snapshot = (
                            execution_runtime_module.normalize_snapshot_rows(
                                raw_end_snapshot,
                                field_name="session_end_snapshot",
                            )
                        )
                    except ValueError as error:
                        runtime_print(str(error), file=sys.stderr)
                        return 1
                    changed_since_end = _changed_paths_between(
                        end_snapshot,
                        diff_before,
                    )
                    if changed_since_end:
                        recovery_baseline_snapshot = dict(end_snapshot)
                        recovery_reason = (
                            "Detected edits after the previous "
                            "`devcovenant gate --end`; opening a recovery "
                            "session that includes those unsessioned edits."
                        )
                        recovery_session_id = str(
                            status_payload.get("session_id", "")
                        ).strip()
                        if workflow_status_error:
                            recovery_required_run_ids = list(
                                workflow_contract_module.required_run_ids(
                                    workflow_contract
                                )
                            )
                        else:
                            recovery_required_run_ids = (
                                _stale_required_run_ids(
                                    repo_root,
                                    workflow_contract,
                                    workflow_payload,
                                    diff_before,
                                    session_id=recovery_session_id,
                                )
                            )
            elif status_exists:
                recovery_reason = (
                    "Gate status is missing session metadata; opening a "
                    "recovery session from the current baseline."
                )

            if recovery_reason:
                recovery_payload: dict[str, object] = (
                    dict(status_payload) if status_payload else {}
                )
                try:
                    top_entry = _latest_changelog_entry(repo_root)
                except ValueError as error:
                    runtime_print(str(error), file=sys.stderr)
                    return 1
                recovery_payload["session_id"] = str(
                    int(start_ts.timestamp() * 1000000)
                )
                recovery_payload["session_state"] = "open"
                recovery_payload["session_start_utc"] = start_ts.isoformat()
                recovery_payload["session_start_epoch"] = start_ts.timestamp()
                recovery_payload["changelog_start_top_entry_fingerprint"] = (
                    _entry_fingerprint(top_entry)
                )
                recovery_payload["changelog_start_top_entry_present"] = bool(
                    top_entry
                )
                recovery_remove_keys = [
                    "session_end_snapshot",
                    "last_run_snapshot",
                    "run_events",
                    "test_events",
                ]
                recovery_updates: dict[str, object] = {}
                if recovery_baseline_snapshot is not None:
                    recovery_updates["session_baseline_snapshot"] = dict(
                        recovery_baseline_snapshot
                    )
                else:
                    recovery_remove_keys.append("session_baseline_snapshot")
                (
                    snapshot_rel_path,
                    _recovery_snapshot_payload,
                ) = merge_session_snapshot_payload(
                    repo_root,
                    recovery_payload,
                    updates=recovery_updates,
                    remove_keys=tuple(recovery_remove_keys),
                )
                recovery_payload["session_snapshot_file"] = snapshot_rel_path
                recovery_payload["session_snapshot_updated_utc"] = (
                    start_ts.isoformat()
                )
                recovery_payload["session_snapshot_updated_epoch"] = (
                    start_ts.timestamp()
                )
                recovery_payload.pop("run_events_count", None)
                recovery_payload.pop("test_events_count", None)
                prune_inline_session_snapshot_fields(recovery_payload)
                recovery_payload["recovery_start_reason"] = recovery_reason
                status_path.parent.mkdir(parents=True, exist_ok=True)
                status_path.write_text(
                    json.dumps(recovery_payload, indent=2) + "\n",
                    encoding="utf-8",
                )
                recovery_status_active = True
            elif status_exists:
                recovery_status_active = False
                recovery_status_previous = None

        command_output = ""
        if is_end or is_mid:
            exit_code, command_output = _run_command_with_output(
                hook_command,
                env=hook_env,
            )
        else:
            exit_code = _run_command(
                hook_command,
                env=hook_env,
                strict=False,
            )
        if is_start and exit_code != 0:
            if recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            runtime_print(
                "Start gate failed. Clear pre-commit violations and rerun "
                "`devcovenant gate --start`.",
                file=sys.stderr,
            )
            return exit_code
        try:
            diff_after_hooks = _current_numstat_snapshot(repo_root)
        except ValueError as error:
            if stage == "start" and recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            runtime_print(str(error), file=sys.stderr)
            return 1
        if is_start and diff_before != diff_after_hooks:
            if recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            runtime_print(
                "Start gate must not mutate the baseline snapshot. "
                "Clear hook-induced edits and rerun "
                "`devcovenant gate --start`.",
                file=sys.stderr,
            )
            return 1

        if (
            stage == "start"
            and recovery_status_active
            and recovery_required_run_ids
        ):
            _restore_status_file(status_path, recovery_status_previous)
            recovery_status_active = False
            recovery_rerun = _format_run_rerun_instructions(
                recovery_required_run_ids,
                required_run_ids=workflow_contract_module.required_run_ids(
                    workflow_contract
                ),
            )
            runtime_print(
                "Recovery start detected unsessioned edits and requires "
                "fresh required workflow runs before recording a new "
                "baseline.",
                file=sys.stderr,
            )
            runtime_print(
                "Run "
                f"{recovery_rerun},"
                " "
                "then rerun `devcovenant gate --start`. Start gate performs "
                "no internal workflow-run runs.",
                file=sys.stderr,
            )
            return 1

        if is_end and _is_blocking_devcov_failure(
            exit_code,
            command_output,
        ):
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            runtime_print(
                "End gate found blocking non-autofixed DevCovenant "
                "violations. Fix violations and rerun "
                "`devcovenant gate --end`.",
                file=sys.stderr,
            )
            return exit_code
        if is_mid and _is_blocking_devcov_failure(
            exit_code,
            command_output,
        ):
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            runtime_print(
                "Mid gate found blocking non-autofixed DevCovenant "
                "violations. Fix violations and rerun `devcovenant gate "
                "--mid` before `devcovenant run`.",
                file=sys.stderr,
            )
            return exit_code

        hook_changed_paths = _changed_paths_between(
            diff_before, diff_after_hooks
        )
        hooks_changed = bool(hook_changed_paths)
        if is_mid and exit_code == 0 and hooks_changed:
            runtime_print(
                "Mid gate detected hook-induced file changes. "
                "Rerun `devcovenant gate --mid` until hooks converge, then "
                "run `devcovenant run`.",
                file=sys.stderr,
            )
            return 1
        if is_mid and exit_code != 0:
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            runtime_print(
                "Mid gate failed. Clear pre-commit violations and rerun "
                "`devcovenant gate --mid` before `devcovenant run`.",
                file=sys.stderr,
            )
            return exit_code
        if is_end and exit_code == 0 and hooks_changed:
            runtime_print(
                "End gate detected hook-induced file changes. "
                "Run `devcovenant run`, then rerun "
                "`devcovenant gate --end`.",
                file=sys.stderr,
            )
            return 1
        if is_end and exit_code == 0 and required_run_ids_pending:
            rerun_required_runs = _format_run_rerun_instructions(
                required_run_ids_pending,
                required_run_ids=workflow_contract_module.required_run_ids(
                    workflow_contract
                ),
            )
            runtime_print(
                "End gate requires fresh required workflow runs before "
                "closure. Run "
                f"{rerun_required_runs},"
                " "
                "then rerun `devcovenant gate --end`.",
                file=sys.stderr,
            )
            return 1
        if is_end and exit_code != 0:
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            return exit_code
        break

    if is_mid:
        _record_workflow_anchor(
            repo_root,
            contract=workflow_contract,
            stage="mid",
            command=command,
            notes=notes,
            when=_utc_now(),
            session_id=session_id,
            session_state="open",
        )
        runtime_print(
            "Completed mid gate pre-commit sweep without changing gate "
            "session lifecycle state."
        )
        return 0

    try:
        payload = _load_status(status_path)
    except ValueError as error:
        runtime_print(str(error), file=sys.stderr)
        return 1
    now = _utc_now()
    prefix = f"pre_commit_{stage}"
    if start_ts is not None:
        payload[f"{prefix}_utc"] = start_ts.isoformat()
        payload[f"{prefix}_epoch"] = start_ts.timestamp()
    else:
        payload[f"{prefix}_utc"] = now.isoformat()
        payload[f"{prefix}_epoch"] = now.timestamp()
    payload[f"{prefix}_command"] = command.strip()
    payload[f"{prefix}_notes"] = notes.strip()
    payload.pop(f"{prefix}_cache_enabled", None)
    payload.pop(f"{prefix}_cache_control_env", None)
    if is_start:
        # Purge legacy keys so old payload shape cannot silently persist.
        payload.pop("sha", None)
        payload.pop("tests_coverage_evidence", None)
        payload.pop("changelog_start_diff_numstat", None)
        payload.pop("changelog_start_exemption_fingerprints", None)
        payload.pop("session_start_signature", None)
        # Clear stale end-stage evidence so ordering checks stay session-bound.
        for key in (
            "pre_commit_end_utc",
            "pre_commit_end_epoch",
            "pre_commit_end_command",
            "pre_commit_end_notes",
            "pre_commit_end_cache_enabled",
            "pre_commit_end_cache_control_env",
        ):
            payload.pop(key, None)
        session_id = str(int(start_ts.timestamp() * 1000000))
        payload["session_id"] = session_id
        payload["session_state"] = "open"
        payload["session_start_utc"] = start_ts.isoformat()
        payload["session_start_epoch"] = start_ts.timestamp()
        payload.pop("session_baseline_epoch", None)
        try:
            header_doc_suffixes, header_keys, header_scan_lines = (
                _resolve_doc_exemption_options(repo_root)
            )
        except ValueError as error:
            if recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            runtime_print(str(error), file=sys.stderr)
            return 1
        snapshot_remove_keys = [
            "session_end_snapshot",
            "last_run_snapshot",
            "run_events",
            "test_events",
        ]
        snapshot_updates: dict[str, object] = {
            # Persist the gate-start filesystem snapshot so policies can scope
            # deleted-file coverage to this session instead of HEAD-wide
            # history.
            "session_start_snapshot": dict(diff_before),
            "document_exemption_baseline": (
                execution_runtime_module.capture_document_exemption_baseline(
                    repo_root,
                    header_doc_suffixes=header_doc_suffixes,
                    header_keys=header_keys,
                    header_scan_lines=header_scan_lines,
                )
            ),
        }
        if recovery_status_active and recovery_baseline_snapshot is not None:
            snapshot_updates["session_baseline_snapshot"] = dict(
                recovery_baseline_snapshot
            )
        else:
            # Normal starts must not carry a stale recovery baseline forward.
            snapshot_remove_keys.append("session_baseline_snapshot")
        (
            snapshot_rel_path,
            _snapshot_payload,
        ) = merge_session_snapshot_payload(
            repo_root,
            payload,
            updates=snapshot_updates,
            remove_keys=tuple(snapshot_remove_keys),
        )
        payload["session_snapshot_file"] = snapshot_rel_path
        payload["session_snapshot_updated_utc"] = start_ts.isoformat()
        payload["session_snapshot_updated_epoch"] = start_ts.timestamp()
        payload.pop("run_events_count", None)
        payload.pop("test_events_count", None)
        payload.update(
            execution_runtime_module.capture_agents_section_hashes(repo_root)
        )
        payload.pop("session_end_utc", None)
        payload.pop("session_end_epoch", None)
        payload.pop("session_end_signature", None)
        payload.pop("recovery_start_reason", None)
        try:
            top_entry = _latest_changelog_entry(repo_root)
        except ValueError as error:
            if recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            runtime_print(str(error), file=sys.stderr)
            return 1
        payload["changelog_start_top_entry_fingerprint"] = _entry_fingerprint(
            top_entry
        )
        payload["changelog_start_top_entry_present"] = bool(top_entry)
    else:
        session_id = str(payload.get("session_id", "")).strip()
        session_state = str(payload.get("session_state", "")).strip().lower()
        if not session_id or session_state != "open":
            runtime_print(
                "Cannot end gate without an active open session. "
                "Run `devcovenant gate --start` first.",
                file=sys.stderr,
            )
            return 1
        payload["session_state"] = "closed"
        payload["session_end_utc"] = now.isoformat()
        payload["session_end_epoch"] = now.timestamp()
        (
            snapshot_rel_path,
            _snapshot_payload,
        ) = merge_session_snapshot_payload(
            repo_root,
            payload,
            updates={"session_end_snapshot": dict(diff_after_hooks)},
        )
        payload["session_snapshot_file"] = snapshot_rel_path
        payload["session_snapshot_updated_utc"] = now.isoformat()
        payload["session_snapshot_updated_epoch"] = now.timestamp()
    prune_inline_session_snapshot_fields(payload)
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime_print(
        f"Recorded {prefix} at {payload[f'{prefix}_utc']} "
        f"for command `{payload[f'{prefix}_command']}`."
    )
    _record_workflow_anchor(
        repo_root,
        contract=workflow_contract,
        stage=stage,
        command=command,
        notes=notes,
        when=start_ts if start_ts is not None else now,
        session_id=str(payload.get("session_id", "")).strip(),
        session_state=str(payload.get("session_state", "")).strip().lower(),
        reset_runs=is_start,
        session_snapshot_file=str(payload.get("session_snapshot_file", "")),
        session_snapshot_updated_utc=str(
            payload.get("session_snapshot_updated_utc", "")
        ),
        session_snapshot_updated_epoch=float(
            payload.get("session_snapshot_updated_epoch") or 0.0
        ),
    )
    return 0
