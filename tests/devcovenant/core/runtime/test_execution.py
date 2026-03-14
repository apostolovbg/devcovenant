"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

MODULE = "devcovenant.core.runtime.execution"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_execution_symbol_contract_is_stable() -> None:
    """Execution runtime helper symbols should remain available."""
    module = importlib.import_module(MODULE)
    expected = [
        "ChildOutputChannel",
        "configure_repo_pycache_prefix",
        "resolve_managed_environment_for_stage",
        "resolve_managed_rerun_command_for_stage",
        "resolve_child_output_plan_for_channel",
        "rewrite_command_for_managed_python",
        "rewrite_command_string_for_managed_python",
        "resolve_required_test_commands",
        "registry_required_commands",
        "run_child_command_with_output_policy",
        "run_and_record_tests",
    ]
    for symbol in expected:
        assert hasattr(module, symbol), symbol


def _unit_test_execution_symbols_cover_runtime_helpers() -> None:
    """Execution runtime should expose expected helper symbols."""
    module = importlib.import_module(MODULE)
    expected = [
        "ConsoleReporter",
        "Reporter",
        "capture_current_numstat_snapshot",
        "capture_current_snapshot_paths",
        "append_active_run_log_output",
        "configure_logs_keep_last",
        "configure_output_mode",
        "configure_logs_keep_last_from_config",
        "configure_output_mode_from_config",
        "clear_active_run_log_context",
        "emit_active_run_log_pointer",
        "find_git_root",
        "finalize_active_run_log_context",
        "get_logs_keep_last",
        "get_output_mode",
        "get_active_run_log_context",
        "merge_active_run_log_metadata",
        "normal_mode_prefers_live_streaming_for_command",
        "print_banner",
        "print_step",
        "read_local_version",
        "record_gate_status",
        "resolve_repo_root",
        "resolve_child_output_plan_for_channel",
        "resolve_tests_output_mode",
        "run_bootstrap_registry_refresh",
        "run_child_command_with_output_policy",
        "run_subprocess_with_runtime_output",
        "runtime_print",
        "set_active_run_log_context",
        "session_delta_paths",
        "snapshot_paths_changed_since",
        "top_level_command_name",
    ]
    for symbol in expected:
        assert hasattr(module, symbol), symbol

    reporter_cls = module.ConsoleReporter
    for method in ["banner", "emit", "step"]:
        assert hasattr(reporter_cls, method), method

    progress_cls = module._TestCommandProgress
    for method in [
        "close",
        "complete_step",
        "describe",
        "fail_step",
        "start_step",
    ]:
        assert hasattr(progress_cls, method), method


def _unit_test_execution_symbol_assertions_cover_public_api() -> None:
    """Execution runtime should provide explicit symbol coverage."""
    module = importlib.import_module(MODULE)
    assert module.Reporter
    assert module.ConsoleReporter
    assert module.append_active_run_log_output
    assert module.capture_current_numstat_snapshot
    assert module.capture_current_snapshot_paths
    assert module.cleanup_repo_bytecode_artifacts
    assert module.clear_active_run_log_context
    assert module.configure_logs_keep_last
    assert module.configure_logs_keep_last_from_config
    assert module.configure_output_mode
    assert module.configure_output_mode_from_config
    assert module.emit_active_run_log_pointer
    assert module.finalize_active_run_log_context
    assert module.find_git_root
    assert module.get_logs_keep_last
    assert module.get_output_mode
    assert module.get_active_run_log_context
    assert module.merge_active_run_log_metadata
    assert module.normal_mode_prefers_live_streaming_for_command
    assert module.print_banner
    assert module.print_step
    assert module.read_local_version
    assert module.record_gate_status
    assert module.registry_required_commands
    assert module.resolve_managed_environment_for_stage
    assert module.resolve_managed_rerun_command_for_stage
    assert module.resolve_child_output_plan_for_channel
    assert module.resolve_repo_root
    assert module.resolve_required_test_commands
    assert module.resolve_tests_output_mode
    assert module.rewrite_command_for_managed_python
    assert module.rewrite_command_string_for_managed_python
    assert module.run_and_record_tests
    assert module.run_bootstrap_registry_refresh
    assert module.run_child_command_with_output_policy
    assert module.run_subprocess_with_runtime_output
    assert module.runtime_print
    assert module.set_active_run_log_context
    assert module.session_delta_paths
    assert module.snapshot_paths_changed_since
    assert module.top_level_command_name
    assert module.warn_version_mismatch
    progress_cls = module._TestCommandProgress
    assert progress_cls.close
    assert progress_cls.complete_step
    assert progress_cls.describe


def _unit_test_console_reporter_flushes_console_streams_by_default() -> None:
    """Console reporter should flush stdout/stderr-style writes by default."""
    module = importlib.import_module(MODULE)

    class _CountingStream:
        """Minimal writable stream that counts flush calls."""

        def __init__(self) -> None:
            """Initialize write/flush counters for reporter assertions."""
            self.writes: list[str] = []
            self.flush_calls = 0

        def write(self, text: str) -> int:
            """Record written text and mimic text-stream write return value."""
            self.writes.append(text)
            return len(text)

        def flush(self) -> None:
            """Increment flush-call count for line-flush assertions."""
            self.flush_calls += 1

    stream = _CountingStream()
    previous_stdout = module.sys.stdout
    try:
        module.sys.stdout = stream
        reporter = module.ConsoleReporter("normal")
        reporter.emit("live line")
    finally:
        module.sys.stdout = previous_stdout

    assert stream.writes == ["live line\n"]
    assert stream.flush_calls == 1


