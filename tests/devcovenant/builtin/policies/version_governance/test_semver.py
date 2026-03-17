"""Tests for the SemVer adapter used by version-governance."""

import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.semver import SemverScheme


class _FakeCheck:
    """Minimal option surface for scheme tests."""

    policy_id = "version-governance"

    def __init__(self, options=None):
        """Store minimal option state for direct scheme tests."""
        self._options = options or {}

    def get_option(self, key, default=None):
        """Return one configured option value."""
        return self._options.get(key, default)

    def _bool_option(self, key):
        """Return one configured option as a boolean."""
        raw = self._options.get(key, False)
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}


class TestSemverScheme(unittest.TestCase):
    """Direct tests for the SemVer scheme adapter."""

    def test_preflight_reports_missing_semver_dependency(self):
        """Preflight should fail clearly when semver is unavailable."""
        scheme = SemverScheme()
        check = _FakeCheck()
        with patch(
            (
                "devcovenant.builtin.policies.version_governance."
                "semver.VersionInfo"
            ),
            None,
        ):
            violations = scheme.preflight(
                check,
                Path("."),
                Path("VERSION"),
            )
        self.assertEqual(len(violations), 1)
        self.assertIn("install `semver`", violations[0].message)

    def test_parse_and_compare_semver_versions(self):
        """SemVer adapter should parse and compare ordered versions."""
        scheme = SemverScheme()
        check = _FakeCheck()
        self.assertEqual(scheme.name, "semver")
        self.assertEqual(
            scheme.version_pattern(check, Path(".")),
            r"\d+\.\d+\.\d+",
        )
        current = scheme.parse_version("1.2.4", check, Path("."))
        previous = scheme.parse_version("1.2.3", check, Path("."))
        comparison = scheme.compare_versions(previous, current)
        self.assertEqual(comparison, -1)
        self.assertEqual(scheme.compare_versions(current, previous), 1)
        self.assertEqual(scheme.compare_versions(current, current), 0)

    def test_validate_release_skips_extra_rules_when_tags_disabled(self):
        """SemVer adapter should skip extra rules when tags are off."""
        scheme = SemverScheme()
        check = _FakeCheck({"semver_scope_tags_required": False})
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: release",
            current_version="1.2.4",
            current_parsed=scheme.parse_version(
                "1.2.4",
                check,
                Path("."),
            ),
            previous_version="1.2.3",
            previous_parsed=scheme.parse_version(
                "1.2.3",
                check,
                Path("."),
            ),
        )
        self.assertEqual(
            scheme.preflight(check, Path("."), Path("VERSION")),
            [],
        )
        self.assertEqual(scheme.validate_release(check, release), [])
