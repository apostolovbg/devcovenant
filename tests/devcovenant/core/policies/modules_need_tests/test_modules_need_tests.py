"""Tests for modules_need_tests policy."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests import modules_need_tests

ModulesNeedTestsCheck = modules_need_tests.ModulesNeedTestsCheck


class TestModulesNeedTestsPolicy(unittest.TestCase):
    """Test suite for modules_need_tests.ModulesNeedTestsCheck."""

    def _configured_python_policy(self) -> ModulesNeedTestsCheck:
        """Return policy instance scoped to project_lib Python files."""
        policy = ModulesNeedTestsCheck()
        policy.set_options(
            {
                "include_prefixes": ["project_lib"],
                "include_suffixes": [".py"],
                "mirror_roots": [],
            },
            {},
        )
        return policy

    @patch("subprocess.check_output")
    def test_detects_module_without_tests(self, mock_subprocess):
        """Policy should detect modules that have no related tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            lib_dir = repo_root / "project_lib"
            lib_dir.mkdir(parents=True, exist_ok=True)
            module = lib_dir / "new_module.py"
            module.write_text("def foo():\n    return 1\n", encoding="utf-8")

            mock_subprocess.return_value = "project_lib/new_module.py\n"

            context = CheckContext(repo_root=repo_root)
            violations = self._configured_python_policy().check(context)

            self.assertEqual(len(violations), 1)
            self.assertIn("no tests found", violations[0].message.lower())

    @patch("subprocess.check_output")
    def test_allows_module_with_related_unittest(self, mock_subprocess):
        """Policy should pass when related unittest-style test exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            lib_dir = repo_root / "project_lib"
            lib_dir.mkdir(parents=True, exist_ok=True)
            module = lib_dir / "service_module.py"
            module.write_text("def run():\n    return 1\n", encoding="utf-8")

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_service_module.py").write_text(
                "import unittest\n\n"
                "class TestServiceModule(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "project_lib/service_module.py\n"
                "tests/test_service_module.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            violations = self._configured_python_policy().check(context)

            self.assertEqual(violations, [])

    @patch("subprocess.check_output")
    def test_rejects_module_level_test_functions(self, mock_subprocess):
        """Policy should reject pytest-style module-level test functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir(parents=True, exist_ok=True)
            (repo_root / "project_lib" / "new_module.py").write_text(
                "def run():\n    return 1\n", encoding="utf-8"
            )

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_new_module.py").write_text(
                "def test_module_level():\n    assert True\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "project_lib/new_module.py\n" "tests/test_new_module.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            violations = self._configured_python_policy().check(context)

            self.assertTrue(violations)
            self.assertTrue(
                any(
                    "Module-level test_* functions are not allowed"
                    in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_rejects_unittest_bridge_usage(self, mock_subprocess):
        """Policy should reject bridge-generated unittest wrappers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir(parents=True, exist_ok=True)
            (repo_root / "project_lib" / "new_module.py").write_text(
                "def run():\n    return 1\n", encoding="utf-8"
            )

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_new_module.py").write_text(
                "from tests.devcovenant.unittest_bridge import "
                "export_unittest_cases\n\n"
                "def _unit_test_x():\n    assert True\n\n"
                "export_"
                "unittest_cases(globals())\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "project_lib/new_module.py\n" "tests/test_new_module.py\n"
            )

            context = CheckContext(repo_root=repo_root)
            violations = self._configured_python_policy().check(context)

            self.assertTrue(violations)
            self.assertTrue(
                any(
                    "Remove unittest bridge usage" in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_mirror_mode_requires_mirrored_test_paths(self, mock_subprocess):
        """Mirror mode should require tests under mirrored target paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module = repo_root / "devcovenant" / "core" / "runner.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text(
                "def run():\n    return True\n", encoding="utf-8"
            )

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_runner.py").write_text(
                "import unittest\n\n"
                "class TestRunner(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "devcovenant/core/runner.py\n" "tests/test_runner.py\n"
            )

            policy = ModulesNeedTestsCheck()
            policy.set_options(
                {
                    "include_prefixes": ["devcovenant"],
                    "include_suffixes": [".py"],
                    "mirror_roots": ["devcovenant=>tests/devcovenant"],
                },
                {},
            )
            context = CheckContext(repo_root=repo_root)
            violations = policy.check(context)

            self.assertTrue(violations)
            self.assertIn(
                "tests/devcovenant/core/test_runner.py",
                violations[0].message,
            )

    @patch("subprocess.check_output")
    def test_mirror_mode_flags_stale_dunder_test(self, mock_subprocess):
        """Mirror mode should reject stale dunder mirror tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module = repo_root / "devcovenant" / "__init__.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("", encoding="utf-8")

            stale_test = (
                repo_root / "tests" / "devcovenant" / "test___init__.py"
            )
            stale_test.parent.mkdir(parents=True, exist_ok=True)
            stale_test.write_text(
                "import unittest\n\n"
                "class TestPlaceholder(unittest.TestCase):\n"
                "    def test_placeholder(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "devcovenant/__init__.py\n"
                "tests/devcovenant/test___init__.py\n"
            )

            policy = ModulesNeedTestsCheck()
            policy.set_options(
                {
                    "include_prefixes": ["devcovenant"],
                    "include_suffixes": [".py"],
                    "mirror_roots": ["devcovenant=>tests/devcovenant"],
                },
                {},
            )
            context = CheckContext(repo_root=repo_root)
            violations = policy.check(context)

            self.assertTrue(
                any(
                    "Remove stale mirrored test" in v.message
                    for v in violations
                )
            )

    @patch("subprocess.check_output")
    def test_mirror_mode_flags_missing_source_test(self, mock_subprocess):
        """Mirror mode should reject mirrored tests with no source module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            test_file = (
                repo_root / "tests" / "devcovenant" / "core" / "test_ghost.py"
            )
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(
                "import unittest\n\n"
                "class TestGhost(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "tests/devcovenant/core/test_ghost.py\n"
            )

            policy = ModulesNeedTestsCheck()
            policy.set_options(
                {
                    "include_prefixes": ["devcovenant"],
                    "include_suffixes": [".py"],
                    "mirror_roots": ["devcovenant=>tests/devcovenant"],
                },
                {},
            )
            context = CheckContext(repo_root=repo_root)
            violations = policy.check(context)

            self.assertTrue(
                any(
                    "Remove stale mirrored test" in violation.message
                    for violation in violations
                )
            )


