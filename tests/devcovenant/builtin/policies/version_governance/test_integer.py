"""Tests for the integer adapter used by version-governance."""

import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.integer import (
    IntegerScheme,
)


class _FakeCheck:
    """Minimal option surface for scheme tests."""

    def get_option(self, key, default=None):
        """Return the provided default because integer needs no options."""
        return default


class TestIntegerScheme(unittest.TestCase):
    """Direct tests for the integer scheme adapter."""

    def test_parse_and_compare_integer_versions(self):
        """Integer adapter should parse and compare forward numeric bumps."""
        scheme = IntegerScheme()
        check = _FakeCheck()
        self.assertEqual(
            scheme.preflight(check, Path("."), Path("VERSION")),
            [],
        )
        self.assertEqual(scheme.version_pattern(check, Path(".")), r"\d+")
        current = scheme.parse_version("43", check, Path("."))
        previous = scheme.parse_version("42", check, Path("."))
        self.assertEqual(current, 43)
        self.assertEqual(scheme.compare_versions(previous, current), -1)
        self.assertEqual(scheme.compare_versions(current, previous), 1)
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: release",
            current_version="43",
            current_parsed=current,
            previous_version="42",
            previous_parsed=previous,
        )
        self.assertEqual(
            scheme.canonicalize_version(current, check, Path(".")),
            "43",
        )
        self.assertEqual(scheme.validate_progression(check, release), [])
        self.assertEqual(scheme.validate_release(check, release), [])

    def test_invalid_integer_version_is_rejected(self):
        """Integer adapter should reject non-numeric version strings."""
        scheme = IntegerScheme()
        check = _FakeCheck()
        with self.assertRaisesRegex(ValueError, "valid integer version"):
            scheme.parse_version("42b", check, Path("."))
