"""Tests for the custom_adapter loader used by version-governance."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.builtin.policies.version_governance.custom_adapter import (
    CustomAdapterScheme,
)


class _FakeCheck:
    """Minimal option surface for custom_adapter scheme tests."""

    policy_id = "version-governance"

    def __init__(self, options=None):
        """Store minimal option state for direct scheme tests."""
        self._options = options or {}

    def get_option(self, key, default=None):
        """Return one configured option value."""
        return self._options.get(key, default)


def _write_custom_adapter(tmp_path: Path) -> Path:
    """Create one repo-local Roman numeral adapter module."""
    adapter_path = tmp_path / "roman_scheme.py"
    adapter_path.write_text(
        "\n".join(
            [
                '"""Roman numeral adapter fixture for tests."""',
                "",
                "_ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}",
                "",
                "",
                "def _to_int(token: str) -> int:",
                "    total = 0",
                "    previous = 0",
                "    for char in reversed(token):",
                "        value = _ROMAN[char]",
                "        if value < previous:",
                "            total -= value",
                "        else:",
                "            total += value",
                "            previous = value",
                "    return total",
                "",
                "",
                "class RomanScheme:",
                "    def version_pattern(self, check, repo_root):",
                '        return r"[IVXLC]+"',
                "",
                "    def parse_version(self, value, check, repo_root):",
                "        return _to_int(str(value or '').strip())",
                "",
                "    def compare_versions(self, left, right):",
                "        if left < right:",
                "            return -1",
                "        if left > right:",
                "            return 1",
                "        return 0",
                "",
                "    def validate_release(self, check, release):",
                "        return []",
                "",
                "",
                "SCHEME = RomanScheme()",
            ]
        ),
        encoding="utf-8",
    )
    return adapter_path


class TestCustomAdapterScheme(unittest.TestCase):
    """Direct tests for the custom_adapter scheme adapter."""

    def test_loads_repo_local_roman_adapter(self):
        """custom_adapter should load one repo-local scheme module."""
        scheme = CustomAdapterScheme()
        self.assertEqual(
            CustomAdapterScheme.__name__,
            "CustomAdapterScheme",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            adapter_path = _write_custom_adapter(repo_root)
            check = _FakeCheck({"custom_adapter_path": adapter_path.name})
            self.assertEqual(
                scheme.preflight(check, repo_root, repo_root / "VERSION"),
                [],
            )
            self.assertEqual(
                scheme.version_pattern(check, repo_root),
                r"[IVXLC]+",
            )
            current = scheme.parse_version("IV", check, repo_root)
            previous = scheme.parse_version("III", check, repo_root)
            self.assertEqual(current, 4)
            self.assertEqual(previous, 3)
            self.assertEqual(scheme.compare_versions(previous, current), -1)
            release = version_governance.VersionReleaseContext(
                repo_root=repo_root,
                policy_id="version-governance",
                version_label="VERSION",
                version_path=repo_root / "VERSION",
                changelog_path=repo_root / "CHANGELOG.md",
                changed_files=[
                    repo_root / "VERSION",
                    repo_root / "CHANGELOG.md",
                ],
                latest_block="- 2026-03-16: roman release",
                current_version="IV",
                current_parsed=current,
                previous_version="III",
                previous_parsed=previous,
            )
            self.assertEqual(scheme.validate_release(check, release), [])

    def test_requires_scheme_export(self):
        """custom_adapter should fail when the module lacks `SCHEME`."""
        scheme = CustomAdapterScheme()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            bad_module = repo_root / "broken_scheme.py"
            bad_module.write_text("VALUE = 1\n", encoding="utf-8")
            check = _FakeCheck({"custom_adapter_path": bad_module.name})
            violations = scheme.preflight(
                check,
                repo_root,
                repo_root / "VERSION",
            )
            self.assertEqual(len(violations), 1)
            self.assertIn("export `SCHEME`", violations[0].message)
