"""Execution helpers for command entrypoints and test orchestration."""

from __future__ import annotations

import argparse
import datetime as _dt
import errno
import hashlib
import json
import os
import re
import select
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence, TextIO

import yaml

try:
    import pty
except ImportError:  # pragma: no cover - non-POSIX runtimes
    pty = None  # type: ignore[assignment]

from devcovenant import __version__ as package_version
from devcovenant.core.runtime import output as output_runtime_module
from devcovenant.core.runtime import run_logging as run_logging_runtime_module
from devcovenant.core.runtime import (
    session_snapshot as session_snapshot_runtime_module,
)
from devcovenant.core.services import event as event_runtime_module
from devcovenant.core.services import registry as registry_runtime_module
from devcovenant.core.services import (
    runtime_profile as test_profile_runtime_module,
)

OutputMode = output_runtime_module.OutputMode


def build_command_parser(
    command_name: str,
    description: str,
) -> argparse.ArgumentParser:
    """Build a command-scoped parser with stable root-command usage text."""
    return argparse.ArgumentParser(
        prog=f"devcovenant {command_name}",
        description=description,
    )


ChildOutputChannel = output_runtime_module.ChildOutputChannel
_OUTPUT_MODE_DEFAULT: OutputMode = output_runtime_module.OUTPUT_MODE_DEFAULT
_MANAGED_ENV_POLICY_ID = "managed-environment"
_MANAGED_ENV_ACTION_RESOLVE_STAGE = "resolve-stage"
_MANAGED_ENV_ACTION_RESOLVE_RERUN = "resolve-rerun-command"
_DEVFLOW_POLICY_ID = "devflow-run-gates"
_DEVFLOW_ACTION_RESOLVE_REQUIRED_COMMANDS = "resolve-required-test-commands"
_TEST_COMMAND_OUTPUT_MODE: OutputMode | None = None
_TEST_COMMAND_LABEL = ""
_PYCACHE_PREFIX_ENABLED = False
_PYCACHE_PREFIX_VALUE: str | None = None
_LOGS_KEEP_LAST_DEFAULT = 0
_LOGS_KEEP_LAST = _LOGS_KEEP_LAST_DEFAULT
_RUN_LOG_TAIL_MAX_LINES = 160
_RUN_LOG_TAIL_MAX_CHARS = 12000
_ACTIVE_RUN_LOG_CONTEXT: run_logging_runtime_module.RunLogContext | None = None
_ACTIVE_RUN_TAIL_LINES: list[str] = []
_ACTIVE_RUN_LOG_POINTER_EMITTED = False
_TOP_LEVEL_COMMAND_ENV = "DEVCOV_TOP_COMMAND"
_WAIT_PROGRESS_MESSAGE = output_runtime_module.WAIT_PROGRESS_MESSAGE
_WAIT_PROGRESS_INITIAL_SECONDS = 15.0
_WAIT_PROGRESS_REPEAT_SECONDS = 60.0


def _normalize_output_mode(raw_value: str | None) -> OutputMode:
    """Normalize an output mode token to one of the allowed runtime modes."""
    return output_runtime_module.normalize_output_mode(
        raw_value,
        default=_OUTPUT_MODE_DEFAULT,
    )


class Reporter(Protocol):
    """Output boundary contract for user-visible runtime messages."""

    mode: OutputMode

    def emit(
        self,
        message: str,
        *,
        stream: TextIO | None = None,
        end: str = "\n",
        flush: bool = False,
        verbose_only: bool = False,
    ) -> None:
        """Emit one message through the configured output boundary."""

    def banner(self, title: str, emoji: str) -> None:
        """Emit a stage banner message."""

    def step(
        self, message: str, emoji: str = "•", *, verbose_only: bool = False
    ) -> None:
        """Emit a short status step."""


class ConsoleReporter:
    """Console output adapter implementing the runtime Reporter contract."""

    def __init__(self, mode: OutputMode) -> None:
        """Initialize reporter with one deterministic output mode."""
        self.mode = mode

    def emit(
        self,
        message: str,
        *,
        stream: TextIO | None = None,
        end: str = "\n",
        flush: bool = False,
        verbose_only: bool = False,
    ) -> None:
        """Write one message to stdout/stderr with mode-aware filtering."""
        target = stream if stream is not None else sys.stdout
        if self.mode == "quiet" and target is sys.stdout:
            return
        if verbose_only and self.mode != "verbose":
            return
        target.write(f"{message}{end}")
        # Line-flush console output by default so normal/verbose status lines
        # remain visible during long-running commands without waiting for
        # process exit or large buffer fills.
        if flush or target in {sys.stdout, sys.stderr}:
            target.flush()

    def banner(self, title: str, emoji: str) -> None:
        """Emit a decorative stage banner in verbose mode only."""
        self.emit("\n" + "=" * 70, verbose_only=True)
        self.emit(f"{emoji} {title}", verbose_only=True)
        self.emit("=" * 70, verbose_only=True)

    def step(
        self, message: str, emoji: str = "•", *, verbose_only: bool = False
    ) -> None:
        """Emit a one-line status message."""
        self.emit(f"{emoji} {message}", verbose_only=verbose_only)


_OUTPUT_MODE: OutputMode = _OUTPUT_MODE_DEFAULT
_REPORTER: Reporter = ConsoleReporter(_OUTPUT_MODE)


def set_active_run_log_context(
    context: run_logging_runtime_module.RunLogContext | None,
) -> None:
    """Activate one per-run log context for runtime output capture."""
    global _ACTIVE_RUN_LOG_CONTEXT, _ACTIVE_RUN_TAIL_LINES
    global _ACTIVE_RUN_LOG_POINTER_EMITTED
    _ACTIVE_RUN_LOG_CONTEXT = context
    _ACTIVE_RUN_TAIL_LINES = []
    _ACTIVE_RUN_LOG_POINTER_EMITTED = False


def get_active_run_log_context() -> (
    run_logging_runtime_module.RunLogContext | None
):
    """Return the active per-run log context, if any."""
    return _ACTIVE_RUN_LOG_CONTEXT


def clear_active_run_log_context() -> None:
    """Clear active per-run log capture state."""
    set_active_run_log_context(None)


def merge_active_run_log_metadata(updates: Mapping[str, Any]) -> None:
    """Merge metadata into the active run context when one is present."""
    context = _ACTIVE_RUN_LOG_CONTEXT
    if context is None:
        return
    context.metadata.update(dict(updates))


def append_active_run_log_output(stream_name: str, text: str) -> None:
    """Append captured output text into the active run-log artifacts."""
    context = _ACTIVE_RUN_LOG_CONTEXT
    payload = str(text)
    if context is None or not payload:
        return
    try:
        run_logging_runtime_module.append_run_stream_output(
            context,
            stream_name,
            payload,
        )
        _record_active_run_tail_text(payload)
    except (OSError, ValueError):
        return


def emit_active_run_log_pointer(
    *,
    file: TextIO | None = None,
    verbose_only: bool = False,
    once: bool = False,
) -> str | None:
    """Emit a deterministic pointer to the active run folder and summaries."""
    global _ACTIVE_RUN_LOG_POINTER_EMITTED
    context = _ACTIVE_RUN_LOG_CONTEXT
    if context is None:
        return None
    paths = context.require_paths()
    run_dir = _run_log_repo_relative(context.repo_root, paths.run_dir)
    summary_txt = _run_log_repo_relative(context.repo_root, paths.summary_txt)
    summary_json = _run_log_repo_relative(
        context.repo_root,
        paths.summary_json,
    )
    message = (
        "Run logs: "
        f"{run_dir} (summary: {summary_txt}, summary.json: {summary_json})"
    )
    if once and _ACTIVE_RUN_LOG_POINTER_EMITTED:
        return message
    runtime_print(message, file=file, verbose_only=verbose_only)
    _ACTIVE_RUN_LOG_POINTER_EMITTED = True
    return message


