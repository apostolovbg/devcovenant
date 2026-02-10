"""Test execution and status recording helpers."""

from __future__ import annotations

import datetime as _dt
import json
import shlex
import subprocess
from pathlib import Path

from devcovenant.core import manifest as manifest_module

DEFAULT_COMMANDS = [
    ["pytest"],
    ["python3", "-m", "unittest", "discover"],
]
DEFAULT_COMMAND_STRINGS = ["pytest", "python3 -m unittest discover"]


def registry_required_commands(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Read required commands for devflow-run-gates from the policy registry."""
    registry_path = manifest_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        return list(zip(DEFAULT_COMMAND_STRINGS, DEFAULT_COMMANDS))

    try:
        import yaml

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
    """Execute command and raise when it fails."""
    result = subprocess.run(command, check=False)
    allowed = allow_codes or {0}
    if result.returncode not in allowed:
        raise subprocess.CalledProcessError(result.returncode, command)


def _parse_commands(command: str) -> list[str]:
    """Return an ordered command list parsed from a shell chain."""
    return [part.strip() for part in command.split("&&") if part.strip()]


def _current_sha(repo_root: Path) -> str:
    """Return current git commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def record_test_status(repo_root: Path, command: str, notes: str = "") -> None:
    """Record test status payload under registry/local/test_status.json."""
    status_path = manifest_module.test_status_path(repo_root)
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
    payload = {
        **existing,
        "last_run": now.isoformat(),
        "last_run_utc": now.isoformat(),
        "last_run_epoch": now.timestamp(),
        "command": command.strip(),
        "commands": _parse_commands(command),
        "sha": _current_sha(repo_root),
        "notes": notes.strip(),
    }
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Recorded test status at {payload['last_run']} "
        f"for command `{payload['command']}`."
    )


def run_and_record_tests(repo_root: Path, notes: str = "") -> int:
    """Run required test commands and record their status."""
    commands = registry_required_commands(repo_root)

    for raw, command in commands:
        print(f"Running: {' '.join(command)}")
        allow_codes = {0}
        if command[1:] == ["-m", "unittest", "discover"]:
            allow_codes.add(5)
        _run_command(command, allow_codes=allow_codes)

    command_str = " && ".join(raw for raw, _ in commands)
    print("Recording test status…")
    record_test_status(repo_root, command_str, notes=notes)
    return 0
