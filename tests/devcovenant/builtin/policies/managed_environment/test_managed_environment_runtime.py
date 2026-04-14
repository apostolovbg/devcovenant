"""Tests for managed-environment runtime helpers."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import MonkeyPatch

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
        "_load_policy_entry",
        "_normalize_metadata_tokens",
        "_resolve_metadata_paths",
        "_resolve_command_search_paths",
        "_parse_managed_commands",
        "_detect_managed_python",
        "_apply_managed_env",
        "_read_managed_stage_runs",
        "_write_managed_stage_runs",
        "_expand_managed_command_tokens",
        "_expand_guidance_command_tokens",
        "_managed_guidance_suffix",
        "_run_managed_commands_for_stage",
        "resolve_managed_environment_for_stage",
        "resolve_cleanup_protected_paths",
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
        "bootstrap",
    ) == (None, None)
    assert module.resolve_managed_environment_for_stage(
        Path("/tmp/repo"),
        "managed",
    ) == (None, None)
    assert module.resolve_managed_environment_for_stage(
        Path("/tmp/repo"),
        "run",
    ) == (None, None)


def _unit_test_start_prepends_command_search_paths(
    monkeypatch: MonkeyPatch,
) -> None:
    """Managed environments should prepend declared command search paths."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
        managed_python = managed_root / "bin" / "python"
        managed_python.parent.mkdir(parents=True, exist_ok=True)
        managed_python.write_text("", encoding="utf-8")
        managed_python.chmod(0o755)
        tool_bin = repo_root / "tool-bin"
        tool_bin.mkdir(parents=True, exist_ok=True)
        tool_command = tool_bin / "pre-commit"
        tool_command.write_text("", encoding="utf-8")
        tool_command.chmod(0o755)

        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "command_search_paths": [str(tool_bin)],
                    "required_commands": ["pre-commit"],
                },
            },
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env={"PATH": ""},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert resolved_env["PATH"].split(os.pathsep) == [
        str(managed_python.parent),
        str(tool_bin),
    ]
    assert (
        Path(resolved_env["VIRTUAL_ENV"]).resolve() == managed_root.resolve()
    )


def _unit_test_invalid_managed_stage_raises() -> None:
    """Managed command parser should reject unknown stage tokens."""
    module = importlib.import_module(MODULE)
    try:
        module._parse_managed_commands(["invalid=>echo hello"])
    except ValueError as error:
        assert "Invalid managed-environment stage" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid stage token.")


def _unit_test_write_managed_stage_runs_uses_run_token() -> None:
    """Persisted managed-stage order should use `run`, not legacy `test`."""
    module = importlib.import_module(MODULE)
    env: dict[str, str] = {}

    module._write_managed_stage_runs(
        env,
        {"start", "run", "end", "bootstrap", "managed", "all"},
    )

    assert env[module._MANAGED_STAGE_RUNS_ENV] == (
        "start,run,end,bootstrap,managed,all"
    )


