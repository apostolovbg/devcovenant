"""
Tests for changelog-coverage policy.
"""

import importlib
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

from devcovenant.core.base import CheckContext, Violation
from devcovenant.core.policies.changelog_coverage.changelog_coverage import (
    ChangelogCoverageCheck,
)
from tests.devcovenant.support import MonkeyPatch


def _summary_block() -> str:
    """Return a valid Change/Why/Impact summary block."""
    return (
        "  Change: Updated docs to cover new behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
    )


def _set_git_diff(monkeypatch: MonkeyPatch, output: str) -> None:
    """Monkeypatch subprocess.run to return the provided diff output."""

    def _fake_run(*_args, **_kwargs):
        """Return a fake subprocess result with the requested output."""
        return SimpleNamespace(stdout=output)

    monkeypatch.setattr("subprocess.run", _fake_run)


def _set_git_diff_with_patches(
    monkeypatch: MonkeyPatch,
    *,
    changed_files: str,
    patches: dict[str, str],
    head_files: dict[str, str] | None = None,
) -> None:
    """Monkeypatch subprocess.run for name-only, patch, and HEAD lookups."""

    head_files = head_files or {}

    def _fake_run(cmd, *_args, **_kwargs):
        """Return a fake subprocess result keyed by the git subcommand."""

        if cmd[:3] == ["git", "diff", "--name-only"]:
            return SimpleNamespace(stdout=changed_files)
        if cmd[:3] == ["git", "diff", "--unified=0"]:
            rel_path = cmd[-1]
            return SimpleNamespace(stdout=patches.get(rel_path, ""))
        if cmd[:2] == ["git", "show"] and cmd[2].startswith("HEAD:"):
            rel_path = cmd[2].split("HEAD:", 1)[1]
            if rel_path in head_files:
                return SimpleNamespace(stdout=head_files[rel_path])
            raise subprocess.CalledProcessError(1, cmd)
        return SimpleNamespace(stdout="")

    monkeypatch.setattr("subprocess.run", _fake_run)


def _unit_test_no_changes_passes(tmp_path: Path, monkeypatch: MonkeyPatch):
    """Empty diffs should yield no violations."""

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    assert checker.check(context) == []


def _unit_test_skipped_prefixes_ignore_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured skipped prefixes should bypass coverage checks."""

    checker = ChangelogCoverageCheck()
    checker.set_options({"skipped_prefixes": ["devcovenant/core"]}, {})
    _set_git_diff(monkeypatch, "devcovenant/core/check.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_skipped_globs_ignore_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured skipped globs should bypass coverage checks."""

    checker = ChangelogCoverageCheck()
    checker.set_options({"skipped_globs": ["*_old.*"]}, {})
    _set_git_diff(monkeypatch, "devcovenant/config_old.yaml\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_root_changelog_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_rng_changelog_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """RNG files must be documented in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")

    checker = ChangelogCoverageCheck()
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "rng_minigames/CHANGELOG.md" in violations[0].message


def _unit_test_collections_disabled_route_to_root(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_changelog_requires_summary_labels(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_summary_requires_action_verbs(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_files_block_auto_fix(tmp_path: Path):
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


def _unit_test_files_block_auto_fix_wraps_summary_lines(tmp_path: Path):
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


def _unit_test_rng_changelog_entry_found(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_rng_files_not_logged_in_root(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_rng_entries_ignore_old_root_sections(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_template_code_block_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_changelog_entries_newest_first(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_line_continuation_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
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


def _unit_test_managed_doc_changes_inside_managed_blocks_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-doc diffs confined to DEVCOV blocks should skip coverage."""

    old_agents = (
        "# AGENTS\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old managed text.\n"
        "<!-- DEVCOV:END -->\n"
        "User text.\n"
    )
    new_agents = old_agents.replace("Old managed text.", "New managed text.")
    (tmp_path / "AGENTS.md").write_text(new_agents, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="AGENTS.md\n",
        patches={
            "AGENTS.md": (
                "@@ -3 +3 @@\n" "-Old managed text.\n" "+New managed text.\n"
            )
        },
        head_files={"AGENTS.md": old_agents},
    )

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_managed_doc_changes_outside_managed_blocks_require_changelog(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-doc diffs outside DEVCOV blocks must still hit coverage."""

    old_readme = (
        "# Old title\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Managed text.\n"
        "<!-- DEVCOV:END -->\n"
    )
    new_readme = old_readme.replace("# Old title", "# New title")
    (tmp_path / "README.md").write_text(new_readme, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="README.md\n",
        patches={"README.md": "@@ -1 +1 @@\n-# Old title\n+# New title\n"},
        head_files={"README.md": old_readme},
    )

    checker = ChangelogCoverageCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("CHANGELOG.md" in violation.message for violation in violations)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_no_changes_passes(self):
        """Run test_no_changes_passes."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_no_changes_passes(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_skipped_prefixes_ignore_paths(self):
        """Run test_skipped_prefixes_ignore_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_skipped_prefixes_ignore_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_skipped_globs_ignore_paths(self):
        """Run test_skipped_globs_ignore_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_skipped_globs_ignore_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_root_changelog_required(self):
        """Run test_root_changelog_required."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_root_changelog_required(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_changelog_required(self):
        """Run test_rng_changelog_required."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_changelog_required(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_collections_disabled_route_to_root(self):
        """Run test_collections_disabled_route_to_root."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_collections_disabled_route_to_root(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_changelog_requires_summary_labels(self):
        """Run test_changelog_requires_summary_labels."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_changelog_requires_summary_labels(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_summary_requires_action_verbs(self):
        """Run test_summary_requires_action_verbs."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_summary_requires_action_verbs(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_files_block_auto_fix(self):
        """Run test_files_block_auto_fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_files_block_auto_fix(tmp_path=tmp_path)

    def test_files_block_auto_fix_wraps_summary_lines(self):
        """Run test_files_block_auto_fix_wraps_summary_lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_files_block_auto_fix_wraps_summary_lines(
                tmp_path=tmp_path
            )

    def test_rng_changelog_entry_found(self):
        """Run test_rng_changelog_entry_found."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_changelog_entry_found(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_files_not_logged_in_root(self):
        """Run test_rng_files_not_logged_in_root."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_files_not_logged_in_root(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_entries_ignore_old_root_sections(self):
        """Run test_rng_entries_ignore_old_root_sections."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_entries_ignore_old_root_sections(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_template_code_block_ignored(self):
        """Run test_template_code_block_ignored."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_template_code_block_ignored(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_changelog_entries_newest_first(self):
        """Run test_changelog_entries_newest_first."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_changelog_entries_newest_first(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_line_continuation_paths(self):
        """Run test_line_continuation_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_line_continuation_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_managed_doc_changes_inside_managed_blocks_are_ignored(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_doc_changes_inside_"
                    "managed_blocks_are_ignored"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_managed_doc_changes_outside_managed_blocks_require_changelog(
        self,
    ):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_doc_changes_outside_"
                    "managed_blocks_require_changelog"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()
