"""Unit tests for the JavaScript new-modules adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import javascript
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for javascript adapter checks."""

    def test_changed_javascript_module_requires_test(self):
        """Changed JS modules should require *.test.js under tests/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "widget.js"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("export const x = 1;\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".js"])
            violations = javascript.check_changes(
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

    def test_changed_javascript_module_passes_with_test(self):
        """JS modules pass when a related *.test.js file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "widget.js"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("export const x = 1;\n", encoding="utf-8")
            tests_path = repo_root / "tests" / "ui" / "widget.test.js"
            tests_path.parent.mkdir(parents=True, exist_ok=True)
            tests_path.write_text("test('ok', ()=>{});\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".js"])
            violations = javascript.check_changes(
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
