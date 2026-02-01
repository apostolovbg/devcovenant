"""Ensure modules under module roots keep tests alongside (adapter-driven)."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Set

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet, build_watchlists

ADAPTER_BY_SUFFIX: Dict[str, str] = {
    ".py": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.python"
    ),
    ".pyi": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.python"
    ),
    ".pyw": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.python"
    ),
    ".js": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.javascript"
    ),
    ".jsx": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.javascript"
    ),
    ".ts": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.typescript"
    ),
    ".tsx": (
        "devcovenant.core.policies.new_modules_need_tests.adapters.typescript"
    ),
    ".go": "devcovenant.core.policies.new_modules_need_tests.adapters.go",
    ".rs": "devcovenant.core.policies.new_modules_need_tests.adapters.rust",
    ".java": "devcovenant.core.policies.new_modules_need_tests.adapters.java",
    ".cs": "devcovenant.core.policies.new_modules_need_tests.adapters.csharp",
}


def _adapter_for(path: Path):
    """Return adapter module for a given file path, or None."""
    module_path = ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if not module_path:
        return None
    return importlib.import_module(module_path)


class NewModulesNeedTestsCheck(PolicyCheck):
    """Ensure new modules ship with accompanying tests via adapters."""

    policy_id = "new-modules-need-tests"
    version = "1.2.0"

    def _collect_repo_changes(
        self, repo_root: Path
    ) -> tuple[Set[Path], Set[Path], Set[Path]]:
        """Return added, modified, deleted files reported by Git."""
        try:
            output = subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=repo_root,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return set(), set(), set()

        added: Set[Path] = set()
        modified: Set[Path] = set()
        deleted: Set[Path] = set()

        for line in output.splitlines():
            if not line or len(line) < 4:
                continue
            status, path_str = line[:2], line[3:]
            path = repo_root / path_str
            index_state, worktree_state = status[0], status[1]

            if index_state == "D" or worktree_state == "D":
                deleted.add(path)
                continue
            if index_state in {"A", "C", "R"} or worktree_state in {
                "A",
                "?",
            }:
                added.add(path)
            elif index_state == "?":
                added.add(path)
            elif index_state in {"M", "R", "C"} or worktree_state == "M":
                modified.add(path)

        return added, modified, deleted

    def check(self, context: CheckContext) -> List[Violation]:
        """Check that new modules have corresponding tests."""
        violations: List[Violation] = []

        added, modified, deleted = self._collect_repo_changes(
            context.repo_root
        )

        module_selector = SelectorSet.from_policy(self)
        _, configured_watch_dirs = build_watchlists(
            self, defaults={"watch_dirs": ["tests"]}
        )
        _, prefixed_tests_dirs = build_watchlists(
            self,
            prefix="tests_",
            defaults={"watch_dirs": configured_watch_dirs or ["tests"]},
        )
        if prefixed_tests_dirs:
            tests_dirs = prefixed_tests_dirs
        elif configured_watch_dirs:
            tests_dirs = configured_watch_dirs
        else:
            tests_dirs = ["tests"]

        adapters_cache: Dict[str, object] = {}

        for path in added | modified | deleted:
            adapter = _adapter_for(path)
            if adapter:
                adapters_cache.setdefault(path.suffix.lower(), adapter)

        for adapter in set(adapters_cache.values()) or [
            importlib.import_module(
                "devcovenant.core.policies.new_modules_need_tests."
                "adapters.python"
            )
        ]:
            violations.extend(
                adapter.check_changes(
                    context=context,
                    policy_id=self.policy_id,
                    selector=module_selector,
                    tests_dirs=tests_dirs,
                    added=added,
                    modified=modified,
                    deleted=deleted,
                )
            )

        return violations
