"""Tests for top-level DevCovenant CLI behavior and command layout."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import devcovenant
import devcovenant.core.execution as execution_runtime_module
from devcovenant import cli
from devcovenant.core.repository_paths import display_path
from tests import MonkeyPatch, current_devcovenant_version

REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_DEVCOVENANT_VERSION = current_devcovenant_version()
ROOT_COMMANDS = (
    ("asset", "asset"),
    ("check", "check"),
    ("clean", "clean"),
    ("custom", "custom"),
    ("demo", "demo"),
    ("gate", "gate"),
    ("run", "run"),
    ("install", "install"),
    ("deploy", "deploy"),
    ("upgrade", "upgrade"),
    ("refresh", "refresh"),
    ("uninstall", "uninstall"),
    ("undeploy", "undeploy"),
    ("policy", "policy"),
    ("quickstart", "quickstart"),
)


def _command_module_file(module_name: str) -> str:
    """Return the file path used to launch one root command module."""
    return f"{module_name}.py"


ASSET_SCRIPT_ROOT = (
    REPO_ROOT
    / "devcovenant"
    / "core"
    / "profiles"
    / "global"
    / "assets"
    / "devcovenant"
)


def _unit_test_cli_dispatches_command_and_args(monkeypatch) -> None:
    """CLI should dispatch to command module main with remaining args."""
    captured: dict[str, object] = {}

    def _fake_main(argv):
        """Capture forwarded argv for assertion."""
        captured["argv"] = list(argv)
        raise SystemExit(0)

    monkeypatch.setattr(
        cli,
        "_load_command_module",
        lambda command: (
            captured.update({"command": command})
            or SimpleNamespace(main=_fake_main)
        ),
    )
    monkeypatch.setattr(
        cli,
        "_maybe_reexec_managed_environment",
        lambda _command, _args: None,
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "cleanup_source_checkout_import_cache",
        lambda _repo_root: False,
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["command"] == "check"
    assert captured["argv"] == []


def _unit_test_cli_cleans_source_checkout_import_cache(monkeypatch) -> None:
    """CLI should clean source-checkout import cache before dispatch."""
    repo_root = REPO_ROOT
    captured: list[Path] = []

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "cleanup_source_checkout_import_cache",
        lambda _repo_root: captured.append(_repo_root) or True,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_repo_pycache_prefix",
        lambda _repo_root: False,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_output_mode_from_config",
        lambda _repo_root: None,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_logs_keep_last_from_config",
        lambda _repo_root: None,
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        cli,
        "_maybe_reexec_managed_environment",
        lambda _command, _args: None,
    )
    monkeypatch.setattr(
        cli,
        "_load_command_module",
        lambda _command: SimpleNamespace(
            main=lambda _argv: (_ for _ in ()).throw(SystemExit(0))
        ),
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured == [repo_root]


def _unit_test_cli_unknown_command_fails(monkeypatch) -> None:
    """Unknown command should exit with parser error."""
    monkeypatch.setattr(sys, "argv", ["devcovenant", "does-not-exist"])
    stderr_buffer = io.StringIO()
    with redirect_stderr(stderr_buffer):
        try:
            cli.main()
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 2
    assert "invalid choice: 'does-not-exist'" in stderr_buffer.getvalue()


def _unit_test_cli_version_flag_prints_version(monkeypatch) -> None:
    """`--version` should print the package version and exit cleanly."""
    monkeypatch.setattr(sys, "argv", ["devcovenant", "--version"])
    stdout_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer):
        try:
            cli.main()
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert (
        stdout_buffer.getvalue().strip()
        == f"devcovenant {CURRENT_DEVCOVENANT_VERSION}"
    )


def _unit_test_cli_reexecs_when_managed_env_differs(monkeypatch) -> None:
    """CLI should re-exec when managed interpreter differs from current."""
    repo_root = REPO_ROOT
    managed_python = str(repo_root / ".venv" / "bin" / "python")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "resolve_managed_environment_for_stage",
        lambda _repo_root, _stage, base_env=None: (
            {"PATH": "/tmp"},
            managed_python,
        ),
    )
    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        cli,
        "_managed_python_is_executable",
        lambda _path: True,
    )

    def _fake_execve(path: str, argv: list[str], env: dict[str, str]) -> None:
        """Capture execve contract and stop control flow."""
        captured["path"] = path
        captured["argv"] = list(argv)
        captured["env"] = dict(env)
        raise SystemExit(0)

    monkeypatch.setattr(cli.os, "execve", _fake_execve)
    monkeypatch.setattr(cli, "_load_command_module", lambda _command: None)

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["path"] == managed_python
    assert captured["argv"] == [
        managed_python,
        "-m",
        "devcovenant",
        "check",
    ]
    env_payload = captured["env"]
    assert isinstance(env_payload, dict)
    assert env_payload[cli._MANAGED_REEXEC_GUARD_ENV] == "1"


def _unit_test_cli_reexec_guard_prevents_loop(monkeypatch) -> None:
    """Second managed re-exec attempt should fail with clear error."""
    repo_root = REPO_ROOT
    managed_python = str(repo_root / ".venv" / "bin" / "python")

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "resolve_managed_environment_for_stage",
        lambda _repo_root, _stage, base_env=None: (
            {"PATH": "/tmp"},
            managed_python,
        ),
    )
    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check"],
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        cli,
        "_managed_python_is_executable",
        lambda _path: True,
    )
    monkeypatch.setenv(cli._MANAGED_REEXEC_GUARD_ENV, "1")

    stderr_buffer = io.StringIO()
    with redirect_stderr(stderr_buffer):
        try:
            cli.main()
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from cli.main().")

    assert code == (
        "Managed-environment auto-rerun did not converge to the expected "
        "interpreter."
    )


def _unit_test_cli_reports_managed_error_without_rerun(monkeypatch) -> None:
    """CLI should report managed-environment errors when no rerun exists."""
    repo_root = REPO_ROOT

    def _raise_missing(_repo_root, _stage, base_env=None):
        """Raise the managed-interpreter missing error for passthrough."""
        raise ValueError("managed-environment interpreter missing")

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "resolve_managed_environment_for_stage",
        _raise_missing,
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == "managed-environment interpreter missing"


def _unit_test_cli_reports_non_executable_managed_python(
    monkeypatch,
) -> None:
    """Non-executable managed Python should surface explicit SystemExit."""
    repo_root = REPO_ROOT
    managed_python = str(repo_root / ".venv" / "bin" / "python")

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "resolve_managed_environment_for_stage",
        lambda _repo_root, _stage, base_env=None: (
            {"PATH": "/tmp"},
            managed_python,
        ),
    )
    monkeypatch.setattr(
        cli,
        "_managed_python_is_executable",
        lambda _path: False,
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

    try:
        cli.main()
    except SystemExit as exc:
        code = str(exc.code)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert "not executable" in code
    assert display_path(Path(managed_python), repo_root=repo_root) in code
    assert managed_python not in code


def _unit_test_cli_applies_root_level_output_override(monkeypatch) -> None:
    """Leading root-level output flags should override config for the run."""
    repo_root = REPO_ROOT
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "cleanup_source_checkout_import_cache",
        lambda _repo_root: False,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_repo_pycache_prefix",
        lambda _repo_root: False,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_output_mode_from_config",
        lambda _repo_root: captured.setdefault("config_called", True),
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_output_mode",
        lambda mode: captured.setdefault("override_mode", mode),
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "configure_logs_keep_last_from_config",
        lambda _repo_root: None,
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        execution_runtime_module,
        "merge_active_run_log_metadata",
        lambda payload: captured.setdefault("metadata", dict(payload)),
    )
    monkeypatch.setattr(
        cli,
        "_maybe_reexec_managed_environment",
        lambda _command, _args: None,
    )
    monkeypatch.setattr(
        cli,
        "_load_command_module",
        lambda _command: SimpleNamespace(
            main=lambda argv: captured.setdefault("argv", list(argv))
            or (_ for _ in ()).throw(SystemExit(0))
        ),
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "--quiet", "check"])

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["override_mode"] == "quiet"
    assert "config_called" not in captured
    assert captured["argv"] == []
    assert captured["metadata"] == {"cli_output_mode_override": "quiet"}


def _unit_test_run_help_is_command_scoped() -> None:
    """`run --help` should expose no extra lifecycle flags."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "run", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo" not in result.stdout
    assert "--install-mode" not in result.stdout
    assert "--docs-mode" not in result.stdout
    assert "--quiet" in result.stdout
    assert "--normal" in result.stdout
    assert "--verbose" in result.stdout


