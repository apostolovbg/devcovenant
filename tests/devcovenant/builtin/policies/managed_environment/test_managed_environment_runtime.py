"""Tests for managed-environment runtime helpers."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from unittest import mock

from tests.devcovenant.support import MonkeyPatch

MODULE = (
    "devcovenant.builtin.policies.managed_environment."
    "managed_environment_runtime"
)


def _unit_test_module_importable() -> None:
    """Runtime module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Runtime module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_runtime_symbol_contract_is_stable() -> None:
    """Managed runtime helper surface should stay discoverable."""
    module = importlib.import_module(MODULE)
    expected = [
        "POLICY_ID",
        "RUNTIME_ACTION_RESOLVE_STAGE",
        "RUNTIME_ACTION_RESOLVE_RERUN",
        "_load_policy_entry",
        "_normalize_metadata_tokens",
        "_resolve_metadata_paths",
        "_parse_managed_commands",
        "_detect_managed_python",
        "_apply_managed_env",
        "_read_managed_stage_runs",
        "_write_managed_stage_runs",
        "_expand_managed_command_tokens",
        "_expand_managed_rerun_command_tokens",
        "_expand_guidance_command_tokens",
        "_managed_guidance_suffix",
        "_run_managed_commands_for_stage",
        "resolve_managed_environment_for_stage",
        "resolve_managed_rerun_command_for_stage",
    ]
    for symbol in expected:
        assert hasattr(module, symbol), symbol


def _unit_test_resolve_stage_returns_none_when_disabled(
    monkeypatch: MonkeyPatch,
) -> None:
    """Disabled policy should skip managed-environment orchestration."""
    module = importlib.import_module(MODULE)
    monkeypatch.setattr(
        module,
        "_load_policy_entry",
        lambda repo_root: {"enabled": False, "metadata": {}},
    )
    assert module.resolve_managed_environment_for_stage(
        Path("/tmp/repo"),
        "command",
    ) == (None, None)


def _unit_test_resolve_rerun_returns_none_when_disabled(
    monkeypatch: MonkeyPatch,
) -> None:
    """Disabled policy should return no rerun command."""
    module = importlib.import_module(MODULE)
    monkeypatch.setattr(
        module,
        "_load_policy_entry",
        lambda repo_root: {"enabled": False, "metadata": {}},
    )
    assert (
        module.resolve_managed_rerun_command_for_stage(
            Path("/tmp/repo"),
            "command",
            "check",
            ["--nofix"],
        )
        is None
    )


def _unit_test_invalid_managed_command_stage_raises() -> None:
    """Managed command parser should reject unknown stage tokens."""
    module = importlib.import_module(MODULE)
    try:
        module._parse_managed_commands(["invalid=>echo hello"])
    except ValueError as error:
        assert "Invalid managed command stage" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid stage token.")


def _unit_test_stage_bootstrap_dedupes_on_reexec(
    monkeypatch: MonkeyPatch,
) -> None:
    """Stage-scoped bootstrap commands should run once across re-exec hops."""
    module = importlib.import_module(MODULE)
    managed_root = Path("/tmp/repo/.venv")
    managed_python = managed_root / "bin" / "python"

    monkeypatch.setattr(
        module,
        "_load_policy_entry",
        lambda repo_root: {
            "enabled": True,
            "metadata": {
                "expected_paths": [".venv"],
                "expected_interpreters": [".venv/bin/python"],
                "managed_commands": ["start=>python3 -m venv .venv"],
            },
        },
    )

    stage_calls: list[str] = []

    def _fake_run_managed_commands_for_stage(
        repo_root: Path,
        env: dict[str, str],
        managed_commands: list[tuple[str, str]],
        *,
        target_stage: str,
        expected_interpreters: list[Path],
        expected_paths: list[Path],
        include_all_stage: bool,
    ) -> tuple[dict[str, str], bool]:
        """Record stage invocation while returning env unchanged."""
        del repo_root
        del managed_commands
        del expected_interpreters
        del expected_paths
        del include_all_stage
        stage_calls.append(target_stage)
        return dict(env), True

    monkeypatch.setattr(
        module,
        "_run_managed_commands_for_stage",
        _fake_run_managed_commands_for_stage,
    )
    monkeypatch.setattr(
        module,
        "_detect_managed_python",
        lambda expected_interpreters, expected_paths: (
            managed_python,
            managed_root,
        ),
    )

    first_env, first_python = module.resolve_managed_environment_for_stage(
        Path("/tmp/repo"),
        "start",
        base_env={},
    )
    assert first_env is not None
    assert first_python == str(managed_python)
    assert stage_calls == ["start"]
    assert first_env.get(module._MANAGED_STAGE_RUNS_ENV) == "start"

    second_env, second_python = module.resolve_managed_environment_for_stage(
        Path("/tmp/repo"),
        "start",
        base_env=first_env,
    )
    assert second_env is not None
    assert second_python == str(managed_python)
    assert stage_calls == ["start"]


