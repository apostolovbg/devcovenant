"""PEP 440 adapter for the version-governance policy."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List

from packaging.version import InvalidVersion, Version

if TYPE_CHECKING:
    from .version_governance import (
        VersionGovernanceCheck,
        VersionReleaseContext,
    )


class Pep440Scheme:
    """Handle PEP 440 parsing and ordering for Python package versions."""

    name = "pep440"

    def preflight(
        self,
        check: "VersionGovernanceCheck",
        repo_root: Path,
        version_path: Path,
    ) -> list:
        """PEP 440 parsing uses the packaged `packaging` dependency."""
        del check, repo_root, version_path
        return []

    def version_pattern(
        self,
        check: "VersionGovernanceCheck",
        repo_root: Path,
    ) -> str:
        """Return a permissive token pattern for PEP 440 changelog headers."""
        del check, repo_root
        return r"[A-Za-z0-9!+._-]+"

    def parse_version(
        self,
        value: str,
        check: "VersionGovernanceCheck",
        repo_root: Path,
    ) -> Version:
        """Parse one PEP 440 version string into a comparable Version."""
        del check, repo_root
        token = str(value or "").strip()
        try:
            return Version(token)
        except InvalidVersion as exc:
            raise ValueError(
                f"`{token}` is not a valid pep440 version"
            ) from exc

    def compare_versions(self, left: Version, right: Version) -> int:
        """Compare two parsed PEP 440 versions."""
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def validate_release(
        self,
        check: "VersionGovernanceCheck",
        release: "VersionReleaseContext",
    ) -> List:
        """PEP 440 imposes no extra changelog-scope rules by default."""
        return []
