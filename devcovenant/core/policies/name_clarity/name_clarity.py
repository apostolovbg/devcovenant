"""Language-agnostic clarity checks using shared translator LanguageUnit."""

from __future__ import annotations

from typing import List

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.selector_runtime import SelectorSet
from devcovenant.core.translator_runtime import flag_name_clarity_identifiers


class NameClarityCheck(PolicyCheck):
    """Warn when placeholder or overly short identifiers are introduced."""

    policy_id = "name-clarity"
    version = "1.3.0"
    DEFAULT_SUFFIXES = [
        ".py",
        ".pyi",
        ".pyw",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".cs",
    ]

    def _selector(self) -> SelectorSet:
        """Return selector describing files enforced by the policy."""
        return SelectorSet.from_policy(
            self, defaults={"include_suffixes": self.DEFAULT_SUFFIXES}
        )

    def check(self, context: CheckContext) -> List[Violation]:
        """Run the check across all matching files using translated units."""
        files = context.all_files or context.changed_files or []
        violations: List[Violation] = []
        selector = self._selector()
        runtime = context.translator_runtime
        if runtime is None:
            return violations

        for path in files:
            if not path.is_file() or not selector.matches(
                path, context.repo_root
            ):
                continue
            resolution = runtime.resolve(
                path=path,
                policy_id=self.policy_id,
                context=context,
            )
            if not resolution.is_resolved:
                violations.extend(resolution.violations)
                continue
            source = path.read_text(encoding="utf-8")
            unit = runtime.translate(
                resolution,
                path=path,
                source=source,
                context=context,
            )
            if unit is None:
                continue
            for fact in flag_name_clarity_identifiers(unit):
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="warning",
                        file_path=path,
                        line_number=fact.line_number,
                        message=(
                            f"Identifier '{fact.name}' is overly generic "
                            "or too short; choose a more descriptive name."
                        ),
                    )
                )

        return violations
