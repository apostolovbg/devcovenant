"""Tests for version_sync policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_sync import version_sync
from devcovenant.core.contracts.policy import CheckContext

VersionSyncCheck = version_sync.VersionSyncCheck


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
        """Return a policy configured for role-based version sync."""
        policy = VersionSyncCheck()
        policy.set_options(
            {
                "version_file": "project_lib/VERSION",
                "changelog_file": "CHANGELOG.md",
                "changelog_header_prefix": "## Version",
                "target_roles": [
                    "docs",
                    "changelog",
                    "package_manifest",
                    "legal",
                ],
                "role_extractors": [
                    "docs=>doc_header_version",
                    "changelog=>changelog_header_version",
                    "package_manifest=>manifest_project_version",
                    "legal=>semver_token",
                ],
                "target_role_files": [
                    "docs=>README.md",
                    "docs=>docs/README.md",
                    "changelog=>CHANGELOG.md",
                    "package_manifest=>pyproject.toml",
                    "package_manifest=>app/pyproject.toml",
                    "legal=>LICENSE",
                    "legal=>app/license.txt",
                ],
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
        """Write a document carrying the Project Version header."""
        readme = root / path
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(f"**Project Version:** {version}\n")
        return readme

    def _write_license(self, root: Path, path: str, version: str) -> Path:
        """Write a license file that declares the version."""
        license_path = root / path
        license_path.parent.mkdir(parents=True, exist_ok=True)
        license_path.write_text(f"Project Version: {version}\nMIT License\n")
        return license_path

    def _write_manifest_json(
        self,
        root: Path,
        path: str,
        version: str,
    ) -> Path:
        """Write a JSON manifest with a root-level version field."""
        manifest = root / path
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(f'{{"version": "{version}"}}\n')
        return manifest

    def _write_manifest_yaml(
        self,
        root: Path,
        path: str,
        version: str,
    ) -> Path:
        """Write a YAML manifest with a root-level version field."""
        manifest = root / path
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(f"version: {version}\n")
        return manifest

    def test_detects_version_mismatch(self):
        """Policy should detect role-target version mismatches."""
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
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            mismatch = [v for v in violations if "does not match" in v.message]
            self.assertTrue(mismatch)

    def test_requires_declared_targets_to_exist(self):
        """Declared role targets should be required when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            missing = [
                v
                for v in violations
                if "Required metadata file missing" in v.message
            ]
            self.assertEqual(len(missing), 1)
            self.assertEqual(
                missing[0].file_path.resolve(),
                (repo_root / "docs/README.md").resolve(),
            )

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
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            version_errs = [
                v
                for v in violations
                if "does not match" in v.message
                or "lacks version" in v.message
            ]
            self.assertEqual(len(version_errs), 0)

    def test_ignores_runtime_literals_outside_role_targets(self):
        """Literal matches outside role targets are not version-sync scope."""
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
            self._write_changelog(repo_root, "1.0.0")

            runtime_file = repo_root / "project.py"
            runtime_file.write_text('APP_VERSION = "1.0.0"\n')

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            self.assertEqual(violations, [])
            self.assertTrue(runtime_file.exists())

    def test_does_not_enforce_forward_bump_progression(self):
        """SemVer bump progression is delegated to semantic-version-scope."""
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
            (repo_root / "CHANGELOG.md").write_text(
                "## Log changes here\n\n## Version 1.0.0\n\n"
                "## Version 1.0.1\n",
                encoding="utf-8",
            )

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_resolves_role_targets_from_globs_and_dirs(self):
        """Role globs and dirs should add extra version-synced docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")

            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_readme(repo_root, "docs/guide.md", "1.0.0")
            self._write_readme(repo_root, "docs/internal.md", "2.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            policy = self._policy()
            policy.set_options(
                {
                    "version_file": "project_lib/VERSION",
                    "changelog_file": "CHANGELOG.md",
                    "changelog_header_prefix": "## Version",
                    "target_roles": [
                        "docs",
                        "changelog",
                        "package_manifest",
                        "legal",
                    ],
                    "role_extractors": [
                        "docs=>doc_header_version",
                        "changelog=>changelog_header_version",
                        "package_manifest=>manifest_project_version",
                        "legal=>semver_token",
                    ],
                    "target_role_files": [
                        "docs=>README.md",
                        "docs=>docs/README.md",
                        "changelog=>CHANGELOG.md",
                        "package_manifest=>pyproject.toml",
                        "package_manifest=>app/pyproject.toml",
                        "legal=>LICENSE",
                        "legal=>app/license.txt",
                    ],
                    "target_role_globs": ["docs=>docs/*.md"],
                    "target_role_dirs": ["docs=>docs"],
                },
                {},
            )
            all_files = [
                path for path in repo_root.rglob("*") if path.is_file()
            ]
            context = CheckContext(repo_root=repo_root, all_files=all_files)
            violations = policy.check(context)

            mismatch = [
                item
                for item in violations
                if item.file_path == repo_root / "docs/internal.md"
                and "does not match" in item.message
            ]
            self.assertEqual(len(mismatch), 1)

    def test_rejects_unknown_extractor(self):
        """Unknown role extractors should raise a config violation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            policy = self._policy()
            policy.set_options(
                {
                    "version_file": "project_lib/VERSION",
                    "changelog_file": "CHANGELOG.md",
                    "target_roles": ["docs"],
                    "role_extractors": ["docs=>unknown_extractor"],
                    "target_role_files": ["docs=>README.md"],
                },
                {},
            )
            violations = policy.check(CheckContext(repo_root=repo_root))
            self.assertEqual(len(violations), 1)
            self.assertIn("unknown extractor", violations[0].message)

    def test_manifest_extractor_supports_json_and_yaml(self):
        """Manifest extractor should parse JSON and YAML manifests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir()
            (repo_root / "project_lib/VERSION").write_text("1.0.0\n")
            self._write_changelog(repo_root, "1.0.0")
            self._write_manifest_json(repo_root, "package.json", "1.0.0")
            self._write_manifest_yaml(
                repo_root,
                "manifests/app.yaml",
                "1.0.0",
            )

            policy = VersionSyncCheck()
            policy.set_options(
                {
                    "version_file": "project_lib/VERSION",
                    "changelog_file": "CHANGELOG.md",
                    "changelog_header_prefix": "## Version",
                    "target_roles": ["package_manifest"],
                    "role_extractors": [
                        "package_manifest=>manifest_project_version"
                    ],
                    "target_role_files": [
                        "package_manifest=>package.json",
                        "package_manifest=>manifests/app.yaml",
                    ],
                },
                {},
            )
            violations = policy.check(CheckContext(repo_root=repo_root))
            self.assertEqual(len(violations), 0)

    def test_manifest_extractor_rejects_unsupported_extensions(self):
        """Manifest extractor should reject unsupported file formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir()
            (repo_root / "project_lib/VERSION").write_text("1.0.0\n")
            self._write_changelog(repo_root, "1.0.0")
            legacy_manifest = repo_root / "manifest.ini"
            legacy_manifest.write_text("version=1.0.0\n")

            policy = VersionSyncCheck()
            policy.set_options(
                {
                    "version_file": "project_lib/VERSION",
                    "changelog_file": "CHANGELOG.md",
                    "changelog_header_prefix": "## Version",
                    "target_roles": ["package_manifest"],
                    "role_extractors": [
                        "package_manifest=>manifest_project_version"
                    ],
                    "target_role_files": ["package_manifest=>manifest.ini"],
                },
                {},
            )
            violations = policy.check(CheckContext(repo_root=repo_root))
            self.assertEqual(len(violations), 1)
            self.assertIn(
                "supports only TOML/JSON/YAML",
                violations[0].message,
            )


if __name__ == "__main__":
    unittest.main()
