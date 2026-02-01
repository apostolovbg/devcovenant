"""Detect suspicious constructs via language adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet

ADAPTER_BY_SUFFIX = {
    ".py": "devcovenant.core.policies.security_scanner.adapters.python",
    ".pyi": "devcovenant.core.policies.security_scanner.adapters.python",
    ".pyw": "devcovenant.core.policies.security_scanner.adapters.python",
    ".js": "devcovenant.core.policies.security_scanner.adapters.javascript",
    ".jsx": "devcovenant.core.policies.security_scanner.adapters.javascript",
    ".ts": "devcovenant.core.policies.security_scanner.adapters.typescript",
    ".tsx": "devcovenant.core.policies.security_scanner.adapters.typescript",
    ".go": "devcovenant.core.policies.security_scanner.adapters.go",
    ".rs": "devcovenant.core.policies.security_scanner.adapters.rust",
    ".java": "devcovenant.core.policies.security_scanner.adapters.java",
    ".cs": "devcovenant.core.policies.security_scanner.adapters.csharp",
}


def _adapter_for(path: Path):
    """Return adapter module for a given file path, or None."""
    module_path = ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if not module_path:
        return None
    return importlib.import_module(module_path)


class SecurityScannerCheck(PolicyCheck):
    """Flag known insecure constructs that breach compliance guidelines."""

    policy_id = "security-scanner"
    version = "1.1.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Search repository modules using adapters."""
        violations: List[Violation] = []
        files = context.all_files or context.changed_files or []
        selector = SelectorSet.from_policy(
            self, defaults={"include_suffixes": list(ADAPTER_BY_SUFFIX.keys())}
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