def _unit_test_stage_bootstrap_dedupes_on_reexec(
    monkeypatch: MonkeyPatch,
) -> None:
    """Stage-scoped bootstrap commands should run once across re-exec hops."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
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
            managed_python.parent.mkdir(parents=True, exist_ok=True)
            managed_python.write_text("", encoding="utf-8")
            managed_python.chmod(0o755)
            return dict(env), True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fake_run_managed_commands_for_stage,
        )
        monkeypatch.setattr(
            module,
            "_select_managed_environment",
            lambda expected_interpreters, expected_paths: (
                managed_python,
                managed_root,
            ),
        )

        first_env, first_python = module.resolve_managed_environment_for_stage(
            repo_root,
            "start",
            base_env={},
        )
        assert first_env is not None
        assert first_python == str(managed_python)
        assert stage_calls == ["start"]
        assert first_env.get(module._MANAGED_STAGE_RUNS_ENV) == "start"

        second_env, second_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env=first_env,
            )
        )
        assert second_env is not None
        assert second_python == str(managed_python)
        assert stage_calls == ["start"]


def _unit_test_start_reuses_ready_current_interpreter(
    monkeypatch: MonkeyPatch,
) -> None:
    """Start should reuse a matching ready interpreter without bootstrap."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
        managed_python = managed_root / "bin" / "python"
        managed_python.parent.mkdir(parents=True, exist_ok=True)
        managed_python.write_text("", encoding="utf-8")
        managed_python.chmod(0o755)

        monkeypatch.setattr(module.sys, "executable", str(managed_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "required_commands": ["python3"],
                    "managed_commands": [
                        "start=>python3 -m venv .venv",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_command_available_in_env",
            lambda command, env: command == "python3",
        )

        stage_calls: list[str] = []

        def _fail_if_bootstrap_runs(*args, **kwargs):
            """Record any unexpected bootstrap call for assertions."""
            del args, kwargs
            stage_calls.append("start")
            return {}, True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fail_if_bootstrap_runs,
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env={},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert resolved_env[module._MANAGED_STAGE_RUNS_ENV] == "start"
    assert stage_calls == []


def _unit_test_start_reuses_symlinked_environment_interpreter(
    monkeypatch: MonkeyPatch,
) -> None:
    """Symlinked env interpreters should keep the env-local launcher path."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
        managed_python = managed_root / "bin" / "python"
        real_python = repo_root / "python-home" / "bin" / "python"
        real_python.parent.mkdir(parents=True, exist_ok=True)
        real_python.write_text("", encoding="utf-8")
        real_python.chmod(0o755)
        managed_python.parent.mkdir(parents=True, exist_ok=True)
        try:
            managed_python.symlink_to(real_python)
        except (AttributeError, NotImplementedError, OSError) as error:
            raise unittest.SkipTest(
                "Symlink support is unavailable in this environment."
            ) from error

        monkeypatch.setattr(module.sys, "executable", str(managed_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "required_commands": ["python3"],
                    "managed_commands": [
                        "start=>python3 -m venv .venv",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_command_available_in_env",
            lambda command, env: command == "python3",
        )

        stage_calls: list[str] = []

        def _fail_if_bootstrap_runs(*args, **kwargs):
            """Record any unexpected bootstrap call for assertions."""
            del args, kwargs
            stage_calls.append("start")
            return {}, True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fail_if_bootstrap_runs,
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env={},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert (
        Path(resolved_env["VIRTUAL_ENV"]).resolve() == managed_root.resolve()
    )
    assert resolved_env["PATH"].split(os.pathsep)[0] == str(
        managed_python.parent
    )
    assert resolved_env[module._MANAGED_STAGE_RUNS_ENV] == "start"
    assert stage_calls == []


def _unit_test_start_reuses_external_environment_root(
    monkeypatch: MonkeyPatch,
) -> None:
    """Managed roots may live outside the repository tree."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        repo_root = temp_path / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)
        managed_root = temp_path / "frappe-bench" / "env"
        managed_python = managed_root / "bin" / "python"
        managed_python.parent.mkdir(parents=True, exist_ok=True)
        managed_python.write_text("", encoding="utf-8")
        managed_python.chmod(0o755)

        monkeypatch.setattr(module.sys, "executable", str(managed_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [str(managed_root)],
                    "expected_interpreters": [str(managed_python)],
                    "required_commands": ["python3"],
                    "managed_commands": [
                        f"start=>{managed_python} -m pip --version",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_command_available_in_env",
            lambda command, env: command == "python3",
        )

        stage_calls: list[str] = []

        def _fail_if_bootstrap_runs(*args, **kwargs):
            """Record any unexpected bootstrap call for assertions."""
            del args, kwargs
            stage_calls.append("start")
            return {}, True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fail_if_bootstrap_runs,
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env={},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert (
        Path(resolved_env["VIRTUAL_ENV"]).resolve() == managed_root.resolve()
    )
    assert resolved_env["PATH"].split(os.pathsep)[0] == str(
        managed_python.parent
    )
    assert resolved_env[module._MANAGED_STAGE_RUNS_ENV] == "start"
    assert stage_calls == []


def _unit_test_start_does_not_reuse_unrelated_host_interpreter(
    monkeypatch: MonkeyPatch,
) -> None:
    """Start should bootstrap instead of reusing an unrelated host Python."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
        managed_python = managed_root / "bin" / "python"
        host_python = repo_root / "hosted" / "bin" / "python"

        monkeypatch.setattr(module.sys, "executable", str(host_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "required_commands": ["python3"],
                    "managed_commands": [
                        "start=>python3 -m venv .venv",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_command_available_in_env",
            lambda command, env: command == "python3",
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
            """Create the managed interpreter during start bootstrap."""
            del repo_root
            del managed_commands
            del expected_interpreters
            del expected_paths
            del include_all_stage
            stage_calls.append(target_stage)
            managed_python.parent.mkdir(parents=True, exist_ok=True)
            managed_python.write_text("", encoding="utf-8")
            managed_python.chmod(0o755)
            return dict(env), True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fake_run_managed_commands_for_stage,
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "start",
                base_env={},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert resolved_env[module._MANAGED_STAGE_RUNS_ENV] == "start"
    assert stage_calls == ["start"]


def _unit_test_run_bootstraps_when_environment_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    """Non-start stages should bootstrap once when no valid env exists yet."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        managed_root = repo_root / ".venv"
        managed_python = managed_root / "bin" / "python"

        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "managed_commands": [
                        "start=>python3 -m venv .venv",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_command_available_in_env",
            lambda command, env: True,
        )
        monkeypatch.setattr(
            module,
            "_select_managed_environment",
            lambda expected_interpreters, expected_paths: (
                managed_python,
                managed_root,
            ),
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
            """Create the missing interpreter only during start bootstrap."""
            del repo_root
            del managed_commands
            del expected_interpreters
            del expected_paths
            del include_all_stage
            if target_stage != "start":
                return dict(env), False
            stage_calls.append(target_stage)
            managed_python.parent.mkdir(parents=True, exist_ok=True)
            managed_python.write_text("", encoding="utf-8")
            managed_python.chmod(0o755)
            return dict(env), True

        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            _fake_run_managed_commands_for_stage,
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "run",
                base_env={},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(managed_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(managed_python)
    assert resolved_env[module._MANAGED_STAGE_RUNS_ENV] == "start"
    assert stage_calls == ["start"]


def _unit_test_bootstrap_stage_uses_current_interpreter_with_flag(
    monkeypatch: MonkeyPatch,
) -> None:
    """Bootstrap stage may use the current interpreter with explicit opt-in."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)
        tool_root = Path(temp_dir) / "toolenv"
        tool_python = tool_root / "bin" / "python"
        tool_python.parent.mkdir(parents=True, exist_ok=True)
        tool_python.write_text("", encoding="utf-8")
        tool_python.chmod(0o755)
        (tool_root / "pyvenv.cfg").write_text("", encoding="utf-8")

        monkeypatch.setattr(module.sys, "executable", str(tool_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "required_commands": ["pre-commit", "pytest"],
                    "allow_current_interpreter_fallback": True,
                    "manual_commands": [
                        "{current_python} -m venv .venv",
                        "{managed_python} -m pip install -r requirements.lock",
                    ],
                    "managed_commands": [],
                },
            },
        )

        resolved_env, resolved_python = (
            module.resolve_managed_environment_for_stage(
                repo_root,
                "bootstrap",
                base_env={"PATH": "/usr/bin"},
            )
        )

    assert resolved_env is not None
    assert resolved_python == str(tool_python)
    assert resolved_env["DEVCOV_MANAGED_PYTHON"] == str(tool_python)
    assert resolved_env["PATH"].split(os.pathsep)[0] == str(tool_python.parent)
    assert Path(resolved_env["VIRTUAL_ENV"]).resolve() == tool_root.resolve()


def _unit_test_bootstrap_stage_requires_explicit_fallback_flag(
    monkeypatch: MonkeyPatch,
) -> None:
    """Implicit bootstrap-stage fallback should fail without a flag."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)
        tool_root = Path(temp_dir) / "toolenv"
        tool_python = tool_root / "bin" / "python"
        tool_python.parent.mkdir(parents=True, exist_ok=True)
        tool_python.write_text("", encoding="utf-8")
        tool_python.chmod(0o755)
        (tool_root / "pyvenv.cfg").write_text("", encoding="utf-8")

        monkeypatch.setattr(module.sys, "executable", str(tool_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "required_commands": ["pre-commit", "pytest"],
                    "manual_commands": [
                        "{current_python} -m venv .venv",
                        "{managed_python} -m pip install -r requirements.lock",
                    ],
                    "managed_commands": [],
                },
            },
        )

        try:
            module.resolve_managed_environment_for_stage(
                repo_root,
                "bootstrap",
                base_env={"PATH": "/usr/bin"},
            )
        except ValueError as error:
            message = str(error)
        else:  # pragma: no cover - defensive
            raise AssertionError(
                "Expected ValueError when fallback flag is missing."
            )

    assert "allow_current_interpreter_fallback" in message


def _unit_test_bootstrap_stage_does_not_mask_declared_bootstrap_contract(
    monkeypatch: MonkeyPatch,
) -> None:
    """Bootstrap-stage reuse should not hide explicit bootstrap logic."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        tool_root = repo_root / "toolenv"
        tool_python = tool_root / "bin" / "python"
        tool_python.parent.mkdir(parents=True, exist_ok=True)
        tool_python.write_text("", encoding="utf-8")
        tool_python.chmod(0o755)
        (tool_root / "pyvenv.cfg").write_text("", encoding="utf-8")

        monkeypatch.setattr(module.sys, "executable", str(tool_python))
        monkeypatch.setattr(
            module,
            "_load_policy_entry",
            lambda repo_root: {
                "enabled": True,
                "metadata": {
                    "expected_paths": [".venv"],
                    "expected_interpreters": [".venv/bin/python"],
                    "managed_commands": [
                        "start=>{current_python} -m venv .venv",
                    ],
                },
            },
        )
        monkeypatch.setattr(
            module,
            "_run_managed_commands_for_stage",
            lambda repo_root, env, managed_commands, **kwargs: (
                dict(env),
                True,
            ),
        )

        try:
            module.resolve_managed_environment_for_stage(
                repo_root,
                "bootstrap",
                base_env={"PATH": "/usr/bin"},
            )
        except ValueError as error:
            message = str(error)
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected ValueError for missing target env.")

    assert "no expected interpreter was found" in message


def _unit_test_guidance_suffix_expands_tokens() -> None:
    """Guidance suffix should expand known tokens with display-safe paths."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/repo")
    managed_root = repo_root / ".venv"
    managed_python = managed_root / "bin" / "python"
    manual_commands = [
        "{current_python} -m pip --version",
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
    assert (
        module.display_path(Path(sys.executable), repo_root=repo_root)
        in suffix
    )
    assert module.display_path(managed_python, repo_root=repo_root) in suffix
    assert module.display_path(managed_root, repo_root=repo_root) in suffix
    assert (
        module.display_path(managed_python.parent, repo_root=repo_root)
        in suffix
    )
    assert module.display_path(repo_root, repo_root=repo_root) in suffix
    assert sys.executable not in suffix
    assert str(repo_root) not in suffix
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


def _unit_test_guidance_suffix_redacts_external_runtime_paths() -> None:
    """Guidance suffix should hide external runtime absolute paths."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/repo")
    managed_root = repo_root / ".venv"
    managed_python = Path("/opt/homebrew/bin/python3")
    suffix = module._managed_guidance_suffix(
        [
            "{current_python} -m venv .venv",
            "{managed_python} -m pip install -r requirements.lock",
            "cd {repo_root}",
        ],
        repo_root=repo_root,
        managed_python=managed_python,
        managed_root=managed_root,
    )
    assert "outside-repo/" in suffix
    assert str(managed_python) not in suffix
    assert sys.executable not in suffix
    assert str(repo_root) not in suffix


def _unit_test_load_policy_entry_requires_registry_or_config() -> None:
    """Missing registry without config should fail explicitly."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        try:
            module._load_policy_entry(repo_root)
        except ValueError as error:
            message = str(error)
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected ValueError for missing registry.")

        assert "requires tracked registry" in message
        assert "devcovenant refresh" in message


def _unit_test_bootstrap_from_config_when_registry_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    """Config metadata should bootstrap managed-environment resolution."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "profiles:\n  active:\n    - global\n",
            encoding="utf-8",
        )

        policy_dir = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "policies"
            / "managed_environment"
        )
        policy_dir.mkdir(parents=True, exist_ok=True)
        (policy_dir / "managed_environment.yaml").write_text(
            "id: managed-environment\n"
            "text: Managed environment.\n"
            "metadata:\n"
            "  enabled: true\n"
            "  expected_interpreters: []\n"
            "  expected_paths: []\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(
            module.metadata_runtime_module,
            "build_metadata_context",
            lambda repo_root: module.metadata_runtime_module.MetadataContext(
                control=module.metadata_runtime_module.PolicyControl({}),
                profile_overlays={},
                autogen_overlays={
                    "managed-environment": {
                        "expected_interpreters": [".venv/bin/python"],
                        "expected_paths": [".venv"],
                    }
                },
                user_overlays={},
                autogen_overrides={},
                user_overrides={},
            ),
        )

        entry = module._load_policy_entry(repo_root)

    assert entry is not None
    assert str(entry["enabled"]).lower() == "true"
    assert entry["metadata"]["expected_interpreters"] == ".venv/bin/python"
    assert entry["metadata"]["expected_paths"] == ".venv"


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


def _unit_test_cleanup_protected_paths_prefer_explicit_metadata() -> None:
    """Cleanup protection should use explicit managed metadata first."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/repo")
    entry = {
        "enabled": True,
        "metadata": {
            "cleanup_protected_paths": [".managed-root", ".bench"],
            "expected_paths": [".venv"],
            "expected_interpreters": [".venv/bin/python"],
        },
    }
    with mock.patch.object(module, "_load_policy_entry", return_value=entry):
        protected = module.resolve_cleanup_protected_paths(repo_root)

    assert protected == (
        (repo_root / ".managed-root").resolve(),
        (repo_root / ".bench").resolve(),
    )


def _unit_test_cleanup_protected_paths_fall_back_to_expected_paths() -> None:
    """Cleanup protection should fall back to expected environment roots."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/repo")
    entry = {
        "enabled": True,
        "metadata": {
            "cleanup_protected_paths": [],
            "expected_paths": [".venv"],
            "expected_interpreters": [".venv/bin/python"],
        },
    }
    with mock.patch.object(module, "_load_policy_entry", return_value=entry):
        protected = module.resolve_cleanup_protected_paths(repo_root)

    assert protected == ((repo_root / ".venv").resolve(),)


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

    def test_start_prepends_command_search_paths(self):
        """Run command search path prepending assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_start_prepends_command_search_paths(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_invalid_managed_stage_raises(self):
        """Run invalid-stage parser assertion."""
        _unit_test_invalid_managed_stage_raises()

    def test_write_managed_stage_runs_uses_run_token(self):
        """Run managed-stage persistence assertions."""
        _unit_test_write_managed_stage_runs_uses_run_token()

    def test_stage_bootstrap_dedupes_on_reexec(self):
        """Run stage bootstrap dedupe assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_stage_bootstrap_dedupes_on_reexec(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_start_reuses_ready_current_interpreter(self):
        """Run start-stage environment reuse assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_start_reuses_ready_current_interpreter(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_start_reuses_symlinked_environment_interpreter(self):
        """Run symlinked-interpreter environment reuse assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_start_reuses_symlinked_environment_interpreter(
                monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_start_reuses_external_environment_root(self):
        """Run external-environment-root reuse assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_start_reuses_external_environment_root(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_start_does_not_reuse_unrelated_host_interpreter(self):
        """Run unrelated-host interpreter bootstrap assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_start_does_not_reuse_unrelated_host_interpreter(
                monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_bootstraps_when_environment_is_missing(self):
        """Run missing-environment bootstrap fallback assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_bootstraps_when_environment_is_missing(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_bootstrap_stage_uses_current_interpreter_with_explicit_flag(
        self,
    ):
        """Run explicit bootstrap-stage fallback assertions."""
        monkeypatch = MonkeyPatch()
        try:
            fn = _unit_test_bootstrap_stage_uses_current_interpreter_with_flag
            fn(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_bootstrap_stage_requires_explicit_fallback_flag(self):
        """Run implicit bootstrap-stage fallback rejection assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_bootstrap_stage_requires_explicit_fallback_flag(
                monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_guidance_suffix_expands_tokens(self):
        """Run managed guidance token expansion assertions."""
        _unit_test_guidance_suffix_expands_tokens()

    def test_guidance_suffix_uses_placeholders_when_missing(self):
        """Run managed guidance placeholder assertions."""
        _unit_test_guidance_suffix_uses_placeholders_when_missing()

    def test_guidance_suffix_redacts_external_runtime_paths(self):
        """Run managed guidance path-redaction assertions."""
        _unit_test_guidance_suffix_redacts_external_runtime_paths()

    def test_load_policy_entry_requires_registry_or_config(self):
        """Run missing-registry-and-config explicit-failure assertions."""
        _unit_test_load_policy_entry_requires_registry_or_config()

    def test_load_policy_entry_bootstraps_from_config_when_registry_missing(
        self,
    ):
        """Run config-bootstrap assertions for missing tracked registry."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_bootstrap_from_config_when_registry_missing(monkeypatch)
        finally:
            monkeypatch.undo()

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

    def test_cleanup_protected_paths_prefer_explicit_metadata(self):
        """Run explicit cleanup-protected-path metadata assertions."""
        _unit_test_cleanup_protected_paths_prefer_explicit_metadata()

    def test_cleanup_protected_paths_fall_back_to_expected_paths(self):
        """Run expected-path cleanup protection fallback assertions."""
        _unit_test_cleanup_protected_paths_fall_back_to_expected_paths()
