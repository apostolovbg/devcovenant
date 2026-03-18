"""Tests for the custom_regex adapter used by version-governance."""

import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.custom_regex import (
    CustomRegexScheme,
)


class _FakeCheck:
    """Minimal option surface for custom_regex scheme tests."""

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


class TestCustomRegexScheme(unittest.TestCase):
    """Direct tests for the custom_regex scheme adapter."""

    def test_parse_and_validate_roman_pattern(self):
        """custom_regex should validate Roman-numeral style strings."""
        scheme = CustomRegexScheme()
        check = _FakeCheck(
            {
                "custom_regex_pattern": r"[IVXLC]+",
                "enforce_bumping": False,
            }
        )
        self.assertEqual(
            CustomRegexScheme.__name__,
            "CustomRegexScheme",
        )
        self.assertEqual(
            scheme.preflight(check, Path("."), Path("VERSION")),
            [],
        )
        self.assertEqual(
            scheme.version_pattern(check, Path(".")),
            r"[IVXLC]+",
        )
        self.assertEqual(scheme.parse_version("IV", check, Path(".")), "IV")
        self.assertEqual(scheme.compare_versions("III", "IV"), -1)
        self.assertIsNone(scheme.canonicalize_version("IV", check, Path(".")))
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: roman release",
            current_version="IV",
            current_parsed="IV",
            previous_version="III",
            previous_parsed="III",
        )
        self.assertEqual(scheme.validate_progression(check, release), [])
        self.assertEqual(scheme.validate_release(check, release), [])
        with self.assertRaisesRegex(ValueError, "custom_regex_pattern"):
            scheme.parse_version("beta3", check, Path("."))

    def test_bump_enforcement_is_rejected(self):
        """custom_regex should fail clearly when ordering is requested."""
        scheme = CustomRegexScheme()
        check = _FakeCheck(
            {
                "custom_regex_pattern": r"[IVXLC]+",
                "enforce_bumping": True,
            }
        )
        violations = scheme.preflight(check, Path("."), Path("VERSION"))
        self.assertEqual(len(violations), 1)
        self.assertIn("custom_adapter", violations[0].message)
