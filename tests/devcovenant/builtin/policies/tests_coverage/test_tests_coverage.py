"""Tests for tests-coverage policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.tests_coverage.tests_coverage import (
    TestsCoverageCheck,
)
from devcovenant.core.policy_contract import ChangeState, CheckContext
from devcovenant.core.translator import TranslatorRuntime


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


def _policy() -> TestsCoverageCheck:
    """Return configured policy for project_lib Python modules."""
    policy = TestsCoverageCheck()
    policy.set_options(
        {
            "include_prefixes": ["project_lib"],
            "include_suffixes": [".py"],
            "watch_dirs": ["tests"],
            "tests_watch_dirs": ["tests"],
            "enforce_symbol_fidelity": True,
            "symbol_kinds": ["function"],
            "symbol_name_min_length": 3,
            "symbol_assertion_window": 2,
            "fixture_marker_pattern": (
                r"\bDEVCOV_FIXTURE_OK:\s*(?P<reason>\S.*)"
            ),
            "assertion_signal_patterns": [
                r"python=>\bassert\b",
                r"python=>\bself\.assert[A-Za-z_]*\s*\(",
            ],
            "tautology_patterns": [
                r"python=>^\s*assert\s+True\s*$",
                r"python=>^\s*self\.assertTrue\s*\(\s*True\s*\)\s*$",
            ],
        },
        {},
    )
    return policy


def _context(
    repo_root: Path,
    *,
    stage: str = "",
    changed_files: list[Path] | None = None,
) -> CheckContext:
    """Build check context for tests-coverage policy runs."""
    return CheckContext(
        repo_root=repo_root,
        changed_files=changed_files or [],
        translator_runtime=_runtime("python", [".py"]),
        change_state=ChangeState(stage=stage),
    )


def _unit_test_passes_with_related_asserting_test():
    """Module should pass when related tests include assertion signals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "project_lib" / "service.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("def run():\n    return 1\n", encoding="utf-8")

        test_file = repo_root / "tests" / "test_service.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(
            "import unittest\n\n"
            "class TestService(unittest.TestCase):\n"
            "    def test_run(self):\n"
            "        result = run()\n"
            "        self.assertEqual(result, 1)\n",
            encoding="utf-8",
        )

        context = _context(repo_root)
        assert _policy().check(context) == []


def _unit_test_flags_related_tests_without_assertions():
    """Module should fail when related tests do not include assertions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "project_lib" / "service.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("def run():\n    return 1\n", encoding="utf-8")

        test_file = repo_root / "tests" / "test_service.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(
            "import unittest\n\n"
            "class TestService(unittest.TestCase):\n"
            "    def test_run(self):\n"
            "        value = 1\n"
            "        value += 1\n",
            encoding="utf-8",
        )

        context = _context(repo_root)
        violations = _policy().check(context)
        assert violations
        assert any(
            "missing assertion coverage signals" in violation.message
            for violation in violations
        )


def _unit_test_ignores_modules_without_related_tests():
    """Policy should skip modules that currently have no related tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "project_lib" / "service.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("def run():\n    return 1\n", encoding="utf-8")

        context = _context(repo_root)
        assert _policy().check(context) == []


def _unit_test_handles_non_utf_related_tests():
    """Non-UTF related tests should not crash policy evaluation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "project_lib" / "service.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("def run():\n    return 1\n", encoding="utf-8")

        test_file = repo_root / "tests" / "test_service.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"\x93binary-non-utf-content")

        context = _context(repo_root)
        violations = _policy().check(context)
        assert violations
        assert any(
            "missing assertion coverage signals" in violation.message
            for violation in violations
        )


def _unit_test_open_stage_skips_checks():
    """Open stage should skip tests-coverage enforcement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = _context(repo_root, stage="open")
        assert _policy().check(context) == []


def _unit_test_flags_missing_symbol_level_assertions():
    """Coverage should fail when related tests omit one module symbol."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        module = repo_root / "project_lib" / "service.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text(
            "def render_report():\n"
            "    return 'ok'\n\n"
            "def publish_report():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        test_file = repo_root / "tests" / "test_service.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(
            "import unittest\n\n"
            "class TestService(unittest.TestCase):\n"
            "    def test_render(self):\n"
            "        result = render_report()\n"
            "        self.assertEqual(result, 'ok')\n",
            encoding="utf-8",
        )

        violations = _policy().check(
            _context(repo_root, changed_files=[module])
        )
        assert violations
        assert any(
            "missing symbol-level assertion coverage" in violation.message
            for violation in violations
        )
        assert any(
            "publish_report" in violation.message for violation in violations
        )


def _unit_test_policy_symbol_contract_is_stable():
    """tests-coverage policy class should keep stable symbol surface."""
    assert TestsCoverageCheck.__name__ == "TestsCoverageCheck"
    assert hasattr(TestsCoverageCheck, "check")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_passes_with_related_asserting_test(self):
        """Run test_passes_with_related_asserting_test."""
        _unit_test_passes_with_related_asserting_test()

    def test_flags_related_tests_without_assertions(self):
        """Run test_flags_related_tests_without_assertions."""
        _unit_test_flags_related_tests_without_assertions()

    def test_ignores_modules_without_related_tests(self):
        """Run test_ignores_modules_without_related_tests."""
        _unit_test_ignores_modules_without_related_tests()

    def test_handles_non_utf_related_tests(self):
        """Run test_handles_non_utf_related_tests."""
        _unit_test_handles_non_utf_related_tests()

    def test_open_stage_skips_checks(self):
        """Run test_open_stage_skips_checks."""
        _unit_test_open_stage_skips_checks()

    def test_flags_missing_symbol_level_assertions(self):
        """Run test_flags_missing_symbol_level_assertions."""
        _unit_test_flags_missing_symbol_level_assertions()

    def test_policy_symbol_contract_is_stable(self):
        """Run tests-coverage policy symbol contract assertions."""
        _unit_test_policy_symbol_contract_is_stable()
