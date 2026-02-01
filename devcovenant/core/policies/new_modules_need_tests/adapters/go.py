"""Go adapter for new-modules-need-tests."""

from __future__ import annotations

from pathlib import Path
from typing import List, Set

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.selector_helpers import SelectorSet

SUFFIX = ".go"


def _is_module(path: Path, selector: SelectorSet, repo_root: Path) -> bool:
    """Return True when the path is a Go module under enforcement."""
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


def _test_exists(module: Path) -> bool:
    """Return True if sibling *_test.go exists."""
    candidate = module.with_name(f"{module.stem}_test.go")
    return candidate.exists()


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
    """Return violations for Go modules lacking *_test.go updates."""
    repo_root = context.repo_root
    violations: List[Violation] = []
    changed_tests = _tests_touched(repo_root, tests_dirs, added | modified)

    new_modules = [p for p in added if _is_module(p, selector, repo_root)]
    removed_modules = [
        p for p in deleted if _is_module(p, selector, repo_root)
    ]

    for module in new_modules:
        if not _test_exists(module) and not changed_tests:
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=module,
                    message="Add *_test.go for new Go module.",
                )
            )

    if removed_modules and not changed_tests:
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=removed_modules[0],
                message="Update/remove *_test.go when removing Go modules.",
            )
        )

    return violations