def _unit_test_console_reporter_suppresses_stdout_in_quiet_mode() -> None:
    """Quiet-mode reporter should suppress stdout but keep stderr visible."""
    module = importlib.import_module(MODULE)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    previous_stdout = module.sys.stdout
    previous_stderr = module.sys.stderr
    try:
        module.sys.stdout = stdout_buffer
        module.sys.stderr = stderr_buffer
        reporter = module.ConsoleReporter("quiet")
        reporter.emit("suppressed stdout")
        reporter.emit("visible stderr", stream=module.sys.stderr)
    finally:
        module.sys.stdout = previous_stdout
        module.sys.stderr = previous_stderr

    assert stdout_buffer.getvalue() == ""
    assert stderr_buffer.getvalue() == "visible stderr\n"


def _unit_test_streaming_helper_emits_wait_heartbeat_for_silent_step() -> None:
    """Heartbeat should follow console silence, not hidden child output."""
    module = importlib.import_module(MODULE)
    stdout_buffer = io.StringIO()
    command = [
        sys.executable,
        "-c",
        "import time; time.sleep(0.08); print('done')",
    ]
    with redirect_stdout(stdout_buffer):
        result, combined = module.run_subprocess_with_runtime_output(
            command,
            emit_console=False,
            capture_combined_output=True,
            heartbeat_message="Please wait. In progress...",
            heartbeat_initial_seconds=0.02,
            heartbeat_repeat_seconds=60.0,
        )
    output = stdout_buffer.getvalue()
    assert result.returncode == 0
    assert "Please wait. In progress..." in output
    assert "done" not in output
    assert "done" in combined


def _unit_test_streaming_helper_prefers_pty_for_console_output() -> None:
    """Console-emitting subprocesses should use PTY path when available."""
    module = importlib.import_module(MODULE)
    previous_pty = module.pty
    previous_pty_runner = module._run_subprocess_with_runtime_output_pty
    previous_pipe_runner = module._run_subprocess_with_runtime_output_pipe
    calls: list[str] = []

    def _fake_pty_runner(*_args, **_kwargs):
        """Record PTY dispatch and return a successful fake completion."""
        calls.append("pty")
        return module.subprocess.CompletedProcess(["echo"], 0), ""

    def _fake_pipe_runner(*_args, **_kwargs):
        """Record pipe dispatch and return a successful fake completion."""
        calls.append("pipe")
        return module.subprocess.CompletedProcess(["echo"], 0), ""

    try:
        module.pty = object()
        module._run_subprocess_with_runtime_output_pty = _fake_pty_runner
        module._run_subprocess_with_runtime_output_pipe = _fake_pipe_runner
        result, combined = module.run_subprocess_with_runtime_output(
            ["echo", "ok"],
            emit_console=True,
            capture_combined_output=True,
        )
    finally:
        module.pty = previous_pty
        module._run_subprocess_with_runtime_output_pty = previous_pty_runner
        module._run_subprocess_with_runtime_output_pipe = previous_pipe_runner

    assert result.returncode == 0
    assert combined == ""
    assert calls == ["pty"]


def _unit_test_streaming_helper_uses_pipe_when_console_is_suppressed() -> None:
    """Hidden-console subprocesses should bypass PTY and use pipe fallback."""
    module = importlib.import_module(MODULE)
    previous_pty = module.pty
    previous_pty_runner = module._run_subprocess_with_runtime_output_pty
    previous_pipe_runner = module._run_subprocess_with_runtime_output_pipe
    calls: list[str] = []

    def _fake_pty_runner(*_args, **_kwargs):
        """Record PTY dispatch and return a successful fake completion."""
        calls.append("pty")
        return module.subprocess.CompletedProcess(["echo"], 0), ""

    def _fake_pipe_runner(*_args, **_kwargs):
        """Record pipe dispatch and return a successful fake completion."""
        calls.append("pipe")
        return module.subprocess.CompletedProcess(["echo"], 0), ""

    try:
        module.pty = object()
        module._run_subprocess_with_runtime_output_pty = _fake_pty_runner
        module._run_subprocess_with_runtime_output_pipe = _fake_pipe_runner
        result, combined = module.run_subprocess_with_runtime_output(
            ["echo", "ok"],
            emit_console=False,
            capture_combined_output=True,
        )
    finally:
        module.pty = previous_pty
        module._run_subprocess_with_runtime_output_pty = previous_pty_runner
        module._run_subprocess_with_runtime_output_pipe = previous_pipe_runner

    assert result.returncode == 0
    assert combined == ""
    assert calls == ["pipe"]