def _unit_test_root_help_lists_command_summaries() -> None:
    """`--help` should expose discoverable top-level command summaries."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Command summary:" in result.stdout
    assert (
        "Write one Desktop copy of a shipped profile asset or managed doc."
        in result.stdout
    )
    assert (
        "Promote or retract builtin policy/profile custom copies and "
        "any mirrored tests." in result.stdout
    )
    assert "Run a disposable evaluation demo." in result.stdout
    assert "Print a terse static reminder." in result.stdout
    assert (
        "Run `devcovenant <command> --help` for command-specific options."
        in result.stdout
    )


def _unit_test_asset_help_is_command_scoped() -> None:
    """`asset --help` should expose only the asset-materialization surface."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "asset", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        "Write one Desktop copy of a shipped profile asset or managed doc."
        in result.stdout
    )
    assert "Optional Desktop filename override." in result.stdout
    assert "--overwrite" in result.stdout
    assert "--open" not in result.stdout
    assert "--close" not in result.stdout


def _unit_test_check_help_shows_check_only_options() -> None:
    """`check --help` should show audit help without legacy flags."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "check", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "read-only DevCovenant audit checks" in result.stdout
    assert "--nofix" not in result.stdout
    assert "--norefresh" not in result.stdout
    assert "--open" not in result.stdout
    assert "--close" not in result.stdout


def _unit_test_install_help_shows_command_scope() -> None:
    """`install --help` should expose only command-scoped defaults."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "install", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage: devcovenant install [-h]" in result.stdout
    assert "--mode" not in result.stdout
    assert "--target" not in result.stdout
    assert "--docs-mode" not in result.stdout
    assert "--nofix" not in result.stdout


