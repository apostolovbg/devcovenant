"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import Violation
from devcovenant.core.services.policy_registry import PolicySyncIssue

MODULE = "devcovenant.core.services.policy_reporting"


def _capture_lines():
    """Return a print sink and collected output buffer."""
    lines: list[str] = []

    def _print(*parts, **_kwargs):
        """Collect printed parts as one line."""
        lines.append(" ".join(str(part) for part in parts))

    return _print, lines


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Reporting helper seam functions should remain callable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "config_auto_fix_enabled",
        "config_fail_threshold",
        "report_single_violation",
        "report_summary",
        "report_sync_issues",
        "report_violations",
        "should_block",
        "violations_by_severity",
    ]:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))


def _unit_test_symbol_assertions_cover_reporting_seam() -> None:
    """Tests should assert the reporting helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.config_auto_fix_enabled
    assert module.config_fail_threshold
    assert module.report_single_violation
    assert module.report_summary
    assert module.report_sync_issues
    assert module.report_violations
    assert module.should_block
    assert module.violations_by_severity


def _unit_test_should_block_respects_threshold() -> None:
    """Blocking helper should honor the configured fail threshold."""
    module = importlib.import_module(MODULE)
    warning_violation = Violation(
        policy_id="line-length-limit",
        severity="warning",
        message="demo warning",
    )
    assert module.should_block([], fail_threshold="error") is False
    assert (
        module.should_block([warning_violation], fail_threshold="error")
        is False
    )
    assert (
        module.should_block([warning_violation], fail_threshold="warning")
        is True
    )


def _unit_test_report_summary_emits_threshold_status() -> None:
    """Summary helper should print blocked status at warning threshold."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    by_severity = {"warning": [object(), object()]}
    module.report_summary(
        by_severity,
        print_fn=print_fn,
        fail_threshold="warning",
        auto_fix_enabled=True,
    )
    joined = "\n".join(lines)
    assert "Summary: 0 critical, 0 errors, 2 warnings, 0 info" in joined
    assert "Status: 🚫 BLOCKED (violations >= warning threshold)" in joined
    assert "devcovenant check" in joined


def _unit_test_report_single_violation_includes_location_and_policy() -> None:
    """Single-violation helper should print location and policy anchor."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    module.report_single_violation(
        Violation(
            policy_id="line-length-limit",
            severity="warning",
            file_path=Path("README.md"),
            line_number=10,
            message="Line exceeds limit",
            suggestion="Wrap the line",
            can_auto_fix=True,
        ),
        print_fn=print_fn,
    )
    joined = "\n".join(lines)
    assert "WARNING: line-length-limit" in joined
    assert "📍 README.md:10" in joined
    assert "Policy: AGENTS.md#line-length-limit" in joined
    assert "Auto-fix: Available in gate workflow" in joined


def _unit_test_report_sync_issues_suggests_test_paths() -> None:
    """Sync-issue helper should suggest deterministic test file paths."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    issues = [
        PolicySyncIssue(
            policy_id="demo-policy",
            policy_text="x" * 520,
            policy_hash="",
            script_path=Path(
                "devcovenant/builtin/policies/demo_policy/demo_policy.py"
            ),
            script_exists=False,
            issue_type="script_missing",
        )
    ]
    module.report_sync_issues(issues, print_fn=print_fn)
    joined = "\n".join(lines)
    assert "POLICY SYNC REQUIRED" in joined
    assert (
        "Create: devcovenant/builtin/policies/demo_policy/demo_policy.py"
        in joined
    )
    assert (
        "tests/devcovenant/builtin/policies/demo_policy/"
        "test_demo_policy.py" in joined
    )
    assert "..." in joined


def _unit_test_report_violations_groups_and_summarizes() -> None:
    """Violation report helper should print grouped details and summary."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    violations = [
        Violation(policy_id="warn-demo", severity="warning", message="warn"),
        Violation(policy_id="err-demo", severity="error", message="err"),
    ]
    module.report_violations(
        violations,
        passed_count=4,
        failed_count=2,
        print_fn=print_fn,
        fail_threshold="error",
        auto_fix_enabled=False,
    )
    joined = "\n".join(lines)
    assert "✅ Passed: 4 policies" in joined
    assert "⚠️  Violations: 2 issues found" in joined
    assert joined.index("ERROR: err-demo") < joined.index("WARNING: warn-demo")
    assert "Status: 🚫 BLOCKED (violations >= error threshold)" in joined


def _unit_test_config_helpers_normalize_engine_values() -> None:
    """Config helpers should normalize fail threshold and auto-fix flag."""
    module = importlib.import_module(MODULE)
    config = {"engine": {"fail_threshold": " Warning ", "auto_fix_enabled": 1}}
    assert module.config_fail_threshold(config) == "warning"
    assert module.config_auto_fix_enabled(config) is True
    assert module.config_fail_threshold({}) == "error"
    assert module.config_auto_fix_enabled({}) is False


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy-reporting helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run reporting helper symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_reporting_seam(self):
        """Run explicit reporting helper symbol assertions."""
        _unit_test_symbol_assertions_cover_reporting_seam()

    def test_should_block_respects_threshold(self):
        """Run fail-threshold blocking helper assertions."""
        _unit_test_should_block_respects_threshold()

    def test_report_summary_emits_threshold_status(self):
        """Run summary helper threshold-status assertions."""
        _unit_test_report_summary_emits_threshold_status()

    def test_report_single_violation_includes_location_and_policy(self):
        """Run single-violation output assertions."""
        _unit_test_report_single_violation_includes_location_and_policy()

    def test_report_sync_issues_suggests_test_paths(self):
        """Run sync-issue output path assertions."""
        _unit_test_report_sync_issues_suggests_test_paths()

    def test_report_violations_groups_and_summarizes(self):
        """Run grouped violation report output assertions."""
        _unit_test_report_violations_groups_and_summarizes()

    def test_config_helpers_normalize_engine_values(self):
        """Run reporting config-helper normalization assertions."""
        _unit_test_config_helpers_normalize_engine_values()