def _unit_test_resolve_child_output_plan_uses_channel_policy_matrix() -> None:
    """Channel-plan helper should resolve from active output mode."""
    module = importlib.import_module(MODULE)
    previous_mode = module.get_output_mode()
    try:
        module.configure_output_mode("normal")
        plan = module.resolve_child_output_plan_for_channel("test_child")
        assert plan.emit_console is False
        assert plan.heartbeat_message == "Please wait. In progress..."
        module.configure_output_mode("quiet")
        plan = module.resolve_child_output_plan_for_channel("gate_child")
        assert plan.emit_console is False
        assert plan.heartbeat_message is None
    finally:
        module.configure_output_mode(previous_mode)


def _unit_test_run_child_command_uses_shared_output_pipeline() -> None:
    """Child command helper should pass resolved policy to stream runner."""
    module = importlib.import_module(MODULE)
    previous_runner = module.run_subprocess_with_runtime_output
    captured: dict[str, object] = {}

    def _fake_runner(command, **kwargs):
        """Capture delegated kwargs and return successful completion."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (module.subprocess.CompletedProcess(["echo"], 0), "")

    try:
        module.run_subprocess_with_runtime_output = _fake_runner
        result, combined = module.run_child_command_with_output_policy(
            ["echo", "ok"],
            channel="test_child",
            capture_combined_output=True,
            output_mode="normal",
        )
    finally:
        module.run_subprocess_with_runtime_output = previous_runner

    kwargs = dict(captured["kwargs"])
    assert result.returncode == 0
    assert combined == ""
    assert kwargs["emit_console"] is False
    assert kwargs["capture_combined_output"] is True
    assert kwargs["heartbeat_message"] == "Please wait. In progress..."


def _unit_test_pipe_fallback_streams_output_before_process_exit() -> None:
    """Pipe fallback should emit child lines before process completion."""
    module = importlib.import_module(MODULE)
    previous_pty = module.pty
    previous_runtime_print = module.runtime_print
    seen_timestamps: dict[str, float] = {}
    command = [
        sys.executable,
        "-c",
        (
            "import time; "
            "print('first-line', flush=True); "
            "time.sleep(0.2); "
            "print('second-line', flush=True)"
        ),
    ]

    def _recording_runtime_print(*args, **kwargs):
        """Capture line timestamps while delegating to runtime output sink."""
        message = " ".join(str(arg) for arg in args)
        now = module.time.monotonic()
        if "first-line" in message:
            seen_timestamps.setdefault("first-line", now)
        if "second-line" in message:
            seen_timestamps.setdefault("second-line", now)
        return previous_runtime_print(*args, **kwargs)

    stdout_buffer = io.StringIO()
    try:
        module.pty = None
        module.runtime_print = _recording_runtime_print
        started = module.time.monotonic()
        with redirect_stdout(stdout_buffer):
            result, _ = module.run_subprocess_with_runtime_output(
                command,
                emit_console=True,
                capture_combined_output=False,
                heartbeat_message=None,
            )
        finished = module.time.monotonic()
    finally:
        module.pty = previous_pty
        module.runtime_print = previous_runtime_print

    assert result.returncode == 0
    assert "first-line" in stdout_buffer.getvalue()
    assert "second-line" in stdout_buffer.getvalue()
    assert "first-line" in seen_timestamps
    assert "second-line" in seen_timestamps
    assert seen_timestamps["first-line"] >= started
    assert seen_timestamps["first-line"] < seen_timestamps["second-line"]
    assert seen_timestamps["first-line"] < finished - 0.05


def _unit_test_normal_mode_command_policy_matrix_defaults() -> None:
    """Normal-mode policy should keep live streaming enabled for commands."""
    module = importlib.import_module(MODULE)
    previous = os.environ.get("DEVCOV_TOP_COMMAND")
    previous_mode = module.get_output_mode()
    try:
        os.environ["DEVCOV_TOP_COMMAND"] = "install"
        module.configure_output_mode("normal")
        assert module.top_level_command_name() == "install"
        assert module.normal_mode_prefers_live_streaming_for_command() is True
        os.environ["DEVCOV_TOP_COMMAND"] = "test"
        assert module.normal_mode_prefers_live_streaming_for_command() is True
        assert (
            module.normal_mode_prefers_live_streaming_for_command("upgrade")
            is True
        )
        assert (
            module.normal_mode_prefers_live_streaming_for_command("check")
            is True
        )
        module.configure_output_mode("quiet")
        assert module.normal_mode_prefers_live_streaming_for_command() is False
    finally:
        module.configure_output_mode(previous_mode)
        if previous is None:
            os.environ.pop("DEVCOV_TOP_COMMAND", None)
        else:
            os.environ["DEVCOV_TOP_COMMAND"] = previous


def _repo_root_for_output_doc_contract() -> Path:
    """Resolve repository root for output-contract doc assertions."""
    return Path(__file__).resolve().parents[4]


def _read_output_doc_contract_text(path: str) -> str:
    """Read one repo-relative text file for output-contract assertions."""
    return (_repo_root_for_output_doc_contract() / path).read_text(
        encoding="utf-8"
    )


def _unit_test_readmes_use_tests_output_mode_for_test_contract() -> None:
    """README surfaces should anchor test output to tests_output_mode."""
    for path in ("README.md", "devcovenant/README.md"):
        content = _read_output_doc_contract_text(path)
        assert "In `engine.tests_output_mode: normal`" in content, path
        assert "In `engine.output_mode: normal`, test progress" not in content


def _unit_test_package_docs_remain_neutral_for_repo_specific_profiles() -> (
    None
):
    """Package docs should avoid repo-specific profile naming."""
    for path in (
        "devcovenant/docs/architecture.md",
        "devcovenant/docs/config.md",
        "devcovenant/docs/installation.md",
        "devcovenant/docs/policies.md",
        "devcovenant/docs/profiles.md",
        "devcovenant/docs/workflow.md",
    ):
        content = _read_output_doc_contract_text(path).lower()
        assert "devcovrepo" not in content, path


def _unit_test_global_config_template_documents_quiet_mode() -> None:
    """Global config template comments should preserve quiet-mode selectors."""
    content = _read_output_doc_contract_text(
        "devcovenant/builtin/profiles/global/assets/config.yaml"
    )
    assert content.count("Allowed values: normal, quiet, verbose") >= 2
    assert "output_mode: verbose" in content
    assert "tests_output_mode: verbose" in content


def _unit_test_normal_mode_test_message_contract_is_stable() -> None:
    """Normal-mode test message should remain concise and log-first."""
    content = _read_output_doc_contract_text(
        "devcovenant/core/runtime/execution.py"
    )
    assert (
        "Please wait for test commands to execute. Full output is "
    ) in content
    assert "available in run logs." in content


def _unit_test_ci_workflow_split_docs_are_consistent() -> None:
    """Docs should keep generated-vs-repo workflow ownership explicit."""
    profiles = _read_output_doc_contract_text("devcovenant/docs/profiles.md")
    workflow = _read_output_doc_contract_text("devcovenant/docs/workflow.md")
    installation = _read_output_doc_contract_text(
        "devcovenant/docs/installation.md"
    )
    readme = _read_output_doc_contract_text("README.md")

    assert "repo-maintained copy of" not in profiles
    assert "refresh-generated output" in profiles
    assert (
        "Repository-maintained workflows (not refresh-generated):"
    ) in workflow
    assert ".github/workflows/build.yml" in installation
    assert ".github/workflows/publish.yml" in installation
    assert "repository-maintained workflows" in installation
    assert "refresh-generated governance gate pipeline" in readme


def _unit_test_workflow_doc_marks_mid_gate_required() -> None:
    """Workflow docs should keep gate --mid mandatory on command surfaces."""
    content = _read_output_doc_contract_text("devcovenant/docs/workflow.md")
    assert "gate --start -> gate --mid loop (rerun until clean)" in content
    assert "run `gate --mid` before tests" in content
    assert "optional mutating preflight" not in content


def _unit_test_repo_pycache_prefix_sets_env_and_runtime_prefix() -> None:
    """Repo pycache prefix config should route bytecode caches out of repo."""
    module = importlib.import_module(MODULE)
    previous_env = os.environ.get("PYTHONPYCACHEPREFIX")
    previous_prefix = getattr(module.sys, "pycache_prefix", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path = repo_root / "devcovenant" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                "profiles:\n  active:\n  - devcovrepo\n"
                "engine:\n"
                "  pycache_prefix_enabled: true\n"
                "  pycache_prefix: ''\n",
                encoding="utf-8",
            )
            enabled = module.configure_repo_pycache_prefix(repo_root)
            assert enabled is True
            resolved = os.environ.get("PYTHONPYCACHEPREFIX")
            assert resolved
            assert resolved != str(repo_root / "devcovenant")
            assert "/devcovenant-pycache/" in resolved.replace("\\", "/")
            assert getattr(module.sys, "pycache_prefix", None) == resolved
            assert module._PYCACHE_PREFIX_ENABLED is True
            assert module._PYCACHE_PREFIX_VALUE == resolved
    finally:
        if previous_env is None:
            os.environ.pop("PYTHONPYCACHEPREFIX", None)
        else:
            os.environ["PYTHONPYCACHEPREFIX"] = previous_env
        try:
            module.sys.pycache_prefix = previous_prefix
        except (AttributeError, TypeError):
            pass
        module._PYCACHE_PREFIX_ENABLED = False
        module._PYCACHE_PREFIX_VALUE = None


def _unit_test_apply_repo_bytecode_env_forces_unbuffered_output() -> None:
    """Repo runtime env helper should force unbuffered child Python output."""
    module = importlib.import_module(MODULE)
    resolved = module._apply_repo_bytecode_env({"PYTHONUNBUFFERED": "0"})
    assert resolved["PYTHONUNBUFFERED"] == "1"


def _unit_test_repo_pycache_prefix_honors_custom_relative_path() -> None:
    """Custom relative pycache prefix should resolve against repo root."""
    module = importlib.import_module(MODULE)
    previous_env = os.environ.get("PYTHONPYCACHEPREFIX")
    previous_prefix = getattr(module.sys, "pycache_prefix", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path = repo_root / "devcovenant" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                "profiles:\n  active:\n  - devcovrepo\n"
                "engine:\n"
                "  pycache_prefix_enabled: true\n"
                "  pycache_prefix: .cache/pycache\n",
                encoding="utf-8",
            )
            enabled = module.configure_repo_pycache_prefix(repo_root)
            assert enabled is True
            expected = str(repo_root / ".cache" / "pycache")
            assert os.environ.get("PYTHONPYCACHEPREFIX") == expected
            assert module._PYCACHE_PREFIX_VALUE == expected
    finally:
        if previous_env is None:
            os.environ.pop("PYTHONPYCACHEPREFIX", None)
        else:
            os.environ["PYTHONPYCACHEPREFIX"] = previous_env
        try:
            module.sys.pycache_prefix = previous_prefix
        except (AttributeError, TypeError):
            pass
        module._PYCACHE_PREFIX_ENABLED = False
        module._PYCACHE_PREFIX_VALUE = None


def _unit_test_repo_bytecode_cleanup_removes_artifacts() -> None:
    """Repo bytecode cleanup should remove cache artifacts."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        cache_dir = repo_root / "devcovenant" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pyc_path = cache_dir / "execution.cpython-314.pyc"
        pyc_path.write_text("test", encoding="utf-8")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "profiles:\n  active:\n  - devcovrepo\n",
            encoding="utf-8",
        )
        removed = module.cleanup_repo_bytecode_artifacts(repo_root)
        assert removed is True
        assert not cache_dir.exists()
        assert not pyc_path.exists()


