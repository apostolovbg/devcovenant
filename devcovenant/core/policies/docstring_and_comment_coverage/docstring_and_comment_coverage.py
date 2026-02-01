"""Enforce docstrings/comments via language adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

ADAPTER_BY_SUFFIX: Dict[str, str] = {
    ".py": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.python"
    ),
    ".pyi": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.python"
    ),
    ".pyw": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.python"
    ),
    ".js": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.javascript"
    ),
    ".jsx": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.javascript"
    ),
    ".ts": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.typescript"
    ),
    ".tsx": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.typescript"
    ),
    ".go": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.go"
    ),
    ".rs": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.rust"
    ),
    ".java": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.java"
    ),
    ".cs": (
        "devcovenant.core.policies."
        "docstring_and_comment_coverage.adapters.csharp"
    ),
}


def _adapter_for(path: Path):
    """Return the adapter module for a given file path, or None."""
    module_path = ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if not module_path:
        return None
    return importlib.import_module(module_path)


class DocstringAndCommentCoverageCheck(PolicyCheck):
    """Treat missing docstrings/comments as policy violations."""

    policy_id = "docstring-and-comment-coverage"
    version = "1.0.0"
    DEFAULT_SUFFIXES = list(ADAPTER_BY_SUFFIX.keys())

    def _build_selector(self) -> SelectorSet:
        """Return the unified selector for this policy."""
        defaults = {
            "include_suffixes": self.DEFAULT_SUFFIXES,
        }
        return SelectorSet.from_policy(self, defaults=defaults)

    def check(self, context: CheckContext) -> List[Violation]:
        """Detect functions, classes or modules without documentation."""
        files = context.all_files or context.changed_files or []
        violations: List[Violation] = []
        selector = self._build_selector()

        for path in files:
            if not path.is_file():
                continue
            if not selector.matches(path, context.repo_root):
                continue

            adapter = _adapter_for(path)
            if adapter is None:
                continue

            try:
                source = path.read_text(encoding="utf-8")
            except OSError:
                continue

            violations.extend(
                adapter.check_file(
                    path=path,
                    source=source,
                    policy_id=self.policy_id,
                )
            )

        return violations
