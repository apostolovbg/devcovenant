"""Detect policy text drift versus descriptor metadata."""

from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyParser
from devcovenant.core.policy_descriptor import load_policy_descriptor


def _normalize(text: str) -> str:
    """Normalize policy text for comparison."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


class DevcovParityGuardCheck(PolicyCheck):
    """Warn when descriptor policy text differs from AGENTS."""

    policy_id = "devcov-parity-guard"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Compare policy text to descriptor text for all policies."""
        agents_rel = Path(self.get_option("policy_definitions", "AGENTS.md"))
        agents_path = context.repo_root / agents_rel
        if not agents_path.exists():
            return []

        parser = PolicyParser(agents_path)
        violations: List[Violation] = []
        for policy in parser.parse_agents_md():
            descriptor = load_policy_descriptor(
                context.repo_root, policy.policy_id
            )
            if not descriptor or not descriptor.text:
                continue
            if _normalize(policy.description) == _normalize(descriptor.text):
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="warning",
                    file_path=agents_path,
                    message=(
                        "Descriptor policy text differs from AGENTS. "
                        f"Policy '{policy.policy_id}' should match its "
                        "descriptor text."
                    ),
                    suggestion=(
                        "Regenerate AGENTS from descriptors or update the "
                        "descriptor text to match the intended policy prose."
                    ),
                )
            )
        return violations
