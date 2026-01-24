"""
Policy: DevCovenant Self-Enforcement.
"""

from __future__ import annotations

from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyParser
from devcovenant.core.registry import PolicyRegistry


class DevCovenantSelfEnforcementCheck(PolicyCheck):
    """
    Verify that the policy registry is synchronized with policy definitions.
    """

    policy_id = "devcov-self-enforcement"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """
        Check for registry sync issues.
        """
        policy_defs_path = self.get_option("policy_definitions", "AGENTS.md")
        registry_path = self.get_option(
            "registry_file", "devcovenant/registry/registry.json"
        )

        policy_defs = context.repo_root / str(policy_defs_path)
        registry_file = context.repo_root / str(registry_path)

        if not policy_defs.exists():
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=policy_defs,
                    message="Policy definitions file is missing.",
                    suggestion="Restore the policy definitions file.",
                    can_auto_fix=False,
                )
            ]

        if not registry_file.exists():
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=registry_file,
                    message="Policy registry file is missing.",
                    suggestion="Run `devcovenant update-hashes`.",
                    can_auto_fix=False,
                )
            ]

        policies = PolicyParser(policy_defs).parse_agents_md()
        registry = PolicyRegistry(registry_file, context.repo_root)
        issues = registry.check_policy_sync(policies)
        violations: List[Violation] = []

        for issue in issues:
            if issue.issue_type == "script_missing":
                message = (
                    f"Policy script missing for policy '{issue.policy_id}'."
                )
                suggestion = "Add the policy script or remove the policy."
            elif issue.issue_type == "new_policy":
                message = (
                    "Policy registry missing entry for policy "
                    f"'{issue.policy_id}'."
                )
                suggestion = "Run `devcovenant update-hashes`."
            else:
                message = (
                    "Policy registry hash mismatch for policy "
                    f"'{issue.policy_id}'."
                )
                suggestion = "Run `devcovenant update-hashes`."

            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=issue.script_path or registry_file,
                    message=message,
                    suggestion=suggestion,
                    can_auto_fix=False,
                )
            )

        return violations
