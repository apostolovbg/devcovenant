"""
Fixer: Package Runtime Mirror

Sync package-shipped mirror artifacts from their canonical repo-root sources.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from devcovenant.core.contracts.policy import FixResult, PolicyFixer, Violation


class PackageRuntimeMirrorFixer(PolicyFixer):
    """Rewrite configured package-runtime mirrors from their source paths."""

    policy_id = "package-runtime-mirror"

    def can_fix(self, violation: Violation) -> bool:
        """Return True when the violation belongs to this mirror policy."""
        return violation.policy_id == self.policy_id

    def fix(self, violation: Violation) -> FixResult:
        """Sync one file or directory mirror from source to target."""
        kind = str(violation.context.get("kind") or "").strip()
        source_value = str(violation.context.get("source_path") or "").strip()
        target_value = str(violation.context.get("target_path") or "").strip()
        if not kind or not source_value or not target_value:
            return FixResult(
                success=False,
                message="Missing kind, source_path, or target_path context.",
            )

        source = Path(source_value)
        target = Path(target_value)
        if kind == "file":
            if not source.is_file():
                return FixResult(
                    success=False,
                    message=f"Mirror source file is missing: {source}.",
                )
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return FixResult(
                success=True,
                message=f"Synced {target} from {source}.",
                files_modified=[target],
            )
        if kind == "dir":
            if not source.is_dir():
                return FixResult(
                    success=False,
                    message=f"Mirror source directory is missing: {source}.",
                )
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target)
            return FixResult(
                success=True,
                message=f"Synced {target} from {source}.",
                files_modified=[target],
            )
        return FixResult(
            success=False,
            message=f"Unsupported package-runtime mirror kind: {kind}.",
        )
