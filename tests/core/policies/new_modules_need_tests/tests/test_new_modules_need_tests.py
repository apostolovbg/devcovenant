"""Tests for new_modules_need_tests policy."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.new_modules_need_tests import (
    new_modules_need_tests,
)

NewModulesNeedTestsCheck = new_modules_need_tests.NewModulesNeedTestsCheck


class TestNewModulesNeedTestsPolicy(unittest.TestCase):
    """Test suite for new_modules_need_tests.NewModulesNeedTestsCheck."""

    def _configured_policy(self) -> NewModulesNeedTestsCheck:
        """Return a policy instance scoped to project_lib/."""
        policy = NewModulesNeedTestsCheck()
        policy.set_options(
            {"include_prefixes": ["project_lib"], "include_suffixes": [".py"]},
            {},
        )
        return policy

    @patch("subprocess.check_output")
    def test_detects_new_module_without_tests(self, mock_subprocess):
        """Policy should detect new modules without test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create the new module file
            lib_dir = repo_root / "project_lib"
            lib_dir.mkdir()
            new_module = lib_dir / "new_module.py"
            new_module.write_text("def foo(): pass\n")

            # Simulate git status showing new module
            mock_subprocess.return_value = "A  project_lib/new_module.py\n"

            context = CheckContext(repo_root=repo_root)
            policy = self._configured_policy()
            violations = policy.check(context)

            self.assertEqual(len(violations), 1)
            self.assertIn("no tests found", violations[0].message.lower())

    @patch("subprocess.check_output")
    def test_detects_untracked_module_without_tests(self, mock_subprocess):
        """Policy should treat untracked modules as new modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            lib_dir = repo_root / "project_lib"
            lib_dir.mkdir()
            new_module = lib_dir / "new_module.py"
            new_module.write_text("def foo(): pass\n")

            mock_subprocess.return_value = "?? project_lib/new_module.py\n"

            context = CheckContext(repo_root=repo_root)
            policy = self._configured_policy()
            violations = policy.check(context)

            self.assertEqual(len(violations), 1)
            self.assertIn("no tests found", violations[0].message.lower())

    @patch("subprocess.check_output")
    def test_allows_new_module_with_tests(self, mock_subprocess):
        """Policy should pass when new modules have tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            tests_dir = repo_root / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_new_module.py").write_text(
                "def test_placeholder():\n    assert True\n"
            )

            # Simulate git status showing new module and test
            mock_subprocess.return_value = (
                "A  project_lib/new_module.py\n"
                "M  tests/test_new_module.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            policy = self._configured_policy()
            violations = policy.check(context)

            self.assertEqual(len(violations), 0)

    @patch("subprocess.check_output")
    def test_detects_removed_module_without_tests(self, mock_subprocess):
        """Policy should flag removed modules when no tests change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            mock_subprocess.return_value = " D project_lib/old_module.py\n"

            context = CheckContext(repo_root=repo_root)
            policy = self._configured_policy()
            violations = policy.check(context)

            self.assertEqual(len(violations), 1)
            self.assertIn("removing modules", violations[0].message)

    @patch("subprocess.check_output")
    def test_allows_removed_module_with_tests(self, mock_subprocess):
        """Policy should allow module removals when tests are updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            mock_subprocess.return_value = (
                " D project_lib/old_module.py\n"
                "M  tests/test_old_module.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            policy = self._configured_policy()
            violations = policy.check(context)

        self.assertEqual(len(violations), 0)

    @patch("subprocess.check_output")
    def test_support_directories_ignored(self, mock_subprocess):
        """Policy should ignore support directories such as adapters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module_path = (
                repo_root
                / "devcovenant"
                / "core"
                / "policies"
                / "docstring_and_comment_coverage"
                / "adapters"
                / "__init__.py"
            )
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text("", encoding="utf-8")

            mock_subprocess.return_value = (
                "A  devcovenant/core/policies/docstring_and_comment_coverage/"
                "adapters/__init__.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            policy = NewModulesNeedTestsCheck()
            policy.set_options(
                {
                    "include_prefixes": ["devcovenant"],
                    "include_suffixes": [".py"],
                },
                {},
            )
            violations = policy.check(context)

            self.assertEqual(len(violations), 0)


@patch("subprocess.check_output")
def test_js_modules_require_tests(mock_subprocess):
    """JS modules should trigger violations without tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "src" / "widget.js"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("export const x = 1;\n")

        mock_subprocess.return_value = "A  src/widget.js\n"

        policy = NewModulesNeedTestsCheck()
        policy.set_options(
            {"include_prefixes": ["src"], "include_suffixes": [".js"]},
            {},
        )
        context = CheckContext(repo_root=repo_root)
        violations = policy.check(context)
        assert violations

        tests = repo_root / "tests"
        tests.mkdir()
        (tests / "widget.test.js").write_text("test('ok', ()=>{});\n")
        mock_subprocess.return_value = (
            "A  src/widget.js\nM  tests/widget.test.js\n"
        )
        assert policy.check(context) == []


@patch("subprocess.check_output")
def test_go_modules_require_tests(mock_subprocess):
    """Go modules should require *_test.go."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "pkg" / "calc.go"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("package pkg\n")

        mock_subprocess.return_value = "A  pkg/calc.go\n"

        policy = NewModulesNeedTestsCheck()
        policy.set_options(
            {"include_prefixes": ["pkg"], "include_suffixes": [".go"]},
            {},
        )
        context = CheckContext(repo_root=repo_root)
        violations = policy.check(context)
        assert violations

        (module.parent / "calc_test.go").write_text("package pkg\n")
        mock_subprocess.return_value = "A  pkg/calc.go\nM  pkg/calc_test.go\n"
        assert policy.check(context) == []
