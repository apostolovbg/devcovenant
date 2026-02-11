"""Unit tests for the Go new-modules adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import go
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for go adapter checks."""

    def test_changed_go_module_requires_test(self):
        """Changed Go modules should require *_test.go under tests/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "pkg" / "calc.go"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("package pkg\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".go"])
            violations = go.check_changes(
                context=context,
                policy_id="modules-need-tests",
                selector=selector,
                tests_dirs=["tests"],
                mirror_roots=[],
                added={module},
                modified=set(),
                deleted=set(),
            )
            self.assertTrue(violations)

    def test_changed_go_module_passes_with_test(self):
        """Go modules pass when related *_test.go exists in tests/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "pkg" / "calc.go"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("package pkg\n", encoding="utf-8")
            tests_path = repo_root / "tests" / "go" / "calc_test.go"
            tests_path.parent.mkdir(parents=True, exist_ok=True)
            tests_path.write_text("package pkg\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".go"])
            violations = go.check_changes(
                context=context,
                policy_id="modules-need-tests",
                selector=selector,
                tests_dirs=["tests"],
                mirror_roots=[],
                added={module},
                modified=set(),
                deleted=set(),
            )
            self.assertEqual(violations, [])