def finalize_active_run_log_context(
    *,
    exit_code: int | None,
    status: str | None = None,
    metadata_updates: Mapping[str, Any] | None = None,
) -> run_logging_runtime_module.RunLogContext | None:
    """Finalize the active run-log context and write summary artifacts."""
    context = _ACTIVE_RUN_LOG_CONTEXT
    if context is None:
        return None
    tail_text = _active_run_tail_text()
    try:
        run_logging_runtime_module.write_run_tail(context, tail_text)
        run_logging_runtime_module.finalize_run_log_context(
            context,
            exit_code=exit_code,
            status=status,
            summary_text=_build_active_run_summary_text(
                context,
                status=status,
                exit_code=exit_code,
            ),
            summary_data=_build_active_run_summary_json(
                context,
                status=status,
                exit_code=exit_code,
            ),
            metadata_updates=metadata_updates,
        )
        run_logging_runtime_module.prune_run_log_directories(
            context.repo_root,
            keep_last=get_logs_keep_last(),
            preserve_run_id=context.run_id,
        )
    except OSError:
        return context
    return context


def _build_active_run_summary_text(
    context: run_logging_runtime_module.RunLogContext,
    *,
    status: str | None,
    exit_code: int | None,
) -> str:
    """Build a generic command-run summary text for CLI-dispatched runs."""
    final_status = _resolve_run_log_status(exit_code, status)
    paths = context.require_paths()
    lines = [
        f"Run ID: {context.run_id}",
        f"Command: {context.command_name}",
        "Argv: " + (" ".join(context.argv) if context.argv else ""),
        f"Status: {final_status}",
        f"Exit Code: {'' if exit_code is None else exit_code}",
        "Run Dir: " + _run_log_repo_relative(context.repo_root, paths.run_dir),
        "stdout.log: "
        + _run_log_repo_relative(context.repo_root, paths.stdout_log),
        "stderr.log: "
        + _run_log_repo_relative(context.repo_root, paths.stderr_log),
        "tail.txt: "
        + _run_log_repo_relative(context.repo_root, paths.tail_txt),
    ]
    test_summary = context.metadata.get("test_summary")
    if isinstance(test_summary, Mapping):
        mode = str(test_summary.get("tests_output_mode", "")).strip()
        if mode:
            lines.append(f"Tests Output Mode: {mode}")
        total = test_summary.get("total_commands")
        passed = test_summary.get("passed_commands")
        failed = test_summary.get("failed_commands")
        if any(value is not None for value in (total, passed, failed)):
            lines.append(
                "Test Commands: "
                f"total={'' if total is None else total}, "
                f"passed={'' if passed is None else passed}, "
                f"failed={'' if failed is None else failed}"
            )
        duration_seconds = test_summary.get("duration_seconds")
        if duration_seconds is not None:
            lines.append(f"Duration Seconds: {duration_seconds}")
        min_command = test_summary.get("duration_seconds_min_command")
        avg_command = test_summary.get("duration_seconds_avg_command")
        max_command = test_summary.get("duration_seconds_max_command")
        duration_events = test_summary.get("duration_events_count")
        if any(
            value is not None
            for value in (min_command, avg_command, max_command)
        ):
            lines.append(
                "Command Duration Seconds: "
                f"min={'' if min_command is None else min_command}, "
                f"avg={'' if avg_command is None else avg_command}, "
                f"max={'' if max_command is None else max_command}, "
                f"events={'' if duration_events is None else duration_events}"
            )
        first_failed = str(
            test_summary.get("first_failed_command", "")
        ).strip()
        if first_failed:
            lines.append(f"First Failed Command: {first_failed}")
        failure_hint = str(test_summary.get("failure_hint", "")).strip()
        if failure_hint:
            lines.append(f"Failure Hint: {failure_hint}")
    profile_artifacts = context.metadata.get("test_profile_artifacts")
    if isinstance(profile_artifacts, Mapping):
        profile_txt = str(
            profile_artifacts.get("test_profile_txt", "")
        ).strip()
        profile_json = str(
            profile_artifacts.get("test_profile_json", "")
        ).strip()
        if profile_txt:
            lines.append(f"Test Profile txt: {profile_txt}")
        if profile_json:
            lines.append(f"Test Profile json: {profile_json}")
    clean_summary = context.metadata.get("clean_summary")
    if isinstance(clean_summary, Mapping):
        scopes = clean_summary.get("selected_scopes")
        if isinstance(scopes, Sequence) and not isinstance(scopes, str):
            scope_text = ", ".join(
                str(item).strip() for item in scopes if str(item).strip()
            )
            if scope_text:
                lines.append(f"Cleanup Scope: {scope_text}")
        removed_count = clean_summary.get("removed_count")
        if removed_count is not None:
            lines.append(f"Removed Targets: {removed_count}")
        skipped_count = clean_summary.get("skipped_protected_count")
        if skipped_count is not None:
            lines.append(f"Skipped Protected Targets: {skipped_count}")
        skipped_paths = clean_summary.get("skipped_protected_paths")
        if isinstance(skipped_paths, Sequence) and not isinstance(
            skipped_paths, str
        ):
            skipped_text = ", ".join(
                str(item).strip()
                for item in skipped_paths
                if str(item).strip()
            )
            if skipped_text:
                lines.append(f"Skipped Protected Paths: {skipped_text}")
    return "\n".join(lines) + "\n"


def _build_active_run_summary_json(
    context: run_logging_runtime_module.RunLogContext,
    *,
    status: str | None,
    exit_code: int | None,
) -> dict[str, Any]:
    """Build a generic command-run summary JSON payload for CLI dispatch."""
    final_status = _resolve_run_log_status(exit_code, status)
    paths = context.require_paths()
    payload = {
        "schema_version": run_logging_runtime_module.RUN_LOG_SCHEMA_VERSION,
        "run_id": context.run_id,
        "command_name": context.command_name,
        "command_family": context.command_name,
        "argv": list(context.argv),
        "status": final_status,
        "exit_code": exit_code,
        "started_at": context.started_at,
        "gate_session_id": context.gate_session_id,
        "artifacts": {
            "run_json": _run_log_repo_relative(
                context.repo_root,
                paths.run_json,
            ),
            "summary_txt": _run_log_repo_relative(
                context.repo_root, paths.summary_txt
            ),
            "summary_json": _run_log_repo_relative(
                context.repo_root, paths.summary_json
            ),
            "stdout_log": _run_log_repo_relative(
                context.repo_root, paths.stdout_log
            ),
            "stderr_log": _run_log_repo_relative(
                context.repo_root, paths.stderr_log
            ),
            "tail_txt": _run_log_repo_relative(
                context.repo_root,
                paths.tail_txt,
            ),
        },
        "metadata": dict(context.metadata),
    }
    clean_summary = context.metadata.get("clean_summary")
    if isinstance(clean_summary, Mapping):
        payload["clean_summary"] = dict(clean_summary)
    return payload


def _resolve_run_log_status(
    exit_code: int | None,
    status: str | None,
) -> str:
    """Resolve final run-log status token from explicit or exit-code values."""
    token = str(status or "").strip().lower()
    if token:
        return token
    if exit_code is None:
        return "unknown"
    return "success" if int(exit_code) == 0 else "failure"


def _record_active_run_tail_text(text: str) -> None:
    """Keep a bounded in-memory tail for the active run summary artifact."""
    global _ACTIVE_RUN_TAIL_LINES
    if not text:
        return
    _ACTIVE_RUN_TAIL_LINES.extend(text.splitlines(keepends=True))
    if len(_ACTIVE_RUN_TAIL_LINES) > (_RUN_LOG_TAIL_MAX_LINES * 2):
        _ACTIVE_RUN_TAIL_LINES = _ACTIVE_RUN_TAIL_LINES[
            -_RUN_LOG_TAIL_MAX_LINES:
        ]
    while len(_ACTIVE_RUN_TAIL_LINES) > _RUN_LOG_TAIL_MAX_LINES:
        _ACTIVE_RUN_TAIL_LINES.pop(0)
    while (
        sum(len(line) for line in _ACTIVE_RUN_TAIL_LINES)
        > _RUN_LOG_TAIL_MAX_CHARS
    ):
        if not _ACTIVE_RUN_TAIL_LINES:
            break
        _ACTIVE_RUN_TAIL_LINES.pop(0)


