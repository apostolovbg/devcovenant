"""Unit tests for the C# new-modules adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import csharp
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for csharp adapter checks."""

    def test_changed_csharp_module_requires_test(self):
        """Changed C# modules should require a related test file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "Widget.cs"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("class Widget {}\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".cs"])
            violations = csharp.check_changes(
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

    def test_changed_csharp_module_passes_with_test(self):
        """C# modules pass when a related *Test.cs exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "Widget.cs"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("class Widget {}\n", encoding="utf-8")
            tests_path = repo_root / "tests" / "cs" / "WidgetTest.cs"
            tests_path.parent.mkdir(parents=True, exist_ok=True)
            tests_path.write_text("class WidgetTest {}\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".cs"])
            violations = csharp.check_changes(
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
