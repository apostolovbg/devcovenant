"""Python adapter for new-modules-need-tests."""

from __future__ import annotations

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


def _is_module(path: Path, selector: SelectorSet, repo_root: Path) -> bool:
    """Return True when path represents a Python module to track."""
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
        ", ".join(sorted(tests_dirs))
        if len(tests_dirs) > 1
        else tests_dirs[0]
    )

    new_modules = [p for p in added if _is_module(p, selector, repo_root)]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root)
    ]
    tests_changed = _collect_changed_tests(
        repo_root, tests_dirs, added | modified | deleted
    )

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

    return violations