@patch("subprocess.check_output")
def _unit_test_js_modules_require_tests(mock_subprocess):
    """JS modules should trigger violations without tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "src" / "widget.js"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("export const x = 1;\n", encoding="utf-8")

        mock_subprocess.return_value = "src/widget.js\n"

        policy = ModulesNeedTestsCheck()
        policy.set_options(
            {"include_prefixes": ["src"], "include_suffixes": [".js"]},
            {},
        )
        context = CheckContext(repo_root=repo_root)
        violations = policy.check(context)
        assert violations

        tests = repo_root / "tests"
        tests.mkdir(parents=True, exist_ok=True)
        (tests / "widget.test.js").write_text("test('ok', ()=>{});\n")
        mock_subprocess.return_value = "src/widget.js\ntests/widget.test.js\n"
        assert policy.check(context) == []


@patch("subprocess.check_output")
def _unit_test_go_modules_require_tests(mock_subprocess):
    """Go modules should require *_test.go under tests/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "pkg" / "calc.go"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("package pkg\n", encoding="utf-8")

        mock_subprocess.return_value = "pkg/calc.go\n"

        policy = ModulesNeedTestsCheck()
        policy.set_options(
            {"include_prefixes": ["pkg"], "include_suffixes": [".go"]},
            {},
        )
        context = CheckContext(repo_root=repo_root)
        violations = policy.check(context)
        assert violations

        tests_root = repo_root / "tests" / "go"
        tests_root.mkdir(parents=True, exist_ok=True)
        (tests_root / "calc_test.go").write_text("package pkg\n")
        mock_subprocess.return_value = "pkg/calc.go\ntests/go/calc_test.go\n"
        assert policy.check(context) == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_js_modules_require_tests(self):
        """Run test_js_modules_require_tests."""
        _unit_test_js_modules_require_tests()

    def test_go_modules_require_tests(self):
        """Run test_go_modules_require_tests."""
        _unit_test_go_modules_require_tests()
