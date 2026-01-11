"""
Policy: DevCovenant Self-Enforcement

Ensures devcovenant follows its own policies.
"""

from typing import List

from devcovenant.base import CheckContext, PolicyCheck, Violation


class DevCovenantSelfEnforcementCheck(PolicyCheck):
    """
    Verify that devcovenant's own policy scripts follow best practices.
    """

    policy_id = "devcov-self-enforcement"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """
        Check that devcovenant policy scripts have tests and follow standards.

        Args:
            context: Check context

        Returns:
            List of violations
        """
        violations = []

        policy_dirs = [
            context.repo_root / "devcovenant" / "common_policy_scripts",
            context.repo_root / "devcovenant" / "custom_policy_scripts",
        ]
        policy_dirs = [path for path in policy_dirs if path.exists()]
        if not policy_dirs:
            return violations

        test_policies_dir = (
            context.repo_root / "devcovenant" / "tests" / "test_policies"
        )

        # Check each policy script
        for policy_dir in policy_dirs:
            for script_path in policy_dir.glob("*.py"):
                if script_path.name == "__init__.py":
                    continue

                # Check if test exists
                test_name = f"test_{script_path.stem}.py"
                test_path = test_policies_dir / test_name

                if not test_path.exists():
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=script_path,
                            message=(
                                f"Policy script '{script_path.name}' lacks "
                                f"corresponding test file"
                            ),
                            suggestion=f"Create test file at: {test_path}",
                            can_auto_fix=False,
                        )
                    )

        return violations
