#!/usr/bin/env python3
"""Run test suites and update the test status registry."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_COMMANDS = [
    ["pytest"],
    ["python3", "-m", "unittest", "discover"],
]


DEFAULT_COMMAND_STRINGS = ["pytest", "python3 -m unittest discover"]


def _registry_required_commands(
    repo_root: Path,
) -> list[tuple[str, list[str]]]:
    """Read required commands for devflow-run-gates from the policy registry.

    Returns a list of argv lists. Falls back to DEFAULT_COMMANDS when the
    registry is missing or the entry is absent.
    """

    registry_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    if not registry_path.exists():
        return list(zip(DEFAULT_COMMAND_STRINGS, DEFAULT_COMMANDS))

    try:
        import yaml  # deferred import to keep startup cheap

        registry_data = (
            yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        )
    except Exception:
        return list(zip(DEFAULT_COMMAND_STRINGS, DEFAULT_COMMANDS))

    gates = (registry_data.get("policies") or {}).get(
        "devflow-run-gates"
    ) or {}
    metadata_map = gates.get("metadata") or {}
    raw_commands = metadata_map.get("required_commands") or []
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
        raw_commands = []

    commands: list[tuple[str, list[str]]] = []
    for entry in raw_commands:
        try:
            import shlex

            if isinstance(entry, list):
                raw = " ".join(
                    str(part).strip() for part in entry if str(part).strip()
                )
            else:
                raw = str(entry).strip()
            tokens = shlex.split(raw)
        except Exception:
            raw, tokens = "", []
        if raw and tokens:
            commands.append((raw, tokens))

    if commands:
        return commands

    return list(zip(DEFAULT_COMMAND_STRINGS, DEFAULT_COMMANDS))


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

    repo_root = Path(__file__).resolve().parents[2]
    commands = _registry_required_commands(repo_root)

    for raw, command in commands:
        print(f"Running: {' '.join(command)}")
        allow_codes = {0}
        if command[1:] == ["-m", "unittest", "discover"]:
            allow_codes.add(5)
        _run_command(command, allow_codes=allow_codes)

    command_str = " && ".join(raw for raw, _ in commands)
    print("Recording test status…")
    update_cmd = [
        sys.executable,
        "-m",
        "devcovenant.update_test_status",
        "--command",
        command_str,
    ]
    if args.notes:
        update_cmd.extend(["--notes", args.notes])
    _run_command(update_cmd)


if __name__ == "__main__":
    main()
