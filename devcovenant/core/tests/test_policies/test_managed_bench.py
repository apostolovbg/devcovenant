"""Tests for the managed bench environment policy."""

import sys
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policy_scripts import managed_bench

ManagedBenchCheck = managed_bench.ManagedBenchCheck


def test_detects_external_interpreter(tmp_path: Path, monkeypatch):
    """External interpreters should trigger a violation."""
    (tmp_path / ".venv").mkdir()
    fake_python = tmp_path / "external" / "python"
    fake_python.parent.mkdir(parents=True, exist_ok=True)
    fake_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(fake_python.parent))
    monkeypatch.setattr(sys, "executable", str(fake_python))

    checker = ManagedBenchCheck()
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)
    assert violations
    assert "virtual environment" in violations[0].message.lower()


def test_allows_managed_bench(tmp_path: Path, monkeypatch):
    """Managed bench paths should be accepted."""
    managed = tmp_path / ".venv"
    managed.mkdir()
    venv_python = managed / "bin"
    venv_python.mkdir()
    venv_executable = venv_python / "python"
    venv_executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))
    monkeypatch.setattr(sys, "executable", str(venv_executable))

    checker = ManagedBenchCheck()
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    assert checker.check(context) == []
