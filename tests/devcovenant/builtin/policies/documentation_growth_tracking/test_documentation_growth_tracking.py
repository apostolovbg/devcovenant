"""Tests for the documentation growth reminder policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.documentation_growth_tracking import (
    documentation_growth_tracking,
)
from devcovenant.core.policy_contract import ChangeState, CheckContext

DocumentationGrowthTrackingCheck = (
    documentation_growth_tracking.DocumentationGrowthTrackingCheck
)


def _checker() -> DocumentationGrowthTrackingCheck:
    """Return the policy configured for app code and README files."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_prefixes": ["app/fictional_app"],
            "user_facing_exclude_prefixes": ["devcovenant", "tests"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md", "app/README.md"],
            "doc_quality_files": ["README.md", "app/README.md"],
            "required_headings": ["Table of Contents", "Overview", "Workflow"],
            "require_toc": True,
            "min_section_count": 2,
            "min_word_count": 20,
            "require_mentions": True,
            "mention_min_length": 3,
            "mention_stopwords": ["app"],
        },
        {},
    )
    return checker


def _unit_test_symbol_contract_is_stable() -> None:
    """Policy module should expose its public checker class explicitly."""
    assert hasattr(
        documentation_growth_tracking,
        "DocumentationGrowthTrackingCheck",
    )
    assert (
        documentation_growth_tracking.DocumentationGrowthTrackingCheck
        is DocumentationGrowthTrackingCheck
    )


def _unit_test_reminder_when_code_changes_without_docs(tmp_path: Path):
    """Code changes should request documentation growth."""
    target = tmp_path / "app" / "fictional_app" / "feature.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("hi")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "doc updates" in violations[0].message


def _unit_test_keyword_matches_trigger_reminders(tmp_path: Path):
    """Keyword-matched paths should require documentation updates."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_keywords": ["api"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
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


def _unit_test_no_reminder_when_docs_are_touched(tmp_path: Path):
    """Documentation updates satisfy the reminder."""
    code_file = tmp_path / "app" / "fictional_app" / "feature.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text('print("hi")\n', encoding="utf-8")
    doc_file = tmp_path / "app" / "README.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Project Version:** 0.1.0\n\n"
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


def _unit_test_quality_violation_when_sections_missing(tmp_path: Path):
    """Docs missing required sections should fail quality checks."""
    doc_file = tmp_path / "README.md"
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Project Version:** 0.1.0\n\n"
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


def _unit_test_quality_passes_when_requirements_met(tmp_path: Path):
    """Docs meeting section and word requirements should pass."""
    doc_file = tmp_path / "README.md"
    doc_file.write_text(
        "# README\n"
        "**Last Updated:** 2026-01-11\n"
        "**Project Version:** 0.1.0\n\n"
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


def _unit_test_excluded_paths_do_not_trigger(tmp_path: Path):
    """Excluded prefixes are ignored."""
    target = tmp_path / "devcovenant" / "helper.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("skip")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])

    assert checker.check(context) == []


def _unit_test_non_matching_paths_do_not_trigger(tmp_path: Path):
    """Files outside the include prefixes do not trigger reminders."""
    target = tmp_path / "scripts" / "helper.py"
    target.parent.mkdir(parents=True)
    target.write_text('print("skip")\n', encoding="utf-8")
    checker = _checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[target])

    assert checker.check(context) == []


def _unit_test_route_requires_specific_docs(tmp_path: Path):
    """Route metadata should require mapped documentation targets."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_prefixes": ["app/fictional_app"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md", "app/README.md"],
            "doc_quality_files": ["README.md", "app/README.md"],
            "doc_routes": ["app/fictional_app/ => app/README.md"],
            "require_mentions": False,
            "mention_min_length": 3,
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
        },
        {},
    )

    code_file = tmp_path / "app" / "fictional_app" / "feature.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("print('feature')\n", encoding="utf-8")
    wrong_doc = tmp_path / "README.md"
    wrong_doc.write_text("# README\n", encoding="utf-8")
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_file, wrong_doc],
    )

    violations = checker.check(context)
    assert violations
    assert any("route" in violation.message for violation in violations)


