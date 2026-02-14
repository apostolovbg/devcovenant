"""Unit tests for no-spaghetti custom policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.policy_contracts import CheckContext
from devcovenant.custom.policies.no_spaghetti.no_spaghetti import (
    NoSpaghettiCheck,
)


def _write_module(path: Path, line_count: int) -> None:
    """Write a module file with a requested number of lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"line_{index} = {index}" for index in range(line_count)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _unit_test_no_spaghetti_flags_too_many_top_level_modules() -> None:
    """Policy should flag when top-level module count exceeds baseline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _write_module(repo_root / "devcovenant/core/a.py", 140)
        _write_module(repo_root / "devcovenant/core/b.py", 140)

        check = NoSpaghettiCheck()
        check.set_options(
            {"max_top_level_modules": "1", "min_module_lines": "120"},
            {},
        )
        context = CheckContext(repo_root=repo_root)

        violations = check.check(context)
        assert any(
            "count exceeds baseline" in item.message for item in violations
        )


def _unit_test_no_spaghetti_flags_new_small_module() -> None:
    """Policy should flag a small module below the strict baseline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _write_module(repo_root / "devcovenant/core/a.py", 20)

        check = NoSpaghettiCheck()
        check.set_options(
            {
                "max_top_level_modules": "5",
                "min_module_lines": "120",
            },
            {},
        )
        context = CheckContext(repo_root=repo_root)

        violations = check.check(context)
        assert any(
            "too small for the baseline" in item.message for item in violations
        )


def _unit_test_no_spaghetti_passes_for_large_module() -> None:
    """Policy should pass when the module meets the minimum line baseline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        module_path = repo_root / "devcovenant/core/a.py"
        _write_module(module_path, 140)

        check = NoSpaghettiCheck()
        check.set_options(
            {
                "max_top_level_modules": "5",
                "min_module_lines": "120",
            },
            {},
        )
        context = CheckContext(repo_root=repo_root)

        violations = check.check(context)
        assert violations == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_no_spaghetti_flags_too_many_top_level_modules(self):
        """Run test_no_spaghetti_flags_too_many_top_level_modules."""
        _unit_test_no_spaghetti_flags_too_many_top_level_modules()

    def test_no_spaghetti_flags_new_small_module(self):
        """Run test_no_spaghetti_flags_new_small_module."""
        _unit_test_no_spaghetti_flags_new_small_module()

    def test_no_spaghetti_passes_for_large_module(self):
        """Run test_no_spaghetti_passes_for_large_module."""
        _unit_test_no_spaghetti_passes_for_large_module()
