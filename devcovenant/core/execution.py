"""Execution helpers for command entrypoints and test orchestration."""

from __future__ import annotations

import datetime as _dt
import json
import re
import shlex
import subprocess
from pathlib import Path

from devcovenant import __version__ as package_version
from devcovenant.core import manifest as manifest_module

DEFAULT_COMMANDS = [
    ["python3", "-m", "unittest", "discover", "-v"],
    ["pytest"],
]
DEFAULT_COMMAND_STRINGS = ["python3 -m unittest discover -v", "pytest"]


def print_banner(title: str, emoji: str) -> None:
    """Print a readable stage banner."""
    print("\n" + "=" * 70)
    print(f"{emoji} {title}")
    print("=" * 70)


def print_step(message: str, emoji: str = "•") -> None:
    """Print a short, single-line status step."""
    print(f"{emoji} {message}")


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
    return repo_root


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
        print(message)


def run_bootstrap_registry_refresh(repo_root: Path) -> None:
    """Run lightweight registry refresh for command startup."""
    print_step("Refreshing local registry", "🔄")
    try:
        from devcovenant.core.repo_refresh import refresh_policy_registry

        refresh_policy_registry(repo_root, skip_freeze=True)
        print_step("Registry refresh complete", "✅")
    except Exception as exc:  # pragma: no cover - defensive
        print_step(f"Registry refresh skipped ({exc})", "⚠️")


def registry_required_commands(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Read required commands from devflow-run-gates metadata."""
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
        normalized = _prioritize_python_unit_then_pytest(commands)
        return normalized
    return list(zip(DEFAULT_COMMAND_STRINGS, DEFAULT_COMMANDS))


def _prioritize_python_unit_then_pytest(
    commands: list[tuple[str, list[str]]],
) -> list[tuple[str, list[str]]]:
    """Run unittest before pytest when both are present."""
    unittest_entry: tuple[str, list[str]] | None = None
    pytest_entry: tuple[str, list[str]] | None = None
    ordered: list[tuple[str, list[str]]] = []

    for raw, tokens in commands:
        token_str = " ".join(tokens).strip().lower()
        if token_str == "python3 -m unittest discover -v":
            unittest_entry = (raw, tokens)
            continue
        if token_str == "pytest":
            pytest_entry = (raw, tokens)
            continue
        ordered.append((raw, tokens))

    if unittest_entry and pytest_entry:
        return [unittest_entry, pytest_entry, *ordered]
    if unittest_entry:
        return [unittest_entry, *ordered]
    if pytest_entry:
        return [pytest_entry, *ordered]
    return commands


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
        if command[:4] == ["python3", "-m", "unittest", "discover"]:
            allow_codes.add(5)
        _run_command(command, allow_codes=allow_codes)

    command_str = " && ".join(raw for raw, _ in commands)
    print("Recording test status…")
    record_test_status(repo_root, command_str, notes=notes)
    return 0
