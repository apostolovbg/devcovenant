"""
Policy: DevCovenant Structure Guard

Ensures required DevCovenant files and directories are present.
"""

from typing import List

import yaml

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.services import registry as manifest_module


class DevCovenantStructureGuardCheck(PolicyCheck):
    """Verify DevCovenant repo structure remains intact."""

    policy_id = "devcov-structure-guard"
    version = "1.0.0"

    def _read_active_profiles(self, repo_root) -> list[str]:
        """Read active profiles from repo config when available."""
        config_path = repo_root / "devcovenant" / "config.yaml"
        if not config_path.exists():
            return []
        try:
            payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return []
        if not isinstance(payload, dict):
            return []
        profiles = payload.get("profiles")
        if not isinstance(profiles, dict):
            return []
        active = profiles.get("active")
        if not isinstance(active, list):
            return []
        return [str(token).strip() for token in active if str(token).strip()]

    def _repo_requires_bytecode_hygiene(self, repo_root) -> bool:
        """Return True when repo profiles enforce bytecode hygiene."""
        return "devcovrepo" in self._read_active_profiles(repo_root)

    def _find_bytecode_artifacts(self, repo_root) -> list[str]:
        """Return repo-relative bytecode artifacts under devcovenant/**."""
        devcovenant_root = repo_root / "devcovenant"
        if not devcovenant_root.exists():
            return []
        artifacts = []
        for path in devcovenant_root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                artifacts.append(str(path.relative_to(repo_root)))
                continue
            if path.is_file() and path.suffix in {".pyc", ".pyo", ".pyd"}:
                artifacts.append(str(path.relative_to(repo_root)))
        return artifacts

    def check(self, context: CheckContext) -> List[Violation]:
        """Check for required DevCovenant files and directories."""
        manifest = manifest_module.ensure_manifest(context.repo_root)
        if manifest is None:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=context.repo_root / "devcovenant",
                    message=(
                        "Manifest is missing and could not be created for "
                        "the current repository."
                    ),
                    suggestion="Restore `devcovenant/` and rerun refresh.",
                    can_auto_fix=False,
                )
            ]

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
            if self._repo_requires_bytecode_hygiene(context.repo_root):
                artifacts = self._find_bytecode_artifacts(context.repo_root)
                if artifacts:
                    sample = artifacts[0]
                    return [
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=context.repo_root / sample,
                            message=(
                                "Repo-local bytecode artifacts were found "
                                f"under devcovenant/: {sample}"
                            ),
                            suggestion=(
                                "Remove bytecode artifacts under devcovenant/ "
                                "and rerun the gate sequence."
                            ),
                            can_auto_fix=False,
                        )
                    ]
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
