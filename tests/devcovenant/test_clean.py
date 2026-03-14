"""Unit tests for the clean command."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
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


def _unit_test_clean_run_defaults_to_all_cleanup_scope() -> None:
    """`clean.run()` should default to all cleanup categories."""
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
                    SimpleNamespace(all=False, build=False, cache=False)
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

    def test_clean_run_defaults_to_all_cleanup_scope(self):
        """Run default clean-scope execution coverage."""
        _unit_test_clean_run_defaults_to_all_cleanup_scope()

    def test_clean_run_can_limit_to_build_only(self):
        """Run build-only clean-scope execution coverage."""
        _unit_test_clean_run_can_limit_to_build_only()
