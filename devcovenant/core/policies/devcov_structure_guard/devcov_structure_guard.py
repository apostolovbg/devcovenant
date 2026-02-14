"""
Policy: DevCovenant Structure Guard

Ensures required DevCovenant files and directories are present.
"""

from typing import List

from devcovenant.core import registry_runtime as manifest_module
from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)


class DevCovenantStructureGuardCheck(PolicyCheck):
    """Verify DevCovenant repo structure remains intact."""

    policy_id = "devcov-structure-guard"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check for required DevCovenant files and directories."""
        manifest = manifest_module.ensure_manifest(context.repo_root)
        if manifest is None:
            required_dirs = []
            required_files = ["devcovenant"]
            required_docs = ["AGENTS.md"]
        else:
            core = manifest.get("core", {})
            docs = manifest.get("docs", {})
            required_dirs = core.get("dirs", [])
            required_files = core.get("files", [])
            required_docs = docs.get("core", [])

        missing = []
        for rel_path in required_dirs:
            path = context.repo_root / rel_path
            if not path.is_dir():
                missing.append(rel_path)
        for rel_path in list(required_files) + list(required_docs):
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
                    "Run `devcovenant refresh` to restore managed files."
                ),
                can_auto_fix=False,
            )
        ]
