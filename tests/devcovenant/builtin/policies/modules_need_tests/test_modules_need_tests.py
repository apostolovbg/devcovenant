"""Tests for modules_need_tests policy."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.builtin.policies.modules_need_tests import modules_need_tests
from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.services.translator_engine import TranslatorRuntime

ModulesNeedTestsCheck = modules_need_tests.ModulesNeedTestsCheck


def _runtime(profile: str, suffixes: list[str]) -> TranslatorRuntime:
    """Build a translator runtime for one language profile."""
    registry = {
        profile: {
            "category": "language",
            "path": f"devcovenant/builtin/profiles/{profile}",
            "translators": [
                {
                    "id": profile,
                    "extensions": suffixes,
                    "can_handle": {
                        "strategy": "module_function",
                        "entrypoint": f"{profile}_translator.py:can_handle",
                    },
                    "translate": {
                        "strategy": "module_function",
                        "entrypoint": f"{profile}_translator.py:translate",
                    },
                }
            ],
        }
    }
    return TranslatorRuntime(
        repo_root=Path.cwd(),
        profile_registry=registry,
        active_profiles=[profile],
    )


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
                "mirror_test_name_templates": [
                    "python=>test_{stem}.py",
                    "python=>{stem}_test.py",
                ],
                "test_style_requirements": ["python=>python_unittest"],
                "placeholder_test_methods": ["test_placeholder"],
            },
            {},
        )
        return policy

    def test_indexed_test_paths_keep_lookup_fields_explicit(self):
        """Indexed test-path metadata should stay explicit and reusable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            test_path = repo_root / "tests" / "test_service_module.py"
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text("import unittest\n", encoding="utf-8")
            indexed = modules_need_tests._index_tests(
                [test_path],
                repo_root=repo_root,
            )

            self.assertEqual(len(indexed), 1)
            self.assertIsInstance(
                indexed[0], modules_need_tests.IndexedTestPath
            )
            self.assertEqual(
                indexed[0].relative_lower,
                "tests/test_service_module.py",
            )
            self.assertEqual(
                indexed[0].compact_test_name,
                "testservicemodulepy",
            )

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

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = self._configured_python_policy().check(context)

            self.assertEqual(violations, [])

    @patch("subprocess.check_output")
    def test_ignores_cache_and_init_artifacts(self, mock_subprocess):
        """Cache/init artifacts under tests should not count as test files."""
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
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            pycache = tests_dir / "__pycache__"
            pycache.mkdir(parents=True, exist_ok=True)
            (pycache / "test_service_module.cpython-314.pyc").write_bytes(
                b"cache"
            )

            mock_subprocess.return_value = (
                "project_lib/service_module.py\n"
                "tests/test_service_module.py\n"
                "tests/__init__.py\n"
                "tests/__pycache__/test_service_module.cpython-314.pyc\n"
            )

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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
    def test_reports_module_utf8_decode_failures(self, mock_subprocess):
        """Undecodable source modules should emit deterministic violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir(parents=True, exist_ok=True)
            module = repo_root / "project_lib" / "new_module.py"
            module.write_bytes(b"\xff\xfe\xfa")

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_new_module.py").write_text(
                "import unittest\n\n"
                "class TestNewModule(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "project_lib/new_module.py\n" "tests/test_new_module.py\n"
            )
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = self._configured_python_policy().check(context)

            self.assertTrue(
                any(
                    "Module sources must be UTF-8 decodable"
                    in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_reports_test_file_utf8_decode_failures(self, mock_subprocess):
        """Undecodable Python tests should fail unittest-style validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir(parents=True, exist_ok=True)
            (repo_root / "project_lib" / "new_module.py").write_text(
                "def run():\n    return 1\n", encoding="utf-8"
            )

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_new_module.py").write_bytes(b"\xff\xfe\xfa")

            mock_subprocess.return_value = (
                "project_lib/new_module.py\n" "tests/test_new_module.py\n"
            )
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = self._configured_python_policy().check(context)

            self.assertTrue(
                any(
                    "Python test modules must be UTF-8 decodable"
                    in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_rejects_placeholder_method_name(self, mock_subprocess):
        """Policy should reject placeholder test method names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir(parents=True, exist_ok=True)
            (repo_root / "project_lib" / "new_module.py").write_text(
                "def run():\n    return 1\n", encoding="utf-8"
            )

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_new_module.py").write_text(
                "import unittest\n\n"
                "class TestNewModule(unittest.TestCase):\n"
                "    def test_placeholder(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            mock_subprocess.return_value = (
                "project_lib/new_module.py\n" "tests/test_new_module.py\n"
            )

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = self._configured_python_policy().check(context)

            self.assertTrue(
                any(
                    "Placeholder test methods are not allowed"
                    in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_module_with_related_test_does_not_require_session_amendment(
        self, mock_subprocess
    ):
        """Structural policy should not require session test amendments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            lib_dir = repo_root / "project_lib"
            lib_dir.mkdir(parents=True, exist_ok=True)
            module = lib_dir / "service_module.py"
            module.write_text("def run():\n    return 1\n", encoding="utf-8")

            tests_dir = repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            related_test = tests_dir / "test_service_module.py"
            related_test.write_text(
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
            context = CheckContext(
                repo_root=repo_root,
                changed_files=[module],
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = self._configured_python_policy().check(context)
            self.assertEqual(violations, [])

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

            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
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
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("python", [".py"]),
            )
            violations = policy.check(context)

            self.assertTrue(
                any(
                    "Remove stale mirrored test" in violation.message
                    for violation in violations
                )
            )

    @patch("subprocess.check_output")
    def test_mirror_mode_flags_stale_non_python_test(self, mock_subprocess):
        """Mirror mode should reject stale mirrored JavaScript tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module = repo_root / "src" / "widget.js"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("export const widget = 1;\n", encoding="utf-8")

            mirrored = repo_root / "tests" / "src" / "widget.test.js"
            mirrored.parent.mkdir(parents=True, exist_ok=True)
            mirrored.write_text("test('widget', ()=>{});\n", encoding="utf-8")

            stale = repo_root / "tests" / "src" / "ghost.test.js"
            stale.write_text("test('ghost', ()=>{});\n", encoding="utf-8")

            mock_subprocess.return_value = (
                "src/widget.js\n"
                "tests/src/widget.test.js\n"
                "tests/src/ghost.test.js\n"
            )

            policy = ModulesNeedTestsCheck()
            policy.set_options(
                {
                    "include_prefixes": ["src"],
                    "include_suffixes": [".js"],
                    "mirror_roots": ["src=>tests/src"],
                    "mirror_test_name_templates": [
                        "javascript=>{stem}.test.js"
                    ],
                },
                {},
            )
            context = CheckContext(
                repo_root=repo_root,
                translator_runtime=_runtime("javascript", [".js"]),
            )
            violations = policy.check(context)
            self.assertTrue(violations)
            self.assertTrue(
                any(
                    "ghost.test.js" in violation.message
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
        context = CheckContext(
            repo_root=repo_root,
            translator_runtime=_runtime("javascript", [".js"]),
        )
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
        context = CheckContext(
            repo_root=repo_root, translator_runtime=_runtime("go", [".go"])
        )
        violations = policy.check(context)
        assert violations

        tests_root = repo_root / "tests" / "go"
        tests_root.mkdir(parents=True, exist_ok=True)
        (tests_root / "calc_test.go").write_text("package pkg\n")
        mock_subprocess.return_value = "pkg/calc.go\ntests/go/calc_test.go\n"
        assert policy.check(context) == []


def _unit_test_modules_need_tests_symbol_contract_is_stable() -> None:
    """Run symbol-level assertions for modules-need-tests public contract."""
    assert hasattr(modules_need_tests, "ModulesNeedTestsCheck")
    assert modules_need_tests.ModulesNeedTestsCheck is ModulesNeedTestsCheck


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_js_modules_require_tests(self):
        """Run test_js_modules_require_tests."""
        _unit_test_js_modules_require_tests()

    def test_go_modules_require_tests(self):
        """Run test_go_modules_require_tests."""
        _unit_test_go_modules_require_tests()

    def test_modules_need_tests_symbol_contract_is_stable(self):
        """Run modules-need-tests symbol contract assertions."""
        _unit_test_modules_need_tests_symbol_contract_is_stable()