def _unit_test_resolve_engine_auto_fix_enabled_defaults_false() -> None:
    """Autofix resolver should default to disabled when key is absent."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "engine:\n  output_mode: normal\n",
            encoding="utf-8",
        )
        assert module.resolve_engine_auto_fix_enabled(repo_root) is False


def _unit_test_resolve_engine_auto_fix_enabled_reads_bool_flag() -> None:
    """Autofix resolver should honor explicit true/false config values."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "engine:\n  auto_fix_enabled: true\n",
            encoding="utf-8",
        )
        assert module.resolve_engine_auto_fix_enabled(repo_root) is True
        config_path.write_text(
            "engine:\n  auto_fix_enabled: false\n",
            encoding="utf-8",
        )
        assert module.resolve_engine_auto_fix_enabled(repo_root) is False


def _unit_test_configure_logs_keep_last_defaults_and_reads_value() -> None:
    """Log-retention config should default to 0 and honor non-negative ints."""
    module = importlib.import_module(MODULE)
    previous_keep = module.get_logs_keep_last()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path = repo_root / "devcovenant" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                "engine:\n  output_mode: normal\n",
                encoding="utf-8",
            )
            assert module.configure_logs_keep_last_from_config(repo_root) == 0
            assert module.get_logs_keep_last() == 0

            config_path.write_text(
                "engine:\n  logs_keep_last: 20\n",
                encoding="utf-8",
            )
            assert module.configure_logs_keep_last_from_config(repo_root) == 20
            assert module.get_logs_keep_last() == 20

            config_path.write_text(
                "engine:\n  logs_keep_last: -7\n",
                encoding="utf-8",
            )
            assert module.configure_logs_keep_last_from_config(repo_root) == 0
            assert module.get_logs_keep_last() == 0
    finally:
        module.configure_logs_keep_last(previous_keep)