def _unit_test_route_passes_when_required_doc_is_touched(tmp_path: Path):
    """Route metadata should pass once mapped doc target is touched."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_prefixes": ["app/fictional_app"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md", "app/README.md"],
            "doc_quality_files": ["README.md", "app/README.md"],
            "doc_routes": ["app/fictional_app/ => app/README.md"],
            "require_mentions": False,
            "mention_min_length": 3,
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
        },
        {},
    )

    code_file = tmp_path / "app" / "fictional_app" / "feature.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("print('feature')\n", encoding="utf-8")
    required_doc = tmp_path / "app" / "README.md"
    required_doc.parent.mkdir(parents=True, exist_ok=True)
    required_doc.write_text("# App README\n", encoding="utf-8")
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_file, required_doc],
    )

    assert checker.check(context) == []


def _unit_test_route_glob_with_dot_prefix_matches(tmp_path: Path):
    """Dot-prefixed glob routes should match dot-prefixed changed paths."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_globs": [".github/workflows/*.yml"],
            "user_facing_suffixes": [".yml"],
            "user_visible_files": ["devcovenant/docs/workflow.md"],
            "doc_quality_files": ["devcovenant/docs/workflow.md"],
            "doc_routes": [
                ".github/workflows/*.yml => devcovenant/docs/workflow.md"
            ],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )

    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: CI\n", encoding="utf-8")
    workflow_doc = tmp_path / "devcovenant" / "docs" / "workflow.md"
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("# Workflow\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[workflow, workflow_doc],
    )
    violations = checker.check(context)
    assert not any(
        "no doc_routes mapping" in item.message for item in violations
    )


def _unit_test_route_mapping_required_for_matched_scope(tmp_path: Path):
    """Configured doc_routes should require a matching route per change."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "doc_routes": ["app/fictional_app/ => app/README.md"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )

    code_file = tmp_path / "src" / "feature.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("print('feature')\n", encoding="utf-8")
    doc_file = tmp_path / "README.md"
    doc_file.write_text("# README\n", encoding="utf-8")
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_file, doc_file],
    )

    violations = checker.check(context)
    assert violations
    assert any("no doc_routes mapping" in item.message for item in violations)


def _unit_test_missing_severity_reports_configuration_error(tmp_path: Path):
    """Missing severity should emit an explicit configuration error."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('x')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)
    assert violations
    assert "severity" in violations[0].message.lower()


def _unit_test_malformed_doc_routes_reports_configuration_error(
    tmp_path: Path,
):
    """Malformed doc_routes should emit explicit configuration errors."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "doc_routes": ["invalid-route-entry"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('x')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)
    assert violations
    assert any("doc_routes" in violation.message for violation in violations)


def _unit_test_invalid_bool_option_reports_configuration_error(
    tmp_path: Path,
):
    """Invalid boolean options should fail without fallback behavior."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
            "require_toc": "sometimes",
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('x')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)
    assert violations
    assert any("require_toc" in violation.message for violation in violations)


def _unit_test_missing_selectors_reports_configuration_error(
    tmp_path: Path,
):
    """Policy config should require explicit user-facing selectors."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('x')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)
    assert violations
    assert any(
        "user-facing selector" in violation.message for violation in violations
    )


def _unit_test_missing_required_options_report_configuration_error(
    tmp_path: Path,
):
    """Missing required scalar options should report explicit config errors."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
        },
        {},
    )
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('x')\n", encoding="utf-8")
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    violations = checker.check(context)

    assert violations
    messages = [violation.message for violation in violations]
    assert any("require_toc" in message for message in messages)
    assert any("min_section_count" in message for message in messages)
    assert any("min_word_count" in message for message in messages)
    assert any("require_mentions" in message for message in messages)
    assert any("mention_min_length" in message for message in messages)


