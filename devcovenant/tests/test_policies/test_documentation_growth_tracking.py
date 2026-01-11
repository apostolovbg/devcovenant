"""Tests for the documentation growth reminder policy."""

from pathlib import Path

from devcovenant.base import CheckContext
from devcovenant.policy_scripts.documentation_growth_tracking import (
    DocumentationGrowthTrackingCheck,
)


def _checker() -> DocumentationGrowthTrackingCheck:
    """Return the policy configured for app code and README files."""
    checker = DocumentationGrowthTrackingCheck()
    checker.set_options(
        {
            "include_prefixes": ["app/gcv_erp_custom"],
            "exclude_prefixes": ["devcovenant", "tests"],
            "user_visible_files": ["README.md", "app/README.md"],
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


def test_no_reminder_when_docs_are_touched(tmp_path: Path):
    """Documentation updates satisfy the reminder."""
    code_file = tmp_path / "app" / "gcv_erp_custom" / "feature.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text('print("hi")\n', encoding="utf-8")
    doc_file = tmp_path / "app" / "README.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text("Docs\n", encoding="utf-8")
    checker = _checker()
    context = CheckContext(
        repo_root=tmp_path, changed_files=[code_file, doc_file]
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
