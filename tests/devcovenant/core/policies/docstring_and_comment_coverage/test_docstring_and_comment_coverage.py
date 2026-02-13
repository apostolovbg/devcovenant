"""Tests for the docstring and comment coverage policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.docstring_and_comment_coverage import (
    docstring_and_comment_coverage,
)
from devcovenant.core.translator_runtime import TranslatorRuntime

DocstringAndCommentCoverageCheck = (
    docstring_and_comment_coverage.DocstringAndCommentCoverageCheck
)


def _runtime(profile: str, suffixes: list[str]) -> TranslatorRuntime:
    """Build a translator runtime for one language profile."""
    registry = {
        profile: {
            "category": "language",
            "path": f"devcovenant/core/profiles/{profile}",
            "translators": [
                {
                    "id": profile,
                    "extensions": suffixes,
                    "can_handle": {
                        "strategy": "module_function",
                        "entrypoint": "translator.py:can_handle",
                    },
                    "translate": {
                        "strategy": "module_function",
                        "entrypoint": "translator.py:translate",
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


def _create_file(tmp_path: Path, source: str) -> Path:
    """Write a sample module under project_lib for testing."""
    target = tmp_path / "project_lib" / "helpers" / "example.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def _unit_test_flags_missing_docstrings(tmp_path: Path):
    """Modules and functions without comments/docstrings trigger violations."""
    source = (
        "def foo():\n"
        "    return 42\n"
        "\n"
        "class Bar:\n"
        "    def baz(self):\n"
        "        pass\n"
    )
    target = _create_file(tmp_path, source)

    checker = DocstringAndCommentCoverageCheck()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        all_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    violations = checker.check(context)

    assert len(violations) >= 3
    assert all(v.severity == "error" for v in violations)
    assert any("Module lacks" in v.message for v in violations)
    assert any(
        "function" in v.message.lower() and "foo" in v.message.lower()
        for v in violations
    )


def _unit_test_comments_satisfy_policy(tmp_path: Path):
    """Long comments before definitions count as documentation."""
    source = (
        "# Library helper module\n"
        "\n"
        "# Explain foo\n"
        "def foo():\n"
        "    # Internal behavior notes\n"
        "    return 1\n"
    )
    target = _create_file(tmp_path, source)

    checker = DocstringAndCommentCoverageCheck()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        all_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    assert checker.check(context) == []


def _unit_test_all_files_scanned_when_no_changes(tmp_path: Path):
    """Ensure all_files is inspected when no changed files are present."""
    source = "def foo():\n    return 5\n"
    target = _create_file(tmp_path, source)

    checker = DocstringAndCommentCoverageCheck()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[],
        all_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    violations = checker.check(context)

    assert any("Module lacks" in v.message for v in violations)


def _unit_test_metadata_skip_prefixes(tmp_path: Path):
    """Policy-def options should allow excluding directories."""
    target = tmp_path / "docs" / "api" / "module.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def foo():\n    return 1\n", encoding="utf-8")

    checker = DocstringAndCommentCoverageCheck()
    checker.set_options(
        {
            "exclude_prefixes": ["docs"],
            "exclude_globs": [],
            "include_suffixes": [".py"],
        },
        {},
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        all_files=[target],
        translator_runtime=_runtime("python", [".py"]),
    )
    assert checker.check(context) == []


def _unit_test_non_python_files_are_checked(tmp_path: Path):
    """Non-Python language files should also receive doc coverage checks."""
    cases = [
        (
            ".js",
            "javascript",
            "// ok\nfunction good() {}\n",
            "function bad() {}\n",
        ),
        (
            ".ts",
            "typescript",
            "// ok\nfunction good(): void {}\n",
            "function bad(): void {}\n",
        ),
        (".go", "go", "// ok\nfunc good() {}\n", "func bad() {}\n"),
        (".rs", "rust", "/// ok\nfn good() {}\n", "fn bad() {}\n"),
        (".java", "java", "/** ok */\nclass Good {}\n", "class Bad {}\n"),
        (".cs", "csharp", "/// ok\nclass Good {}\n", "class Bad {}\n"),
    ]

    for suffix, profile, good_src, bad_src in cases:
        good = tmp_path / "project_lib" / f"good{suffix}"
        bad = tmp_path / "project_lib" / f"bad{suffix}"
        good.parent.mkdir(parents=True, exist_ok=True)
        good.write_text(good_src, encoding="utf-8")
        bad.write_text(bad_src, encoding="utf-8")

        checker = DocstringAndCommentCoverageCheck()
        checker.set_options(
            {
                "include_suffixes": [suffix],
                "include_prefixes": ["project_lib"],
            },
            {},
        )
        context = CheckContext(
            repo_root=tmp_path,
            changed_files=[good, bad],
            all_files=[good, bad],
            translator_runtime=_runtime(profile, [suffix]),
        )
        violations = checker.check(context)

        assert any(v.file_path == bad for v in violations)
        assert not any(v.file_path == good for v in violations)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_flags_missing_docstrings(self):
        """Run test_flags_missing_docstrings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_flags_missing_docstrings(tmp_path=tmp_path)

    def test_comments_satisfy_policy(self):
        """Run test_comments_satisfy_policy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_comments_satisfy_policy(tmp_path=tmp_path)

    def test_all_files_scanned_when_no_changes(self):
        """Run test_all_files_scanned_when_no_changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_all_files_scanned_when_no_changes(tmp_path=tmp_path)

    def test_metadata_skip_prefixes(self):
        """Run test_metadata_skip_prefixes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_metadata_skip_prefixes(tmp_path=tmp_path)

    def test_non_python_files_are_checked(self):
        """Run test_non_python_files_are_checked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_non_python_files_are_checked(tmp_path=tmp_path)
