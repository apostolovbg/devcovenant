"""Gate execution helpers for DevCovenant gate --start/--end."""

from __future__ import annotations

import datetime as _dt
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from devcovenant.core import manifest as manifest_module


def _utc_now() -> _dt.datetime:
    """Return the current UTC time."""
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _load_status(path: Path) -> dict:
    """Load the current status payload, returning an empty dict on failure."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _run_command(command: str, env: dict[str, str] | None = None) -> None:
    """Execute a shell command string and raise on failure."""
    parts = shlex.split(command)
    if not parts:
        raise SystemExit("Pre-commit command is empty.")
    try:
        subprocess.run(parts, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        rendered = " ".join(exc.cmd) if exc.cmd else command
        print(
            f"Pre-commit command failed with exit code {exc.returncode}:"
            f" {rendered}",
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode)


def _git_diff(repo_root: Path) -> str:
    """Return current git diff output, or empty string when unavailable."""
    try:
        result = subprocess.run(
            ["git", "diff", "--binary"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _run_tests(repo_root: Path, env: dict[str, str]) -> None:
    """Run repository tests through the canonical test command."""
    command = [sys.executable, "-m", "devcovenant", "test"]
    subprocess.run(command, check=True, env=env, cwd=repo_root)


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

    status_path = manifest_module.test_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DEVCOV_DEVFLOW_PHASE"] = phase
    start_ts = _utc_now() if phase == "start" else None
    attempt = 0
    max_attempts = 5
    force_tests = False

    while True:
        diff_before = _git_diff(repo_root)
        _run_command(command, env=env)
        diff_after_hooks = _git_diff(repo_root)
        hooks_changed = diff_after_hooks != diff_before
        tests_changed = False

        if phase == "end" and (hooks_changed or force_tests):
            if hooks_changed:
                print(
                    "Detected changes after pre-commit; rerunning tests "
                    "to validate the updated tree."
                )
            elif force_tests:
                print("Rerunning tests to validate prior fixer changes.")
            _run_tests(repo_root, env)
            diff_after_tests = _git_diff(repo_root)
            tests_changed = diff_after_tests != diff_after_hooks

        if phase == "end" and (hooks_changed or tests_changed):
            attempt += 1
            if attempt >= max_attempts:
                print(
                    "Maximum rerun attempts reached; tree still dirty. "
                    "Failing end gate."
                )
                return 1
            if tests_changed:
                print(
                    "Detected changes after tests; rerunning hooks and tests."
                )
                force_tests = True
            else:
                force_tests = False
            print("Rerunning pre-commit hooks to verify clean tree...")
            continue
        break

    payload = _load_status(status_path)
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
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Recorded {prefix} at {payload[f'{prefix}_utc']} "
        f"for command `{payload[f'{prefix}_command']}`."
    )
    return 0