def _active_run_tail_text() -> str:
    """Return bounded tail text for the active run context."""
    return "".join(_ACTIVE_RUN_TAIL_LINES)


def _run_log_repo_relative(repo_root: Path, path: Path) -> str:
    """Return repo-relative path when available for runtime log pointers."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def configure_output_mode(mode: str | None) -> OutputMode:
    """Configure global output mode for this process runtime."""
    global _OUTPUT_MODE, _REPORTER
    normalized = (
        _normalize_output_mode(mode)
        if mode is not None
        else _OUTPUT_MODE_DEFAULT
    )
    _OUTPUT_MODE = normalized
    _REPORTER = ConsoleReporter(normalized)
    return normalized


def get_output_mode() -> OutputMode:
    """Return active runtime output mode."""
    return _OUTPUT_MODE


def configure_logs_keep_last(value: object | None) -> int:
    """Configure run-log retention (`0` keeps all run folders)."""
    global _LOGS_KEEP_LAST
    _LOGS_KEEP_LAST = _normalize_logs_keep_last(value)
    return _LOGS_KEEP_LAST


def get_logs_keep_last() -> int:
    """Return run-log retention count (`0` means unlimited retention)."""
    return _LOGS_KEEP_LAST


def _read_engine_config(repo_root: Path) -> dict[str, Any]:
    """Read `engine` config mapping from repo config when available."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, dict):
        return {}
    engine_cfg = payload.get("engine")
    if not isinstance(engine_cfg, dict):
        return {}
    return engine_cfg


def resolve_engine_auto_fix_enabled(repo_root: Path) -> bool:
    """Resolve gate-managed autofix enablement from repo config."""
    engine_cfg = _read_engine_config(repo_root)
    raw_value = engine_cfg.get("auto_fix_enabled")
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        token = raw_value.strip().lower()
        if token in {"true", "1", "yes", "on", "enabled"}:
            return True
        if token in {"false", "0", "no", "off", "disabled"}:
            return False
    return False