def _unit_test_all_command_help_uses_scoped_prog() -> None:
    """Every root command help surface should show scoped usage text."""
    for command_name, _module_name in ROOT_COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", "devcovenant", command_name, "--help"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (
            f"usage: devcovenant {command_name} [-h]" in result.stdout
        ), result.stdout


def _unit_test_gate_help_is_command_scoped() -> None:
    """`gate --help` should expose only gate options."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "gate", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "gate session lifecycle commands" in result.stdout
    assert "--open" in result.stdout
    assert "--verify" in result.stdout
    assert "--close" in result.stdout
    legacy_names = ("sta" + "rt", "m" + "id", "en" + "d")
    for legacy_name in legacy_names:
        assert f"--{legacy_name}" not in result.stdout
    assert "short gate session status" in result.stdout
    assert "--nofix" not in result.stdout
    assert "--norefresh" not in result.stdout
    assert "--quiet" in result.stdout
    assert "--normal" in result.stdout
    assert "--verbose" in result.stdout


def _unit_test_custom_help_is_command_scoped() -> None:
    """`custom --help` should expose only the customization surface."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "custom", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        "Promote or retract builtin policy/profile custom copies"
        in result.stdout
    )
    assert "--policy" in result.stdout
    assert "--profile" in result.stdout
    assert "--do" in result.stdout
    assert "--undo" in result.stdout
    assert "--open" not in result.stdout
    assert "--close" not in result.stdout


def _unit_test_root_command_modules_exist() -> None:
    """All CLI command modules should exist at package root."""
    for _command_name, module_name in ROOT_COMMANDS:
        root_path = (
            REPO_ROOT / "devcovenant" / _command_module_file(module_name)
        )
        assert root_path.exists(), str(root_path)


def _unit_test_command_modules_not_duplicated_as_profile_assets() -> None:
    """Root command modules should not be duplicated in profile assets."""
    for _command_name, module_name in ROOT_COMMANDS:
        duplicate_path = ASSET_SCRIPT_ROOT / _command_module_file(module_name)
        assert not duplicate_path.exists(), str(duplicate_path)


