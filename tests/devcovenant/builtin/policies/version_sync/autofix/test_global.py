"""Unit tests for version-sync global autofix."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.policy_contract import Violation

VersionSyncFixer = import_module(
    "devcovenant.builtin.policies.version_sync.autofix.global"
).VersionSyncFixer


def _violation(
    target: Path,
    *,
    extractor_name: str,
    tracked_version: str = "2.3.4",
) -> Violation:
    """Build one version-sync mismatch violation for autofix tests."""
    return Violation(
        policy_id="version-sync",
        severity="error",
        message="mismatch",
        file_path=target,
        context={
            "extractor_name": extractor_name,
            "tracked_version": tracked_version,
            "changelog_prefix": "## Version",
        },
    )


def _unit_test_can_fix_requires_context() -> None:
    """Fixer should require the declared extractor and tracked version."""
    fixer = VersionSyncFixer()
    assert (
        fixer.can_fix(
            _violation(
                Path("README.md"),
                extractor_name="project_version_line",
            )
        )
        is True
    )
    assert (
        fixer.can_fix(
            Violation(
                policy_id="version-sync",
                severity="error",
                message="missing context",
                file_path=Path("README.md"),
                context={},
            )
        )
        is False
    )


def _unit_test_fix_rewrites_project_version_line() -> None:
    """Fixer should rewrite Project Version headers to the tracked value."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "README.md"
        target.write_text(
            "# Demo\n**Project Version:** 0.1.0\n",
            encoding="utf-8",
        )
        fixer = VersionSyncFixer()
        result = fixer.fix(
            _violation(target, extractor_name="project_version_line")
        )
        assert result.success is True
        assert "**Project Version:** 2.3.4" in target.read_text(
            encoding="utf-8"
        )


def _unit_test_fix_rewrites_changelog_header() -> None:
    """Fixer should rewrite the latest changelog header version."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "CHANGELOG.md"
        target.write_text(
            "# Changelog\n\n## Log changes here\n\n## Version 0.1.0\n",
            encoding="utf-8",
        )
        fixer = VersionSyncFixer()
        result = fixer.fix(
            _violation(target, extractor_name="changelog_header_version")
        )
        assert result.success is True
        assert "## Version 2.3.4" in target.read_text(encoding="utf-8")


def _unit_test_fix_rewrites_toml_manifest_version() -> None:
    """Fixer should rewrite TOML package manifests to the tracked value."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "pyproject.toml"
        target.write_text(
            '[project]\nname = "demo"\nversion = "0.1.0"\n'
            "[project.urls]\n"
            'Documentation = "https://example.com/tree/v0.1.0/docs"\n'
            'Changelog = "https://example.com/blob/v0.1.0/CHANGELOG.md"\n',
            encoding="utf-8",
        )
        fixer = VersionSyncFixer()
        result = fixer.fix(
            _violation(target, extractor_name="manifest_project_version")
        )
        assert result.success is True
        content = target.read_text(encoding="utf-8")
        assert 'version = "2.3.4"' in content
        assert "/tree/v2.3.4/docs" in content
        assert "/blob/v2.3.4/CHANGELOG.md" in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_can_fix_requires_context(self):
        """Run test_can_fix_requires_context."""
        _unit_test_can_fix_requires_context()

    def test_fix_rewrites_project_version_line(self):
        """Run test_fix_rewrites_project_version_line."""
        _unit_test_fix_rewrites_project_version_line()

    def test_fix_rewrites_changelog_header(self):
        """Run test_fix_rewrites_changelog_header."""
        _unit_test_fix_rewrites_changelog_header()

    def test_fix_rewrites_toml_manifest_version(self):
        """Run test_fix_rewrites_toml_manifest_version."""
        _unit_test_fix_rewrites_toml_manifest_version()
