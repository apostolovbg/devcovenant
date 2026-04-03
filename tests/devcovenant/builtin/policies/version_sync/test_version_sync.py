"""Tests for version_sync policy."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.calver import CalverScheme
from devcovenant.builtin.policies.version_governance.custom_regex import (
    CustomRegexScheme,
)
from devcovenant.builtin.policies.version_governance.pep440 import Pep440Scheme
from devcovenant.builtin.policies.version_governance.semver import SemverScheme
from devcovenant.builtin.policies.version_sync import version_sync
from devcovenant.core.policy_contract import CheckContext

VersionSyncCheck = version_sync.VersionSyncCheck


class _RomanNumeralScheme:
    """Minimal custom adapter stand-in for scheme-agnostic sync tests."""

    name = "custom_adapter"

    _VALUES = {
        "I": 1,
        "V": 5,
        "X": 10,
    }

    def preflight(self, check, repo_root, version_path):
        """Roman test adapter has no extra runtime prerequisites."""
        del check, repo_root, version_path
        return []

    def version_pattern(self, check, repo_root):
        """Expose the Roman numeral token pattern for changelog headers."""
        del check, repo_root
        return r"[IVX]+"

    def parse_version(self, value, check, repo_root):
        """Translate one Roman numeral token into a comparable integer."""
        del check, repo_root
        token = str(value or "").strip().upper()
        if token not in {"I", "V", "X"}:
            raise ValueError(f"`{token}` is not a supported Roman release")
        return self._VALUES[token]

    def compare_versions(self, left, right):
        """Compare parsed Roman numeral values numerically."""
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def validate_release(self, check, release):
        """Roman test adapter does not add extra release rules."""
        del check, release
        return []


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

    def _policy(
        self,
        *,
        role_legality_schemes: list[str] | None = None,
    ) -> VersionSyncCheck:
        """Return a policy configured for role-based version sync."""
        policy = VersionSyncCheck()
        metadata_options = {
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
                "docs=>project_version_line",
                "changelog=>changelog_header_version",
                "package_manifest=>manifest_project_version",
                "legal=>project_version_line",
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
        }
        if role_legality_schemes:
            metadata_options["role_legality_schemes"] = role_legality_schemes
        policy.set_options(metadata_options, {})
        return policy

    def _resolved_scheme(self, scheme_name: str = "semver", **options):
        """Return one patched version-governance runtime tuple."""
        checker = version_governance.VersionGovernanceCheck()
        checker.set_options({"scheme": scheme_name, **options}, {})
        schemes = {
            "semver": SemverScheme(),
            "calver": CalverScheme(),
            "pep440": Pep440Scheme(),
            "custom_regex": CustomRegexScheme(),
            "custom_adapter": _RomanNumeralScheme(),
        }
        return scheme_name, schemes[scheme_name], checker

    def test_module_exposes_versionsync_class_alias(self):
        """Module-level class alias should point at the policy class."""
        self.assertIs(VersionSyncCheck, version_sync.VersionSyncCheck)
        self.assertEqual(VersionSyncCheck().policy_id, "version-sync")
        self.assertTrue(callable(version_sync.write_synced_target_version))

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
        """Write a legal text file with a Project Version line."""
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
            self._write_pyproject(repo_root, "2.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
                violations = policy.check(context)

            mismatch = [v for v in violations if "does not match" in v.message]
            self.assertTrue(mismatch)
            manifest_mismatch = next(
                violation
                for violation in mismatch
                if violation.file_path is not None
                and violation.file_path.resolve()
                == (repo_root / "pyproject.toml").resolve()
            )
            self.assertTrue(manifest_mismatch.can_auto_fix)
            self.assertEqual(
                manifest_mismatch.context["extractor_name"],
                "manifest_project_version",
            )
            self.assertEqual(
                manifest_mismatch.context["tracked_version"],
                "1.0.0",
            )

    def test_detects_manifest_release_url_version_mismatch(self):
        """Tagged manifest URLs should stay synchronized with the version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.0.0\n")
            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            (repo_root / "pyproject.toml").write_text(
                "[project]\n"
                'version = "1.0.0"\n'
                "[project.urls]\n"
                'Documentation = "https://example.com/tree/v2.0.0/docs"\n'
                'Changelog = "https://example.com/blob/v2.0.0/CHANGELOG.md"\n',
                encoding="utf-8",
            )
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")
            self._write_changelog(repo_root, "1.0.0")

            policy = VersionSyncCheck()
            policy.set_options(
                {
                    "version_file": "project_lib/VERSION",
                    "changelog_file": "CHANGELOG.md",
                    "changelog_header_prefix": "## Version",
                    "target_roles": ["docs", "changelog", "package_manifest"],
                    "role_extractors": [
                        "docs=>project_version_line",
                        "changelog=>changelog_header_version",
                        "package_manifest=>manifest_project_version",
                    ],
                    "target_role_files": [
                        "docs=>README.md",
                        "docs=>docs/README.md",
                        "changelog=>CHANGELOG.md",
                        "package_manifest=>pyproject.toml",
                    ],
                },
                {},
            )
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
                violations = policy.check(CheckContext(repo_root=repo_root))

            messages = [violation.message for violation in violations]
            self.assertTrue(
                any(
                    "Documentation URL version 2.0.0 does not match" in msg
                    for msg in messages
                )
            )
            self.assertTrue(
                any(
                    "Changelog URL version 2.0.0 does not match" in msg
                    for msg in messages
                )
            )

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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])
            self.assertTrue(runtime_file.exists())

    def test_does_not_enforce_forward_bump_progression(self):
        """Forward bump progression is delegated to version-governance."""
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
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
                        "docs=>project_version_line",
                        "changelog=>changelog_header_version",
                        "package_manifest=>manifest_project_version",
                        "legal=>project_version_line",
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
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
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
                violations = policy.check(CheckContext(repo_root=repo_root))
            self.assertEqual(len(violations), 1)
            self.assertIn(
                "supports only TOML/JSON/YAML",
                violations[0].message,
            )

    def test_accepts_pep440_normalized_equivalence(self):
        """Scheme-aware equality should accept equivalent PEP 440 spellings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("1.2.0beta3\n")

            self._write_readme(repo_root, "README.md", "1.2.0beta3")
            self._write_readme(repo_root, "docs/README.md", "1.2.0b3")
            self._write_pyproject(repo_root, "1.2.0b3")
            self._write_pyproject(
                repo_root, "1.2.0beta3", "app/pyproject.toml"
            )
            self._write_license(repo_root, "LICENSE", "1.2.0beta3")
            self._write_license(repo_root, "app/license.txt", "1.2.0b3")
            self._write_changelog(repo_root, "1.2.0b3")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("pep440"),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_accepts_calver_normalized_equivalence(self):
        """CalVer comparison should accept equal numeric forms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("2026.03\n")

            self._write_readme(repo_root, "README.md", "2026.3")
            self._write_readme(repo_root, "docs/README.md", "2026.03")
            self._write_pyproject(repo_root, "2026.3")
            self._write_pyproject(repo_root, "2026.03", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "2026.03")
            self._write_license(repo_root, "app/license.txt", "2026.3")
            self._write_changelog(repo_root, "2026.3")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("calver"),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_accepts_custom_regex_scheme(self):
        """Custom regex schemes should sync non-SemVer repository versions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("XIV\n")

            self._write_readme(repo_root, "README.md", "XIV")
            self._write_readme(repo_root, "docs/README.md", "XIV")
            self._write_pyproject(repo_root, "XIV")
            self._write_pyproject(repo_root, "XIV", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "XIV")
            self._write_license(repo_root, "app/license.txt", "XIV")
            self._write_changelog(repo_root, "XIV")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme(
                    "custom_regex",
                    custom_regex_pattern=r"[IVX]+",
                ),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_accepts_custom_adapter_scheme(self):
        """Custom adapters should drive repo-defined sync equality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("V\n")

            self._write_readme(repo_root, "README.md", "V")
            self._write_readme(repo_root, "docs/README.md", "V")
            self._write_pyproject(repo_root, "V")
            self._write_pyproject(repo_root, "V", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "V")
            self._write_license(repo_root, "app/license.txt", "V")
            self._write_changelog(repo_root, "V")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("custom_adapter"),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_enforces_pep440_legality_for_python_manifests(self):
        """Package legality should fail invalid Python manifest versions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("XIV\n")

            self._write_readme(repo_root, "README.md", "XIV")
            self._write_readme(repo_root, "docs/README.md", "XIV")
            self._write_pyproject(repo_root, "XIV")
            self._write_pyproject(repo_root, "XIV", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "XIV")
            self._write_license(repo_root, "app/license.txt", "XIV")
            self._write_changelog(repo_root, "XIV")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy(
                role_legality_schemes=["package_manifest=>pep440"]
            )
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme(
                    "custom_regex",
                    custom_regex_pattern=r"[IVX]+",
                ),
            ):
                violations = policy.check(context)

            self.assertEqual(len(violations), 2)
            self.assertTrue(
                all(
                    "is not legal for required scheme `pep440`"
                    in violation.message
                    for violation in violations
                )
            )

    def test_keeps_repo_scheme_flexible_while_enforcing_package_legality(self):
        """CalVer repo equality can coexist with PEP 440 manifest legality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            version_dir = repo_root / "project_lib"
            version_dir.mkdir()
            (version_dir / "VERSION").write_text("2026.03\n")

            self._write_readme(repo_root, "README.md", "2026.3")
            self._write_readme(repo_root, "docs/README.md", "2026.03")
            self._write_pyproject(repo_root, "2026.3")
            self._write_pyproject(repo_root, "2026.03", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "2026.03")
            self._write_license(repo_root, "app/license.txt", "2026.3")
            self._write_changelog(repo_root, "2026.3")

            context = CheckContext(repo_root=repo_root)
            policy = self._policy(
                role_legality_schemes=["package_manifest=>pep440"]
            )
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("calver"),
            ):
                violations = policy.check(context)

            self.assertEqual(violations, [])

    def test_rejects_unknown_role_legality_scheme(self):
        """Legality mappings should fail explicitly for unknown schemes."""
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

            policy = self._policy(
                role_legality_schemes=["package_manifest=>does_not_exist"]
            )
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                return_value=self._resolved_scheme("semver"),
            ):
                violations = policy.check(CheckContext(repo_root=repo_root))

            self.assertEqual(len(violations), 1)
            self.assertIn(
                "role_legality_schemes` uses unsupported scheme",
                violations[0].message,
            )

    def test_reports_version_governance_resolution_failures(self):
        """Version-sync should fail explicitly when scheme resolution fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "project_lib").mkdir()
            (repo_root / "project_lib/VERSION").write_text("1.0.0\n")
            self._write_changelog(repo_root, "1.0.0")
            self._write_readme(repo_root, "README.md", "1.0.0")
            self._write_readme(repo_root, "docs/README.md", "1.0.0")
            self._write_pyproject(repo_root, "1.0.0")
            self._write_pyproject(repo_root, "1.0.0", "app/pyproject.toml")
            self._write_license(repo_root, "LICENSE", "1.0.0")
            self._write_license(repo_root, "app/license.txt", "1.0.0")

            policy = self._policy()
            with mock.patch.object(
                version_sync.version_governance,
                "resolve_runtime_scheme",
                side_effect=ValueError("no governed scheme configured"),
            ):
                violations = policy.check(CheckContext(repo_root=repo_root))

            self.assertEqual(len(violations), 1)
            self.assertIn(
                "Cannot resolve version-governance runtime",
                violations[0].message,
            )


if __name__ == "__main__":
    unittest.main()
