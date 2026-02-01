"""Enforce docstrings/comments via language adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

PYTHON_SUFFIXES = {".py", ".pyi", ".pyw"}


def _adapter_for(path: Path):
    """Return the adapter module for a given file path, or None."""
    if path.suffix.lower() in PYTHON_SUFFIXES:
        return importlib.import_module(
            "devcovenant.core.policies."
            "docstring_and_comment_coverage.adapters.python"
        )
    return None


class DocstringAndCommentCoverageCheck(PolicyCheck):
    """Treat missing docstrings/comments as policy violations."""

    policy_id = "docstring-and-comment-coverage"
    version = "1.0.0"
    DEFAULT_SUFFIXES = [".py"]

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
