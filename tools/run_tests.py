#!/usr/bin/env python3
"""Run test suites and update the test status registry."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_COMMANDS = [
    ["pytest"],
    [sys.executable, "-m", "unittest", "discover"],
]


def _run_command(
    command: list[str], allow_codes: set[int] | None = None
) -> None:
    """Execute *command* and raise when it fails."""
    result = subprocess.run(command, check=False)
    allowed = allow_codes or {0}
    if result.returncode not in allowed:
        raise subprocess.CalledProcessError(result.returncode, command)


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Run the project test suites and record their status."
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes recorded alongside the test status entry.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    for command in DEFAULT_COMMANDS:
        print(f"Running: {' '.join(command)}")
        allow_codes = {0}
        if command[1:] == ["-m", "unittest", "discover"]:
            allow_codes.add(5)
        _run_command(command, allow_codes=allow_codes)

    command_str = "pytest && python -m unittest discover"
    print("Recording test status…")
    update_cmd = [
        sys.executable,
        str(repo_root / "tools" / "update_test_status.py"),
        "--command",
        command_str,
    ]
    if args.notes:
        update_cmd.extend(["--notes", args.notes])
    _run_command(update_cmd)


if __name__ == "__main__":
    main()
