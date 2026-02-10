"""Python adapter for new-modules-need-tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Set

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

SKIP_SEGMENTS = {"adapters", "fixers", "assets", "tests"}
PY_SUFFIXES = {".py", ".pyi", ".pyw"}


def _existing_tests(repo_root: Path, tests_dirs: List[str]) -> List[Path]:
    """Return existing test files under the configured roots."""
    test_files: List[Path] = []
    for test_dir in tests_dirs:
        root = repo_root / test_dir
        if not root.exists():
            continue
        test_files.extend(root.rglob("test_*.py"))
    return test_files


def _collect_changed_tests(
    repo_root: Path, tests_dirs: List[str], paths: Set[Path]
) -> List[Path]:
    """Collect touched files that live under tests/."""
    tests = []
    for path in paths:
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if any(
            rel == test_dir or rel.startswith(f"{test_dir}/")
            for test_dir in tests_dirs
        ):
            tests.append(path)
    return tests


def _is_python_test_file(path: Path) -> bool:
    """Return True when file is a Python test module."""
    return path.name.startswith("test_") and path.suffix.lower() == ".py"


def _inherits_testcase(node: ast.ClassDef) -> bool:
    """Return True when class derives from unittest.TestCase."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "TestCase":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "TestCase":
            return True
    return False


def _validate_unittest_style(path: Path) -> str | None:
    """Return violation message when Python tests are not unittest-style."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    if "export_unittest_cases(" in content:
        return (
            "Remove unittest bridge usage and define explicit "
            "unittest.TestCase tests."
        )

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Let syntax-related policies report parser errors.
        return None

    top_level_tests = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    if top_level_tests:
        return (
            "Module-level test_* functions are not allowed; "
            "use unittest.TestCase methods."
        )

    has_unittest_tests = False
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not _inherits_testcase(node):
            continue
        if any(
            isinstance(method, ast.FunctionDef)
            and method.name.startswith("test_")
            for method in node.body
        ):
            has_unittest_tests = True
            break

    if not has_unittest_tests:
        return (
            "Python test modules must define unittest.TestCase "
            "classes with test_* methods."
        )

    return None


def _is_module(path: Path, selector: SelectorSet, repo_root: Path) -> bool:
    """Return True when path represents a Python module to track."""
    if "devcovenant/core/profiles/" in path.as_posix():
        return False
    if path.suffix.lower() not in PY_SUFFIXES:
        return False
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        rel = path
    rel_parts = rel.parts
    if rel_parts and rel_parts[0] == "devcovenant":
        if any(segment in SKIP_SEGMENTS for segment in rel_parts):
            return False
    return selector.matches(path, repo_root)


def check_changes(
    *,
    context: CheckContext,
    policy_id: str,
    selector: SelectorSet,
    tests_dirs: List[str],
    added: Set[Path],
    modified: Set[Path],
    deleted: Set[Path],
) -> List[Violation]:
    """Return violations for new/removed Python modules without tests."""
    violations: List[Violation] = []
    repo_root = context.repo_root
    tests_label = (
        ", ".join(sorted(tests_dirs)) if len(tests_dirs) > 1 else tests_dirs[0]
    )

    new_modules = [p for p in added if _is_module(p, selector, repo_root)]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root)
    ]
    tests_changed = _collect_changed_tests(
        repo_root, tests_dirs, added | modified | deleted
    )
    changed_python_tests = [
        test_path
        for test_path in tests_changed
        if test_path.exists() and _is_python_test_file(test_path)
    ]

    if new_modules and not _existing_tests(repo_root, tests_dirs):
        targets = ", ".join(
            sorted(
                path.relative_to(repo_root).as_posix() for path in new_modules
            )
        )
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=new_modules[0],
                message=(
                    "No tests found under "
                    f"{tests_label}; add test_*.py files before "
                    f"adding modules: {targets}"
                ),
            )
        )
        return violations

    if new_modules and not tests_changed:
        targets = ", ".join(
            sorted(
                path.relative_to(repo_root).as_posix() for path in new_modules
            )
        )
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=new_modules[0],
                message=(
                    f"Add or update tests under {tests_label}/ "
                    f"for new modules: {targets}"
                ),
            )
        )

    if removed_modules and not tests_changed:
        targets = ", ".join(
            sorted(
                path.relative_to(repo_root).as_posix()
                for path in removed_modules
            )
        )
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=removed_modules[0],
                message=(
                    f"Adjust tests under {tests_label}/ "
                    f"when removing modules: {targets}"
                ),
            )
        )

    for test_path in sorted(changed_python_tests):
        message = _validate_unittest_style(test_path)
        if not message:
            continue
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=test_path,
                message=message,
            )
        )

    return violations
