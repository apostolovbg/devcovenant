"""Unit tests for the clean command."""

from __future__ import annotations

import io
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
                    SimpleNamespace(all=True, build=False, cache=False)
                )

        assert result == 0
        assert not (repo_root / "build").exists()
        assert not (repo_root / "pkg" / "__pycache__").exists()
        rendered = output.getvalue()
        assert "Command: clean" in rendered
        assert "Cleanup scope: build, cache" in rendered


def _unit_test_clean_run_can_limit_to_build_only() -> None:
    """`clean.run()` should honor build-only selection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        (repo_root / "dist").mkdir()
        (repo_root / ".coverage").write_text("coverage\n", encoding="utf-8")

        with patch(
            "devcovenant.clean.resolve_repo_root",
            return_value=repo_root,
        ):
            result = clean.run(
                SimpleNamespace(all=False, build=True, cache=False)
            )

        assert result == 0
        assert not (repo_root / "dist").exists()
        assert (repo_root / ".coverage").exists()


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
