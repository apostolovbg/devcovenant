"""
Policy: DevCovenant Structure Guard

Ensures required DevCovenant files and directories are present.
"""

from pathlib import Path
from typing import List

from devcovenant.base import CheckContext, PolicyCheck, Violation


class DevCovenantStructureGuardCheck(PolicyCheck):
    """Verify DevCovenant repo structure remains intact."""

    policy_id = "devcov-structure-guard"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check for required DevCovenant files and directories."""
        required = [
            "AGENTS.md",
            "DEVCOVENANT.md",
            "README.md",
            "VERSION",
            "CHANGELOG.md",
            "devcovenant/common_policy_scripts",
            "devcovenant/custom_policy_scripts",
            "devcovenant/common_policy_patches",
            "devcovenant/registry.json",
            "tools/run_pre_commit.py",
            "tools/run_tests.py",
        ]
        missing = []
        for rel_path in required:
            path = context.repo_root / rel_path
            if not path.exists():
                missing.append(rel_path)

        if not missing:
            return []

        message = "Missing required DevCovenant paths: " + ", ".join(missing)
        return [
            Violation(
                policy_id=self.policy_id,
                severity="error",
                file_path=context.repo_root / missing[0],
                message=message,
                suggestion=(
                    "Run tools/install_devcovenant.py --target . "
                    "--force-docs --force-config"
                ),
                can_auto_fix=False,
            )
        ]
