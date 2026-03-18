"""Tests for the PEP 440 adapter used by version-governance."""

import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.pep440 import Pep440Scheme


class _FakeCheck:
    """Minimal option surface for scheme tests."""

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


class TestPep440Scheme(unittest.TestCase):
    """Direct tests for the PEP 440 scheme adapter."""

    def test_parse_and_compare_pep440_versions(self):
        """PEP 440 adapter should parse and compare prerelease versions."""
        scheme = Pep440Scheme()
        check = _FakeCheck()
        self.assertEqual(
            scheme.preflight(check, Path("."), Path("VERSION")),
            [],
        )
        self.assertEqual(scheme.name, "pep440")
        self.assertEqual(
            scheme.version_pattern(check, Path(".")),
            r"[A-Za-z0-9!+._-]+",
        )
        current = scheme.parse_version("1.2.0rc1", check, Path("."))
        previous = scheme.parse_version("1.2.0b3", check, Path("."))
        self.assertEqual(str(previous), "1.2.0b3")
        self.assertEqual(str(current), "1.2.0rc1")
        self.assertEqual(scheme.compare_versions(previous, current), -1)
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: release candidate",
            current_version="1.2.0rc1",
            current_parsed=current,
            previous_version="1.2.0b3",
            previous_parsed=previous,
        )
        self.assertEqual(
            scheme.canonicalize_version(previous, check, Path(".")),
            "1.2.0b3",
        )
        self.assertEqual(scheme.validate_progression(check, release), [])
        self.assertEqual(scheme.validate_release(check, release), [])

    def test_beta_alias_and_invalid_versions(self):
        """PEP 440 should normalize beta aliases and reject invalid tokens."""
        scheme = Pep440Scheme()
        check = _FakeCheck()
        beta = scheme.parse_version("1.2.0beta3", check, Path("."))
        self.assertEqual(str(beta), "1.2.0b3")
        with self.assertRaisesRegex(ValueError, "valid pep440 version"):
            scheme.parse_version("omicron5", check, Path("."))

    def test_prerelease_marker_can_be_disabled(self):
        """PEP 440 should report disabled prerelease markers explicitly."""
        scheme = Pep440Scheme()
        check = _FakeCheck({"pep440_allow_prereleases": False})
        current = scheme.parse_version("1.2.0rc1", check, Path("."))
        previous = scheme.parse_version("1.2.0b3", check, Path("."))
        release = version_governance.VersionReleaseContext(
            repo_root=Path("."),
            policy_id="version-governance",
            version_label="VERSION",
            version_path=Path("VERSION"),
            changelog_path=Path("CHANGELOG.md"),
            changed_files=[Path("VERSION"), Path("CHANGELOG.md")],
            latest_block="- 2026-03-16: release candidate",
            current_version="1.2.0rc1",
            current_parsed=current,
            previous_version="1.2.0b3",
            previous_parsed=previous,
        )
        violations = scheme.validate_progression(check, release)
        self.assertEqual(len(violations), 1)
        self.assertIn("prerelease", violations[0].message.lower())
