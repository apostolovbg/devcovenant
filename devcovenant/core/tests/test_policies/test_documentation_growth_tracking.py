"""Tests for the documentation growth reminder policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policy_scripts import documentation_growth_tracking

DocumentationGrowthTrackingCheck = (
    documentation_growth_tracking.DocumentationGrowthTrackingCheck
)


def _checker() -> DocumentationGrowthTrackingCheck:
    """Return the policy configured for app code and README files."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "user_facing_prefixes": ["app/gcv_erp_custom"],
            "user_facing_exclude_prefixes": ["devcovenant", "tests"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md", "app/README.md"],
            "required_headings": ["Table of Contents", "Overview", "Workflow"],
            "require_toc": True,
            "min_section_count": 2,
            "min_word_count": 20,
            "quality_severity": "warning",
            "require_mentions": True,
            "mention_min_length": 3,
            "mention_stopwords": ["app"],
            "mention_severity": "warning",
        },
        {},
    )
    return checker


def test_reminder_when_code_changes_without_docs(tmp_path: Path):
    """Code changes should request documentation growth."""
    target = tmp_path / "app" / "gcv_erp_custom" / "feature.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("hi")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "doc updates" in violations[0].message


def test_keyword_matches_trigger_reminders(tmp_path: Path):
    """Keyword-matched paths should require documentation updates."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "user_facing_keywords": ["api"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
        },
        {},
    )
    target = tmp_path / "src" / "api" / "client.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('api')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)

    assert violations
    assert "doc updates" in violations[0].message


def test_no_reminder_when_docs_are_touched(tmp_path: Path):
    """Documentation updates satisfy the reminder."""
    code_file = tmp_path / "app" / "gcv_erp_custom" / "feature.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text('print("hi")\n', encoding="utf-8")
    doc_file = tmp_path / "app" / "README.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Version:** 0.1.0\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n\n"
        "## Overview\n"
        "This doc explains the feature module used in tests.\n\n"
        "## Workflow\n"
        "Update docs whenever user-facing code changes.\n",
        encoding="utf-8",
    )
    checker = _checker()
    context = CheckContext(
        repo_root=tmp_path, changed_files=[code_file, doc_file]
    )

    assert checker.check(context) == []


def test_quality_violation_when_sections_missing(tmp_path: Path):
    """Docs missing required sections should fail quality checks."""
    doc_file = tmp_path / "README.md"
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Version:** 0.1.0\n\n"
        "## Overview\n"
        "Short doc.\n",
        encoding="utf-8",
    )
    checker = _checker()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[doc_file],
        all_files=[doc_file],
    )
    violations = checker.check(context)

    assert violations
    assert "Documentation quality issue" in violations[0].message


def test_quality_passes_when_requirements_met(tmp_path: Path):
    """Docs meeting section and word requirements should pass."""
    doc_file = tmp_path / "README.md"
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Version:** 0.1.0\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n\n"
        "## Overview\n"
        "This overview supplies enough words to pass the minimum word\n"
        "count for the quality check in this test.\n\n"
        "## Workflow\n"
        "Follow the documentation workflow and keep notes up to date.\n",
        encoding="utf-8",
    )
    checker = _checker()
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[doc_file],
        all_files=[doc_file],
    )

    assert checker.check(context) == []


def test_excluded_paths_do_not_trigger(tmp_path: Path):
    """Excluded prefixes are ignored."""
    target = tmp_path / "devcovenant" / "helper.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("skip")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])

    assert checker.check(context) == []


def test_non_matching_paths_do_not_trigger(tmp_path: Path):
    """Files outside the include prefixes do not trigger reminders."""
    target = tmp_path / "scripts" / "helper.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("skip")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])

    assert checker.check(context) == []
