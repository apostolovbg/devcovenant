"""Unit tests for readme-sync policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.readme_sync.readme_sync import ReadmeSyncCheck


def _write_pyproject(
    repo_root: Path,
    repository_url: str | None = None,
) -> None:
    """Write minimal package metadata for README sync tests."""
    payload = "[project]\n" 'name = "Demo"\n' 'version = "0.0.0"\n'
    if repository_url is not None:
        payload += "[project.urls]\n" f'Repository = "{repository_url}"\n'
    (repo_root / "pyproject.toml").write_text(
        payload,
        encoding="utf-8",
    )


def _unit_test_reports_missing_packaged_readme() -> None:
    """Policy should fail when devcovenant/README.md is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        _write_pyproject(
            repo_root,
            "https://example.com/team/devcovenant-fork",
        )
        (repo_root / "README.md").write_text(
            "# Root\n\n"
            "[Docs](devcovenant/docs/workflow.md)\n\n"
            "<!-- REPO-ONLY:BEGIN -->x<!-- REPO-ONLY:END -->\n",
            encoding="utf-8",
        )

        check = ReadmeSyncCheck()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations
        assert "devcovenant/README.md is missing" in violations[0].message
        assert violations[0].can_auto_fix is True
        assert (
            "[Docs]("
            "https://example.com/team/devcovenant-fork/blob/v0.0.0/"
            "devcovenant/docs/workflow.md)"
        ) in str(violations[0].context.get("expected_text"))


def _unit_test_strips_repo_only_blocks_for_match() -> None:
    """Policy should ignore repo-only blocks and rewrite package links."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        root_readme = repo_root / "README.md"
        packaged_readme = repo_root / "devcovenant" / "README.md"
        packaged_readme.parent.mkdir(parents=True, exist_ok=True)
        _write_pyproject(
            repo_root,
            "https://example.com/team/devcovenant-fork",
        )

        root_readme.write_text(
            "# Root\n\n"
            "Line A\n\n"
            "[Docs](devcovenant/docs/workflow.md)\n\n"
            "<!-- REPO-ONLY:BEGIN -->\n"
            "Private\n"
            "<!-- REPO-ONLY:END -->\n\n"
            "Line B\n",
            encoding="utf-8",
        )
        packaged_readme.write_text(
            "# Root\n\n"
            "Line A\n\n"
            "[Docs]("
            "https://example.com/team/devcovenant-fork/blob/v0.0.0/"
            "devcovenant/docs/workflow.md)\n\n"
            "Line B\n",
            encoding="utf-8",
        )

        check = ReadmeSyncCheck()
        violations = check.check(CheckContext(repo_root=repo_root))
        assert violations == []


def _unit_test_reports_missing_repository_url_for_public_links() -> None:
    """Policy should fail clearly when package link base cannot be resolved."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        packaged_readme = repo_root / "devcovenant" / "README.md"
        packaged_readme.parent.mkdir(parents=True, exist_ok=True)
        _write_pyproject(repo_root)

        (repo_root / "README.md").write_text(
            "# Root\n\n"
            "[Docs](devcovenant/docs/workflow.md)\n\n"
            "<!-- REPO-ONLY:BEGIN -->x<!-- REPO-ONLY:END -->\n",
            encoding="utf-8",
        )
        packaged_readme.write_text("# Root\n", encoding="utf-8")

        check = ReadmeSyncCheck()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations
        assert "project.urls.Repository" in violations[0].message


def _unit_test_rewrites_repo_relative_images_to_release_stable_urls() -> None:
    """Policy should rewrite repo-relative images for packaged README use."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        packaged_readme = repo_root / "devcovenant" / "README.md"
        packaged_readme.parent.mkdir(parents=True, exist_ok=True)
        _write_pyproject(
            repo_root,
            "https://github.com/example/devcovenant-fork",
        )

        (repo_root / "README.md").write_text(
            "# Root\n\n"
            "![Banner](devcovenant/docs/banner.png)\n\n"
            "<!-- REPO-ONLY:BEGIN -->x<!-- REPO-ONLY:END -->\n",
            encoding="utf-8",
        )
        packaged_readme.write_text(
            "# Root\n\n"
            "![Banner]("
            "https://raw.githubusercontent.com/example/devcovenant-fork/"
            "v0.0.0/devcovenant/docs/banner.png)\n",
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

    def test_reports_missing_repository_url_for_public_links(self):
        """Run test_reports_missing_repository_url_for_public_links."""
        _unit_test_reports_missing_repository_url_for_public_links()

    def test_rewrites_repo_relative_images_to_release_stable_urls(self):
        """Run repo-relative packaged image rewrite assertions."""
        _unit_test_rewrites_repo_relative_images_to_release_stable_urls()
