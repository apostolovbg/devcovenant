"""Tests for top-level DevCovenant CLI behavior and command layout."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import devcovenant
from devcovenant import cli
from tests.devcovenant.support import MonkeyPatch

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_COMMAND_MODULES = (
    "check",
    "gate",
    "test",
    "install",
    "deploy",
    "upgrade",
    "refresh",
    "uninstall",
    "undeploy",
    "update_lock",
)
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
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["command"] == "check"
    assert captured["argv"] == ["--nofix"]


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


def _unit_test_cli_reexecs_when_managed_env_differs(monkeypatch) -> None:
    """CLI should re-exec when managed interpreter differs from current."""
    repo_root = REPO_ROOT
    managed_python = str(repo_root / ".venv" / "bin" / "python")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli.execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
        "resolve_managed_environment_for_stage",
        lambda _repo_root, _stage, base_env=None: (
            {"PATH": "/tmp"},
            managed_python,
        ),
    )
    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
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
        "--nofix",
    ]
    env_payload = captured["env"]
    assert isinstance(env_payload, dict)
    assert env_payload[cli._MANAGED_REEXEC_GUARD_ENV] == "1"


def _unit_test_cli_reexec_guard_prevents_loop(monkeypatch) -> None:
    """Second managed re-exec attempt should fail with clear error."""
    repo_root = REPO_ROOT
    managed_python = str(repo_root / ".venv" / "bin" / "python")

    monkeypatch.setattr(
        cli.execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
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
        ["devcovenant", "check", "--nofix"],
    )
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
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


def _unit_test_cli_reexecs_with_managed_rerun_command(monkeypatch) -> None:
    """CLI should re-exec through metadata rerun command when configured."""
    repo_root = REPO_ROOT
    captured: dict[str, object] = {}

    def _raise_missing(_repo_root, _stage, base_env=None):
        """Raise the managed-interpreter missing error for fallback tests."""
        raise ValueError("managed-environment interpreter missing")

    monkeypatch.setattr(
        cli.execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
        "resolve_managed_environment_for_stage",
        _raise_missing,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
        "resolve_managed_rerun_command_for_stage",
        lambda _repo_root, _stage, _command, _args, **_kwargs: [
            "bench",
            "exec",
            "--",
            "devcovenant",
            _command,
            *_args,
        ],
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])
    monkeypatch.setattr(
        cli,
        "_initialize_cli_run_logging",
        lambda *_args, **_kwargs: None,
    )

    def _fake_execvpe(path: str, argv: list[str], env: dict[str, str]) -> None:
        """Capture execvpe contract and stop control flow."""
        captured["path"] = path
        captured["argv"] = list(argv)
        captured["env"] = dict(env)
        raise SystemExit(0)

    monkeypatch.setattr(cli.os, "execvpe", _fake_execvpe)
    monkeypatch.setattr(cli, "_load_command_module", lambda _command: None)

    try:
        cli.main()
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected SystemExit from cli.main().")

    assert code == 0
    assert captured["path"] == "bench"
    assert captured["argv"] == [
        "bench",
        "exec",
        "--",
        "devcovenant",
        "check",
        "--nofix",
    ]
    env_payload = captured["env"]
    assert isinstance(env_payload, dict)
    assert env_payload[cli._MANAGED_REEXEC_GUARD_ENV] == "1"


def _unit_test_cli_reports_managed_error_without_rerun(monkeypatch) -> None:
    """CLI should report managed-environment errors when no rerun exists."""
    repo_root = REPO_ROOT

    def _raise_missing(_repo_root, _stage, base_env=None):
        """Raise the managed-interpreter missing error for passthrough."""
        raise ValueError("managed-environment interpreter missing")

    monkeypatch.setattr(
        cli.execution_runtime_module,
        "find_git_root",
        lambda _path: repo_root,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
        "resolve_managed_environment_for_stage",
        _raise_missing,
    )
    monkeypatch.setattr(
        cli.execution_runtime_module,
        "resolve_managed_rerun_command_for_stage",
        lambda _repo_root, _stage, _command, _args, **_kwargs: None,
    )
    monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])
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


def _unit_test_test_help_is_command_scoped() -> None:
    """`test --help` should expose no extra lifecycle flags."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "test", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo" not in result.stdout
    assert "--install-mode" not in result.stdout
    assert "--docs-mode" not in result.stdout


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
    assert "--start" not in result.stdout
    assert "--end" not in result.stdout


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
    assert "--mode" not in result.stdout
    assert "--target" not in result.stdout
    assert "--docs-mode" not in result.stdout
    assert "--nofix" not in result.stdout


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
    assert "--start" in result.stdout
    assert "--end" in result.stdout
    assert "short gate session status" in result.stdout
    assert "--nofix" not in result.stdout
    assert "--norefresh" not in result.stdout


