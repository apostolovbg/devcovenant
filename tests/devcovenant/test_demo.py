"""Tests for the disposable DevCovenant demo command."""

from __future__ import annotations

import argparse
import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import devcovenant.demo as demo


def _unit_test_demo_parser_uses_command_scoped_prog() -> None:
    """Demo parser should expose stable command-scoped help text."""
    parser = demo._build_parser()
    assert parser.prog == "devcovenant demo"
    help_text = parser.format_help()
    assert "--quiet" in help_text
    assert "--normal" in help_text
    assert "--verbose" in help_text


def _unit_test_demo_runs_fixed_lifecycle() -> None:
    """Demo should orchestrate one fixed disposable lifecycle."""
    order: list[str] = []

    def _record(label: str):
        """Return one recorder for a patched demo helper."""

        def _runner(*_args, **_kwargs):
            """Record one demo helper invocation."""
            order.append(label)
            return 0

        return _runner

    def _record_gate(repo_root, stage: str):
        """Record the gate stage for the lifecycle sequence."""
        del repo_root
        order.append(f"gate:{stage}")
        return 0

    buffer = StringIO()
    with (
        patch.object(demo, "_seed_demo_repo", _record("seed")),
        patch.object(demo, "_mark_config_reviewed", _record("review")),
        patch.object(demo, "_write_smoke_test", _record("smoke")),
        patch.object(demo, "_run_install", _record("install")),
        patch.object(demo, "_run_deploy", _record("deploy")),
        patch.object(demo, "_run_custom_teaser", _record("custom")),
        patch.object(demo, "_run_gate_stage", _record_gate),
        patch.object(demo, "_run_workflow_runs", _record("run")),
    ):
        with redirect_stdout(buffer):
            result = demo.run(argparse.Namespace())

    assert result == 0
    assert order == [
        "seed",
        "install",
        "review",
        "deploy",
        "custom",
        "gate:open",
        "smoke",
        "gate:verify",
        "run",
        "gate:close",
    ]
    text = buffer.getvalue()
    assert "DevCovenant demo" in text
    assert "Disposable repo:" in text
    assert "Materialize the userproject customization teaser" in text
    assert "Verify, run, and close the workflow cycle" in text


def _unit_test_demo_main_exits_cleanly() -> None:
    """Demo main should parse args and exit cleanly."""
    with patch.object(demo, "run", return_value=0) as run_mock:
        try:
            demo.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from demo.main().")

    assert code == 0
    run_mock.assert_called_once()


def _unit_test_demo_command_prefers_the_current_package_root() -> None:
    """Demo subprocesses should import the active package root first."""
    captured: dict[str, object] = {}

    def _fake_run(*args, **kwargs):
        """Capture the demo subprocess invocation."""
        captured["args"] = args
        captured["kwargs"] = kwargs

        class _Result:
            """Stand in for subprocess.CompletedProcess."""

            returncode = 0

        return _Result()

    with patch.object(demo.subprocess, "run", side_effect=_fake_run):
        result = demo._run_demo_command(Path("/tmp/demo"), "install")

    assert result == 0
    env = captured["kwargs"]["env"]
    assert isinstance(env, dict)
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(
        Path(demo.__file__).resolve().parents[1]
    )


class DemoCommandTests(unittest.TestCase):
    """unittest wrappers for demo command coverage."""

    def test_demo_parser_uses_command_scoped_prog(self):
        """Run demo parser help coverage."""
        _unit_test_demo_parser_uses_command_scoped_prog()

    def test_demo_runs_fixed_lifecycle(self):
        """Run demo orchestration coverage."""
        _unit_test_demo_runs_fixed_lifecycle()

    def test_demo_main_exits_cleanly(self):
        """Run demo main coverage."""
        _unit_test_demo_main_exits_cleanly()

    def test_demo_command_prefers_the_current_package_root(self):
        """Run demo subprocess environment coverage."""
        _unit_test_demo_command_prefers_the_current_package_root()
