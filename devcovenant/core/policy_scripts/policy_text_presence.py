"""Ensure every policy definition includes descriptive text."""

from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyParser


class PolicyTextPresenceCheck(PolicyCheck):
    """Require descriptive text for every policy."""

    policy_id = "policy-text-presence"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Validate that policies include descriptive text."""
        agents_rel = Path(self.get_option("policy_definitions", "AGENTS.md"))
        agents_path = context.repo_root / agents_rel
        if not agents_path.exists():
            return []

        parser = PolicyParser(agents_path)
        violations: List[Violation] = []
        for policy in parser.parse_agents_md():
            description = policy.description.strip()
            if _has_meaningful_text(description):
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=agents_path,
                    message=(
                        "Policy definitions must include descriptive text. "
                        f"Missing text for policy '{policy.policy_id}'."
                    ),
                )
            )
        return violations


def _has_meaningful_text(description: str) -> bool:
    """Return True when the policy description is non-empty and useful."""
    if not description:
        return False
    normalized = description.strip()
    if not normalized:
        return False
    if normalized.lower().startswith("<!-- devcov:"):
        return False
    if all(line.strip() in {"---", ""} for line in normalized.splitlines()):
        return False
    return True
