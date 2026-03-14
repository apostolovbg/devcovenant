"""Gate execution helpers for DevCovenant gate --start/--end."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import yaml

from devcovenant.core import execution_runtime as execution_runtime_module
from devcovenant.core import registry_runtime as registry_runtime_module

runtime_print = execution_runtime_module.runtime_print


def _utc_now() -> _dt.datetime:
    """Return the current UTC time."""
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _load_status(path: Path) -> dict:
    """Load the current status payload."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid gate status JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Gate status payload must be a mapping: {path}")
    return payload


_DATE_ENTRY_PATTERN = re.compile(r"^\s*-\s*\d{4}-\d{2}-\d{2}\b")
_MANAGED_BEGIN = "<!-- DEVCOV:BEGIN -->"
_MANAGED_END = "<!-- DEVCOV:END -->"
_LOG_MARKER = "## Log changes here"
_TEST_IRRELEVANT_FILES = {"changelog.md"}
_DEVCOV_POLICY_HOOK_TOKEN = "enforce repository policies (DevCovenant)"
_DEVCOV_BLOCKING_MARKERS = (
    "Status: 🚫 BLOCKED",
    "Status: BLOCKED",
    "critical violations must be fixed",
    "violations >= error threshold",
)


def _visible_changelog_lines(changelog_text: str) -> list[str]:
    """Return changelog lines outside managed blocks and fenced examples."""
    start = changelog_text.find(_LOG_MARKER)
    content = changelog_text[start:] if start >= 0 else changelog_text
    visible: list[str] = []
    in_managed = False
    in_fence = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == _MANAGED_BEGIN:
            in_managed = True
            continue
        if stripped == _MANAGED_END:
            in_managed = False
            continue
        if in_managed:
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        visible.append(line)
    return visible


def _latest_changelog_entry(repo_root: Path) -> str:
    """Return the topmost changelog entry from the latest version section."""
    changelog_path = repo_root / _resolve_main_changelog(repo_root)
    if not changelog_path.exists():
        return ""
    lines = _visible_changelog_lines(
        changelog_path.read_text(encoding="utf-8")
    )

    version_start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith("## Version"):
            version_start = index
            break
    if version_start is None:
        return ""

    entry_start: int | None = None
    for index in range(version_start + 1, len(lines)):
        if _DATE_ENTRY_PATTERN.match(lines[index]):
            entry_start = index
            break
    if entry_start is None:
        return ""

    entry_end = len(lines)
    for index in range(entry_start + 1, len(lines)):
        if _DATE_ENTRY_PATTERN.match(lines[index]):
            entry_end = index
            break

    return "\n".join(lines[entry_start:entry_end]).strip()


def _resolve_main_changelog(repo_root: Path) -> Path:
    """Resolve main changelog path from changelog-coverage metadata."""
    metadata = _load_changelog_metadata(repo_root)
    raw_target = metadata.get("main_changelog", "")
    if isinstance(raw_target, list):
        target = ""
        for entry in raw_target:
            token = str(entry).strip()
            if token:
                target = token
                break
    else:
        target = str(raw_target).strip()
    if not target:
        raise ValueError(
            (
                "`changelog-coverage.main_changelog` is missing in "
                "policy metadata."
            )
        )
    return Path(target)