def _read_profiles_from_config(repo_root: Path) -> list[str]:
    """Read active profile list from repo config when available."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return []
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(payload, dict):
        return []
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        return []
    active = profiles.get("active")
    if not isinstance(active, list):
        return []
    return [str(token).strip() for token in active if str(token).strip()]


def _repo_uses_repo_bytecode_hygiene(repo_root: Path) -> bool:
    """Return True when repo profiles enable repo-local bytecode hygiene."""
    return "devcovrepo" in _read_profiles_from_config(repo_root)


def _normalize_engine_bool(raw_value: object, *, default: bool) -> bool:
    """Normalize common boolean config tokens to a bool value."""
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        token = raw_value.strip().lower()
        if token in {"true", "1", "yes", "on", "enabled"}:
            return True
        if token in {"false", "0", "no", "off", "disabled"}:
            return False
    return default


def _read_pycache_prefix_enabled_from_config(repo_root: Path) -> bool:
    """Read `engine.pycache_prefix_enabled` with repo-profile fallback."""
    engine_cfg = _read_engine_config(repo_root)
    default_enabled = _repo_uses_repo_bytecode_hygiene(repo_root)
    if "pycache_prefix_enabled" not in engine_cfg:
        return default_enabled
    return _normalize_engine_bool(
        engine_cfg.get("pycache_prefix_enabled"),
        default=default_enabled,
    )


def _default_repo_pycache_prefix(repo_root: Path) -> str:
    """Return a stable temp pycache root for one repository checkout."""
    try:
        repo_token = str(repo_root.resolve())
    except OSError:
        repo_token = str(repo_root)
    suffix = hashlib.sha256(repo_token.encode("utf-8")).hexdigest()[:12]
    return str(Path(tempfile.gettempdir()) / "devcovenant-pycache" / suffix)


def _read_pycache_prefix_from_config(repo_root: Path) -> str:
    """Read and resolve `engine.pycache_prefix` (empty => auto temp path)."""
    engine_cfg = _read_engine_config(repo_root)
    raw_value = engine_cfg.get("pycache_prefix")
    token = str(raw_value or "").strip()
    if not token:
        return _default_repo_pycache_prefix(repo_root)
    path = Path(token).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return str(path)


def configure_repo_pycache_prefix(repo_root: Path) -> bool:
    """Configure repo-scoped Python bytecode cache routing when enabled."""
    global _PYCACHE_PREFIX_ENABLED, _PYCACHE_PREFIX_VALUE
    if not _read_pycache_prefix_enabled_from_config(repo_root):
        _PYCACHE_PREFIX_ENABLED = False
        _PYCACHE_PREFIX_VALUE = None
        return False
    prefix = _read_pycache_prefix_from_config(repo_root)
    try:
        Path(prefix).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    _PYCACHE_PREFIX_ENABLED = True
    _PYCACHE_PREFIX_VALUE = prefix
    try:
        setattr(sys, "pycache_prefix", prefix)
    except (AttributeError, TypeError):
        pass
    os.environ["PYTHONPYCACHEPREFIX"] = prefix
    return True


def cleanup_repo_bytecode_artifacts(repo_root: Path) -> bool:
    """Remove repo-local bytecode artifacts when repo hygiene is enabled."""
    if not _repo_uses_repo_bytecode_hygiene(repo_root):
        return False
    root = repo_root / "devcovenant"
    if not root.exists():
        return False
    removed = False
    for path in root.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed = True
    for path in root.rglob("*.pyc"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                continue
            removed = True
    for path in root.rglob("*.pyo"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                continue
            removed = True
    for path in root.rglob("*.pyd"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                continue
            removed = True
    return removed


def _apply_repo_bytecode_env(env: dict[str, str]) -> dict[str, str]:
    """Attach repo runtime env flags for bytecode hygiene and live output."""
    if _PYCACHE_PREFIX_ENABLED and _PYCACHE_PREFIX_VALUE:
        env["PYTHONPYCACHEPREFIX"] = _PYCACHE_PREFIX_VALUE
    # Keep child Python commands unbuffered so line-by-line streaming remains
    # live in both normal and verbose modes.
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _read_output_mode_from_config(repo_root: Path) -> str | None:
    """Read optional `engine.output_mode` from repo config."""
    engine_cfg = _read_engine_config(repo_root)
    token = str(engine_cfg.get("output_mode", "")).strip()
    return token or None


def _normalize_logs_keep_last(raw_value: object) -> int:
    """Normalize `engine.logs_keep_last` to a non-negative integer."""
    if isinstance(raw_value, bool):
        return _LOGS_KEEP_LAST_DEFAULT
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return _LOGS_KEEP_LAST_DEFAULT
    return max(0, value)


def _read_logs_keep_last_from_config(repo_root: Path) -> int:
    """Read `engine.logs_keep_last` from repo config (`0` keeps all)."""
    engine_cfg = _read_engine_config(repo_root)
    return _normalize_logs_keep_last(engine_cfg.get("logs_keep_last"))


def _read_tests_output_mode_from_config(repo_root: Path) -> str | None:
    """
    Read optional `engine.tests_output_mode` from repo config.

    Compatibility fallback:
    - If `tests_output_mode` is unset, reuse `output_mode`.
    """
    engine_cfg = _read_engine_config(repo_root)
    tests_token = str(engine_cfg.get("tests_output_mode", "")).strip()
    if tests_token:
        return tests_token
    output_token = str(engine_cfg.get("output_mode", "")).strip()
    return output_token or None


def configure_output_mode_from_config(repo_root: Path) -> OutputMode:
    """Configure output mode from `devcovenant/config.yaml`."""
    return configure_output_mode(_read_output_mode_from_config(repo_root))


def configure_logs_keep_last_from_config(repo_root: Path) -> int:
    """Configure run-log retention from `devcovenant/config.yaml`."""
    return configure_logs_keep_last(
        _read_logs_keep_last_from_config(repo_root)
    )


def resolve_tests_output_mode(repo_root: Path) -> OutputMode:
    """Resolve tests output mode from config with compatibility fallback."""
    return _normalize_output_mode(
        _read_tests_output_mode_from_config(repo_root)
    )


def runtime_print(
    *args: object,
    sep: str = " ",
    end: str = "\n",
    file: TextIO | None = None,
    flush: bool = False,
    verbose_only: bool = False,
) -> None:
    """
    Print via the output boundary with built-in-print-compatible semantics.

    Existing runtime call sites can migrate from direct `print()` usage
    without changing caller-side argument shapes.
    """
    message = sep.join(str(arg) for arg in args)
    stream = file if file is not None else sys.stdout
    if stream is sys.stdout:
        append_active_run_log_output("stdout", f"{message}{end}")
    elif stream is sys.stderr:
        append_active_run_log_output("stderr", f"{message}{end}")
    if stream in {sys.stdout, sys.stderr}:
        _REPORTER.emit(
            message,
            stream=stream,
            end=end,
            flush=flush,
            verbose_only=verbose_only,
        )
        return
    if verbose_only and _OUTPUT_MODE != "verbose":
        return
    stream.write(f"{message}{end}")
    if flush:
        stream.flush()


def print_banner(title: str, emoji: str) -> None:
    """Print a readable stage banner via the output boundary."""
    _REPORTER.banner(title, emoji)


def print_step(message: str, emoji: str = "•") -> None:
    """Print a short, single-line status step via output boundary."""
    _REPORTER.step(message, emoji)


def top_level_command_name() -> str:
    """Return the normalized top-level CLI command name from environment."""
    return str(os.environ.get(_TOP_LEVEL_COMMAND_ENV, "")).strip().lower()


def normal_mode_prefers_live_streaming_for_command(
    command_name: str | None = None,
) -> bool:
    """Return whether normal mode should keep console streaming live."""
    del command_name
    plan = output_runtime_module.resolve_child_output_plan(
        get_output_mode(),
        "generic_child",
    )
    return plan.emit_console


def resolve_child_output_plan_for_channel(
    channel: ChildOutputChannel,
    *,
    output_mode: str | None = None,
) -> output_runtime_module.ChildOutputPlan:
    """Resolve child-command output behavior for one output channel."""
    if output_mode is None:
        effective_mode = get_output_mode()
    else:
        effective_mode = _normalize_output_mode(output_mode)
    return output_runtime_module.resolve_child_output_plan(
        effective_mode,
        channel,
    )


def run_child_command_with_output_policy(
    command: Sequence[str],
    *,
    channel: ChildOutputChannel,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    capture_combined_output: bool = False,
    output_mode: str | None = None,
    heartbeat_initial_seconds: float = _WAIT_PROGRESS_INITIAL_SECONDS,
    heartbeat_repeat_seconds: float = _WAIT_PROGRESS_REPEAT_SECONDS,
    verbose_only_console: bool = False,
) -> tuple[subprocess.CompletedProcess, str]:
    """
    Run one child command through the shared mode-aware output pipeline.

    This is the single policy gateway for child-process streaming behavior.
    Channel + mode resolve console suppression and heartbeat behavior in one
    place before command execution.
    """
    output_plan = resolve_child_output_plan_for_channel(
        channel,
        output_mode=output_mode,
    )
    return run_subprocess_with_runtime_output(
        command,
        env=env,
        cwd=cwd,
        emit_console=output_plan.emit_console,
        capture_combined_output=capture_combined_output,
        heartbeat_message=output_plan.heartbeat_message,
        heartbeat_initial_seconds=heartbeat_initial_seconds,
        heartbeat_repeat_seconds=heartbeat_repeat_seconds,
        verbose_only_console=verbose_only_console,
    )


def run_subprocess_with_runtime_output(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    emit_console: bool = True,
    capture_combined_output: bool = False,
    heartbeat_message: str | None = None,
    heartbeat_initial_seconds: float = _WAIT_PROGRESS_INITIAL_SECONDS,
    heartbeat_repeat_seconds: float = _WAIT_PROGRESS_REPEAT_SECONDS,
    verbose_only_console: bool = False,
) -> tuple[subprocess.CompletedProcess, str]:
    """
    Run one subprocess with live line handling, log capture, and heartbeat.

    Output is always appended to the active run log context when one exists.
    Console emission is caller-controlled so normal-mode flood suppression can
    hide child output while still providing heartbeat liveness lines.
    """
    if emit_console and pty is not None:
        return _run_subprocess_with_runtime_output_pty(
            command,
            env=env,
            cwd=cwd,
            capture_combined_output=capture_combined_output,
            heartbeat_message=heartbeat_message,
            heartbeat_initial_seconds=heartbeat_initial_seconds,
            heartbeat_repeat_seconds=heartbeat_repeat_seconds,
            verbose_only_console=verbose_only_console,
        )

    return _run_subprocess_with_runtime_output_pipe(
        command,
        env=env,
        cwd=cwd,
        emit_console=emit_console,
        capture_combined_output=capture_combined_output,
        heartbeat_message=heartbeat_message,
        heartbeat_initial_seconds=heartbeat_initial_seconds,
        heartbeat_repeat_seconds=heartbeat_repeat_seconds,
        verbose_only_console=verbose_only_console,
    )


def _emit_subprocess_chunk(
    chunk: str,
    *,
    emit_console: bool,
    verbose_only_console: bool,
) -> None:
    """Route one subprocess output chunk through runtime output/log sinks."""
    if not chunk:
        return
    if emit_console:
        runtime_print(
            chunk,
            end="",
            verbose_only=verbose_only_console,
        )
    else:
        append_active_run_log_output("stdout", chunk)


def _run_subprocess_with_runtime_output_pty(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    capture_combined_output: bool = False,
    heartbeat_message: str | None = None,
    heartbeat_initial_seconds: float = _WAIT_PROGRESS_INITIAL_SECONDS,
    heartbeat_repeat_seconds: float = _WAIT_PROGRESS_REPEAT_SECONDS,
    verbose_only_console: bool = False,
) -> tuple[subprocess.CompletedProcess, str]:
    """Run one subprocess through a PTY to avoid child-output buffering."""
    if pty is None:
        raise RuntimeError("PTY runtime path is unavailable.")
    command_env = _apply_repo_bytecode_env(dict(env or os.environ))
    command_tokens = [str(token) for token in command]
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        command_tokens,
        stdin=subprocess.DEVNULL,
        stdout=slave_fd,
        stderr=slave_fd,
        env=command_env,
        cwd=cwd,
        bufsize=0,
        close_fds=True,
    )
    combined_chunks: list[str] = []
    os.close(slave_fd)

    heartbeat_token = str(heartbeat_message or "").strip()
    next_heartbeat: float | None = None
    if heartbeat_token:
        next_heartbeat = time.monotonic() + max(
            0.0, float(heartbeat_initial_seconds)
        )

    try:
        while True:
            timeout = 1.0
            now = time.monotonic()
            if next_heartbeat is not None:
                timeout = max(0.01, min(1.0, next_heartbeat - now))
            ready, _, _ = select.select([master_fd], [], [], timeout)
            if not ready:
                if (
                    next_heartbeat is not None
                    and process.poll() is None
                    and time.monotonic() >= next_heartbeat
                ):
                    runtime_print(heartbeat_token)
                    next_heartbeat = time.monotonic() + max(
                        1.0, float(heartbeat_repeat_seconds)
                    )
                if process.poll() is not None:
                    break
                continue

            try:
                chunk_bytes = os.read(master_fd, 4096)
            except OSError as exc:
                if exc.errno == errno.EIO and process.poll() is not None:
                    break
                raise
            if not chunk_bytes:
                if process.poll() is not None:
                    break
                continue
            chunk = chunk_bytes.decode("utf-8", errors="replace")
            if capture_combined_output:
                combined_chunks.append(chunk)
            _emit_subprocess_chunk(
                chunk,
                emit_console=True,
                verbose_only_console=verbose_only_console,
            )
            if next_heartbeat is not None:
                next_heartbeat = time.monotonic() + max(
                    1.0, float(heartbeat_repeat_seconds)
                )
    finally:
        process.wait()
        try:
            os.close(master_fd)
        except OSError:
            pass

    completed = subprocess.CompletedProcess(
        command_tokens,
        int(process.returncode or 0),
    )
    return completed, "".join(combined_chunks)


def _run_subprocess_with_runtime_output_pipe(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    emit_console: bool = True,
    capture_combined_output: bool = False,
    heartbeat_message: str | None = None,
    heartbeat_initial_seconds: float = _WAIT_PROGRESS_INITIAL_SECONDS,
    heartbeat_repeat_seconds: float = _WAIT_PROGRESS_REPEAT_SECONDS,
    verbose_only_console: bool = False,
) -> tuple[subprocess.CompletedProcess, str]:
    """Run one subprocess through pipes with live queue-based streaming."""
    command_env = _apply_repo_bytecode_env(dict(env or os.environ))
    command_tokens = [str(token) for token in command]
    process = subprocess.Popen(
        command_tokens,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
        env=command_env,
        cwd=cwd,
        bufsize=0,
    )
    output_stream = process.stdout
    if output_stream is None:
        process.wait()
        completed = subprocess.CompletedProcess(
            command_tokens,
            int(process.returncode or 0),
        )
        return completed, ""
    output_fd = output_stream.fileno()
    combined_chunks: list[str] = []
    heartbeat_token = str(heartbeat_message or "").strip()
    next_heartbeat: float | None = None
    if heartbeat_token:
        next_heartbeat = time.monotonic() + max(
            0.0, float(heartbeat_initial_seconds)
        )

    try:
        while True:
            timeout = 1.0
            now = time.monotonic()
            if next_heartbeat is not None:
                timeout = max(0.01, min(1.0, next_heartbeat - now))
            ready, _, _ = select.select([output_fd], [], [], timeout)
            if not ready:
                if (
                    next_heartbeat is not None
                    and process.poll() is None
                    and time.monotonic() >= next_heartbeat
                ):
                    runtime_print(heartbeat_token)
                    next_heartbeat = time.monotonic() + max(
                        1.0, float(heartbeat_repeat_seconds)
                    )
                if process.poll() is not None:
                    break
                continue

            try:
                chunk_bytes = os.read(output_fd, 4096)
            except OSError as exc:
                if exc.errno in {errno.EIO, errno.EBADF} and (
                    process.poll() is not None
                ):
                    break
                raise
            if not chunk_bytes:
                if process.poll() is not None:
                    break
                continue
            chunk = chunk_bytes.decode("utf-8", errors="replace")
            if capture_combined_output:
                combined_chunks.append(chunk)
            _emit_subprocess_chunk(
                chunk,
                emit_console=emit_console,
                verbose_only_console=verbose_only_console,
            )
            if next_heartbeat is not None and emit_console:
                next_heartbeat = time.monotonic() + max(
                    1.0, float(heartbeat_repeat_seconds)
                )
    finally:
        process.wait()
        try:
            output_stream.close()
        except OSError:
            pass

    completed = subprocess.CompletedProcess(
        command_tokens,
        int(process.returncode or 0),
    )
    return completed, "".join(combined_chunks)


def find_git_root(path: Path) -> Path | None:
    """Return the nearest git root for a path."""
    current = path.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def resolve_repo_root(*, require_install: bool = False) -> Path:
    """Resolve and validate the current git repository root."""
    repo_root = find_git_root(Path.cwd())
    if repo_root is None:
        raise SystemExit(
            "DevCovenant commands must run inside a git repository."
        )
    if require_install and not (repo_root / "devcovenant").exists():
        raise SystemExit(
            "DevCovenant is not installed in this repo. "
            "Run `devcovenant install` first."
        )
    configure_repo_pycache_prefix(repo_root)
    configure_output_mode_from_config(repo_root)
    return repo_root


def _snapshot_ignored_dirs(repo_root: Path) -> set[str]:
    """Return snapshot ignored directories from defaults plus config."""
    return session_snapshot_runtime_module._snapshot_ignored_dirs(repo_root)


def _snapshot_files(repo_root: Path, ignored_dirs: set[str]) -> list[Path]:
    """Collect snapshot files under repo root using ignore-dir filtering."""
    return session_snapshot_runtime_module._snapshot_files(
        repo_root,
        ignored_dirs,
    )


def _sha256_file(path: Path) -> str:
    """Return SHA-256 digest for one file path."""
    return session_snapshot_runtime_module._sha256_file(path)


def _hash_lines(lines: list[str]) -> str:
    """Return deterministic SHA-256 digest for normalized text lines."""
    return session_snapshot_runtime_module._hash_lines(lines)


def capture_current_numstat_snapshot(repo_root: Path) -> dict[str, str]:
    """Return deterministic filesystem-hash snapshot rows."""
    rows: dict[str, str] = {}
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        if rel in session_snapshot_runtime_module._SNAPSHOT_IGNORED_FILES:
            continue
        if any(
            rel == prefix.rstrip("/") or rel.startswith(prefix)
            for prefix in (
                session_snapshot_runtime_module._SNAPSHOT_IGNORED_PREFIXES
            )
        ):
            continue
        digest = _sha256_file(file_path)
        rows[rel] = f"{digest}\t{rel}"
    return rows


def capture_current_snapshot_paths(repo_root: Path) -> list[str]:
    """Return deterministic repo-relative path list from filesystem scan."""
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    return [path.relative_to(repo_root).as_posix() for path in files]


changed_numstat_paths = session_snapshot_runtime_module.changed_numstat_paths
diff_snapshot_paths = session_snapshot_runtime_module.diff_snapshot_paths
snapshot_signature = session_snapshot_runtime_module.snapshot_signature
normalize_snapshot_rows = (
    session_snapshot_runtime_module.normalize_snapshot_rows
)
snapshot_row_style = session_snapshot_runtime_module.snapshot_row_style


def snapshot_paths_changed_since(repo_root: Path, epoch: float) -> set[str]:
    """Return snapshot paths whose mtime is at or after the given epoch."""
    return session_snapshot_runtime_module.snapshot_paths_changed_since(
        repo_root,
        epoch,
    )


def session_delta_paths(
    repo_root: Path,
    start_snapshot: dict[str, str],
    current_snapshot: dict[str, str],
    *,
    session_start_epoch: float | None = None,
) -> set[str]:
    """Return session delta paths using shared snapshot comparison logic."""
    start_style = snapshot_row_style(start_snapshot)
    current_style = snapshot_row_style(current_snapshot)
    if start_style == "legacy_numstat" and current_style == "filesystem_hash":
        if session_start_epoch is None:
            raise ValueError(
                "Invalid gate status payload: `session_start_epoch` is "
                "required for legacy snapshot migration."
            )
        return snapshot_paths_changed_since(repo_root, session_start_epoch)
    return changed_numstat_paths(start_snapshot, current_snapshot)


capture_agents_section_hashes = (
    session_snapshot_runtime_module.capture_agents_section_hashes
)
document_exemption_fingerprint_for_path = (
    session_snapshot_runtime_module.document_exemption_fingerprint_for_path
)
capture_document_exemption_baseline = (
    session_snapshot_runtime_module.capture_document_exemption_baseline
)


def read_local_version(repo_root: Path) -> str | None:
    """Read the local devcovenant version from repo_root."""
    init_path = repo_root / "devcovenant" / "__init__.py"
    if not init_path.exists():
        return None
    pattern = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
    match = pattern.search(init_path.read_text(encoding="utf-8"))
    if match:
        return match.group(1).strip()
    return None


def warn_version_mismatch(repo_root: Path) -> None:
    """Warn when the local devcovenant version differs from the CLI."""
    local_version = read_local_version(repo_root)
    if not local_version:
        return
    if local_version != package_version:
        message = (
            "⚠️  Local DevCovenant version differs from CLI.\n"
            f"   Local: {local_version}\n"
            f"   CLI:   {package_version}\n"
            "Use the local version via `python3 -m devcovenant` or update."
        )
        runtime_print(message)


def run_bootstrap_registry_refresh(repo_root: Path) -> None:
    """Run lightweight registry refresh for command startup."""
    print_step("Refreshing local registry", "🔄")
    from devcovenant.core.flow.refresh import refresh_policy_registry

    refresh_exit = refresh_policy_registry(repo_root)
    if refresh_exit != 0:
        raise SystemExit("Registry refresh failed.")
    print_step("Registry refresh complete", "✅")


def _run_policy_runtime_action(
    repo_root: Path,
    *,
    policy_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    """Run one policy runtime action through engine dispatch."""
    from devcovenant.core.services.policy_engine import (
        run_policy_runtime_action,
    )

    return run_policy_runtime_action(
        repo_root,
        policy_id=policy_id,
        action=action,
        payload=payload or {},
    )


def resolve_managed_environment_for_stage(
    repo_root: Path,
    stage: str,
    *,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Resolve managed-environment state via policy-owned runtime action."""
    stage_token = str(stage or "").strip().lower()
    payload = {
        "stage": stage_token,
        "base_env": dict(base_env or os.environ),
    }
    result = _run_policy_runtime_action(
        repo_root,
        policy_id=_MANAGED_ENV_POLICY_ID,
        action=_MANAGED_ENV_ACTION_RESOLVE_STAGE,
        payload=payload,
    )
    if not isinstance(result, tuple) or len(result) != 2:
        raise ValueError(
            "managed-environment runtime action returned invalid payload."
        )
    env_raw, managed_python_raw = result
    if env_raw is None and managed_python_raw is None:
        return None, None
    if not isinstance(env_raw, dict):
        raise ValueError(
            "managed-environment runtime returned invalid environment payload."
        )
    if not isinstance(managed_python_raw, str):
        raise ValueError(
            "managed-environment runtime returned invalid interpreter payload."
        )
    return dict(env_raw), managed_python_raw


