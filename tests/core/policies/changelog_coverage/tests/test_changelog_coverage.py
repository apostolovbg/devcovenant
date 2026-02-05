"""
Tests for changelog-coverage policy.
"""

from datetime import date
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.changelog_coverage.changelog_coverage import (
    ChangelogCoverageCheck,
)


def _set_git_diff(monkeypatch: pytest.MonkeyPatch, output: str) -> None:
    """Monkeypatch subprocess.run to return the provided diff output."""

    def _fake_run(*_args, **_kwargs):
        """Return a fake subprocess result with the requested output."""
        return SimpleNamespace(stdout=output)

    monkeypatch.setattr("subprocess.run", _fake_run)


def test_no_changes_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Empty diffs should yield no violations."""

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    assert checker.check(context) == []


def test_skipped_prefixes_ignore_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Configured skipped prefixes should bypass coverage checks."""

    checker = ChangelogCoverageCheck()
    checker.set_options({"skipped_prefixes": ["devcovenant/core"]}, {})
    _set_git_diff(monkeypatch, "devcovenant/core/check.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_skipped_globs_ignore_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Configured skipped globs should bypass coverage checks."""

    checker = ChangelogCoverageCheck()
    checker.set_options({"skipped_globs": ["*_old.*"]}, {})
    _set_git_diff(monkeypatch, "devcovenant/config_old.yaml\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_root_changelog_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Non-RNG files must be listed in the root changelog."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}: docs/readme.md\n"
        "  Files:\n"
        "  docs/readme.md\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    messages = " ".join(v.message for v in violations)
    assert "src/module.py" in messages
    assert "docs/readme.md" in messages


def test_rng_changelog_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RNG files must be documented in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "rng_minigames/CHANGELOG.md" in violations[0].message


def test_collections_disabled_route_to_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """When collections are disabled, prefixed paths go to root."""

    today = date.today().isoformat()
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n- {today}: initial\n", encoding="utf-8"
    )

    checker = ChangelogCoverageCheck()
    checker.set_options({"collections": "none"}, {})
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    messages = " ".join(v.message for v in violations)
    assert "CHANGELOG.md" in messages
    assert "Files" in messages


def test_changelog_requires_descriptive_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Latest entry must include a real summary sentence."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}: Fix bug\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("descriptive summary" in v.message for v in violations)


def test_summary_word_minimum_can_be_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Configurable summary word minimum should be honored."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}: Fix bug\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    checker.set_options({"summary_words_min": 2}, {})
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_rng_changelog_entry_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RNG files pass when mentioned in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    summary = "rng update logged for coverage policy with extra detail today"
    rng_text = (
        "## Version 1.0.0\n"
        f"- {today}: {summary}\n"
        "  Files:\n"
        "  rng_minigames/emoji_meteors/game.py\n"
    )
    rng_changelog.write_text(
        rng_text,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_rng_files_not_logged_in_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RNG files should not appear in the root changelog."""

    root_changelog = tmp_path / "CHANGELOG.md"
    today = date.today().isoformat()
    summary = "rng update logged for coverage policy with extra detail today"
    rng_entry = (
        "## Version 1.0.0\n"
        f"- {today}: {summary}\n"
        "  Files:\n"
        "  rng_minigames/emoji_meteors/game.py\n"
    )
    root_changelog.write_text(
        rng_entry,
        encoding="utf-8",
    )
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    rng_changelog.write_text(
        rng_entry,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "root changelog" in violations[0].message


def test_rng_entries_ignore_old_root_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Old root entries mentioning RNG files should not trigger violations."""

    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## Version 2.0.0
            - entry about docs/readme.md

            ## Version 1.0.0
            - rng_minigames/emoji_meteors/game.py
            """
        ).strip(),
        encoding="utf-8",
    )
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    rng_changelog.write_text(
        "## Version 2.0.0\n- rng_minigames/emoji_meteors/game.py",
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_template_code_block_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Template code blocks should not count as latest entries."""

    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## How to Log Changes
            ```
            ## Version 0.1.0
            - 2026-01-07: Template entry (Contributor)
              Files:
              docs/readme.md
            ```

            ## Log changes here

            ## Version 0.2.0
            - 2026-01-08: Update src/module.py (AI assistant)
            """
        ).strip(),
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def test_changelog_entries_newest_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Latest changelog section should list newest entries first."""
    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## Version 1.0.0
            - 2026-01-05: update src/module.py
            - 2026-01-07: update src/module.py
            """
        ).strip(),
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any("newest-first" in v.message for v in violations)


def test_line_continuation_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Backslash-wrapped paths should satisfy changelog coverage."""

    root_changelog = tmp_path / "CHANGELOG.md"
    summary = (
        "Update docs with extra guidance for coverage tests today entries"
    )
    changelog = "\n".join(
        [
            "## Version 1.0.0",
            f"- {date.today().isoformat()}: {summary}",
            "  Files:",
            "  devcovenant/core/policies/dependency_license_sync/assets/\\",
            "    licenses/README.md",
        ]
    )
    root_changelog.write_text(changelog, encoding="utf-8")
    diff_path = (
        "devcovenant/core/policies/"
        "dependency_license_sync/assets/licenses/README.md\n"
    )
    _set_git_diff(monkeypatch, diff_path)

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []
