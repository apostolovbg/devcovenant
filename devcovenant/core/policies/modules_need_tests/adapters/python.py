"""Python adapter for modules-need-tests."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Sequence, Set, Tuple

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

PY_SUFFIXES = {".py", ".pyi", ".pyw"}
IGNORED_MODULE_STEMS = {"__init__", "__main__"}


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


def _is_under_tests(
    path: Path, repo_root: Path, tests_dirs: List[str]
) -> bool:
    """Return True when a path resolves under configured tests roots."""
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return any(
        rel == test_dir or rel.startswith(f"{test_dir}/")
        for test_dir in tests_dirs
    )


def _is_python_test_file(path: Path) -> bool:
    """Return True when file is a Python test module."""
    return path.name.startswith("test_") and path.suffix.lower() == ".py"


def _has_related_python_test(
    module: Path,
    test_files: Sequence[Path],
) -> bool:
    """Return True when any test file appears related to ``module``."""
    module_name = module.stem.lower()
    module_compact = re.sub(r"[^a-zA-Z0-9]+", "", module_name)
    if not module_compact:
        return False
    for test_path in test_files:
        test_name = test_path.stem.lower()
        test_compact = re.sub(r"[^a-zA-Z0-9]+", "", test_name)
        if module_name in test_name:
            return True
        if module_compact and module_compact in test_compact:
            return True
    return False


def _mirror_test_candidates(
    module: Path,
    repo_root: Path,
    mirror_roots: Sequence[Tuple[str, str]],
) -> List[Path]:
    """Return mirror test candidates for a module under configured roots."""
    try:
        rel = module.relative_to(repo_root).as_posix()
    except ValueError:
        return []
    candidates: List[Path] = []
    for source_prefix, tests_prefix in mirror_roots:
        if rel != source_prefix and not rel.startswith(f"{source_prefix}/"):
            continue
        remainder = rel[len(source_prefix) :].lstrip("/")
        if not remainder:
            continue
        remainder_path = Path(remainder)
        tests_parent = repo_root / tests_prefix / remainder_path.parent
        stem = remainder_path.stem
        candidates.extend(
            [
                tests_parent / f"test_{stem}.py",
                tests_parent / f"{stem}_test.py",
            ]
        )
    return candidates


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


def _is_module(
    path: Path,
    selector: SelectorSet,
    repo_root: Path,
    tests_dirs: List[str],
) -> bool:
    """Return True when path represents a Python module to track."""
    if path.suffix.lower() not in PY_SUFFIXES:
        return False
    if path.stem in IGNORED_MODULE_STEMS:
        return False
    if path.name.startswith("test_"):
        return False
    if _is_under_tests(path, repo_root, tests_dirs):
        return False
    return selector.matches(path, repo_root)


def _iter_mirror_test_files(
    repo_root: Path, mirror_roots: Sequence[Tuple[str, str]]
) -> List[Path]:
    """Return test files located in mirror target roots."""
    discovered: List[Path] = []
    seen: Set[Path] = set()
    for _source_prefix, tests_prefix in mirror_roots:
        tests_root = repo_root / tests_prefix
        if not tests_root.exists():
            continue
        for pattern in ("test_*.py", "*_test.py"):
            for candidate in tests_root.rglob(pattern):
                if not candidate.is_file() or candidate in seen:
                    continue
                seen.add(candidate)
                discovered.append(candidate)
    return discovered


def _source_for_mirror_test(
    test_file: Path,
    repo_root: Path,
    mirror_roots: Sequence[Tuple[str, str]],
) -> Path | None:
    """Map a mirror test path back to the source module it targets."""
    for source_prefix, tests_prefix in mirror_roots:
        tests_root = repo_root / tests_prefix
        try:
            rel = test_file.relative_to(tests_root)
        except ValueError:
            continue
        name = rel.name
        if name.startswith("test_") and name.endswith(".py"):
            module_stem = name[5:-3]
        elif name.endswith("_test.py"):
            module_stem = name[:-8]
        else:
            return None
        if not module_stem:
            return None
        return repo_root / source_prefix / rel.parent / f"{module_stem}.py"
    return None


def check_changes(
    *,
    context: CheckContext,
    policy_id: str,
    selector: SelectorSet,
    tests_dirs: List[str],
    mirror_roots: List[Tuple[str, str]],
    added: Set[Path],
    modified: Set[Path],
    deleted: Set[Path],
) -> List[Violation]:
    """Return violations for changed Python modules missing tests."""
    violations: List[Violation] = []
    repo_root = context.repo_root
    tests_label = (
        ", ".join(sorted(tests_dirs)) if len(tests_dirs) > 1 else tests_dirs[0]
    )

    changed_modules = [
        p
        for p in (added | modified)
        if _is_module(p, selector, repo_root, tests_dirs)
    ]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root, tests_dirs)
    ]
    tests_changed = _collect_changed_tests(
        repo_root, tests_dirs, added | modified | deleted
    )
    existing_python_tests = _existing_tests(repo_root, tests_dirs)
    changed_python_tests = [
        test_path
        for test_path in tests_changed
        if test_path.exists() and _is_python_test_file(test_path)
    ]

    if changed_modules and not existing_python_tests:
        targets = ", ".join(
            sorted(
                path.relative_to(repo_root).as_posix()
                for path in changed_modules
            )
        )
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=changed_modules[0],
                message=(
                    "No tests found under "
                    f"{tests_label}; add test_*.py files before "
                    f"changing modules: {targets}"
                ),
            )
        )
        return violations

    for module in sorted(changed_modules):
        mirror_candidates = _mirror_test_candidates(
            module, repo_root, mirror_roots
        )
        if mirror_candidates:
            if any(candidate.exists() for candidate in mirror_candidates):
                continue
            expected = ", ".join(
                candidate.relative_to(repo_root).as_posix()
                for candidate in mirror_candidates
            )
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=module,
                    message=(
                        "Mirror mode requires tests under mirrored paths. "
                        f"Add one of: {expected}"
                    ),
                )
            )
            continue
        if _has_related_python_test(module, existing_python_tests):
            continue
        module_rel = module.relative_to(repo_root).as_posix()
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=module,
                message=(
                    f"Add or update related tests under {tests_label}/ "
                    f"for changed module: {module_rel}"
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

    if mirror_roots:
        for test_file in sorted(
            _iter_mirror_test_files(repo_root, mirror_roots)
        ):
            source_file = _source_for_mirror_test(
                test_file, repo_root, mirror_roots
            )
            if source_file is None:
                continue
            if source_file.exists() and _is_module(
                source_file, selector, repo_root, tests_dirs
            ):
                continue
            test_rel = test_file.relative_to(repo_root).as_posix()
            source_rel = source_file.relative_to(repo_root).as_posix()
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=test_file,
                    message=(
                        "Remove stale mirrored test with no valid source "
                        f"module: {test_rel} (expected source {source_rel})"
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
