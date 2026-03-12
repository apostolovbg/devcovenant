"""Tests for last-updated policy."""

import importlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from devcovenant.builtin.policies.last_updated import last_updated
from devcovenant.core.contracts.policy import CheckContext, Violation

fixer_module = importlib.import_module(
    "devcovenant.builtin.policies.last_updated.autofix.global"
)
LastUpdatedCheck = last_updated.LastUpdatedCheck
LastUpdatedFixer = fixer_module.LastUpdatedFixer


def _unit_test_required_file_missing_marker(tmp_path: Path) -> None:
    """Required docs must include a Last Updated marker."""
    doc_path = tmp_path / "README.md"
    doc_path.write_text("# Title\nContent\n", encoding="utf-8")

    checker = last_updated.LastUpdatedCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[doc_path])
    violations = checker.check(context)
    assert violations
    assert any(violation.can_auto_fix for violation in violations)


def _unit_test_last_updated_allowed_in_header_zone(tmp_path: Path) -> None:
    """Allow Last Updated marker anywhere in the generated header zone."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "\n".join(
            [
                "# Title",
                "**Doc ID:** README",
                "**Doc Type:** readme",
                "**Project Version:** 1.0.0",
                "**Last Updated:** 2026-01-07",
                "<!-- DEVCOV:BEGIN -->",
                "block",
                "<!-- DEVCOV:END -->",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checker = last_updated.LastUpdatedCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[md_path])
    assert checker.check(context) == []


def _unit_test_marker_in_non_allowlisted_file(tmp_path: Path) -> None:
    """Last Updated markers in non-allowlisted files are flagged."""
    script_path = tmp_path / "script.py"
    script_path.write_text(
        "**Last Updated:** 2026-01-07\n",
        encoding="utf-8",
    )

    checker = last_updated.LastUpdatedCheck()
    checker.set_options(
        {"allowed_globs": "**/README.md"},
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[script_path])
    violations = checker.check(context)
    assert violations
    assert all(not violation.can_auto_fix for violation in violations)


def _unit_test_stale_marker_on_touched_doc(tmp_path: Path) -> None:
    """Touched allowlisted docs should refresh stale Last Updated markers."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "# Title\n**Last Updated:** 2020-01-01\n",
        encoding="utf-8",
    )

    checker = last_updated.LastUpdatedCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[md_path],
        changed_files=[md_path],
    )
    violations = checker.check(context)
    assert violations
    assert any(
        "current UTC date" in violation.message for violation in violations
    )


def _unit_test_yaml_templates_outside_include_scope(tmp_path: Path) -> None:
    """YAML descriptors stay outside markdown include scope."""
    yaml_path = tmp_path / "template.yaml"
    yaml_path.write_text(
        "title: Template\nlast_updated: true\n",
        encoding="utf-8",
    )

    checker = last_updated.LastUpdatedCheck()
    checker.set_options(
        {
            "include_suffixes": [".md"],
            "include_globs": ["*.md"],
            "allowed_globs": ["**/README.md"],
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[yaml_path])
    assert checker.check(context) == []


def _unit_test_fix_inserts_marker(tmp_path: Path) -> None:
    """Fixer inserts a UTC Last Updated marker when it is missing."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "# Title\nContent\n",
        encoding="utf-8",
    )

    fixer = LastUpdatedFixer()
    violation = Violation(
        policy_id="last-updated",
        severity="warning",
        message="test",
        file_path=md_path,
    )
    result = fixer.fix(violation)
    assert result.success
    lines = md_path.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("**Last Updated:**") for line in lines)


def _unit_test_fix_updates_existing_marker(tmp_path: Path) -> None:
    """Fixer refreshes existing markers to today's UTC date."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "# Title\n**Last Updated:** 2020-01-01\n",
        encoding="utf-8",
    )

    fixer = LastUpdatedFixer()
    violation = Violation(
        policy_id="last-updated",
        severity="warning",
        message="test",
        file_path=md_path,
    )
    fixer.fix(violation)
    date_line = next(
        (
            line
            for line in md_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("**Last Updated:**")
        ),
        "",
    )
    assert date_line.endswith(datetime.now(timezone.utc).date().isoformat())


def _unit_test_last_updated_symbol_contract_is_stable() -> None:
    """Policy/fixer symbols should stay importable and callable."""
    assert callable(LastUpdatedCheck)
    assert hasattr(LastUpdatedCheck, "check")
    assert callable(getattr(LastUpdatedCheck, "check"))
    assert callable(LastUpdatedFixer)
    assert hasattr(LastUpdatedFixer, "fix")
    assert callable(getattr(LastUpdatedFixer, "fix"))


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_required_file_missing_marker(self):
        """Run test_required_file_missing_marker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_required_file_missing_marker(tmp_path=tmp_path)

    def test_last_updated_allowed_in_header_zone(self):
        """Run test_last_updated_allowed_in_header_zone."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_last_updated_allowed_in_header_zone(tmp_path=tmp_path)

    def test_marker_in_non_allowlisted_file(self):
        """Run test_marker_in_non_allowlisted_file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_marker_in_non_allowlisted_file(tmp_path=tmp_path)

    def test_stale_marker_on_touched_doc(self):
        """Run test_stale_marker_on_touched_doc."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_stale_marker_on_touched_doc(tmp_path=tmp_path)

    def test_yaml_templates_outside_include_scope(self):
        """Run test_yaml_templates_outside_include_scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_yaml_templates_outside_include_scope(tmp_path=tmp_path)

    def test_fix_inserts_marker(self):
        """Run test_fix_inserts_marker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_fix_inserts_marker(tmp_path=tmp_path)

    def test_fix_updates_existing_marker(self):
        """Run test_fix_updates_existing_marker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_fix_updates_existing_marker(tmp_path=tmp_path)

    def test_last_updated_symbol_contract_is_stable(self):
        """Run symbol-contract assertions for last-updated policy/fixer."""
        _unit_test_last_updated_symbol_contract_is_stable()