def _unit_test_command_modules_support_file_path_help() -> None:
    """File-path invocation should work without PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for _command_name, module_name in ROOT_COMMANDS:
        result = subprocess.run(
            [
                sys.executable,
                f"devcovenant/{_command_module_file(module_name)}",
                "--help",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def _unit_test_launcher_contract_has_no_in_package_bootstrap() -> None:
    """Launcher contract should avoid in-package startup bootstrap tricks."""
    cli_text = (REPO_ROOT / "devcovenant" / "cli.py").read_text(
        encoding="utf-8"
    )
    main_text = (REPO_ROOT / "devcovenant" / "__main__.py").read_text(
        encoding="utf-8"
    )
    assert not (REPO_ROOT / "devcovenant" / "launcher_bootstrap.py").exists()
    assert "launcher_bootstrap" not in cli_text
    assert "launcher_bootstrap" not in main_text
    assert "apply_repo_pycache_prefix_from_cwd" not in cli_text
    assert "apply_repo_pycache_prefix_from_cwd" not in main_text


def _unit_test_cli_writes_run_logs_and_pointer_on_success(monkeypatch) -> None:
    """CLI should finalize a success run folder and print a log pointer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        monkeypatch.setattr(
            execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            execution_runtime_module,
            "configure_repo_pycache_prefix",
            lambda _repo_root: False,
        )
        monkeypatch.setattr(
            cli,
            "_maybe_reexec_managed_environment",
            lambda _command, _args: None,
        )
        monkeypatch.setattr(
            cli,
            "_load_command_module",
            lambda _command: SimpleNamespace(
                main=lambda _argv: (_ for _ in ()).throw(SystemExit(0))
            ),
        )
        monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                cli.main()
            except SystemExit as exc:
                code = exc.code
            else:  # pragma: no cover - defensive
                raise AssertionError("Expected SystemExit from cli.main().")

        assert code == 0
        assert "Run logs: devcovenant/logs/" in stdout_buffer.getvalue()
        logs_root = repo_root / "devcovenant" / "logs"
        run_dirs = sorted(
            path for path in logs_root.iterdir() if path.is_dir()
        )
        assert len(run_dirs) == 1
        latest_payload = json.loads(
            (
                repo_root
                / "devcovenant"
                / "registry"
                / "runtime"
                / "latest.json"
            ).read_text(encoding="utf-8")
        )
        run_payload = json.loads(
            (run_dirs[0] / "run.json").read_text(encoding="utf-8")
        )
        assert latest_payload["run_id"] == run_dirs[0].name
        assert latest_payload["status"] == "success"
        assert run_payload["status"] == "success"
        assert run_payload["command_name"] == "check"
        assert run_payload["invoked_python"]
        assert run_payload["effective_python"]
        assert "managed_environment_active" in run_payload
        assert "managed_reexec_applied" in run_payload


