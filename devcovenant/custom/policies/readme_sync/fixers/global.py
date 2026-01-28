"""
Fixer: README Sync

Auto-sync devcovenant/README.md from README.md (repo-only blocks removed).
"""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.base import FixResult, PolicyFixer, Violation


class ReadmeSyncFixer(PolicyFixer):
    """Write the expected README text into devcovenant/README.md."""

    policy_id = "readme-sync"

    def can_fix(self, violation: Violation) -> bool:
        """Return True when the violation targets readme-sync."""
        return violation.policy_id == self.policy_id

    def fix(self, violation: Violation) -> FixResult:
        """Apply the expected text to the target README."""
        expected = violation.context.get("expected_text")
        target = violation.context.get("target_path")
        if not expected or not target:
            return FixResult(
                success=False,
                message="Missing expected_text or target_path in context.",
            )
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(expected), encoding="utf-8")
        return FixResult(
            success=True,
            message="Synced devcovenant/README.md from README.md.",
            files_modified=[path],
        )
