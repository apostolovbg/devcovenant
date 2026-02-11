"""Unit tests for the TypeScript new-modules adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import typescript
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for typescript adapter checks."""

    def test_changed_typescript_module_requires_test(self):
        """Changed TS modules should require *.test.ts under tests/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "widget.ts"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("export const x = 1;\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".ts"])
            violations = typescript.check_changes(
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

    def test_changed_typescript_module_passes_with_test(self):
        """TS modules pass when a related *.test.ts exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "widget.ts"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("export const x = 1;\n", encoding="utf-8")
            tests_path = repo_root / "tests" / "ui" / "widget.test.ts"
            tests_path.parent.mkdir(parents=True, exist_ok=True)
            tests_path.write_text("it('ok', ()=>{});\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".ts"])
            violations = typescript.check_changes(
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
