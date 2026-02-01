"""Adapter-driven clarity checks for short/generic identifiers."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

ADAPTER_BY_SUFFIX = {
    ".py": "devcovenant.core.policies.name_clarity.adapters.python",
    ".pyi": "devcovenant.core.policies.name_clarity.adapters.python",
    ".pyw": "devcovenant.core.policies.name_clarity.adapters.python",
    ".js": "devcovenant.core.policies.name_clarity.adapters.javascript",
    ".jsx": "devcovenant.core.policies.name_clarity.adapters.javascript",
    ".ts": "devcovenant.core.policies.name_clarity.adapters.typescript",
    ".tsx": "devcovenant.core.policies.name_clarity.adapters.typescript",
    ".go": "devcovenant.core.policies.name_clarity.adapters.go",
    ".rs": "devcovenant.core.policies.name_clarity.adapters.rust",
    ".java": "devcovenant.core.policies.name_clarity.adapters.java",
    ".cs": "devcovenant.core.policies.name_clarity.adapters.csharp",
}


def _adapter_for(path: Path):
    """Return adapter module for the given file path, or None."""
    module_path = ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if not module_path:
        return None
    return importlib.import_module(module_path)


class NameClarityCheck(PolicyCheck):
    """Warn when placeholder or overly short identifiers are introduced."""

    policy_id = "name-clarity"
    version = "1.2.0"
    DEFAULT_SUFFIXES = list(ADAPTER_BY_SUFFIX.keys())

    def _selector(self) -> SelectorSet:
        """Return selector describing files enforced by the policy."""
        return SelectorSet.from_policy(
            self, defaults={"include_suffixes": self.DEFAULT_SUFFIXES}
        )

    def check(self, context: CheckContext) -> List[Violation]:
        """Run the check across all matching files using adapters."""
        files = context.all_files or context.changed_files or []
        violations: List[Violation] = []
        selector = self._selector()

        for path in files:
            if not path.is_file():
                continue
            if not selector.matches(path, context.repo_root):
                continue

            adapter = _adapter_for(path)
            if adapter is None:
                continue

            text = path.read_text(encoding="utf-8")
            violations.extend(
                adapter.check_file(
                    path=path,
                    source=text,
                    policy_id=self.policy_id,
                )
            )

        return violations
