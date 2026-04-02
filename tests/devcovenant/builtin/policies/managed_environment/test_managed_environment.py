"""Tests for the managed environment policy."""

import sys
import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.managed_environment import (
    managed_environment,
)
from devcovenant.core.policy_contract import CheckContext
from tests import MonkeyPatch

ManagedEnvironmentCheck = managed_environment.ManagedEnvironmentCheck


def _unit_test_contract_symbols_covered() -> None:
    """Managed-environment module should expose stable contract symbols."""
    module = managed_environment
    assert hasattr(module, "ManagedEnvironmentCheck")
    checker_class = module.ManagedEnvironmentCheck
    assert hasattr(checker_class, "check")
    assert hasattr(checker_class, "run_runtime_action")


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
            "manual_commands": ["source .venv/bin/activate"],
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
            "manual_commands": ["source .venv/bin/activate"],
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
    assert not any("manual_commands" in v.message for v in violations)


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


def _unit_test_managed_commands_replace_manual_warning(
    tmp_path: Path, monkeypatch
):
    """Managed commands should suppress missing-manual warning."""
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
            "managed_commands": ["start=>python3 -m venv .venv"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    assert checker.check(context) == []


def _unit_test_required_commands_accept_dash_underscore_variants(
    tmp_path: Path, monkeypatch
):
    """Required command checks should accept dash/underscore variants."""
    managed = tmp_path / ".venv"
    managed.mkdir()
    venv_python = managed / "bin"
    venv_python.mkdir()
    venv_executable = venv_python / "python"
    venv_executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))
    monkeypatch.setattr(sys, "executable", str(venv_executable))
    monkeypatch.setattr(
        managed_environment.shutil,
        "which",
        lambda token: "/usr/bin/pre-commit" if token == "pre-commit" else None,
    )

    checker = ManagedEnvironmentCheck()
    checker.set_options(
        {
            "expected_paths": [".venv"],
            "required_commands": ["pre_commit"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)
    assert all(
        "Required commands are missing" not in v.message for v in violations
    )


def _unit_test_manual_command_guidance_expands_tokens(
    tmp_path: Path, monkeypatch
):
    """Manual command guidance should expand managed token values."""
    managed = tmp_path / ".venv"
    managed.mkdir()
    venv_bin = managed / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    venv_python = venv_bin / "python"
    venv_python.write_text("", encoding="utf-8")
    external_python = tmp_path / "external" / "python"
    external_python.parent.mkdir(parents=True, exist_ok=True)
    external_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(external_python.parent))
    monkeypatch.setattr(sys, "executable", str(external_python))

    checker = ManagedEnvironmentCheck()
    checker.set_options(
        {
            "expected_paths": [".venv"],
            "manual_commands": [
                "source {managed_bin}/activate",
                "{managed_python} -m venv {managed_root}",
                "cd {repo_root}",
            ],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[])
    violations = checker.check(context)
    assert violations
    message = " ".join(v.message for v in violations if v.severity == "error")
    assert str(venv_bin) in message
    assert str(venv_python) in message
    assert str(managed) in message
    assert str(tmp_path) in message
    assert "{managed_" not in message


def _unit_test_runtime_action_resolve_stage_dispatches(monkeypatch) -> None:
    """Runtime resolve-stage action should delegate to runtime helpers."""
    checker = ManagedEnvironmentCheck()
    captured: dict[str, object] = {}
    runtime_helpers = managed_environment.managed_environment_runtime

    def _fake_resolve(repo_root: Path, stage: str, *, base_env=None):
        """Capture resolve-stage parameters for assertions."""
        captured["repo_root"] = str(repo_root)
        captured["stage"] = stage
        captured["base_env"] = dict(base_env or {})
        return {"PATH": "/tmp"}, "/tmp/python"

    monkeypatch.setattr(
        runtime_helpers,
        "resolve_managed_environment_for_stage",
        _fake_resolve,
    )
    result = checker.run_runtime_action(
        runtime_helpers.RUNTIME_ACTION_RESOLVE_STAGE,
        repo_root=Path("/tmp/repo"),
        payload={"stage": "test", "base_env": {"PATH": "/usr/bin"}},
    )
    assert result == ({"PATH": "/tmp"}, "/tmp/python")
    assert captured["repo_root"] == str(Path("/tmp/repo"))
    assert captured["stage"] == "test"
    assert captured["base_env"] == {"PATH": "/usr/bin"}


def _unit_test_runtime_action_unknown_raises() -> None:
    """Unknown runtime action should raise a ValueError."""
    checker = ManagedEnvironmentCheck()
    try:
        checker.run_runtime_action(
            "unknown-action",
            repo_root=Path("/tmp/repo"),
            payload={},
        )
    except ValueError as error:
        assert "Unsupported managed-environment runtime action" in str(error)
    else:
        raise AssertionError("Expected ValueError for unsupported action.")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_contract_symbols_covered(self):
        """Run managed-environment contract symbol assertions."""
        _unit_test_contract_symbols_covered()

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

    def test_managed_commands_replace_manual_warning(self):
        """Run test_managed_commands_replace_manual_warning."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_managed_commands_replace_manual_warning(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_required_commands_accept_dash_underscore_variants(self):
        """Run test_required_commands_accept_dash_underscore_variants."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_required_commands_accept_dash_underscore_variants(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_manual_command_guidance_expands_tokens(self):
        """Run manual-command guidance expansion assertions."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_manual_command_guidance_expands_tokens(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_runtime_action_resolve_stage_dispatches(self):
        """Run runtime resolve-stage dispatcher assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_runtime_action_resolve_stage_dispatches(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_runtime_action_unknown_raises(self):
        """Run unsupported runtime-action assertion."""
        _unit_test_runtime_action_unknown_raises()