def _unit_test_uses_session_paths(tmp_path: Path):
    """Policy should read change_state.session_paths."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_prefixes": ["app/fictional_app"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    code_file = tmp_path / "app" / "fictional_app" / "feature.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("print('feature')\n", encoding="utf-8")
    doc_file = tmp_path / "README.md"
    doc_file.write_text("# README\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_file],
        change_state=ChangeState(
            session_paths=[doc_file],
            session_valid=True,
        ),
    )
    assert checker.check(context) == []


def _unit_test_current_snapshot_paths_trigger_runtime_scope(tmp_path: Path):
    """Current snapshot paths should trigger runtime-scoped validation."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "severity": "warning",
            "user_facing_prefixes": ["app/fictional_app"],
            "user_facing_suffixes": [".py"],
            "user_visible_files": ["README.md"],
            "doc_quality_files": ["README.md"],
            "required_headings": [],
            "require_toc": False,
            "min_section_count": 0,
            "min_word_count": 0,
            "require_mentions": False,
            "mention_min_length": 3,
        },
        {},
    )
    code_file = tmp_path / "app" / "fictional_app" / "feature.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("print('feature')\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_file],
        change_state=ChangeState(
            current_snapshot_paths=[code_file],
            session_valid=False,
            session_error="Run `devcovenant gate --open` first.",
        ),
    )
    violations = checker.check(context)
    assert violations
    assert "gate --open" in violations[0].message


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_symbol_contract_is_stable(self):
        """Run documentation-growth symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_reminder_when_code_changes_without_docs(self):
        """Run test_reminder_when_code_changes_without_docs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_reminder_when_code_changes_without_docs(
                tmp_path=tmp_path
            )

    def test_keyword_matches_trigger_reminders(self):
        """Run test_keyword_matches_trigger_reminders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_keyword_matches_trigger_reminders(tmp_path=tmp_path)

    def test_no_reminder_when_docs_are_touched(self):
        """Run test_no_reminder_when_docs_are_touched."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_no_reminder_when_docs_are_touched(tmp_path=tmp_path)

    def test_quality_violation_when_sections_missing(self):
        """Run test_quality_violation_when_sections_missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_quality_violation_when_sections_missing(
                tmp_path=tmp_path
            )

    def test_quality_passes_when_requirements_met(self):
        """Run test_quality_passes_when_requirements_met."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_quality_passes_when_requirements_met(tmp_path=tmp_path)

    def test_excluded_paths_do_not_trigger(self):
        """Run test_excluded_paths_do_not_trigger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_excluded_paths_do_not_trigger(tmp_path=tmp_path)

    def test_non_matching_paths_do_not_trigger(self):
        """Run test_non_matching_paths_do_not_trigger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_non_matching_paths_do_not_trigger(tmp_path=tmp_path)

    def test_route_requires_specific_docs(self):
        """Run test_route_requires_specific_docs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_route_requires_specific_docs(tmp_path=tmp_path)

    def test_route_passes_when_required_doc_is_touched(self):
        """Run test_route_passes_when_required_doc_is_touched."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_route_passes_when_required_doc_is_touched(
                tmp_path=tmp_path
            )

    def test_route_glob_with_dot_prefix_matches(self):
        """Run test_route_glob_with_dot_prefix_matches."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_route_glob_with_dot_prefix_matches(tmp_path=tmp_path)

    def test_route_mapping_required_for_matched_scope(self):
        """Run test_route_mapping_required_for_matched_scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_route_mapping_required_for_matched_scope(
                tmp_path=tmp_path
            )

    def test_missing_severity_reports_configuration_error(self):
        """Run test_missing_severity_reports_configuration_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_missing_severity_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_malformed_doc_routes_reports_configuration_error(self):
        """Run test_malformed_doc_routes_reports_configuration_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_malformed_doc_routes_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_invalid_bool_option_reports_configuration_error(self):
        """Run test_invalid_bool_option_reports_configuration_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_invalid_bool_option_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_missing_user_facing_selectors_reports_configuration_error(
        self,
    ):
        """Run missing-selectors configuration-error test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_missing_selectors_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_missing_required_options_report_configuration_error(self):
        """Run missing-required-options configuration-error test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_missing_required_options_report_configuration_error(
                tmp_path=tmp_path
            )

    def test_uses_session_paths(self):
        """Run test_uses_session_paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_uses_session_paths(tmp_path=tmp_path)

    def test_current_snapshot_paths_trigger_runtime_scope(self):
        """Run test_current_snapshot_paths_trigger_runtime_scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_current_snapshot_paths_trigger_runtime_scope(
                tmp_path=tmp_path
            )
