#!/usr/bin/env python3
"""Record the latest test run in the status registry."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
from pathlib import Path

from devcovenant.core import manifest as manifest_module


def _utc_now() -> _dt.datetime:
    """Return the current UTC time."""
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _parse_commands(command: str) -> list[str]:
    """Return an ordered list of commands parsed from a shell string."""
    return [part.strip() for part in command.split("&&") if part.strip()]


def _current_sha(repo_root: Path) -> str:
    """Return the current Git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise SystemExit(f"Unable to read git SHA: {exc}") from exc
    return result.stdout.strip()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update test_status.json after running tests."
    )
    parser.add_argument(
        "--command",
        required=True,
        help=(
            "Command used to run the suites "
            '(e.g., "pytest && python -m unittest discover").'
        ),
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes about the environment or deviations.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    status_path = manifest_module.test_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    now = _utc_now()
    command = args.command.strip()
    existing: dict[str, object] = {}
    if status_path.exists():
        try:
            existing = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except json.JSONDecodeError:
            existing = {}

    payload = {
        **existing,
        "last_run": now.isoformat(),
        "last_run_utc": now.isoformat(),
        "last_run_epoch": now.timestamp(),
        "command": command,
        "commands": _parse_commands(command),
        "sha": _current_sha(repo_root),
        "notes": args.notes.strip(),
    }
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Recorded test status at {payload['last_run']} "
        f"for command `{payload['command']}`."
    )


if __name__ == "__main__":
    main()
