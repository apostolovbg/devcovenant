"""Tests for the managed environment policy."""

import sys
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.managed_environment import managed_environment

ManagedEnvironmentCheck = managed_environment.ManagedEnvironmentCheck


def test_detects_external_interpreter(tmp_path: Path, monkeypatch):
    """External interpreters should trigger a violation."""
    (tmp_path / ".venv").mkdir()
    fake_python = tmp_path / "external" / "python"
    fake_python.parent.mkdir(parents=True, exist_ok=True)
    fake_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(fake_python.parent))
    monkeypatch.setattr(sys, "executable", str(fake_python))

    checker = ManagedEnvironmentCheck()
    checker.set_options(
        {
            "expected_paths": [".venv"],
            "command_hints": ["source .venv/bin/activate"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)
    assert violations
    assert any(v.severity == "error" for v in violations)


def test_allows_managed_environment(tmp_path: Path, monkeypatch):
    """Managed environment paths should be accepted."""
    managed = tmp_path / ".venv"
    managed.mkdir()
    venv_python = managed / "bin"
    venv_python.mkdir()
    venv_executable = venv_python / "python"
    venv_executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))
    monkeypatch.setattr(sys, "executable", str(venv_executable))

    checker = ManagedEnvironmentCheck()
    checker.set_options(
        {
            "expected_paths": [".venv"],
            "command_hints": ["source .venv/bin/activate"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    assert checker.check(context) == []


def test_warns_when_metadata_empty(tmp_path: Path):
    """Empty metadata should emit warning guidance."""
    checker = ManagedEnvironmentCheck()
    checker.set_options({}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)

    assert violations
    assert all(v.severity == "warning" for v in violations)
    assert any("expected_paths" in v.message for v in violations)
    assert any("command_hints" in v.message for v in violations)


def test_required_commands_replace_hint_warning(tmp_path: Path, monkeypatch):
    """Required commands suppress the missing-hints warning."""
    managed = tmp_path / ".venv"
    managed.mkdir()
    venv_python = managed / "bin"
    venv_python.mkdir()
    venv_executable = venv_python / "python"
    venv_executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))
    monkeypatch.setattr(sys, "executable", str(venv_executable))

    checker = ManagedEnvironmentCheck()
    checker.set_options(
        {
            "expected_paths": [".venv"],
            "required_commands": ["python3"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    assert checker.check(context) == []
