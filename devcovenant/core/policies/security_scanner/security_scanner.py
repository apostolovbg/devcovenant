"""Detect suspicious constructs via language adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

PYTHON_SUFFIXES = {".py", ".pyi", ".pyw"}


def _adapter_for(path: Path):
    """Return adapter module for a given file path, or None."""
    if path.suffix.lower() in PYTHON_SUFFIXES:
        return importlib.import_module(
            "devcovenant.core.policies.security_scanner.adapters.python"
        )
    return None


class SecurityScannerCheck(PolicyCheck):
    """Flag known insecure constructs that breach compliance guidelines."""

    policy_id = "security-scanner"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Search repository modules using adapters."""
        violations: List[Violation] = []
        files = context.all_files or context.changed_files or []
        selector = SelectorSet.from_policy(
            self, defaults={"include_suffixes": [".py"]}
        )

        for path in files:
            if not path.is_file():
                continue
            try:
                path.relative_to(context.repo_root)
            except ValueError:
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
