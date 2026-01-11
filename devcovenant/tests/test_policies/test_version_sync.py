"""Tests for version_sync policy."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from devcovenant.base import CheckContext
from devcovenant.policy_scripts.version_sync import VersionSyncCheck


class TestVersionSyncPolicy(unittest.TestCase):
    """Test suite for VersionSyncCheck."""

    def _write_pyproject(
        self,
        repo_root: Path,
        version: str,
        name: str = "pyproject.toml",
    ) -> Path:
        """Create a minimal pyproject.toml with the requested version."""
        pyproject = repo_root / name
        pyproject.parent.mkdir(parents=True, exist_ok=True)
        pyproject.write_text(f'[project]\nversion = "{version}"\n')
        return pyproject

    def _policy(self) -> VersionSyncCheck:
        """Return a policy configured for project_lib."""
        policy = VersionSyncCheck()
        policy.set_options(
            {
                "version_file": "project_lib/VERSION",
                "readme_files": "README.md,docs/README.md",
                "pyproject_files": "pyproject.toml,app/pyproject.toml",
                "license_files": "LICENSE,app/license.txt",
                "runtime_entrypoints": ["project.py"],
                "runtime_roots": ["project_lib"],
                "changelog_file": "CHANGELOG.md",
            },
            {},
        )
        return policy

    def _write_changelog(self, root: Path, version: str) -> Path:
        """Write a changelog with the provided version."""
        changelog = root / "CHANGELOG.md"
        changelog.write_text(f"## Log changes here\n\n## Version {version}\n")
        return changelog

    def _write_readme(self, root: Path, path: str, version: str) -> Path:
        """Write a README carrying the version header."""
        readme = root / path
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(f"**Version:** {version}\n")
        return readme

    def _write_citation(self, root: Path, version: str) -> Path:
        """Write a minimal two-entry CITATION.cff."""
        citation = root / "CITATION.cff"
        citation.write_text(f'version: "{version}"\nversion: "{version}"\n')
        return citation

    def _write_license(self, root: Path, path: str, version: str) -> Path:
        """Write a license file that declares the version."""
        license_path = root / path
        license_path.parent.mkdir(parents=True, exist_ok=True)
        license_path.write_text(f"Project Version: {version}\nMIT License\n")
        return license_path

    def test_detects_version_mismatch(self):
        """Policy should detect version mismatches across files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "2.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_citation(repo_root, "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            mismatch = [v for v in violations if "does not match" in v.message]
            self.assertTrue(mismatch)

    def test_allows_matching_versions(self):
        """Policy should pass when versions match everywhere."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_citation(repo_root, "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            version_errs = [
                v for v in violations if "does not match" in v.message
            ]
            self.assertEqual(len(version_errs), 0)

    def test_flags_hardcoded_runtime_version(self):
        """Policy should reject hard-coded versions in runtime code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_citation(repo_root, "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            runtime_file = repo_root / "project.py"
            runtime_file.write_text('APP_VERSION = "1.0.0"\n')

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            hardcoded = [
                v
                for v in violations
                if "Hard-coded suite version" in v.message
            ]
            self.assertEqual(len(hardcoded), 1)
            self.assertEqual(hardcoded[0].file_path, runtime_file)

    def test_requires_forward_semver_bump(self):
        """Policy should forbid decreasing or same version numbers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_citation(repo_root, "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                policy, "_previous_version", return_value="1.0.1"
            ):
                violations = policy.check(context)

            bump_violations = [
                v
                for v in violations
                if "forward-moving SemVer bump" in v.message
            ]
            self.assertEqual(len(bump_violations), 1)


if __name__ == "__main__":
    unittest.main()