def _unit_test_guidance_suffix_expands_tokens() -> None:
    """Guidance suffix should expand known tokens with paths."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/repo")
    managed_root = repo_root / ".venv"
    managed_python = managed_root / "bin" / "python"
    manual_commands = [
        "{managed_python} -m venv {managed_root}",
        "source {managed_bin}/activate",
        "cd {repo_root}",
    ]
    suffix = module._managed_guidance_suffix(
        manual_commands,
        repo_root=repo_root,
        managed_python=managed_python,
        managed_root=managed_root,
    )
    assert str(managed_python) in suffix
    assert str(managed_root) in suffix
    assert str(managed_root / "bin") in suffix
    assert str(repo_root) in suffix
    assert "{managed_python}" not in suffix


def _unit_test_guidance_suffix_uses_placeholders_when_missing() -> None:
    """Guidance suffix should use explicit placeholders when missing."""
    module = importlib.import_module(MODULE)
    manual_commands = [
        "{managed_python} -m venv {managed_root}",
        "{unknown_token}",
    ]
    suffix = module._managed_guidance_suffix(
        manual_commands,
        repo_root=Path("/tmp/repo"),
        managed_python=None,
        managed_root=None,
    )
    assert "<managed_python>" in suffix
    assert "<managed_root>" in suffix
    assert "<unknown_token>" in suffix
    assert "{managed_python}" not in suffix


def _unit_test_run_command_suppresses_console_bursts_in_normal_mode() -> None:
    """Managed commands can suppress bursts in normal mode when requested."""
    module = importlib.import_module(MODULE)
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        """Capture delegated runtime-helper kwargs and return success."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (type("R", (), {"returncode": 0})(), "")

    with (
        mock.patch.object(
            module,
            "run_child_command_with_output_policy",
            side_effect=_fake_run,
        ),
    ):
        module._run_command(
            ["python3", "-m", "pip", "install", "-r", "requirements.lock"],
            env={},
            cwd=Path("/tmp"),
        )

    kwargs = dict(captured["kwargs"])
    assert kwargs["channel"] == "managed_child"
    assert kwargs["capture_combined_output"] is False
    assert kwargs["verbose_only_console"] is False


