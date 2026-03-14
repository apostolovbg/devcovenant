"""
Fixer for dependency-license-sync violations.
"""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.policies.dependency_license_sync import (
    dependency_license_sync,
)
from devcovenant.core.policy_contracts import FixResult, PolicyFixer, Violation


class DependencyLicenseSyncFixer(PolicyFixer):
    """Ensure the license report and directory reflect dependency updates."""

    policy_id = "dependency-license-sync"

    def can_fix(self, violation: Violation) -> bool:
        """Only run when dependency manifests are known."""
        return violation.policy_id == self.policy_id and bool(
            violation.context.get("changed_dependency_files")
        )

    def fix(self, violation: Violation) -> FixResult:
        """Update the license report and directory markers."""
        repo_root = getattr(self, "repo_root", Path.cwd())
        changed_files = violation.context.get("changed_dependency_files", [])
        try:
            modified = dependency_license_sync.refresh_license_artifacts(
                repo_root=repo_root,
                changed_dependency_files=changed_files,
                third_party_file=violation.context["third_party_file"],
                licenses_dir=violation.context["licenses_dir"],
                report_heading=violation.context["report_heading"],
            )
        except ValueError as error:
            return FixResult(
                success=False,
                message=str(error),
            )
        if modified:
            file_list = ", ".join(path.as_posix() for path in modified)
            return FixResult(
                success=True,
                message=(
                    "Updated dependency-license-sync artifacts: "
                    f"{file_list}"
                ),
                files_modified=modified,
            )
        return FixResult(
            success=True,
            message="Dependency-license-sync artifacts are already in sync.",
        )
