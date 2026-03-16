"""Unit tests for the clean command."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import clean
from tests.devcovenant import repo_seed_cache


def _unit_test_clean_module_symbol_contract_is_stable() -> None:
    """Clean command module should expose the stable callable surface."""
    assert clean.run
    assert clean.main


def _unit_test_clean_flow_symbol_contract_is_stable() -> None:
    """Clean flow module should expose the orchestration entrypoint."""
    module = __import__("devcovenant.core.flow.clean", fromlist=["clean_repo"])
    assert module.clean_repo


def _unit_test_clean_main_requires_explicit_scope() -> None:
    """`devcovenant clean` should reject empty scope selection."""
    stderr = io.StringIO()
    try:
        with redirect_stderr(stderr):
            clean.main([])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit for empty clean scope.")
    rendered = stderr.getvalue()
    assert "usage: devcovenant clean" in rendered
    assert "select at least one cleanup scope" in rendered


def _unit_test_clean_help_uses_clean_prog() -> None:
    """Help output should render the clean subcommand usage prefix."""
    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            clean.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("Expected SystemExit for help output.")
    assert "usage: devcovenant clean" in stdout.getvalue()


def _unit_test_clean_run_honors_all_cleanup_scope() -> None:
    """`clean.run()` should honor the explicit all-scope selection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        (repo_root / "build").mkdir()
        (repo_root / "pkg" / "__pycache__").mkdir(parents=True)

        output = io.StringIO()
        with redirect_stdout(output):
            with patch(
                "devcovenant.clean.resolve_repo_root",
                return_value=repo_root,
            ):
                result = clean.run(
                    SimpleNamespace(
                        all=True,
                        build=False,
                        cache=False,
                        registry=False,
                        logs=False,
                    )
                )

        assert result == 0
        assert not (repo_root / "build").exists()
        assert not (repo_root / "pkg" / "__pycache__").exists()
        rendered = output.getvalue()
        assert "Command: clean" in rendered
        assert "Cleanup scope: build, cache, registry, logs" in rendered


def _unit_test_clean_run_can_limit_to_build_only() -> None:
    """`clean.run()` should honor build-only selection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        (repo_root / "dist").mkdir()
        release_tree = repo_root / f"{repo_root.name}-2.45.6"
        release_tree.mkdir()
        (release_tree / "PKG-INFO").write_text("artifact\n", encoding="utf-8")
        other_release_tree = repo_root / "otherproject-2.45.6"
        other_release_tree.mkdir()
        (other_release_tree / "PKG-INFO").write_text(
            "artifact\n",
            encoding="utf-8",
        )
        (repo_root / ".coverage").write_text("coverage\n", encoding="utf-8")

        with patch(
            "devcovenant.clean.resolve_repo_root",
            return_value=repo_root,
        ):
            result = clean.run(
                SimpleNamespace(
                    all=False,
                    build=True,
                    cache=False,
                    registry=False,
                    logs=False,
                )
            )

        assert result == 0
        assert not (repo_root / "dist").exists()
        assert not release_tree.exists()
        assert other_release_tree.exists()
        assert (repo_root / ".coverage").exists()


def _unit_test_clean_run_can_limit_to_logs_only() -> None:
    """`clean.run()` should honor logs-only selection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        logs_root = repo_root / "devcovenant" / "logs"
        logs_root.mkdir(parents=True, exist_ok=True)
        (logs_root / "README.md").write_text("tracked\n", encoding="utf-8")
        run_dir = logs_root / "20260315T000000000000Z-clean-test"
        run_dir.mkdir()

        with patch(
            "devcovenant.clean.resolve_repo_root",
            return_value=repo_root,
        ):
            result = clean.run(
                SimpleNamespace(
                    all=False,
                    build=False,
                    cache=False,
                    registry=False,
                    logs=True,
                )
            )

        assert result == 0
        assert not run_dir.exists()
        assert (logs_root / "README.md").is_file()


def _unit_test_clean_run_rejects_open_gate_session() -> None:
    """`clean.run()` should fail when a gate session is open."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps({"session_state": "open"}, indent=2) + "\n",
            encoding="utf-8",
        )
        (repo_root / "build").mkdir()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            redirect_stdout(stdout),
            redirect_stderr(stderr),
            patch(
                "devcovenant.clean.resolve_repo_root",
                return_value=repo_root,
            ),
        ):
            result = clean.run(
                SimpleNamespace(
                    all=False,
                    build=True,
                    cache=False,
                    registry=False,
                    logs=False,
                )
            )

        assert result == 1
        assert (repo_root / "build").exists()
        assert (
            "Cannot run `clean` while a gate session is open"
            in stderr.getvalue()
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for clean command regression coverage."""

    def test_clean_module_symbol_contract_is_stable(self):
        """Run clean command symbol contract coverage."""
        _unit_test_clean_module_symbol_contract_is_stable()

    def test_clean_flow_symbol_contract_is_stable(self):
        """Run clean flow symbol contract coverage."""
        _unit_test_clean_flow_symbol_contract_is_stable()

    def test_clean_main_requires_explicit_scope(self):
        """Run empty-scope CLI validation coverage."""
        _unit_test_clean_main_requires_explicit_scope()

    def test_clean_help_uses_clean_prog(self):
        """Run clean help-program rendering coverage."""
        _unit_test_clean_help_uses_clean_prog()

    def test_clean_run_honors_all_cleanup_scope(self):
        """Run explicit all-scope execution coverage."""
        _unit_test_clean_run_honors_all_cleanup_scope()

    def test_clean_run_can_limit_to_build_only(self):
        """Run build-only clean-scope execution coverage."""
        _unit_test_clean_run_can_limit_to_build_only()

    def test_clean_run_can_limit_to_logs_only(self):
        """Run logs-only clean-scope execution coverage."""
        _unit_test_clean_run_can_limit_to_logs_only()

    def test_clean_run_rejects_open_gate_session(self):
        """Run open-session clean rejection coverage."""
        _unit_test_clean_run_rejects_open_gate_session()