def _unit_test_cli_writes_run_logs_and_pointer_on_exception(
    monkeypatch,
) -> None:
    """CLI should normalize unhandled errors and keep traceback in logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        monkeypatch.setattr(
            execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            execution_runtime_module,
            "configure_repo_pycache_prefix",
            lambda _repo_root: False,
        )
        monkeypatch.setattr(
            cli,
            "_maybe_reexec_managed_environment",
            lambda _command, _args: None,
        )

        def _raise(_argv):
            """Raise one deterministic exception for CLI error-path tests."""
            raise RuntimeError("boom")

        monkeypatch.setattr(
            cli,
            "_load_command_module",
            lambda _command: SimpleNamespace(main=_raise),
        )
        monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                cli.main()
            except SystemExit as exc:
                code = exc.code
            else:  # pragma: no cover - defensive
                raise AssertionError("Expected SystemExit from cli.main().")

        assert code == 1
        assert "Error [internal-error]:" in stderr_buffer.getvalue()
        assert "Run logs: devcovenant/logs/" in stderr_buffer.getvalue()
        logs_root = repo_root / "devcovenant" / "logs"
        run_dirs = sorted(
            path for path in logs_root.iterdir() if path.is_dir()
        )
        assert len(run_dirs) == 1
        run_dir = run_dirs[0]
        run_payload = json.loads(
            (run_dir / "run.json").read_text(encoding="utf-8")
        )
        stderr_log = (run_dir / "stderr.log").read_text(encoding="utf-8")
        assert run_payload["status"] == "exception"
        assert "RuntimeError: boom" in stderr_log


def _unit_test_cli_adopts_handoff_run_log_without_duplicate_folder(
    monkeypatch,
) -> None:
    """CLI should reuse the handed-off run folder after managed re-exec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        run_logging = execution_runtime_module.run_logging_runtime_module
        existing = run_logging.create_run_log_context(
            repo_root,
            "check",
            ["devcovenant", "check"],
        )
        monkeypatch.setenv(cli._RUN_LOG_HANDOFF_REPO_ENV, str(repo_root))
        monkeypatch.setenv(cli._RUN_LOG_HANDOFF_RUN_ID_ENV, existing.run_id)
        monkeypatch.setenv(cli._MANAGED_REEXEC_SOURCE_ENV, "/usr/bin/python3")
        monkeypatch.setattr(
            execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            execution_runtime_module,
            "configure_repo_pycache_prefix",
            lambda _repo_root: False,
        )
        monkeypatch.setattr(
            cli,
            "_maybe_reexec_managed_environment",
            lambda _command, _args: None,
        )
        monkeypatch.setattr(
            cli,
            "_load_command_module",
            lambda _command: SimpleNamespace(
                main=lambda _argv: (_ for _ in ()).throw(SystemExit(0))
            ),
        )
        monkeypatch.setattr(sys, "argv", ["devcovenant", "check"])

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                cli.main()
            except SystemExit as exc:
                code = exc.code
            else:  # pragma: no cover - defensive
                raise AssertionError("Expected SystemExit from cli.main().")

        assert code == 0
        logs_root = repo_root / "devcovenant" / "logs"
        run_dirs = sorted(
            path for path in logs_root.iterdir() if path.is_dir()
        )
        assert [path.name for path in run_dirs] == [existing.run_id]
        run_payload = json.loads(
            (run_dirs[0] / "run.json").read_text(encoding="utf-8")
        )
        assert run_payload["status"] == "success"
        assert run_payload["managed_reexec_applied"] is True
        assert run_payload["invoked_python"] == "/usr/bin/python3"
        assert run_payload["effective_python"]