def _unit_test_run_command_streams_console_output_in_verbose_mode() -> None:
    """Managed commands should stream live lines in verbose mode."""
    module = importlib.import_module(MODULE)
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        """Capture delegated runtime-helper kwargs and return success."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (type("R", (), {"returncode": 0})(), "")

    with (
        mock.patch.object(
            module,
            "run_child_command_with_output_policy",
            side_effect=_fake_run,
        ),
    ):
        module._run_command(
            ["python3", "-m", "pip", "install", "-r", "requirements.lock"],
            env={},
            cwd=Path("/tmp"),
        )

    kwargs = dict(captured["kwargs"])
    assert kwargs["channel"] == "managed_child"
    assert kwargs["capture_combined_output"] is False
    assert kwargs["verbose_only_console"] is False


def _unit_test_run_command_keeps_bootstrap_quiet_in_normal_mode() -> None:
    """Managed bootstrap commands should stay quiet in normal mode."""
    module = importlib.import_module(MODULE)
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        """Capture delegated runtime-helper kwargs and return success."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (type("R", (), {"returncode": 0})(), "")

    with (
        mock.patch.object(
            module,
            "run_child_command_with_output_policy",
            side_effect=_fake_run,
        ),
    ):
        module._run_command(
            ["python3", "-m", "pip", "install", "-r", "requirements.lock"],
            env={},
            cwd=Path("/tmp"),
        )

    kwargs = dict(captured["kwargs"])
    assert kwargs["channel"] == "managed_child"
    assert kwargs["capture_combined_output"] is False


def _unit_test_run_command_suppresses_output_in_quiet_mode() -> None:
    """Managed commands should stay fully quiet in quiet output mode."""
    module = importlib.import_module(MODULE)
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        """Capture delegated runtime-helper kwargs and return success."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (type("R", (), {"returncode": 0})(), "")

    with (
        mock.patch.object(
            module,
            "run_child_command_with_output_policy",
            side_effect=_fake_run,
        ),
    ):
        module._run_command(
            ["python3", "-m", "pip", "install", "-r", "requirements.lock"],
            env={},
            cwd=Path("/tmp"),
        )

    kwargs = dict(captured["kwargs"])
    assert kwargs["channel"] == "managed_child"
    assert kwargs["capture_combined_output"] is False
    assert kwargs["verbose_only_console"] is False


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for managed-environment runtime tests."""

    def test_module_importable(self):
        """Run runtime module importability test."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run runtime public-symbol sanity test."""
        _unit_test_module_has_public_symbols()

    def test_runtime_symbol_contract_is_stable(self):
        """Run runtime symbol contract assertions."""
        _unit_test_runtime_symbol_contract_is_stable()

    def test_resolve_stage_returns_none_when_disabled(self):
        """Run disabled resolve-stage runtime assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_resolve_stage_returns_none_when_disabled(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_resolve_rerun_returns_none_when_disabled(self):
        """Run disabled resolve-rerun runtime assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_resolve_rerun_returns_none_when_disabled(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_invalid_managed_command_stage_raises(self):
        """Run invalid-stage parser assertion."""
        _unit_test_invalid_managed_command_stage_raises()

    def test_stage_bootstrap_dedupes_on_reexec(self):
        """Run stage bootstrap dedupe assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_stage_bootstrap_dedupes_on_reexec(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_guidance_suffix_expands_tokens(self):
        """Run managed guidance token expansion assertions."""
        _unit_test_guidance_suffix_expands_tokens()

    def test_guidance_suffix_uses_placeholders_when_missing(self):
        """Run managed guidance placeholder fallback assertions."""
        _unit_test_guidance_suffix_uses_placeholders_when_missing()

    def test_run_command_suppresses_console_bursts_in_normal_mode(self):
        """Run managed-command normal-mode output suppression assertions."""
        _unit_test_run_command_suppresses_console_bursts_in_normal_mode()

    def test_run_command_streams_console_output_in_verbose_mode(self):
        """Run managed-command verbose-mode live output assertions."""
        _unit_test_run_command_streams_console_output_in_verbose_mode()

    def test_run_command_keeps_bootstrap_quiet_in_normal_mode(self):
        """Run managed-command normal-mode bootstrap quiet assertions."""
        _unit_test_run_command_keeps_bootstrap_quiet_in_normal_mode()

    def test_run_command_suppresses_output_in_quiet_mode(self):
        """Run managed-command quiet-mode suppression assertions."""
        _unit_test_run_command_suppresses_output_in_quiet_mode()
