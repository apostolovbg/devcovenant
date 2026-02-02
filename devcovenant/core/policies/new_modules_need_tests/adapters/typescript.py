"""TS/TSX adapter for new-modules-need-tests."""

from __future__ import annotations

from pathlib import Path
from typing import List, Set

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

TEST_SUFFIXES = (".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx")
SUFFIXES = {".ts", ".tsx"}


def _is_module(path: Path, selector: SelectorSet, repo_root: Path) -> bool:
    """Return True when the path is a TS module under enforcement."""
    if "devcovenant/core/profiles/" in path.as_posix():
        return False
    if path.suffix.lower() not in SUFFIXES:
        return False
    return selector.matches(path, repo_root)


def _test_exists(repo_root: Path, tests_dirs: List[str], stem: str) -> bool:
    """Return True if a matching test file exists under tests dirs."""
    for tests_dir in tests_dirs:
        root = repo_root / tests_dir
        if not root.exists():
            continue
        for suffix in TEST_SUFFIXES:
            candidate = root / f"{stem}{suffix}"
            if candidate.exists():
                return True
        for suffix in SUFFIXES:
            candidate = root / "__tests__" / f"{stem}{suffix}"
            if candidate.exists():
                return True
    return False


def _tests_touched(repo_root: Path, tests_dirs: List[str], paths: Set[Path]):
    """Return True if any file under tests dirs changed."""
    for path in paths:
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if any(rel == t or rel.startswith(f"{t}/") for t in tests_dirs):
            return True
    return False


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
    """Return violations for TS modules lacking companion tests."""
    repo_root = context.repo_root
    changed_tests = _tests_touched(repo_root, tests_dirs, added | modified)
    violations: List[Violation] = []

    new_modules = [p for p in added if _is_module(p, selector, repo_root)]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root)
    ]

    for module in new_modules:
        stem = module.stem
        if not _test_exists(repo_root, tests_dirs, stem) and not changed_tests:
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=module,
                    message=(
                        "Add *.test.ts/ *.spec.ts (or __tests__) "
                        "for module."
                    ),
                )
            )

    if removed_modules and not changed_tests:
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=removed_modules[0],
                message="Update tests to reflect removed TS modules.",
            )
        )

    return violations
