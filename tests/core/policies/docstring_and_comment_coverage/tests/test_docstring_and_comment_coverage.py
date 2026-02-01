"""Tests for the docstring and comment coverage policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.docstring_and_comment_coverage import (
    docstring_and_comment_coverage,
)

DocstringAndCommentCoverageCheck = (
    docstring_and_comment_coverage.DocstringAndCommentCoverageCheck
)


def _create_file(tmp_path: Path, source: str) -> Path:
    """Write a sample module under project_lib for testing."""
    target = tmp_path / "project_lib" / "helpers" / "example.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_flags_missing_docstrings(tmp_path: Path):
    """Modules and functions without comments or docstrings
    trigger violations."""
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
    )
    violations = checker.check(context)

    assert len(violations) >= 3
    assert all(v.severity == "error" for v in violations)
    assert any("Module lacks" in v.message for v in violations)
    assert any(
        "function" in v.message.lower() and "foo" in v.message.lower()
        for v in violations
    )


def test_comments_satisfy_policy(tmp_path: Path):
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
    )
    violations = checker.check(context)

    assert violations == []


def test_all_files_scanned_when_no_changes(tmp_path: Path):
    """Ensure all_files is inspected when no changed files are present."""
    source = "def foo():\n    return 5\n"
    target = _create_file(tmp_path, source)

    checker = DocstringAndCommentCoverageCheck()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[],
        all_files=[target],
    )
    violations = checker.check(context)

    assert any("Module lacks" in v.message for v in violations)


def test_metadata_skip_prefixes(tmp_path: Path):
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
    )
    violations = checker.check(context)

    assert (
        not violations
    ), "Metadata exclusions should allow repo-specific gaps"


def test_non_python_files_are_skipped(tmp_path: Path):
    """Non-Python files should be checked via adapters."""
    cases = [
        (".js", "// ok\nfunction good() {}\n", "function bad() {}\n"),
        (
            ".ts",
            "// ok\nfunction good(): void {}\n",
            "function bad(): void {}\n",
        ),
        (".go", "// ok\nfunc good() {}\n", "func bad() {}\n"),
        (".rs", "/// ok\nfn good() {}\n", "fn bad() {}\n"),
        (".java", "/** ok */\nclass Good {}\n", "class Bad {}\n"),
        (".cs", "/// ok\nclass Good {}\n", "class Bad {}\n"),
    ]

    for suffix, good_src, bad_src in cases:
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
        )
        violations = checker.check(context)

        assert any(v.file_path == bad for v in violations)
        assert not any(v.file_path == good for v in violations)
