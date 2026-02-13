"""Tests for the security scanner policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.security_scanner import security_scanner
from devcovenant.core.translator_runtime import TranslatorRuntime

SecurityScannerCheck = security_scanner.SecurityScannerCheck


def _runtime(profile: str, suffixes: list[str]) -> TranslatorRuntime:
    """Build a translator runtime for one language profile."""
    registry = {
        profile: {
            "category": "language",
            "translators": [
                {
                    "id": profile,
                    "extensions": suffixes,
                    "can_handle": {
                        "strategy": "module_function",
                        "entrypoint": (
                            "devcovenant.core.translator_runtime."
                            "can_handle_declared_extensions"
                        ),
                    },
                    "translate": {
                        "strategy": "module_function",
                        "entrypoint": (
                            "devcovenant.core.translator_runtime."
                            "translate_language_unit"
                        ),
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


def _configured_policy() -> SecurityScannerCheck:
    """Return a policy instance scoped to the project_lib tree."""
    policy = SecurityScannerCheck()
    policy.set_options(
        {
            "include_suffixes": [".py"],
            "exclude_globs": ["tests/**", "**/tests/**"],
            "exclude_prefixes": ["project_lib/vendor"],
        },
        {},
    )
    return policy


def _write_module(tmp_path: Path, name: str, source: str) -> Path:
    """Create a sample module under project_lib for scanning."""
    target = tmp_path / "project_lib" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def _unit_test_detects_insecure_eval(tmp_path: Path):
    """`eval` usage raises a violation."""
    source = "def foo():\n    return eval('2+2')\n"
    target = _write_module(tmp_path, "helper.py", source)

    checker = _configured_policy()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    violations = checker.check(context)

    assert violations
    assert any("eval" in v.message for v in violations)


def _unit_test_allows_safe_modules(tmp_path: Path):
    """Modules without risky patterns are ignored."""
    source = "def foo():\n    return 4\n"
    target = _write_module(tmp_path, "helper.py", source)

    checker = _configured_policy()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    assert checker.check(context) == []


def _unit_test_ignores_tests(tmp_path: Path):
    """Test files are skipped even when they contain risky constructs."""
    target = tmp_path / "tests" / "dummy.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("exec('42')\n", encoding="utf-8")

    checker = _configured_policy()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    assert checker.check(context) == []


def _unit_test_non_python_files_are_ignored(tmp_path: Path):
    """Files without active translators should be ignored."""
    target = tmp_path / "project_lib" / "ui" / "component.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("console.log('safe');\n", encoding="utf-8")

    checker = _configured_policy()
    checker.set_options(
        {
            "include_suffixes": [".py", ".js"],
            "exclude_globs": [],
            "exclude_prefixes": [],
        },
        {},
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    assert checker.check(context) == []


def _unit_test_translators_flag_risky_patterns(tmp_path: Path):
    """Non-Python translators should detect risky constructs."""
    cases = [
        (".js", "const x = eval('2+2');\n", "javascript"),
        (".ts", "const x = eval('2+2');\n", "typescript"),
        (".go", 'package main\nimport "os/exec"\n', "go"),
        (".rs", "unsafe { let x = 1; }\n", "rust"),
        (
            ".java",
            'class Demo { void r(){ Runtime.getRuntime().exec("ls");}}\n',
            "java",
        ),
        (
            ".cs",
            (
                "class Demo { void R(){ "
                'System.Diagnostics.Process.Start("ls");}}\n'
            ),
            "csharp",
        ),
    ]

    for suffix, source, profile in cases:
        path = tmp_path / "project_lib" / f"sample{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

        checker = SecurityScannerCheck()
        checker.set_options(
            {
                "include_suffixes": [suffix],
                "exclude_globs": [],
                "exclude_prefixes": [],
            },
            {},
        )
        context = CheckContext(
            repo_root=tmp_path,
            changed_files=[path],
            translator_runtime=_runtime(profile, [suffix]),
        )
        violations = checker.check(context)
        assert violations, f"expected violation for {suffix}"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_detects_insecure_eval(self):
        """Run test_detects_insecure_eval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_detects_insecure_eval(tmp_path=tmp_path)

    def test_allows_safe_modules(self):
        """Run test_allows_safe_modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_allows_safe_modules(tmp_path=tmp_path)

    def test_ignores_tests(self):
        """Run test_ignores_tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ignores_tests(tmp_path=tmp_path)

    def test_non_python_files_are_ignored(self):
        """Run test_non_python_files_are_ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_non_python_files_are_ignored(tmp_path=tmp_path)

    def test_translators_flag_risky_patterns(self):
        """Run test_translators_flag_risky_patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_translators_flag_risky_patterns(tmp_path=tmp_path)