def resolve_managed_rerun_command_for_stage(
    repo_root: Path,
    stage: str,
    command_name: str,
    command_args: Sequence[str],
    *,
    managed_python: str | None = None,
    managed_root: str | None = None,
) -> list[str] | None:
    """Resolve one managed rerun command via policy runtime action."""
    stage_token = str(stage or "").strip().lower()
    result = _run_policy_runtime_action(
        repo_root,
        policy_id=_MANAGED_ENV_POLICY_ID,
        action=_MANAGED_ENV_ACTION_RESOLVE_RERUN,
        payload={
            "stage": stage_token,
            "command_name": command_name,
            "command_args": [str(token) for token in command_args],
            "managed_python": managed_python or "",
            "managed_root": managed_root or "",
        },
    )
    if result is None:
        return None
    if not isinstance(result, list):
        raise ValueError(
            "managed-environment rerun runtime returned invalid payload."
        )
    return [str(token) for token in result]


def _looks_like_python_launcher(token: str) -> bool:
    """Return True when token points to a Python launcher."""
    name = Path(str(token).strip()).name.lower()
    if name in {"py", "py.exe"}:
        return True
    return name.startswith("python")


def rewrite_command_for_managed_python(
    command: Sequence[str],
    managed_python: str | None,
) -> list[str]:
    """Replace command python launcher with managed interpreter path."""
    rewritten = [str(token) for token in command]
    if not rewritten or not managed_python:
        return rewritten
    if not _looks_like_python_launcher(rewritten[0]):
        return rewritten
    rewritten[0] = managed_python
    return rewritten


