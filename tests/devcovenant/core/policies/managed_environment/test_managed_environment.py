"""Tests for the managed environment policy."""

import sys
import tempfile
import unittest
from pathlib import Path

from devcovenant.core.policies.managed_environment import managed_environment
from devcovenant.core.policy_contracts import CheckContext
from tests.devcovenant.support import MonkeyPatch

ManagedEnvironmentCheck = managed_environment.ManagedEnvironmentCheck


def _unit_test_detects_external_interpreter(tmp_path: Path, monkeypatch):
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


def _unit_test_allows_managed_environment(tmp_path: Path, monkeypatch):
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


def _unit_test_warns_when_metadata_empty(tmp_path: Path):
    """Empty metadata should emit warning guidance."""
    checker = ManagedEnvironmentCheck()
    checker.set_options({}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)

    assert violations
    assert all(v.severity == "warning" for v in violations)
    assert any("expected_paths" in v.message for v in violations)
    assert any("command_hints" in v.message for v in violations)


def _unit_test_required_commands_replace_hint_warning(
    tmp_path: Path, monkeypatch
):
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_detects_external_interpreter(self):
        """Run test_detects_external_interpreter."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_detects_external_interpreter(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_allows_managed_environment(self):
        """Run test_allows_managed_environment."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_allows_managed_environment(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_warns_when_metadata_empty(self):
        """Run test_warns_when_metadata_empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_warns_when_metadata_empty(tmp_path=tmp_path)

    def test_required_commands_replace_hint_warning(self):
        """Run test_required_commands_replace_hint_warning."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_required_commands_replace_hint_warning(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()
