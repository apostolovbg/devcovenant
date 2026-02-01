"""Adapter-driven clarity checks for short/generic identifiers."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

PYTHON_SUFFIXES = {".py", ".pyi", ".pyw"}


def _adapter_for(path: Path):
    """Return adapter module for the given file path, or None."""
    if path.suffix.lower() in PYTHON_SUFFIXES:
        return importlib.import_module(
            "devcovenant.core.policies.name_clarity.adapters.python"
        )
    return None


class NameClarityCheck(PolicyCheck):
    """Warn when placeholder or overly short identifiers are introduced."""

    policy_id = "name-clarity"
    version = "1.1.0"
    DEFAULT_SUFFIXES = [".py"]

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