def rewrite_command_string_for_managed_python(
    command: str,
    managed_python: str | None,
) -> str:
    """Rewrite shell command string with managed Python launcher."""
    if not managed_python:
        return command
    tokens = shlex.split(command)
    rewritten = rewrite_command_for_managed_python(tokens, managed_python)
    return shlex.join(rewritten)


def registry_required_commands(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Read required commands from devflow-run-gates runtime action."""
    commands, _, _ = resolve_required_test_commands(repo_root)
    return commands


def _normalize_required_commands(
    raw_commands: object,
    *,
    field_name: str,
) -> list[tuple[str, list[str]]]:
    """Normalize one command metadata field into raw/tokens tuples."""
    if isinstance(raw_commands, str):
        raw_commands = [
            item.strip()
            for item in raw_commands.replace("\n", ",").split(",")
            if item.strip()
        ]
    elif isinstance(raw_commands, list):
        normalized: list[object] = []
        for command_entry in raw_commands:
            if isinstance(command_entry, str):
                normalized.extend(
                    entry.strip()
                    for entry in command_entry.replace("\n", ",").split(",")
                    if entry.strip()
                )
            else:
                normalized.append(command_entry)
        raw_commands = normalized
    else:
        raise ValueError(
            f"Invalid `{field_name}` payload: expected string or list."
        )

    commands: list[tuple[str, list[str]]] = []
    for entry in raw_commands:
        if isinstance(entry, list):
            raw = " ".join(
                str(part).strip() for part in entry if str(part).strip()
            )
        else:
            raw = str(entry).strip()
        if not raw:
            raise ValueError(f"Invalid `{field_name}` command: empty token.")
        tokens = shlex.split(raw)
        if not tokens:
            raise ValueError(f"Invalid `{field_name}` command: `{raw}`.")
        commands.append((raw, tokens))
    return commands


def resolve_required_test_commands(
    repo_root: Path,
    *,
    tests_mode: OutputMode | None = None,
) -> tuple[list[tuple[str, list[str]]], OutputMode, str]:
    """Resolve required test commands via devflow policy runtime action."""
    resolved_mode = tests_mode or resolve_tests_output_mode(repo_root)
    result = _run_policy_runtime_action(
        repo_root,
        policy_id=_DEVFLOW_POLICY_ID,
        action=_DEVFLOW_ACTION_RESOLVE_REQUIRED_COMMANDS,
        payload={"tests_output_mode": resolved_mode},
    )
    if not isinstance(result, dict):
        raise ValueError(
            "devflow-run-gates runtime action returned invalid payload."
        )
    source_field_raw = result.get("source_field", "required_commands")
    source_field = str(source_field_raw).strip() or "required_commands"
    commands_raw = result.get("commands")
    commands = _normalize_required_commands(
        commands_raw,
        field_name=source_field,
    )
    return commands, resolved_mode, source_field


def _run_command(
    command: Sequence[str],
    allow_codes: set[int] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Execute command and raise when it fails."""
    effective_mode = _TEST_COMMAND_OUTPUT_MODE or get_output_mode()
    command_env = _apply_repo_bytecode_env(dict(env or os.environ))
    result, _ = run_child_command_with_output_policy(
        command,
        channel="test_child",
        env=command_env,
        cwd=cwd,
        capture_combined_output=False,
        output_mode=effective_mode,
    )
    allowed = allow_codes or {0}
    if result.returncode not in allowed:
        output_plan = resolve_child_output_plan_for_channel(
            "test_child",
            output_mode=effective_mode,
        )
        if output_plan.child_output_suppressed:
            rendered = shlex.join([str(token) for token in command])
            runtime_print(
                "Test child command failed while child output is "
                f"suppressed by mode `{effective_mode}` "
                f"(exit {result.returncode}): {rendered}",
                file=sys.stderr,
            )
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def _parse_commands(command: str) -> list[str]:
    """Return an ordered command list parsed from a shell chain."""
    return [part.strip() for part in command.split("&&") if part.strip()]


def record_gate_status(
    repo_root: Path,
    command: str,
    notes: str = "",
    test_events: Iterable[Mapping[str, Any]] | None = None,
    tests_output_mode: str | None = None,
    tests_required_commands_key: str | None = None,
) -> None:
    """Record gate status payload under registry/local/gate_status.json."""
    status_path = registry_runtime_module.gate_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, object] = {}
    if status_path.exists():
        try:
            existing = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except json.JSONDecodeError:
            existing = {}

    now = _dt.datetime.now(tz=_dt.timezone.utc)
    run_snapshot = capture_current_numstat_snapshot(repo_root)
    active_session_id = str(existing.get("session_id", "")).strip()
    payload = {
        **existing,
        "last_run": now.isoformat(),
        "last_run_utc": now.isoformat(),
        "last_run_epoch": now.timestamp(),
        "last_run_snapshot": run_snapshot,
        "command": command.strip(),
        "commands": _parse_commands(command),
        "notes": notes.strip(),
    }
    if active_session_id:
        payload["last_run_session_id"] = active_session_id
    else:
        payload.pop("last_run_session_id", None)
    if test_events:
        payload["test_events"] = [dict(entry) for entry in test_events]
    else:
        payload.pop("test_events", None)
    if tests_output_mode:
        payload["tests_output_mode"] = _normalize_output_mode(
            tests_output_mode
        )
    else:
        payload.pop("tests_output_mode", None)
    token = str(tests_required_commands_key or "").strip()
    if token:
        payload["tests_required_commands_key"] = token
    else:
        payload.pop("tests_required_commands_key", None)
    # Purge legacy gate-status keys instead of carrying them forward.
    payload.pop("sha", None)
    payload.pop("tests_coverage_evidence", None)
    payload.pop("changelog_start_diff_numstat", None)
    payload.pop("changelog_start_exemption_fingerprints", None)
    payload.pop("cache_enabled", None)
    payload.pop("cache_control_env", None)
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime_print(
        f"Recorded gate status at {payload['last_run']} "
        f"for command `{payload['command']}`.",
        verbose_only=True,
    )