def _unit_test_active_run_log_captures_runtime_and_subprocess_output() -> None:
    """Active run logging captures runtime prints and subprocess output."""
    module = importlib.import_module(MODULE)
    run_logging = module.run_logging_runtime_module
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = run_logging.create_run_log_context(
            repo_root,
            "test",
            ["devcovenant", "test"],
        )
        previous_test_mode = module._TEST_COMMAND_OUTPUT_MODE
        previous_test_label = module._TEST_COMMAND_LABEL
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        try:
            module.set_active_run_log_context(context)
            with (
                redirect_stdout(stdout_buffer),
                redirect_stderr(stderr_buffer),
            ):
                module.runtime_print("runtime line")
                module._TEST_COMMAND_OUTPUT_MODE = None
                module._TEST_COMMAND_LABEL = ""
                module._run_command(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import sys; "
                            "print('subprocess stdout'); "
                            "print('subprocess stderr', file=sys.stderr)"
                        ),
                    ],
                    allow_codes={0},
                    cwd=repo_root,
                )
                module.emit_active_run_log_pointer()
            module.finalize_active_run_log_context(
                exit_code=0,
                status="success",
            )
        finally:
            module._TEST_COMMAND_OUTPUT_MODE = previous_test_mode
            module._TEST_COMMAND_LABEL = previous_test_label
            module.clear_active_run_log_context()

        stdout_log = context.require_paths().stdout_log.read_text(
            encoding="utf-8"
        )
        stderr_log = context.require_paths().stderr_log.read_text(
            encoding="utf-8"
        )
        tail_text = context.require_paths().tail_txt.read_text(
            encoding="utf-8"
        )
        summary_json = context.require_paths().summary_json.read_text(
            encoding="utf-8"
        )

        assert "runtime line" in stdout_log
        assert "subprocess stdout" in stdout_log
        assert "subprocess stderr" in stdout_log
        assert "Run logs:" in stdout_log
        assert "subprocess stderr" not in stderr_log
        assert "Run logs:" in tail_text
        assert '"command_family": "test"' in summary_json


