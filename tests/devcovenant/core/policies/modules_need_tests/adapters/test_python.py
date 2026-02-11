"""Unit tests for the Python modules-need-tests adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import python
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for python adapter checks."""

    def test_changed_python_module_requires_related_test(self):
        """Changed Python modules should require related tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "project_lib" / "worker.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text(
                "def run():\n    return True\n", encoding="utf-8"
            )
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".py"])
            violations = python.check_changes(
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

    def test_mirror_mode_requires_mirrored_test_location(self):
        """Mirror mode requires tests inside the mirrored tests prefix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "devcovenant" / "core" / "runner.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text(
                "def run():\n    return True\n", encoding="utf-8"
            )
            tests_root = repo_root / "tests"
            tests_root.mkdir(parents=True, exist_ok=True)
            (tests_root / "test_runner.py").write_text(
                "import unittest\n\n"
                "class TestRunner(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".py"])
            violations = python.check_changes(
                context=context,
                policy_id="modules-need-tests",
                selector=selector,
                tests_dirs=["tests"],
                mirror_roots=[("devcovenant", "tests/devcovenant")],
                added={module},
                modified=set(),
                deleted=set(),
            )
            self.assertTrue(violations)
