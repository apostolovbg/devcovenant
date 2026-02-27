"""Unit tests for readme-sync policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.readme_sync.readme_sync import ReadmeSyncCheck


def _unit_test_reports_missing_packaged_readme() -> None:
    """Policy should fail when devcovenant/README.md is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "README.md").write_text(
            "# Root\n\n<!-- REPO-ONLY:BEGIN -->x<!-- REPO-ONLY:END -->\n",
            encoding="utf-8",
        )

        check = ReadmeSyncCheck()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations
        assert "devcovenant/README.md is missing" in violations[0].message
        assert violations[0].can_auto_fix is True


def _unit_test_strips_repo_only_blocks_for_match() -> None:
    """Policy should ignore repo-only blocks when comparing docs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        root_readme = repo_root / "README.md"
        packaged_readme = repo_root / "devcovenant" / "README.md"
        packaged_readme.parent.mkdir(parents=True, exist_ok=True)

        root_readme.write_text(
            "# Root\n\n"
            "Line A\n\n"
            "<!-- REPO-ONLY:BEGIN -->\n"
            "Private\n"
            "<!-- REPO-ONLY:END -->\n\n"
            "Line B\n",
            encoding="utf-8",
        )
        packaged_readme.write_text(
            "# Root\n\nLine A\n\nLine B\n",
            encoding="utf-8",
        )

        check = ReadmeSyncCheck()
        violations = check.check(CheckContext(repo_root=repo_root))
        assert violations == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_reports_missing_packaged_readme(self):
        """Run test_reports_missing_packaged_readme."""
        _unit_test_reports_missing_packaged_readme()

    def test_strips_repo_only_blocks_for_match(self):
        """Run test_strips_repo_only_blocks_for_match."""
        _unit_test_strips_repo_only_blocks_for_match()
