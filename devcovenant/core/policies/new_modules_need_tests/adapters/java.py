"""Java adapter for new-modules-need-tests."""

from __future__ import annotations

from pathlib import Path
from typing import List, Set

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

SUFFIX = ".java"


def _is_module(path: Path, selector: SelectorSet, repo_root: Path) -> bool:
    """Return True when the path is a Java source under enforcement."""
    return path.suffix.lower() == SUFFIX and selector.matches(path, repo_root)


def _tests_touched(repo_root: Path, tests_dirs: List[str], paths: Set[Path]):
    """Return True if any test directory file changed."""
    for path in paths:
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if any(rel == t or rel.startswith(f"{t}/") for t in tests_dirs):
            return True
    return False


def _test_exists(repo_root: Path, tests_dirs: List[str], stem: str) -> bool:
    """Return True if *Test.java/Tests.java exists under tests dirs."""
    for tests_dir in tests_dirs:
        root = repo_root / tests_dir
        if not root.exists():
            continue
        for suffix in ("Test.java", "Tests.java"):
            candidate = root / f"{stem}{suffix}"
            if candidate.exists():
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
    """Return violations for Java modules lacking tests."""
    repo_root = context.repo_root
    violations: List[Violation] = []
    changed_tests = _tests_touched(repo_root, tests_dirs, added | modified)

    new_modules = [p for p in added if _is_module(p, selector, repo_root)]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root)
    ]

    for module in new_modules:
        has_test = _test_exists(repo_root, tests_dirs, module.stem)
        if not has_test and not changed_tests:
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=module,
                    message="Add *Test.java for new Java module.",
                )
            )

    if removed_modules and not changed_tests:
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=removed_modules[0],
                message="Update tests when removing Java modules.",
            )
        )

    return violations