def _unit_test_emit_active_run_log_pointer_supports_once_semantics() -> None:
    """One-time pointer mode should avoid duplicate console pointer lines."""
    module = importlib.import_module(MODULE)
    run_logging = module.run_logging_runtime_module
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = run_logging.create_run_log_context(
            repo_root,
            "test",
            ["devcovenant", "test"],
        )
        stdout_buffer = io.StringIO()
        try:
            module.set_active_run_log_context(context)
            with redirect_stdout(stdout_buffer):
                first = module.emit_active_run_log_pointer(once=True)
                second = module.emit_active_run_log_pointer(once=True)
            module.finalize_active_run_log_context(
                exit_code=0,
                status="success",
            )
        finally:
            module.clear_active_run_log_context()

        output = stdout_buffer.getvalue()
        assert first is not None
        assert second == first
        assert output.count("Run logs: ") == 1


def _unit_test_test_command_progress_emits_sparse_lines_in_normal_mode() -> (
    None
):
    """Normal-mode test progress should emit sparse deterministic lines."""
    module = importlib.import_module(MODULE)
    stdout_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer):
        with module._TestCommandProgress(2, output_mode="normal") as progress:
            progress.describe("python3 -m unittest discover -v")
            progress.start_step("python3 -m unittest discover -v")
            progress.complete_step("python3 -m unittest discover -v")
            progress.describe("pytest")
            progress.start_step("pytest")
            progress.fail_step("pytest", 2)
    output = stdout_buffer.getvalue()
    assert "▶ [1/2] python3 -m unittest discover -v" in output
    assert "\n[1/2] python3 -m unittest discover -v\n" not in output
    assert "▶ [2/2] pytest" in output
    assert "[2/2] FAILED: pytest (exit 2)" in output


def _unit_test_normal_mode_test_child_output_is_suppressed_and_logged() -> (
    None
):
    """Normal-mode test child output should be suppressed yet still logged."""
    module = importlib.import_module(MODULE)
    run_logging = module.run_logging_runtime_module
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = run_logging.create_run_log_context(
            repo_root,
            "test",
            ["devcovenant", "test"],
        )
        previous_test_mode = module._TEST_COMMAND_OUTPUT_MODE
        previous_test_label = module._TEST_COMMAND_LABEL
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        try:
            module.set_active_run_log_context(context)
            module._TEST_COMMAND_OUTPUT_MODE = "normal"
            module._TEST_COMMAND_LABEL = "pytest"
            with (
                redirect_stdout(stdout_buffer),
                redirect_stderr(stderr_buffer),
            ):
                module._run_command(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import sys; "
                            "print('normal stdout line'); "
                            "print('normal stderr line', file=sys.stderr)"
                        ),
                    ],
                    allow_codes={0},
                    cwd=repo_root,
                )
            module.finalize_active_run_log_context(
                exit_code=0,
                status="success",
            )
        finally:
            module._TEST_COMMAND_OUTPUT_MODE = previous_test_mode
            module._TEST_COMMAND_LABEL = previous_test_label
            module.clear_active_run_log_context()

        console_output = stdout_buffer.getvalue()
        assert "normal stdout line" not in console_output
        assert "normal stderr line" not in console_output
        stdout_log = context.require_paths().stdout_log.read_text(
            encoding="utf-8"
        )
        assert "normal stdout line" in stdout_log
        assert "normal stderr line" in stdout_log


def _unit_test_build_test_run_summary_metadata_includes_counts_and_hints() -> (
    None
):
    """Test summary metadata should include counts, duration, and hints."""
    module = importlib.import_module(MODULE)
    started = module._dt.datetime(
        2026,
        2,
        25,
        12,
        0,
        0,
        tzinfo=module._dt.timezone.utc,
    )
    finished = started + module._dt.timedelta(seconds=3.25)
    events = [
        SimpleNamespace(
            to_dict=lambda: {
                "command": ["pytest"],
                "duration_seconds": 1.5,
                "status": "failure",
                "started_at": "2026-02-25T12:00:00+00:00",
                "finished_at": "2026-02-25T12:00:01.500000+00:00",
                "metadata": {"exit_code": 1},
                "exit_code": 1,
            }
        )
    ]
    payload = module._build_test_run_summary_metadata(
        commands=[("pytest", ["pytest"])],
        events=events,
        tests_output_mode="normal",
        source_field="required_commands",
        started=started,
        finished=finished,
        first_failed_command="pytest",
        first_failed_exit_code=1,
        passed_commands=0,
        failed_commands=1,
    )
    assert payload["total_commands"] == 1
    assert payload["passed_commands"] == 0
    assert payload["failed_commands"] == 1
    assert payload["duration_seconds"] == 3.25
    assert payload["duration_breakdown_version"] == "1.0"
    assert payload["duration_events_count"] == 1
    assert payload["duration_seconds_min_command"] == 1.5
    assert payload["duration_seconds_avg_command"] == 1.5
    assert payload["duration_seconds_max_command"] == 1.5
    assert len(payload["command_durations"]) == 1
    assert payload["command_durations"][0]["duration_seconds"] == 1.5
    assert payload["command_durations"][0]["command"] == "pytest"
    assert payload["first_failed_command"] == "pytest"
    assert payload["failure_hint"]
    assert payload["normal_console_flood_suppressed"] is True
    assert payload["normal_console_streaming"] is False