def _unit_test_root_command_modules_exist() -> None:
    """All CLI command modules should exist at package root."""
    for module_name in ROOT_COMMAND_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        assert root_path.exists(), str(root_path)


def _unit_test_command_modules_not_duplicated_as_profile_assets() -> None:
    """Root command modules should not be duplicated in profile assets."""
    for module_name in ROOT_COMMAND_MODULES:
        duplicate_path = ASSET_SCRIPT_ROOT / f"{module_name}.py"
        assert not duplicate_path.exists(), str(duplicate_path)


def _unit_test_command_modules_support_file_path_help() -> None:
    """File-path invocation should work without PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for module_name in ROOT_COMMAND_MODULES:
        result = subprocess.run(
            [sys.executable, f"devcovenant/{module_name}.py", "--help"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def _unit_test_cli_writes_run_logs_and_pointer_on_success(monkeypatch) -> None:
    """CLI should finalize a success run folder and print a log pointer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        monkeypatch.setattr(
            cli.execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            cli.execution_runtime_module,
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
        monkeypatch.setattr(sys, "argv", ["devcovenant", "check", "--nofix"])

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
            (logs_root / "latest.json").read_text(encoding="utf-8")
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
    """CLI should log tracebacks and print a pointer when command raises."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / ".git").mkdir()
        (repo_root / "devcovenant").mkdir()
        monkeypatch.setattr(
            cli.execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            cli.execution_runtime_module,
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
            except RuntimeError as exc:
                message = str(exc)
            else:  # pragma: no cover - defensive
                raise AssertionError("Expected RuntimeError from cli.main().")

        assert message == "boom"
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
        run_logging = cli.execution_runtime_module.run_logging_runtime_module
        existing = run_logging.create_run_log_context(
            repo_root,
            "check",
            ["devcovenant", "check"],
        )
        monkeypatch.setenv(cli._RUN_LOG_HANDOFF_REPO_ENV, str(repo_root))
        monkeypatch.setenv(cli._RUN_LOG_HANDOFF_RUN_ID_ENV, existing.run_id)
        monkeypatch.setenv(cli._MANAGED_REEXEC_SOURCE_ENV, "/usr/bin/python3")
        monkeypatch.setattr(
            cli.execution_runtime_module,
            "find_git_root",
            lambda _path: repo_root,
        )
        monkeypatch.setattr(
            cli.execution_runtime_module,
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


def _unit_test_package_exports_are_explicit() -> None:
    """Package root should export only documented stable symbols."""
    assert devcovenant.__all__ == ["__version__"]


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
            "DevCovenant - Self-enforcing policy system",
            result.stdout,
        )

    def test_cli_unknown_command_fails(self):
        """Run test_cli_unknown_command_fails."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_unknown_command_fails(monkeypatch=monkeypatch)
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

    def test_cli_reexecs_with_managed_rerun_command(self):
        """Run test_cli_reexecs_with_managed_rerun_command."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_cli_reexecs_with_managed_rerun_command(
                monkeypatch=monkeypatch
            )
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

    def test_test_help_is_command_scoped(self):
        """Run test_test_help_is_command_scoped."""
        _unit_test_test_help_is_command_scoped()

    def test_check_help_shows_check_only_options(self):
        """Run test_check_help_shows_check_only_options."""
        _unit_test_check_help_shows_check_only_options()

    def test_install_help_shows_command_scope(self):
        """Run test_install_help_shows_command_scope."""
        _unit_test_install_help_shows_command_scope()

    def test_gate_help_is_command_scoped(self):
        """Run test_gate_help_is_command_scoped."""
        _unit_test_gate_help_is_command_scoped()

    def test_root_command_modules_exist(self):
        """Run test_root_command_modules_exist."""
        _unit_test_root_command_modules_exist()

    def test_command_modules_not_duplicated_as_profile_assets(self):
        """Run test_command_modules_not_duplicated_as_profile_assets."""
        _unit_test_command_modules_not_duplicated_as_profile_assets()

    def test_command_modules_support_file_path_help(self):
        """Run test_command_modules_support_file_path_help."""
        _unit_test_command_modules_support_file_path_help()

    def test_package_exports_are_explicit(self):
        """Run test_package_exports_are_explicit."""
        _unit_test_package_exports_are_explicit()

    def test_runtime_classes_not_exposed_at_package_root(self):
        """Run test_runtime_classes_not_exposed_at_package_root."""
        _unit_test_runtime_classes_not_exposed_at_package_root()

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
