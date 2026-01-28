"""Tests for the DevFlow run gates policy."""

from __future__ import annotations

import json
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.devflow_run_gates import devflow_run_gates

DevflowRunGates = devflow_run_gates.DevflowRunGates


def make_ctx(
    tmp_path: Path,
    changed: list[str],
    config: dict | None = None,
) -> CheckContext:
    """Build a test context with the specified changed files."""
    files = [tmp_path / path for path in changed]
    for file_path in files:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# code", encoding="utf-8")
    return CheckContext(
        repo_root=tmp_path,
        changed_files=files,
        all_files=files,
        mode="pre-commit",
        config=config or {},
    )


def test_requires_tests_for_code_change(tmp_path: Path) -> None:
    """Missing test status should trigger a violation."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    check = DevflowRunGates()
    violations = check.check(ctx)
    assert violations, "missing test_status should trigger a violation"
    status_path = tmp_path / ".devcov-state" / "test_status.json"
    assert status_path.exists()


def test_start_phase_skips_missing_status(tmp_path: Path, monkeypatch) -> None:
    """Start-phase runs should not require test status yet."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    monkeypatch.setenv("DEVCOV_DEVFLOW_PHASE", "start")
    check = DevflowRunGates()
    violations = check.check(ctx)
    assert not violations


def test_passes_when_tests_are_fresh(tmp_path: Path) -> None:
    """Recent test runs should satisfy the gate."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    status_path = tmp_path / ".devcov-state" / "test_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    code_mtime = (tmp_path / "src" / "example.py").stat().st_mtime
    now = code_mtime + 10
    status = {
        "last_run_utc": "2025-12-27T00:00:00Z",
        "last_run_epoch": now,
        "commands": ["pytest", "python3 -m unittest discover"],
        "pre_commit_start_utc": "2025-12-26T00:00:00Z",
        "pre_commit_start_epoch": code_mtime - 10,
        "pre_commit_start_command": "pre-commit run --all-files",
        "pre_commit_end_utc": "2025-12-27T00:00:00Z",
        "pre_commit_end_epoch": code_mtime + 5,
        "pre_commit_end_command": "pre-commit run --all-files",
    }
    status_path.write_text(json.dumps(status), encoding="utf-8")

    check = DevflowRunGates()
    violations = check.check(ctx)
    assert not violations


def test_requires_pre_commit_start(tmp_path: Path) -> None:
    """Missing start pre-commit should trigger a violation."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    status_path = tmp_path / ".devcov-state" / "test_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    code_mtime = (tmp_path / "src" / "example.py").stat().st_mtime
    status = {
        "last_run_utc": "2025-12-27T00:00:00Z",
        "last_run_epoch": code_mtime + 10,
        "commands": ["pytest", "python3 -m unittest discover"],
        "pre_commit_end_utc": "2025-12-27T00:00:00Z",
        "pre_commit_end_epoch": code_mtime + 5,
        "pre_commit_end_command": "pre-commit run --all-files",
    }
    status_path.write_text(json.dumps(status), encoding="utf-8")

    check = DevflowRunGates()
    violations = check.check(ctx)
    assert any(
        "Session start pre-commit run is missing" in v.message
        for v in violations
    )


def test_requires_pre_commit_end(tmp_path: Path) -> None:
    """Missing end pre-commit should trigger a violation."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    status_path = tmp_path / ".devcov-state" / "test_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    code_mtime = (tmp_path / "src" / "example.py").stat().st_mtime
    status = {
        "last_run_utc": "2025-12-27T00:00:00Z",
        "last_run_epoch": code_mtime + 10,
        "commands": ["pytest", "python3 -m unittest discover"],
        "pre_commit_start_utc": "2025-12-26T00:00:00Z",
        "pre_commit_start_epoch": code_mtime - 10,
        "pre_commit_start_command": "pre-commit run --all-files",
    }
    status_path.write_text(json.dumps(status), encoding="utf-8")

    check = DevflowRunGates()
    violations = check.check(ctx)
    assert any(
        "Session end pre-commit run is missing" in v.message
        for v in violations
    )


def test_any_change_requires_tests(tmp_path: Path) -> None:
    """Any change, even documentation, should require test status."""
    ctx = make_ctx(tmp_path, ["docs/readme.md"])
    check = DevflowRunGates()
    violations = check.check(ctx)
    assert violations


def test_custom_status_path(tmp_path: Path) -> None:
    """Custom status paths should be honored."""
    ctx = make_ctx(
        tmp_path,
        ["src/example.py"],
        config={
            "policies": {
                "devflow-run-gates": {
                    "test_status_file": "alt/status.json",
                    "required_commands": ["pytest"],
                    "code_extensions": [".py"],
                }
            }
        },
    )
    status_path = tmp_path / "alt" / "status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    code_mtime = (tmp_path / "src" / "example.py").stat().st_mtime
    payload = {
        "last_run_utc": "2025-12-27T00:00:00Z",
        "last_run_epoch": code_mtime + 10,
        "commands": ["pytest"],
        "pre_commit_start_utc": "2025-12-26T00:00:00Z",
        "pre_commit_start_epoch": code_mtime - 10,
        "pre_commit_start_command": "pre-commit run --all-files",
        "pre_commit_end_utc": "2025-12-27T00:00:00Z",
        "pre_commit_end_epoch": code_mtime + 5,
        "pre_commit_end_command": "pre-commit run --all-files",
    }
    status_path.write_text(json.dumps(payload), encoding="utf-8")

    check = DevflowRunGates()
    check.set_options({}, ctx.get_policy_config("devflow-run-gates"))
    violations = check.check(ctx)
    assert not violations, "Custom path should be respected"


def test_metadata_config_overrides(tmp_path: Path) -> None:
    """Policy-def metadata should configure file paths and commands."""
    ctx = make_ctx(tmp_path, ["src/example.py"])
    status_path = tmp_path / "alt" / "status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    code_mtime = (tmp_path / "src" / "example.py").stat().st_mtime
    payload = {
        "last_run_utc": "2025-12-27T00:00:00Z",
        "last_run_epoch": code_mtime + 10,
        "commands": ["pytest"],
        "pre_commit_start_utc": "2025-12-26T00:00:00Z",
        "pre_commit_start_epoch": code_mtime - 10,
        "pre_commit_start_command": "pre-commit run --all-files",
        "pre_commit_end_utc": "2025-12-27T00:00:00Z",
        "pre_commit_end_epoch": code_mtime + 5,
        "pre_commit_end_command": "pre-commit run --all-files",
    }
    status_path.write_text(json.dumps(payload), encoding="utf-8")

    check = DevflowRunGates()
    check.set_options(
        {
            "test_status_file": "alt/status.json",
            "required_commands": ["pytest"],
            "code_extensions": [".py"],
        },
        {},
    )
    violations = check.check(ctx)
    assert (
        violations == []
    ), "Metadata-provided options should satisfy path/command checks"
