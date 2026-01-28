#!/usr/bin/env python3
"""Run pre-commit and record the run in the test status registry."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


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
    """Execute the command string via subprocess."""
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
    """Return the current git diff, or an empty string when unavailable."""
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
    """Run the repository test runner."""
    command = [sys.executable, str(repo_root / "tools" / "run_tests.py")]
    subprocess.run(command, check=True, env=env)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run pre-commit and record it as a start/end marker."
    )
    parser.add_argument(
        "--phase",
        choices=("start", "end"),
        required=True,
        help="Record the pre-commit run as the session start or end.",
    )
    parser.add_argument(
        "--command",
        default="pre-commit run --all-files",
        help="Pre-commit command to execute and record.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes recorded alongside the pre-commit run.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    status_path = (
        repo_root / "devcovenant" / "registry" / "local" / "test_status.json"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DEVCOV_DEVFLOW_PHASE"] = args.phase
    start_ts = _utc_now() if args.phase == "start" else None
    diff_before = _git_diff(repo_root)
    _run_command(args.command, env=env)
    diff_after = _git_diff(repo_root)
    if args.phase == "end" and diff_before != diff_after:
        _run_tests(repo_root, env)

    payload = _load_status(status_path)
    now = _utc_now()
    prefix = f"pre_commit_{args.phase}"
    if start_ts is not None:
        payload[f"{prefix}_utc"] = start_ts.isoformat()
        payload[f"{prefix}_epoch"] = start_ts.timestamp()
    else:
        payload[f"{prefix}_utc"] = now.isoformat()
        payload[f"{prefix}_epoch"] = now.timestamp()
    payload[f"{prefix}_command"] = args.command.strip()
    payload[f"{prefix}_notes"] = args.notes.strip()
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Recorded {prefix} at {payload[f'{prefix}_utc']} "
        f"for command `{payload[f'{prefix}_command']}`."
    )


if __name__ == "__main__":
    main()