class _TestCommandProgress:
    """Track required test commands with sparse deterministic console lines."""

    def __init__(self, total: int, output_mode: OutputMode):
        """Initialize counter state for sparse normal-mode progress lines."""
        self.total = total
        self._count = 0
        self._normal_mode = output_mode == "normal"
        self._current_description = ""
        self._completed_descriptions: list[str] = []

    def __enter__(self):
        """Return self for context-manager parity."""
        return self

    def describe(self, description: str) -> None:
        """Store the current command description for deterministic updates."""
        self._current_description = str(description)

    def start_step(self, description: str) -> None:
        """Emit a deterministic start marker so long runs show liveness."""
        if not self._normal_mode:
            return
        runtime_print(f"▶ [{self._count + 1}/{self.total}] {description}")

    def complete_step(self, description: str) -> None:
        """Advance state and keep normal-mode progress output non-duplicate."""
        self._count += 1
        self._completed_descriptions.append(str(description))
        if self._normal_mode:
            # Normal mode already emitted the start marker and heartbeats.
            # Keep completion silent to avoid duplicate progress lines.
            return

    def fail_step(
        self,
        description: str,
        exit_code: int | None = None,
    ) -> None:
        """Emit a deterministic failure marker in normal mode."""
        if not self._normal_mode:
            return
        code_text = "" if exit_code is None else f" (exit {int(exit_code)})"
        runtime_print(
            f"[{self._count + 1}/{self.total}] "
            f"FAILED: {description}{code_text}"
        )

    def close(self) -> None:
        """Preserve context-manager API; no bar resources are allocated."""
        return None

    def __exit__(self, exc_type, exc, exc_tb):
        """Preserve context-manager semantics."""
        self.close()


def _emit_test_runtime_message(
    message: str,
    tests_output_mode: OutputMode,
    *,
    verbose_only: bool = False,
) -> None:
    """Emit one test-runtime line according to the tests output mode."""
    if verbose_only and tests_output_mode != "verbose":
        return
    runtime_print(message)


def run_and_record_tests(repo_root: Path, notes: str = "") -> int:
    """Run required test commands and record their status."""
    global _TEST_COMMAND_OUTPUT_MODE, _TEST_COMMAND_LABEL
    configure_repo_pycache_prefix(repo_root)
    tests_output_mode = resolve_tests_output_mode(repo_root)
    try:
        commands, resolved_mode, source_field = resolve_required_test_commands(
            repo_root,
            tests_mode=tests_output_mode,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not commands:
        raise SystemExit(
            "No required test commands are configured for "
            f"`engine.tests_output_mode: {resolved_mode}`. Set "
            "`devflow-run-gates.required_commands` in active profile "
            "overlays."
        )
    try:
        managed_env, managed_python = resolve_managed_environment_for_stage(
            repo_root,
            "test",
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # Clear any stale warnings from prior calls in this process.
    event_runtime_module.consume_test_event_adapter_warnings()
    adapters = event_runtime_module.load_test_event_adapters(repo_root)
    adapter_warnings = (
        event_runtime_module.consume_test_event_adapter_warnings()
    )
    for warning in adapter_warnings:
        runtime_print(
            f"WARNING: test-event adapter load issue: {warning}",
            file=sys.stderr,
        )

    event_manager = event_runtime_module.TestEventManager(adapters)
    test_run_started = _dt.datetime.now(tz=_dt.timezone.utc)
    first_failed_command = ""
    first_failed_exit_code: int | None = None
    passed_commands = 0
    failed_commands = 0

    merge_active_run_log_metadata(
        {
            "tests_output_mode": resolved_mode,
            "tests_source_field": source_field,
            "normal_console_mode": resolved_mode == "normal",
            "quiet_console_mode": resolved_mode == "quiet",
            "full_output_in_logs": True,
            "console_output_policy": (
                "test output mode controls console detail; run logs retain "
                "full child output"
            ),
        }
    )
    if resolved_mode == "normal":
        _emit_test_runtime_message(
            "Please wait for test commands to execute. Full output is "
            "available in run logs.",
            resolved_mode,
        )
        emit_active_run_log_pointer(once=True)

    with _TestCommandProgress(
        len(commands),
        output_mode=resolved_mode,
    ) as progress:
        for raw, command in commands:
            command_tokens = rewrite_command_for_managed_python(
                command,
                managed_python,
            )
            command_str = " ".join(command_tokens)
            progress.describe(raw)
            progress.start_step(raw)
            _emit_test_runtime_message(
                f"Running: {command_str}",
                resolved_mode,
                verbose_only=True,
            )
            started = _dt.datetime.now(tz=_dt.timezone.utc)
            try:
                run_kwargs: dict[str, Any] = {"allow_codes": {0}}
                if managed_env is not None:
                    run_kwargs["env"] = managed_env
                    run_kwargs["cwd"] = repo_root
                previous_mode = _TEST_COMMAND_OUTPUT_MODE
                previous_label = _TEST_COMMAND_LABEL
                if resolved_mode == "normal":
                    _TEST_COMMAND_OUTPUT_MODE = "normal"
                    _TEST_COMMAND_LABEL = raw
                else:
                    _TEST_COMMAND_OUTPUT_MODE = None
                    _TEST_COMMAND_LABEL = ""
                try:
                    result = _run_command(command_tokens, **run_kwargs)
                finally:
                    _TEST_COMMAND_OUTPUT_MODE = previous_mode
                    _TEST_COMMAND_LABEL = previous_label
            except subprocess.CalledProcessError as exc:
                finished = _dt.datetime.now(tz=_dt.timezone.utc)
                failed_commands += 1
                if not first_failed_command:
                    first_failed_command = command_str
                    first_failed_exit_code = int(exc.returncode or 1)
                event_manager.record_command(
                    command=command_tokens,
                    command_str=command_str,
                    started=started,
                    finished=finished,
                    exit_code=int(exc.returncode or 1),
                )
                progress.fail_step(raw, int(exc.returncode or 1))
                merge_active_run_log_metadata(
                    _build_test_run_metadata_with_profile(
                        commands=commands,
                        events=event_manager.events,
                        tests_output_mode=resolved_mode,
                        source_field=source_field,
                        started=test_run_started,
                        finished=finished,
                        first_failed_command=first_failed_command,
                        first_failed_exit_code=first_failed_exit_code,
                        passed_commands=passed_commands,
                        failed_commands=failed_commands,
                    )
                )
                raise
            finished = _dt.datetime.now(tz=_dt.timezone.utc)
            passed_commands += 1
            event_manager.record_command(
                command=command_tokens,
                command_str=command_str,
                started=started,
                finished=finished,
                exit_code=result.returncode,
            )
            progress.complete_step(raw)

    command_str = " && ".join(raw for raw, _ in commands)
    _emit_test_runtime_message(
        "Recording gate status…",
        resolved_mode,
        verbose_only=True,
    )
    record_gate_status(
        repo_root,
        command_str,
        notes=notes,
        test_events=[event.to_dict() for event in event_manager.events],
        tests_output_mode=resolved_mode,
        tests_required_commands_key=source_field,
    )
    merge_active_run_log_metadata(
        _build_test_run_metadata_with_profile(
            commands=commands,
            events=event_manager.events,
            tests_output_mode=resolved_mode,
            source_field=source_field,
            started=test_run_started,
            finished=_dt.datetime.now(tz=_dt.timezone.utc),
            first_failed_command=first_failed_command,
            first_failed_exit_code=first_failed_exit_code,
            passed_commands=passed_commands,
            failed_commands=failed_commands,
        )
    )
    return 0


def _build_test_run_metadata_with_profile(
    *,
    commands: Sequence[tuple[str, Sequence[str]]],
    events: Sequence[Any],
    tests_output_mode: OutputMode,
    source_field: str,
    started: _dt.datetime,
    finished: _dt.datetime,
    first_failed_command: str,
    first_failed_exit_code: int | None,
    passed_commands: int,
    failed_commands: int,
) -> dict[str, Any]:
    """Build run metadata bundle with summary fields and profile artifacts."""
    summary_payload = _build_test_run_summary_metadata(
        commands=commands,
        events=events,
        tests_output_mode=tests_output_mode,
        source_field=source_field,
        started=started,
        finished=finished,
        first_failed_command=first_failed_command,
        first_failed_exit_code=first_failed_exit_code,
        passed_commands=passed_commands,
        failed_commands=failed_commands,
    )
    profile_payload, profile_artifacts = (
        _build_and_write_test_profile_artifacts(
            commands=commands,
            events=events,
            tests_output_mode=tests_output_mode,
            source_field=source_field,
            started=started,
            finished=finished,
        )
    )
    return {
        "test_summary": summary_payload,
        "test_profile": profile_payload,
        "test_profile_artifacts": profile_artifacts,
    }


def _build_and_write_test_profile_artifacts(
    *,
    commands: Sequence[tuple[str, Sequence[str]]],
    events: Sequence[Any],
    tests_output_mode: OutputMode,
    source_field: str,
    started: _dt.datetime,
    finished: _dt.datetime,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build and persist per-run test profile artifacts when run logs exist."""
    event_rows: list[dict[str, Any]] = []
    for event in events:
        to_dict = getattr(event, "to_dict", None)
        if not callable(to_dict):
            continue
        payload = to_dict()
        if isinstance(payload, dict):
            event_rows.append(dict(payload))
    profile_payload = (
        test_profile_runtime_module.build_test_runtime_profile_payload(
            commands=commands,
            events=event_rows,
            tests_output_mode=tests_output_mode,
            source_field=source_field,
            started=started,
            finished=finished,
        )
    )
    profile_text = (
        test_profile_runtime_module.render_test_runtime_profile_text(
            profile_payload
        )
    )
    context = get_active_run_log_context()
    if context is None:
        return profile_payload, {}
    run_dir = context.require_paths().run_dir
    profile_json_path = run_dir / "test_profile.json"
    profile_txt_path = run_dir / "test_profile.txt"
    profile_json_path.write_text(
        json.dumps(profile_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    profile_txt_path.write_text(profile_text, encoding="utf-8")
    artifacts = {
        "test_profile_json": _run_log_repo_relative(
            context.repo_root,
            profile_json_path,
        ),
        "test_profile_txt": _run_log_repo_relative(
            context.repo_root,
            profile_txt_path,
        ),
    }
    return profile_payload, artifacts


def _build_test_run_summary_metadata(
    *,
    commands: Sequence[tuple[str, Sequence[str]]],
    events: Sequence[Any],
    tests_output_mode: OutputMode,
    source_field: str,
    started: _dt.datetime,
    finished: _dt.datetime,
    first_failed_command: str,
    first_failed_exit_code: int | None,
    passed_commands: int,
    failed_commands: int,
) -> dict[str, Any]:
    """Build structured summary metadata for `devcovenant test` runs."""
    total_commands = len(commands)
    duration_seconds = round(
        max(
            0.0,
            (finished - started).total_seconds(),
        ),
        3,
    )
    event_rows: list[dict[str, Any]] = []
    for event in events:
        to_dict = getattr(event, "to_dict", None)
        if callable(to_dict):
            payload = to_dict()
            if isinstance(payload, dict):
                event_rows.append(dict(payload))
    duration_values: list[float] = []
    command_durations: list[dict[str, Any]] = []
    for index, (raw_command, command_tokens) in enumerate(commands, start=1):
        event_payload = (
            event_rows[index - 1] if index <= len(event_rows) else {}
        )
        metadata = (
            event_payload.get("metadata")
            if isinstance(event_payload.get("metadata"), Mapping)
            else {}
        )
        event_command = event_payload.get("command")
        if isinstance(event_command, list):
            command_text = " ".join(str(token) for token in event_command)
        else:
            command_text = " ".join(str(token) for token in command_tokens)
        duration_raw = event_payload.get("duration_seconds")
        duration_value: float | None = None
        try:
            duration_value = round(max(0.0, float(duration_raw)), 6)
        except (TypeError, ValueError):
            duration_value = None
        if duration_value is not None:
            duration_values.append(duration_value)
        command_durations.append(
            {
                "index": index,
                "raw_command": str(raw_command),
                "command": command_text.strip(),
                "status": str(event_payload.get("status", "")).strip(),
                "duration_seconds": duration_value,
                "started_at": str(event_payload.get("started_at", "")).strip(),
                "finished_at": str(
                    event_payload.get("finished_at", "")
                ).strip(),
                "exit_code": metadata.get("exit_code"),
            }
        )
    min_duration = min(duration_values) if duration_values else None
    max_duration = max(duration_values) if duration_values else None
    avg_duration = (
        round(sum(duration_values) / len(duration_values), 6)
        if duration_values
        else None
    )
    return {
        "command_name": "test",
        "tests_output_mode": tests_output_mode,
        "tests_required_commands_key": source_field,
        "normal_console_flood_suppressed": tests_output_mode
        in {"normal", "quiet"},
        "normal_console_streaming": tests_output_mode == "verbose",
        "quiet_console_mode": tests_output_mode == "quiet",
        "full_output_in_logs": True,
        "total_commands": total_commands,
        "passed_commands": passed_commands,
        "failed_commands": failed_commands,
        "duration_seconds": duration_seconds,
        "duration_breakdown_version": "1.0",
        "duration_events_count": len(duration_values),
        "duration_seconds_min_command": min_duration,
        "duration_seconds_max_command": max_duration,
        "duration_seconds_avg_command": avg_duration,
        "first_failed_command": first_failed_command or "",
        "first_failed_exit_code": first_failed_exit_code,
        "failure_hint": (
            "See tail.txt and stdout.log/stderr.log in the run folder."
            if failed_commands
            else ""
        ),
        "commands": [raw for raw, _ in commands],
        "command_durations": command_durations,
        "events": event_rows,
    }
