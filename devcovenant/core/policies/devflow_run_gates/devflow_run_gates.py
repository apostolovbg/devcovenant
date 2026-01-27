"""Session gates: pre-commit at start/end and tests after code edits."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Iterable, List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation

_DEFAULT_STATUS = (
    Path("devcovenant") / "registry" / "local" / "test_status.json"
)
_DEFAULT_COMMANDS = ["pytest", "python -m unittest discover"]
_DEFAULT_PRE_COMMIT_COMMAND = "pre-commit run --all-files"
_DEFAULT_PRE_COMMIT_START_KEY = "pre_commit_start_epoch"
_DEFAULT_PRE_COMMIT_END_KEY = "pre_commit_end_epoch"
_DEFAULT_PRE_COMMIT_START_COMMAND_KEY = "pre_commit_start_command"
_DEFAULT_PRE_COMMIT_END_COMMAND_KEY = "pre_commit_end_command"


def _git_changed_files(repo_root: Path) -> list[Path]:
    """Return changed files from git status, if available."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ")[-1]
        paths.append(repo_root / path_part)
    return paths


def _resolve_status_path(policy: "DevflowRunGates") -> Path:
    """Return the configured test status path relative to the repository."""
    raw = policy.get_option("test_status_file", str(_DEFAULT_STATUS))
    return Path(raw)


def _code_extensions(policy: "DevflowRunGates") -> set[str] | None:
    """Return the set of extensions considered code for gating purposes."""
    entries_option = policy.get_option("code_extensions")
    if isinstance(entries_option, str):
        entries = [entries_option]
    else:
        entries = list(entries_option or [])
    return {
        entry.strip().lower()
        for entry in entries
        if isinstance(entry, str) and entry.strip()
    }


def _required_commands(policy: "DevflowRunGates") -> list[str]:
    """Return ordered commands that must appear in the status file."""
    commands_option = policy.get_option(
        "required_commands", list(_DEFAULT_COMMANDS)
    )
    if isinstance(commands_option, str):
        commands = [commands_option]
    else:
        commands = list(commands_option or [])
    cleaned = [
        command.strip()
        for command in commands
        if isinstance(command, str) and command.strip()
    ]
    return [command.lower() for command in cleaned]


def _load_test_status(status_file: Path) -> dict | None:
    """Return the parsed test status file, or None when missing/invalid."""

    if not status_file.is_file():
        return None
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_code_mtime(
    files: Iterable[Path], extensions: set[str] | None
) -> float:
    """Return the newest modification time among code-like files."""

    latest = 0.0
    for path in files:
        if extensions and path.suffix.lower() not in extensions:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        latest = max(latest, stat.st_mtime)
    return latest


def _earliest_code_mtime(
    files: Iterable[Path], extensions: set[str] | None
) -> float:
    """Return the oldest modification time among code-like files."""

    earliest: float | None = None
    for path in files:
        if extensions and path.suffix.lower() not in extensions:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        if earliest is None:
            earliest = stat.st_mtime
        else:
            earliest = min(earliest, stat.st_mtime)
    return earliest or 0.0


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
    """Return the key name used for pre-commit timestamps/commands."""
    option_value = policy.get_option(key, default)
    return str(option_value).strip() or default


class DevflowRunGates(PolicyCheck):
    """Ensure hooks and tests run around every task."""

    @property
    def policy_id(self) -> str:
        """Return the policy identifier."""

        return "devflow-run-gates"

    def check(self, ctx: CheckContext) -> List[Violation]:
        """Validate test recency after code changes; pre-commit is active."""

        violations: List[Violation] = []
        repo_root = ctx.repo_root
        status_rel = _resolve_status_path(self)
        extensions = _code_extensions(self)
        required_commands = _required_commands(self)

        files = list(ctx.changed_files or [])
        if ctx.mode == "pre-commit":
            git_files = _git_changed_files(repo_root)
            if git_files:
                files = git_files
        status_abs = (repo_root / status_rel).resolve()
        files = [path for path in files if path.resolve() != status_abs]

        code_mtime = _latest_code_mtime(files, extensions)
        if code_mtime == 0.0:
            return violations
        earliest_code_mtime = _earliest_code_mtime(files, extensions)

        phase = os.environ.get("DEVCOV_DEVFLOW_PHASE", "").strip().lower()
        if phase == "start":
            return violations

        status = _load_test_status(repo_root / status_rel)
        if not status:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Code changed but "
                        "devcovenant/registry/local/test_status.json is missing; "
                        "run `python3 tools/run_tests.py` before replying."
                    ),
                )
            )
            return violations

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

        if require_start:
            try:
                start_ts = float(status.get(start_epoch_key) or 0.0)
            except Exception:
                start_ts = 0.0
            if start_ts <= 0.0:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session start pre-commit run is missing. Run "
                            "`python3 tools/run_pre_commit.py --phase start` "
                            "before editing code."
                        ),
                    )
                )
            elif earliest_code_mtime and start_ts > earliest_code_mtime:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session start pre-commit run occurred after "
                            "code changes. Run `python3 tools/run_pre_commit."
                            "py --phase start` before editing code and rerun "
                            "after resetting the session."
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
                            "Re-run the start gate with "
                            "`python3 tools/run_pre_commit.py --phase start`."
                        ),
                    )
                )

        if require_end:
            try:
                end_ts = float(status.get(end_epoch_key) or 0.0)
            except Exception:
                end_ts = 0.0
            if end_ts <= 0.0:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session end pre-commit run is missing. Run "
                            "`python3 tools/run_pre_commit.py --phase end` "
                            "before replying."
                        ),
                    )
                )
            elif end_ts < code_mtime:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=status_rel,
                        message=(
                            "Session end pre-commit run predates code "
                            "changes. Run `python3 tools/run_pre_commit.py "
                            "--phase end` after edits complete."
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
                            "Re-run the end gate with "
                            "`python3 tools/run_pre_commit.py --phase end`."
                        ),
                    )
                )

        last_run = status.get("last_run_utc") or ""
        try:
            last_ts = float(status.get("last_run_epoch") or 0.0)
        except Exception:
            last_ts = 0.0

        commands: list[str] = status.get("commands") or []
        commands_lower = " ".join(commands).lower()

        missing = [
            command
            for command in required_commands
            if command not in commands_lower
        ]

        if missing:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Latest recorded test status is missing required "
                        f"commands: {', '.join(missing)}. Run "
                        "`python3 tools/run_tests.py` before replying."
                    ),
                )
            )
        elif last_ts < code_mtime:
            when = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(code_mtime))
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_rel,
                    message=(
                        "Code changed after the last recorded test run "
                        f"({last_run or 'unknown'}); rerun "
                        "`python3 tools/run_tests.py` so tests post-date the "
                        f"newest code change (latest code mtime: {when}Z)."
                    ),
                )
            )

        return violations
