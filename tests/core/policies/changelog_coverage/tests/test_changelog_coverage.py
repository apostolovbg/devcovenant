"""
Tests for changelog-coverage policy.
"""

import importlib
from datetime import date
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.policies.changelog_coverage.changelog_coverage import (
    ChangelogCoverageCheck,
)


def _summary_block() -> str:
    """Return a valid Change/Why/Impact summary block."""
    return (
        "  Change: Updated docs to cover new behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
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
        f"- {today}:\n"
        f"{_summary_block()}"
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
        f"## Version 1.0.0\n- {today}:\n{_summary_block()}",
        encoding="utf-8",
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


def test_changelog_requires_summary_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Latest entry must include labeled summary lines."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
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
    assert any("summary lines" in v.message for v in violations)


def test_summary_requires_action_verbs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Summary lines must include an action verb from the list."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: New behavior here\n"
        "  Why: Explanation present\n"
        "  Impact: Some effect\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = ChangelogCoverageCheck()
    checker.set_options({"summary_verbs": ["updated"]}, {})
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("action verb" in v.message for v in violations)


def test_files_block_auto_fix(tmp_path: Path):
    """Auto-fixer should populate the Files block for the latest entry."""

    today = date.today().isoformat()
    changelog_text = "## Version 1.0.0\n" f"- {today}:\n" f"{_summary_block()}"
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text(changelog_text, encoding="utf-8")

    violation = Violation(
        policy_id="changelog-coverage",
        severity="error",
        message="Missing Files block",
        file_path=changelog_path,
        can_auto_fix=True,
        context={"expected_files": ["src/module.py"]},
    )
    module = importlib.import_module(
        "devcovenant.core.policies.changelog_coverage.fixers.global"
    )
    fixer = module.ChangelogCoverageFixer()
    fixer.repo_root = tmp_path

    result = fixer.fix(violation)

    assert result.success
    updated = changelog_path.read_text(encoding="utf-8")
    assert "Files:" in updated
    assert "src/module.py" in updated


def test_files_block_auto_fix_wraps_summary_lines(tmp_path: Path):
    """Auto-fixer wraps long summary lines with backslash continuations."""

    today = date.today().isoformat()
    long_change = (
        "Change: Updated documentation with extensive guidance for "
        "coverage enforcement and changelog formatting across teams"
    )
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"  {long_change}\n"
        "  Why: Clarified contributor expectations\n"
        "  Impact: Users see updated guidance in docs\n"
    )
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text(changelog_text, encoding="utf-8")

    violation = Violation(
        policy_id="changelog-coverage",
        severity="error",
        message="Missing Files block",
        file_path=changelog_path,
        can_auto_fix=True,
        context={"expected_files": ["src/module.py"]},
    )
    module = importlib.import_module(
        "devcovenant.core.policies.changelog_coverage.fixers.global"
    )
    fixer = module.ChangelogCoverageFixer()
    fixer.repo_root = tmp_path

    result = fixer.fix(violation)

    assert result.success
    updated = changelog_path.read_text(encoding="utf-8")
    assert "Change: Updated documentation" in updated
    assert "\\\n" in updated


def test_rng_changelog_entry_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """RNG files pass when mentioned in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rng_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"{_summary_block()}"
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
    rng_entry = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"{_summary_block()}"
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
            - 2026-01-07:
              Change: Updated rng event behavior
              Why: Clarified event logging for QA
              Impact: Reviewers see updated rng logs
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
            - 2026-01-05:
              Change: Updated src/module.py behavior
              Why: Clarified coverage expectations
              Impact: Users see updated module behavior
            - 2026-01-07:
              Change: Updated src/module.py behavior
              Why: Clarified coverage expectations
              Impact: Users see updated module behavior
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
    changelog = "\n".join(
        [
            "## Version 1.0.0",
            f"- {date.today().isoformat()}:",
            "  Change: Updated docs with extra guidance for coverage tests",
            "  Why: Clarified expectations for contributors",
            "  Impact: Users see updated coverage notes now",
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