def _unit_test_cli_uninstall_skips_run_log_pointer(monkeypatch) -> None:
    """`uninstall` should not emit a run-log pointer it cannot preserve."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        monkeypatch.setattr(
            execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            execution_runtime_module,
            "configure_repo_pycache_prefix",
            lambda _repo_root: False,
        )
        monkeypatch.setattr(
            cli,
            "_maybe_reexec_managed_environment",
            lambda _command, _args: None,
        )
        monkeypatch.setattr(
            cli,
            "_load_command_module",
            lambda _command: SimpleNamespace(
                main=lambda _argv: (_ for _ in ()).throw(SystemExit(0))
            ),
        )
        monkeypatch.setattr(sys, "argv", ["devcovenant", "uninstall"])

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                cli.main()
            except SystemExit as exc:
                code = exc.code
            else:  # pragma: no cover - defensive
                raise AssertionError("Expected SystemExit from cli.main().")

        assert code == 0
        assert "Run logs:" not in stdout_buffer.getvalue()
        assert "Run logs:" not in stderr_buffer.getvalue()
        assert not (repo_root / "devcovenant" / "logs").exists()


def _unit_test_package_exports_are_explicit() -> None:
    """Package root should export only documented stable symbols."""
    assert devcovenant.__all__ == ["__version__"]


def _unit_test_source_checkout_import_disables_bytecode() -> None:
    """Source-checkout imports should disable Python cache-file writes."""
    package_init = (REPO_ROOT / "devcovenant" / "__init__.py").read_text(
        encoding="utf-8"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        package_dir = repo_root / "devcovenant"
        package_dir.mkdir(parents=True, exist_ok=True)
        (repo_root / ".git").mkdir()
        (package_dir / "__init__.py").write_text(
            package_init,
            encoding="utf-8",
        )
        (package_dir / "__main__.py").write_text(
            "from devcovenant import __version__\n",
            encoding="utf-8",
        )
        (package_dir / "VERSION").write_text(
            CURRENT_DEVCOVENANT_VERSION + "\n",
            encoding="utf-8",
        )
        (package_dir / "cli.py").write_text(
            "__all__ = []\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, os, pathlib, sys, devcovenant; "
                    "pkg = pathlib.Path("
                    "devcovenant.__file__).resolve().parent; "
                    "print(json.dumps({"
                    "'dont_write': sys.dont_write_bytecode, "
                    "'pycache_exists': (pkg / '__pycache__').exists()}))"
                ),
            ],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout.strip())
        assert payload["dont_write"] is True
        assert payload["pycache_exists"] is False


def _unit_test_source_checkout_import_cleans_repo_cache_on_exit() -> None:
    """Source imports should remove their own package cache on exit."""
    cache_dir = REPO_ROOT / "devcovenant" / "__pycache__"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    env = os.environ.copy()
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import devcovenant; print(devcovenant.__version__)",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == CURRENT_DEVCOVENANT_VERSION
    assert not cache_dir.exists()


def _unit_test_non_source_import_keeps_default_bytecode_mode() -> None:
    """Non-source imports should not force bytecode suppression."""
    package_init = (REPO_ROOT / "devcovenant" / "__init__.py").read_text(
        encoding="utf-8"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        package_dir = repo_root / "devcovenant"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text(
            package_init,
            encoding="utf-8",
        )
        (package_dir / "VERSION").write_text(
            CURRENT_DEVCOVENANT_VERSION + "\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys, devcovenant; "
                    "print(json.dumps({"
                    "'dont_write': sys.dont_write_bytecode}))"
                ),
            ],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout.strip())
        assert payload["dont_write"] is False


def _unit_test_test_mirror_import_disables_bytecode() -> None:
    """Source test-mirror imports should also avoid repo-local bytecode."""
    package_init = (REPO_ROOT / "devcovenant" / "__init__.py").read_text(
        encoding="utf-8"
    )
    tests_init = (REPO_ROOT / "tests" / "__init__.py").read_text(
        encoding="utf-8"
    )
    mirror_init = (
        REPO_ROOT / "tests" / "devcovenant" / "__init__.py"
    ).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        package_dir = repo_root / "devcovenant"
        tests_dir = repo_root / "tests"
        mirror_dir = tests_dir / "devcovenant"
        package_dir.mkdir(parents=True, exist_ok=True)
        mirror_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text(
            package_init,
            encoding="utf-8",
        )
        (package_dir / "__main__.py").write_text(
            "from devcovenant import __version__\n",
            encoding="utf-8",
        )
        (package_dir / "VERSION").write_text(
            CURRENT_DEVCOVENANT_VERSION + "\n",
            encoding="utf-8",
        )
        (package_dir / "cli.py").write_text(
            "__all__ = []\n",
            encoding="utf-8",
        )
        (tests_dir / "__init__.py").write_text(
            tests_init,
            encoding="utf-8",
        )
        (mirror_dir / "__init__.py").write_text(
            mirror_init,
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, pathlib, sys, tests.devcovenant; "
                    "pkg = pathlib.Path(tests.devcovenant.__file__)"
                    ".resolve().parent; "
                    "print(json.dumps({"
                    "'dont_write': sys.dont_write_bytecode, "
                    "'pycache_exists': (pkg / '__pycache__').exists()}))"
                ),
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout.strip())
        assert payload["dont_write"] is True
        assert payload["pycache_exists"] is False


def _unit_test_runtime_classes_not_exposed_at_package_root() -> None:
    """Runtime internals should not be exposed by the package root."""
    assert not hasattr(devcovenant, "DevCovenantEngine")
    assert not hasattr(devcovenant, "PolicyParser")
    assert not hasattr(devcovenant, "PolicyRegistry")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_cli_dispatches_command_and_args(self):
        """Run test_cli_dispatches_command_and_args."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_dispatches_command_and_args(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_cli_without_command_prints_help(self):
        """Run test_cli_without_command_prints_help."""
        result = subprocess.run(
            [sys.executable, "-m", "devcovenant"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "DevCovenant - repository governance framework",
            result.stdout,
        )

    def test_cli_unknown_command_fails(self):
        """Run test_cli_unknown_command_fails."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_unknown_command_fails(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_cli_version_flag_prints_version(self):
        """Run top-level version flag assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_version_flag_prints_version(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_cli_cleans_source_checkout_import_cache(self):
        """Run test_cli_cleans_source_checkout_import_cache."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_cleans_source_checkout_import_cache(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_reexecs_when_managed_env_differs(self):
        """Run test_cli_reexecs_when_managed_env_differs."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_reexecs_when_managed_env_differs(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_reexec_guard_prevents_loop(self):
        """Run test_cli_reexec_guard_prevents_loop."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_reexec_guard_prevents_loop(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_cli_reports_managed_error_without_rerun(self):
        """Run test_cli_reports_managed_error_without_rerun."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_reports_managed_error_without_rerun(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_reports_non_executable_managed_python(self):
        """Run non-executable managed Python SystemExit assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_reports_non_executable_managed_python(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_applies_root_level_output_override(self):
        """Run root-level output-override dispatch assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_applies_root_level_output_override(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_help_is_command_scoped(self):
        """Run test_run_help_is_command_scoped."""
        _unit_test_run_help_is_command_scoped()

    def test_root_help_lists_command_summaries(self):
        """Run test_root_help_lists_command_summaries."""
        _unit_test_root_help_lists_command_summaries()

    def test_asset_help_is_command_scoped(self):
        """Run test_asset_help_is_command_scoped."""
        _unit_test_asset_help_is_command_scoped()

    def test_check_help_shows_check_only_options(self):
        """Run test_check_help_shows_check_only_options."""
        _unit_test_check_help_shows_check_only_options()

    def test_install_help_shows_command_scope(self):
        """Run test_install_help_shows_command_scope."""
        _unit_test_install_help_shows_command_scope()

    def test_gate_help_is_command_scoped(self):
        """Run test_gate_help_is_command_scoped."""
        _unit_test_gate_help_is_command_scoped()

    def test_custom_help_is_command_scoped(self):
        """Run test_custom_help_is_command_scoped."""
        _unit_test_custom_help_is_command_scoped()

    def test_all_command_help_uses_scoped_prog(self):
        """Run test_all_command_help_uses_scoped_prog."""
        _unit_test_all_command_help_uses_scoped_prog()

    def test_root_command_modules_exist(self):
        """Run test_root_command_modules_exist."""
        _unit_test_root_command_modules_exist()

    def test_command_modules_not_duplicated_as_profile_assets(self):
        """Run test_command_modules_not_duplicated_as_profile_assets."""
        _unit_test_command_modules_not_duplicated_as_profile_assets()

    def test_command_modules_support_file_path_help(self):
        """Run test_command_modules_support_file_path_help."""
        _unit_test_command_modules_support_file_path_help()

    def test_launcher_contract_has_no_in_package_bootstrap(self):
        """Run no-bootstrap launcher source contract assertions."""
        _unit_test_launcher_contract_has_no_in_package_bootstrap()

    def test_package_exports_are_explicit(self):
        """Run test_package_exports_are_explicit."""
        _unit_test_package_exports_are_explicit()

    def test_runtime_classes_not_exposed_at_package_root(self):
        """Run test_runtime_classes_not_exposed_at_package_root."""
        _unit_test_runtime_classes_not_exposed_at_package_root()

    def test_source_checkout_import_disables_bytecode(self):
        """Run source-checkout bytecode suppression coverage."""
        _unit_test_source_checkout_import_disables_bytecode()

    def test_source_checkout_import_cleans_repo_cache_on_exit(self):
        """Run source-checkout package-cache cleanup coverage."""
        _unit_test_source_checkout_import_cleans_repo_cache_on_exit()

    def test_non_source_import_keeps_default_bytecode_mode(self):
        """Run non-source bytecode-default coverage."""
        _unit_test_non_source_import_keeps_default_bytecode_mode()

    def test_test_mirror_import_disables_bytecode(self):
        """Run source-test bytecode suppression coverage."""
        _unit_test_test_mirror_import_disables_bytecode()

    def test_cli_writes_run_logs_and_pointer_on_success(self):
        """Run CLI success-path run-log pointer assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_writes_run_logs_and_pointer_on_success(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_writes_run_logs_and_pointer_on_exception(self):
        """Run CLI exception-path run-log pointer assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_writes_run_logs_and_pointer_on_exception(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_adopts_handoff_run_log_without_duplicate_folder(self):
        """Run CLI managed re-exec run-log handoff reuse assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_adopts_handoff_run_log_without_duplicate_folder(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_cli_uninstall_skips_run_log_pointer(self):
        """Run uninstall run-log bypass assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_uninstall_skips_run_log_pointer(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()
