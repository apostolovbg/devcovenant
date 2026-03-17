"""Tests for the CalVer adapter used by version-governance."""

import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.calver import CalverScheme


class _FakeCheck:
    """Minimal option surface for scheme tests."""

    def __init__(self, options=None):
        """Store minimal option state for direct scheme tests."""
        self._options = options or {}

    def get_option(self, key, default=None):
        """Return one configured option value."""
        return self._options.get(key, default)


class TestCalverScheme(unittest.TestCase):
    """Direct tests for the CalVer scheme adapter."""

    def test_parse_and_compare_calver_versions(self):
        """CalVer adapter should parse and compare numeric date versions."""
        scheme = CalverScheme()
        check = _FakeCheck()
        self.assertEqual(
            scheme.preflight(check, Path("."), Path("VERSION")),
            [],
        )
        self.assertEqual(
            scheme.version_pattern(check, Path(".")),
            r"\d{4}\.\d{1,2}(?:\.\d{1,2})?",
        )
        current = scheme.parse_version("2026.03.16", check, Path("."))
        previous = scheme.parse_version("2026.03.15", check, Path("."))
        self.assertEqual(current, (2026, 3, 16))
        self.assertEqual(scheme.compare_versions(previous, current), -1)
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: release",
            current_version="2026.03.16",
            current_parsed=current,
            previous_version="2026.03.15",
            previous_parsed=previous,
        )
        self.assertEqual(scheme.validate_release(check, release), [])

    def test_custom_pattern_is_used_for_validation(self):
        """CalVer adapter should honor a custom configured regex."""
        scheme = CalverScheme()
        check = _FakeCheck({"calver_pattern": r"\d{4}\.\d{2}"})
        self.assertEqual(
            scheme.parse_version("2026.03", check, Path(".")),
            (2026, 3),
        )
        with self.assertRaisesRegex(ValueError, "valid calver version"):
            scheme.parse_version("2026.3.16", check, Path("."))
