"""Unit tests for package-doc-sync policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.package_doc_sync.package_doc_sync import (
    PackageDocSyncCheck,
)
from devcovenant.core.policy_contract import CheckContext


def _build_check() -> PackageDocSyncCheck:
    """Return one checker configured for repo README package sync."""
    check = PackageDocSyncCheck()
    check.set_options(
        {
            "sync_pairs": ["README.md=>devcovenant/README.md"],
            "omit_block_pairs": [
                "<!-- REPO-ONLY:BEGIN -->=><!-- REPO-ONLY:END -->"
            ],
            "rewrite_repo_relative_links": True,
        },
        {},
    )
    return check


def _write_pyproject(
    repo_root: Path,
    repository_url: str | None = None,
) -> None:
    """Write minimal package metadata for package-doc sync tests."""
    payload = "[project]\n" 'name = "Demo"\n' 'version = "0.0.0"\n'
    if repository_url is not None:
        payload += "[project.urls]\n" f'Repository = "{repository_url}"\n'
    (repo_root / "pyproject.toml").write_text(
        payload,
        encoding="utf-8",
    )


def _unit_test_reports_missing_packaged_doc() -> None:
    """Policy should fail when the configured target doc is missing."""
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

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations
        assert "`devcovenant/README.md` is missing" in violations[0].message
        assert violations[0].can_auto_fix is True
        assert (
            "[Docs]("
            "https://example.com/team/devcovenant-fork/blob/v0.0.0/"
            "devcovenant/docs/workflow.md)"
        ) in str(violations[0].context.get("expected_text"))


def _unit_test_strips_repo_only_blocks_for_match() -> None:
    """Policy should ignore configured omit blocks and rewrite links."""
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

        check = _build_check()
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

        check = _build_check()
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

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations == []


def _unit_test_supports_multiple_sync_pairs() -> None:
    """Policy should handle more than one configured sync pair."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        docs_dir = repo_root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        package_docs_dir = repo_root / "devcovenant" / "docs"
        package_docs_dir.mkdir(parents=True, exist_ok=True)
        _write_pyproject(
            repo_root,
            "https://example.com/team/devcovenant-fork",
        )
        (repo_root / "README.md").write_text(
            "# Root\n\n" "<!-- REPO-ONLY:BEGIN -->x<!-- REPO-ONLY:END -->\n",
            encoding="utf-8",
        )
        (repo_root / "devcovenant" / "README.md").write_text(
            "# Root\n",
            encoding="utf-8",
        )
        (docs_dir / "guide.md").write_text("Guide\n", encoding="utf-8")

        check = PackageDocSyncCheck()
        check.set_options(
            {
                "sync_pairs": [
                    "README.md=>devcovenant/README.md",
                    "docs/guide.md=>devcovenant/docs/guide.md",
                ],
                "omit_block_pairs": [
                    "<!-- REPO-ONLY:BEGIN -->=><!-- REPO-ONLY:END -->"
                ],
                "rewrite_repo_relative_links": True,
            },
            {},
        )
        violations = check.check(CheckContext(repo_root=repo_root))

        assert len(violations) == 1
        assert (
            "`devcovenant/docs/guide.md` is missing" in violations[0].message
        )


def _unit_test_symbol_contract_is_stable() -> None:
    """Checker symbol contract should stay explicit and importable."""
    assert PackageDocSyncCheck.__name__ == "PackageDocSyncCheck"
    assert hasattr(PackageDocSyncCheck, "check")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_reports_missing_packaged_doc(self):
        """Run test_reports_missing_packaged_doc."""
        _unit_test_reports_missing_packaged_doc()

    def test_strips_repo_only_blocks_for_match(self):
        """Run test_strips_repo_only_blocks_for_match."""
        _unit_test_strips_repo_only_blocks_for_match()

    def test_reports_missing_repository_url_for_public_links(self):
        """Run test_reports_missing_repository_url_for_public_links."""
        _unit_test_reports_missing_repository_url_for_public_links()

    def test_rewrites_repo_relative_images_to_release_stable_urls(self):
        """Run repo-relative packaged image rewrite assertions."""
        _unit_test_rewrites_repo_relative_images_to_release_stable_urls()

    def test_supports_multiple_sync_pairs(self):
        """Run multiple sync-pair assertions."""
        _unit_test_supports_multiple_sync_pairs()

    def test_symbol_contract_is_stable(self):
        """Run symbol-contract assertions."""
        _unit_test_symbol_contract_is_stable()
