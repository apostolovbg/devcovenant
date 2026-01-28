"""Tests for the readme-sync policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.custom.policies.readme_sync.readme_sync import (
    ReadmeSyncCheck,
)


def _write_readmes(repo_root: Path, repo_text: str, target_text: str) -> None:
    """Write README.md and devcovenant/README.md content."""
    (repo_root / "README.md").write_text(repo_text, encoding="utf-8")
    target = repo_root / "devcovenant"
    target.mkdir(parents=True, exist_ok=True)
    (target / "README.md").write_text(target_text, encoding="utf-8")


def test_readme_sync_passes_when_synced(tmp_path: Path) -> None:
    """Pass when repo README matches devcovenant README minus repo-only blocks."""
    policy = ReadmeSyncCheck()
    repo_text = "\n".join(
        [
            "# Title",
            "",
            "<!-- REPO-ONLY:BEGIN -->",
            "repo-only",
            "<!-- REPO-ONLY:END -->",
            "",
            "shared content",
            "",
        ]
    )
    target_text = "# Title\n\nshared content\n"
    _write_readmes(tmp_path, repo_text, target_text)
    context = CheckContext(repo_root=tmp_path)
    violations = policy.check(context)
    assert not violations


def test_readme_sync_flags_missing_markers(tmp_path: Path) -> None:
    """Fail when repo-only markers are missing."""
    policy = ReadmeSyncCheck()
    _write_readmes(tmp_path, "# Title\nshared\n", "# Title\nshared\n")
    context = CheckContext(repo_root=tmp_path)
    violations = policy.check(context)
    assert violations
    assert "repo-only block markers" in violations[0].message


def test_readme_sync_offers_fix_on_mismatch(tmp_path: Path) -> None:
    """Mismatch should be auto-fixable."""
    policy = ReadmeSyncCheck()
    repo_text = "\n".join(
        [
            "# Title",
            "",
            "<!-- REPO-ONLY:BEGIN -->",
            "repo-only",
            "<!-- REPO-ONLY:END -->",
            "",
            "shared content",
            "",
        ]
    )
    _write_readmes(tmp_path, repo_text, "# Title\n\nmismatch\n")
    context = CheckContext(repo_root=tmp_path)
    violations = policy.check(context)
    assert len(violations) == 1
    assert violations[0].can_auto_fix is True
