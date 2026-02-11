"""JS/JSX adapter for modules-need-tests."""

from __future__ import annotations

from pathlib import Path
from typing import List, Set, Tuple

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

TEST_SUFFIXES = (".test.js", ".spec.js", ".test.jsx", ".spec.jsx")
SUFFIXES = {".js", ".jsx"}


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


def _is_module(
    path: Path,
    selector: SelectorSet,
    repo_root: Path,
    tests_dirs: List[str],
) -> bool:
    """Return True when the path is a JS module under enforcement."""
    if path.suffix.lower() not in SUFFIXES:
        return False
    name = path.name.lower()
    if ".test." in name or ".spec." in name or name.startswith("test_"):
        return False
    if _is_under_tests(path, repo_root, tests_dirs):
        return False
    return selector.matches(path, repo_root)


def _test_exists(repo_root: Path, tests_dirs: List[str], stem: str) -> bool:
    """Return True if a matching test file exists under tests dirs."""
    needle = stem.lower()
    for tests_dir in tests_dirs:
        root = repo_root / tests_dir
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            name = candidate.name.lower()
            if ".test." in name or ".spec." in name:
                if needle in name:
                    return True
            if name.startswith("test_") and needle in name:
                return True
    return False


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
    """Return violations for JS modules without tests."""
    repo_root = context.repo_root
    del mirror_roots
    violations: List[Violation] = []

    changed_modules = [
        p
        for p in (added | modified)
        if _is_module(p, selector, repo_root, tests_dirs)
    ]

    for module in changed_modules:
        stem = module.stem
        if not _test_exists(repo_root, tests_dirs, stem):
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=module,
                    message=(
                        "Add a *.test.js/.spec.js test for changed "
                        f"module {stem}"
                    ),
                )
            )

    return violations