def _unit_test_test_profile_artifacts_are_written_for_active_run() -> None:
    """Test runs should emit repeatable profiling artifacts in run logs."""
    module = importlib.import_module(MODULE)
    logging_module = importlib.import_module(
        "devcovenant.core.runtime.run_logging"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = logging_module.create_run_log_context(
            repo_root=repo_root,
            command_name="test",
            argv=("devcovenant", "test"),
        )
        module.set_active_run_log_context(context)
        started = module._dt.datetime(
            2026,
            2,
            27,
            12,
            0,
            0,
            tzinfo=module._dt.timezone.utc,
        )
        finished = started + module._dt.timedelta(seconds=30.0)
        events = [
            SimpleNamespace(
                to_dict=lambda: {
                    "command": ["python3", "-m", "unittest", "discover", "-v"],
                    "duration_seconds": 10.0,
                    "status": "success",
                    "metadata": {"exit_code": 0},
                }
            ),
            SimpleNamespace(
                to_dict=lambda: {
                    "command": ["pytest"],
                    "duration_seconds": 12.5,
                    "status": "success",
                    "metadata": {"exit_code": 0},
                }
            ),
            SimpleNamespace(
                to_dict=lambda: {
                    "command": ["ruff", "check", "."],
                    "duration_seconds": 3.25,
                    "status": "success",
                    "metadata": {"exit_code": 0},
                }
            ),
        ]
        try:
            payload, artifacts = (
                module._build_and_write_test_profile_artifacts(
                    commands=[
                        (
                            "python3 -m unittest discover -v",
                            ["python3", "-m", "unittest", "discover", "-v"],
                        ),
                        ("pytest", ["pytest"]),
                        ("ruff check .", ["ruff", "check", "."]),
                    ],
                    events=events,
                    tests_output_mode="normal",
                    source_field="required_commands",
                    started=started,
                    finished=finished,
                )
            )
            assert payload["total_configured_commands"] == 3
            assert payload["recorded_events"] == 3
            assert artifacts["test_profile_json"].endswith("test_profile.json")
            assert artifacts["test_profile_txt"].endswith("test_profile.txt")
            profile_json = (
                context.require_paths().run_dir / "test_profile.json"
            )
            profile_txt = context.require_paths().run_dir / "test_profile.txt"
            assert profile_json.exists()
            assert profile_txt.exists()
            loaded = module.json.loads(
                profile_json.read_text(encoding="utf-8")
            )
            assert loaded["recorded_events"] == 3
            assert loaded["slowest_commands"][0]["raw_command"] == "pytest"
            rendered = profile_txt.read_text(encoding="utf-8")
            assert "Group Breakdown:" in rendered
            assert "Slowest Commands:" in rendered
        finally:
            module.clear_active_run_log_context()


def _unit_test_clean_summary_artifacts_include_command_details() -> None:
    """Clean-run summaries should expose cleanup details in artifacts."""
    module = importlib.import_module(MODULE)
    logging_module = importlib.import_module(
        "devcovenant.core.runtime.run_logging"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = logging_module.create_run_log_context(
            repo_root=repo_root,
            command_name="clean",
            argv=("devcovenant", "clean", "--build"),
        )
        try:
            module.set_active_run_log_context(context)
            module.merge_active_run_log_metadata(
                {
                    "clean_summary": {
                        "selected_scopes": ["build"],
                        "removed_count": 2,
                        "removed_paths": ["build", "dist"],
                        "skipped_protected_count": 1,
                        "skipped_protected_paths": ["devcovenant/logs"],
                    }
                }
            )
            module.finalize_active_run_log_context(
                exit_code=0,
                status="success",
            )
        finally:
            module.clear_active_run_log_context()

        summary_txt = context.require_paths().summary_txt.read_text(
            encoding="utf-8"
        )
        summary_json = context.require_paths().summary_json.read_text(
            encoding="utf-8"
        )
        assert "Cleanup Scope: build" in summary_txt
        assert "Removed Targets: 2" in summary_txt
        assert "Skipped Protected Targets: 1" in summary_txt
        assert '"clean_summary": {' in summary_json
        assert '"removed_count": 2' in summary_json


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_execution_symbol_contract_is_stable(self):
        """Run execution runtime symbol contract assertions."""
        _unit_test_execution_symbol_contract_is_stable()

    def test_execution_symbols_cover_runtime_helpers(self):
        """Run execution runtime helper coverage assertions."""
        _unit_test_execution_symbols_cover_runtime_helpers()

    def test_execution_symbol_assertions_cover_public_api(self):
        """Run execution runtime explicit symbol assertions."""
        _unit_test_execution_symbol_assertions_cover_public_api()

    def test_console_reporter_flushes_console_streams_by_default(self):
        """Run console output line-flush default assertions."""
        _unit_test_console_reporter_flushes_console_streams_by_default()

    def test_console_reporter_suppresses_stdout_in_quiet_mode(self):
        """Run quiet-mode stdout suppression assertions for reporter."""
        _unit_test_console_reporter_suppresses_stdout_in_quiet_mode()

    def test_streaming_helper_emits_wait_heartbeat_for_silent_step(self):
        """Run silent-step heartbeat assertions for streaming helper."""
        _unit_test_streaming_helper_emits_wait_heartbeat_for_silent_step()

    def test_streaming_helper_prefers_pty_for_console_output(self):
        """Run PTY-dispatch assertions for console-emitting subprocesses."""
        _unit_test_streaming_helper_prefers_pty_for_console_output()

    def test_streaming_helper_uses_pipe_when_console_is_suppressed(self):
        """Run pipe-dispatch assertions for hidden-console subprocesses."""
        _unit_test_streaming_helper_uses_pipe_when_console_is_suppressed()

    def test_resolve_child_output_plan_uses_channel_policy_matrix(self):
        """Run channel-plan resolution assertions from active mode."""
        _unit_test_resolve_child_output_plan_uses_channel_policy_matrix()

    def test_run_child_command_uses_shared_output_pipeline(self):
        """Run shared child-command output-pipeline assertions."""
        _unit_test_run_child_command_uses_shared_output_pipeline()

    def test_pipe_fallback_streams_output_before_process_exit(self):
        """Run pipe-fallback progressive-streaming timing assertions."""
        _unit_test_pipe_fallback_streams_output_before_process_exit()

    def test_normal_mode_command_policy_matrix_defaults(self):
        """Run normal-mode command policy matrix assertions."""
        _unit_test_normal_mode_command_policy_matrix_defaults()

    def test_readmes_use_tests_output_mode_for_test_contract(self):
        """Run README output-contract wording assertions."""
        _unit_test_readmes_use_tests_output_mode_for_test_contract()

    def test_package_docs_remain_neutral_for_repo_specific_profiles(self):
        """Run package-doc neutrality assertions for profile wording."""
        _unit_test_package_docs_remain_neutral_for_repo_specific_profiles()

    def test_global_config_template_documents_quiet_mode(self):
        """Run quiet-mode selector comment assertions in config template."""
        _unit_test_global_config_template_documents_quiet_mode()

    def test_normal_mode_test_message_contract_is_stable(self):
        """Run normal-mode test-message contract assertions."""
        _unit_test_normal_mode_test_message_contract_is_stable()

    def test_ci_workflow_split_docs_are_consistent(self):
        """Run CI workflow ownership wording consistency assertions."""
        _unit_test_ci_workflow_split_docs_are_consistent()

    def test_workflow_doc_marks_mid_gate_required(self):
        """Run required gate-mid wording assertions for workflow docs."""
        _unit_test_workflow_doc_marks_mid_gate_required()

    def test_repo_pycache_prefix_sets_env_and_runtime_prefix(self):
        """Run repo pycache-prefix env and runtime-prefix assertions."""
        _unit_test_repo_pycache_prefix_sets_env_and_runtime_prefix()

    def test_repo_pycache_prefix_honors_custom_relative_path(self):
        """Run custom relative pycache-prefix resolution assertions."""
        _unit_test_repo_pycache_prefix_honors_custom_relative_path()

    def test_apply_repo_bytecode_env_forces_unbuffered_output(self):
        """Run PYTHONUNBUFFERED runtime-env enforcement assertions."""
        _unit_test_apply_repo_bytecode_env_forces_unbuffered_output()

    def test_repo_bytecode_cleanup_removes_artifacts(self):
        """Run repo bytecode cleanup removal test."""
        _unit_test_repo_bytecode_cleanup_removes_artifacts()

    def test_resolve_engine_auto_fix_enabled_defaults_false(self):
        """Run autofix resolver default-disabled assertions."""
        _unit_test_resolve_engine_auto_fix_enabled_defaults_false()

    def test_resolve_engine_auto_fix_enabled_reads_bool_flag(self):
        """Run autofix resolver explicit-boolean assertions."""
        _unit_test_resolve_engine_auto_fix_enabled_reads_bool_flag()

    def test_configure_logs_keep_last_defaults_and_reads_value(self):
        """Run log-retention config parsing and default assertions."""
        _unit_test_configure_logs_keep_last_defaults_and_reads_value()

    def test_active_run_log_captures_runtime_and_subprocess_output(self):
        """Run active run-log capture assertions for runtime and subprocess."""
        _unit_test_active_run_log_captures_runtime_and_subprocess_output()

    def test_emit_active_run_log_pointer_supports_once_semantics(self):
        """Run one-time run-log pointer emission assertions."""
        _unit_test_emit_active_run_log_pointer_supports_once_semantics()

    def test_test_command_progress_emits_sparse_lines_in_normal_mode(self):
        """Run sparse normal-mode progress-line assertions."""
        _unit_test_test_command_progress_emits_sparse_lines_in_normal_mode()

    def test_normal_mode_test_child_output_is_suppressed_and_is_logged(self):
        """Run normal-mode suppression and run-log capture assertions."""
        _unit_test_normal_mode_test_child_output_is_suppressed_and_logged()

    def test_build_test_run_summary_metadata_includes_counts_and_hints(self):
        """Run test-summary metadata shape and hint assertions."""
        _unit_test_build_test_run_summary_metadata_includes_counts_and_hints()

    def test_test_profile_artifacts_are_written_for_active_run(self):
        """Run active-run profiling artifact generation assertions."""
        _unit_test_test_profile_artifacts_are_written_for_active_run()

    def test_clean_summary_artifacts_include_command_details(self):
        """Run clean-summary artifact detail assertions."""
        _unit_test_clean_summary_artifacts_include_command_details()