def _load_changelog_metadata(repo_root: Path) -> dict[str, object]:
    """Return changelog-coverage metadata mapping from policy registry."""
    registry_path = registry_runtime_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        raise ValueError(
            f"Missing policy registry file: {registry_path}. "
            "Run `devcovenant refresh`."
        )
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in policy registry {registry_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Unable to read policy registry {registry_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Invalid policy registry payload in {registry_path}: "
            "expected a mapping."
        )
    policies = payload.get("policies", {})
    if not isinstance(policies, dict):
        raise ValueError(
            f"Invalid policy registry payload in {registry_path}: "
            "`policies` must be a mapping."
        )
    changelog_coverage = policies.get("changelog-coverage", {})
    if not isinstance(changelog_coverage, dict):
        raise ValueError(
            "Missing `changelog-coverage` policy entry in policy registry."
        )
    metadata = changelog_coverage.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(
            "Invalid `changelog-coverage.metadata` payload in policy registry."
        )
    return metadata


def _normalize_list_option(
    value: object,
    default: list[str],
) -> list[str]:
    """Normalize metadata value into non-empty string list."""
    if value is None:
        source: list[str] = default
    elif isinstance(value, str):
        source = [entry.strip() for entry in value.split(",") if entry.strip()]
    elif isinstance(value, list):
        source = [str(entry).strip() for entry in value if str(entry).strip()]
    else:
        source = [str(value).strip()]
    normalized = [entry for entry in source if entry]
    return normalized or default


def _resolve_doc_exemption_options(
    repo_root: Path,
) -> tuple[list[str], list[str], int]:
    """Resolve doc allowlist metadata from changelog-coverage descriptor."""
    metadata = _load_changelog_metadata(repo_root)
    suffixes = _normalize_list_option(
        metadata.get("header_doc_suffixes"),
        [".md", ".rst", ".txt"],
    )
    header_keys = _normalize_list_option(
        metadata.get("header_keys"),
        ["Last Updated", "Version"],
    )
    raw_scan = metadata.get("header_scan_lines", 4)
    try:
        scan_lines = int(raw_scan)
    except (TypeError, ValueError):
        scan_lines = 4
    if scan_lines < 0:
        scan_lines = 0
    return suffixes, header_keys, scan_lines


def _entry_fingerprint(entry_text: str) -> str:
    """Return a deterministic hash for an entry block."""
    if not entry_text.strip():
        return ""
    normalized = "\n".join(
        line.rstrip() for line in entry_text.strip().splitlines()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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
    parts = shlex.split(command)
    if not parts:
        raise SystemExit("Pre-commit command is empty.")
    result = subprocess.run(parts, check=False, env=env)
    exit_code = int(result.returncode)
    if strict and exit_code != 0:
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
    result = subprocess.run(
        parts,
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    stdout_text = result.stdout or ""
    stderr_text = result.stderr or ""
    if stdout_text:
        runtime_print(stdout_text, end="")
    if stderr_text:
        runtime_print(stderr_text, end="", file=sys.stderr)
    return int(result.returncode), f"{stdout_text}\n{stderr_text}"


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


def _run_tests(repo_root: Path, env: dict[str, str]) -> None:
    """Run repository tests through the canonical test command."""
    test_env = dict(env)
    test_env.pop("DEVCOV_DEVFLOW_PHASE", None)
    managed_python = str(test_env.get("DEVCOV_MANAGED_PYTHON", "")).strip()
    python_executable = managed_python or sys.executable
    command = [python_executable, "-m", "devcovenant", "test"]
    subprocess.run(
        command,
        check=True,
        env=test_env,
        cwd=repo_root,
    )


def _current_numstat_snapshot(repo_root: Path) -> dict[str, str]:
    """Return lightweight filesystem snapshot rows keyed by relative path."""
    snapshot: dict[str, str] = {}
    for rel in execution_runtime_module.capture_current_snapshot_paths(
        repo_root
    ):
        path = repo_root / rel
        try:
            stat = path.stat()
        except OSError as exc:
            raise ValueError(
                f"Unable to stat snapshot file {path}: {exc}"
            ) from exc
        snapshot[rel] = f"{stat.st_mtime_ns}\t{stat.st_size}\t{rel}"
    return snapshot


def _changed_paths_between(
    before: dict[str, str], after: dict[str, str]
) -> set[str]:
    """Return changed paths present in the current snapshot."""
    changed: set[str] = set()
    for path, row in after.items():
        if before.get(path) != row:
            changed.add(path)
    return changed


def run_pre_commit_gate(
    repo_root: Path,
    phase: str,
    *,
    command: str = "python3 -m pre_commit run --all-files",
    notes: str = "",
) -> int:
    """Run and record a start/end gate phase."""
    if phase not in {"start", "end"}:
        raise SystemExit("phase must be 'start' or 'end'.")

    status_path = registry_runtime_module.gate_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    if phase == "end":
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
                "Cannot end gate without an active open session. "
                "Run `devcovenant gate --start` first.",
                file=sys.stderr,
            )
            return 1

    start_ts = _utc_now() if phase == "start" else None
    attempt = 0
    max_attempts = 5
    force_tests = False
    recovery_status_active = False
    recovery_status_previous: bytes | None = None
    try:
        managed_env, managed_python = (
            execution_runtime_module.resolve_managed_environment_for_stage(
                repo_root,
                phase,
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
    if phase == "end":
        try:
            last_run_epoch = float(pre_payload.get("last_run_epoch") or 0.0)
        except (TypeError, ValueError):
            last_run_epoch = 0.0
        try:
            session_start_epoch = float(
                pre_payload.get("session_start_epoch") or 0.0
            )
        except (TypeError, ValueError):
            session_start_epoch = 0.0
        if last_run_epoch <= 0.0 or (
            session_start_epoch > 0.0 and last_run_epoch < session_start_epoch
        ):
            force_tests = True
        else:
            try:
                changed_since_tests = (
                    execution_runtime_module.snapshot_paths_changed_since(
                        repo_root,
                        last_run_epoch,
                    )
                )
            except ValueError as error:
                runtime_print(str(error), file=sys.stderr)
                return 1
            if any(
                _is_test_relevant_path(path) for path in changed_since_tests
            ):
                force_tests = True

    while True:
        env = dict(managed_env or os.environ)
        env["DEVCOV_DEVFLOW_PHASE"] = phase
        try:
            diff_before = _current_numstat_snapshot(repo_root)
        except ValueError as error:
            runtime_print(str(error), file=sys.stderr)
            return 1
        if phase == "start":
            status_exists = status_path.exists()
            status_payload: dict[str, object] = {}
            status_parse_error = ""
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

            session_state = (
                str(status_payload.get("session_state", "")).strip().lower()
            )
            recovery_reason = ""
            recovery_baseline_epoch: float | None = None
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
                try:
                    end_epoch = float(status_payload["session_end_epoch"])
                except (KeyError, TypeError, ValueError):
                    end_epoch = 0.0
                if end_epoch <= 0.0:
                    recovery_reason = (
                        "Closed gate status is missing `session_end_epoch`; "
                        "opening a recovery session from the current "
                        "baseline."
                    )
                else:
                    changed_since_end = (
                        execution_runtime_module.snapshot_paths_changed_since(
                            repo_root,
                            end_epoch,
                        )
                    )
                    if changed_since_end:
                        recovery_baseline_epoch = end_epoch
                        recovery_reason = (
                            "Detected edits after the previous "
                            "`devcovenant gate --end`; opening a recovery "
                            "session that includes those unsessioned edits."
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
                recovery_payload["session_id"] = str(
                    int(start_ts.timestamp() * 1000000)
                )
                recovery_payload["session_state"] = "open"
                recovery_payload["session_start_utc"] = start_ts.isoformat()
                recovery_payload["session_start_epoch"] = start_ts.timestamp()
                if recovery_baseline_epoch is not None:
                    recovery_payload["session_baseline_epoch"] = (
                        recovery_baseline_epoch
                    )
                else:
                    recovery_payload.pop("session_baseline_epoch", None)
                recovery_payload["recovery_start_reason"] = recovery_reason
                status_path.parent.mkdir(parents=True, exist_ok=True)
                status_path.write_text(
                    json.dumps(recovery_payload, indent=2) + "\n",
                    encoding="utf-8",
                )
                recovery_status_active = True
                env.pop("DEVCOV_DEVFLOW_PHASE", None)
            elif status_exists:
                recovery_status_active = False
                recovery_status_previous = None

        command_output = ""
        if phase == "end":
            exit_code, command_output = _run_command_with_output(
                effective_command,
                env=env,
            )
        else:
            exit_code = _run_command(
                effective_command,
                env=env,
                strict=False,
            )
        if phase == "start" and exit_code != 0:
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
            if phase == "start" and recovery_status_active:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
            runtime_print(str(error), file=sys.stderr)
            return 1
        if phase == "start" and diff_before != diff_after_hooks:
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

        if phase == "start" and recovery_status_active:
            try:
                _run_tests(repo_root, env)
            except subprocess.CalledProcessError as error:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
                runtime_print(
                    "Recovery start tests failed. Clear violations and rerun "
                    "`devcovenant gate --start`.",
                    file=sys.stderr,
                )
                return int(error.returncode or 1)
            try:
                diff_after_tests = _current_numstat_snapshot(repo_root)
            except ValueError as error:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
                runtime_print(str(error), file=sys.stderr)
                return 1
            if diff_before != diff_after_tests:
                _restore_status_file(status_path, recovery_status_previous)
                recovery_status_active = False
                runtime_print(
                    "Recovery start tests must not mutate the baseline "
                    "snapshot. Clear test-induced edits and rerun "
                    "`devcovenant gate --start`.",
                    file=sys.stderr,
                )
                return 1

        if phase == "end" and _is_blocking_devcov_failure(
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
                "violations. Failing without test reruns. Fix violations "
                "and rerun `devcovenant gate --end`.",
                file=sys.stderr,
            )
            return exit_code

        hook_changed_paths = _changed_paths_between(
            diff_before, diff_after_hooks
        )
        hooks_changed = bool(hook_changed_paths)
        hooks_require_tests = any(
            _is_test_relevant_path(path) for path in hook_changed_paths
        )
        tests_changed = False

        if phase == "end" and (hooks_require_tests or force_tests):
            if hooks_require_tests:
                runtime_print(
                    "Detected test-relevant changes after pre-commit; "
                    "rerunning tests to validate the updated tree.",
                    verbose_only=True,
                )
            elif force_tests:
                runtime_print(
                    "Rerunning tests to validate prior fixer changes.",
                    verbose_only=True,
                )
            try:
                _run_tests(repo_root, env)
            except subprocess.CalledProcessError as error:
                runtime_print(
                    "End gate test rerun failed. Clear violations and rerun "
                    "`devcovenant gate --end`.",
                    file=sys.stderr,
                )
                return int(error.returncode or 1)
            try:
                diff_after_tests = _current_numstat_snapshot(repo_root)
            except ValueError as error:
                runtime_print(str(error), file=sys.stderr)
                return 1
            tests_changed = (
                _changed_paths_between(diff_after_hooks, diff_after_tests)
                != set()
            )

        if phase == "end" and (hooks_changed or tests_changed):
            attempt += 1
            if attempt >= max_attempts:
                runtime_print(
                    "Maximum rerun attempts reached; tree still dirty. "
                    "Failing end gate."
                )
                return 1
            if tests_changed:
                runtime_print(
                    "Detected changes after tests; rerunning hooks and tests.",
                    verbose_only=True,
                )
                force_tests = True
            else:
                force_tests = False
            runtime_print(
                "Rerunning pre-commit hooks to verify clean tree...",
                verbose_only=True,
            )
            continue
        if phase == "end" and exit_code != 0:
            rendered = " ".join(shlex.split(command)) or command
            runtime_print(
                "Pre-commit command failed with exit code "
                f"{exit_code}: {rendered}",
                file=sys.stderr,
            )
            return exit_code
        break

    try:
        payload = _load_status(status_path)
    except ValueError as error:
        runtime_print(str(error), file=sys.stderr)
        return 1
    now = _utc_now()
    prefix = f"pre_commit_{phase}"
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
    if phase == "start":
        # Purge legacy keys so old payload shape cannot silently persist.
        payload.pop("sha", None)
        payload.pop("tests_coverage_evidence", None)
        payload.pop("changelog_start_diff_numstat", None)
        payload.pop("changelog_start_exemption_fingerprints", None)
        payload.pop("session_start_signature", None)
        session_id = str(int(start_ts.timestamp() * 1000000))
        payload["session_id"] = session_id
        payload["session_state"] = "open"
        payload["session_start_utc"] = start_ts.isoformat()
        payload["session_start_epoch"] = start_ts.timestamp()
        if recovery_status_active:
            baseline_epoch = payload.get("session_baseline_epoch")
            try:
                baseline_epoch_value = float(baseline_epoch)
            except (TypeError, ValueError):
                baseline_epoch_value = 0.0
            if (
                baseline_epoch_value <= 0.0
                or baseline_epoch_value > start_ts.timestamp()
            ):
                payload.pop("session_baseline_epoch", None)
            else:
                payload["session_baseline_epoch"] = baseline_epoch_value
        else:
            # Normal starts must not carry a stale recovery baseline forward.
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
        payload["document_exemption_baseline"] = (
            execution_runtime_module.capture_document_exemption_baseline(
                repo_root,
                header_doc_suffixes=header_doc_suffixes,
                header_keys=header_keys,
                header_scan_lines=header_scan_lines,
            )
        )
        payload.pop("session_end_utc", None)
        payload.pop("session_end_epoch", None)
        payload.pop("session_end_signature", None)
        payload.pop("session_end_snapshot", None)
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
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime_print(
        f"Recorded {prefix} at {payload[f'{prefix}_utc']} "
        f"for command `{payload[f'{prefix}_command']}`."
    )
    return 0
