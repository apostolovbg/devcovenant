"""Reporting and blocking helpers for policy-engine output contracts."""

from __future__ import annotations

from typing import Callable

from devcovenant.core.contracts.policy import Violation
from devcovenant.core.services.policy_registry import PolicySyncIssue

_SEVERITY_ORDER = ("critical", "error", "warning", "info")
_SEVERITY_LEVELS = {
    "critical": 4,
    "error": 3,
    "warning": 2,
    "info": 1,
}


def _sync_issue_test_file(issue: PolicySyncIssue) -> str:
    """Return the suggested test file path for a sync issue."""
    policy_slug = issue.policy_id.replace("-", "_")
    script_path = str(issue.script_path).replace("\\", "/")
    if "/builtin/policies/" in script_path:
        return (
            "tests/devcovenant/builtin/policies/"
            f"{policy_slug}/test_{policy_slug}.py"
        )
    if "/custom/policies/" in script_path:
        return (
            "tests/devcovenant/custom/policies/"
            f"{policy_slug}/test_{policy_slug}.py"
        )
    return (
        "tests/devcovenant/builtin/policies/"
        f"{policy_slug}/test_{policy_slug}.py"
    )


def report_sync_issues(
    issues: list[PolicySyncIssue],
    *,
    print_fn: Callable[..., None],
) -> None:
    """Report policy sync issues in AI-friendly format."""
    print_fn("\n" + "=" * 70)
    print_fn("🔄 POLICY SYNC REQUIRED")
    print_fn("=" * 70)
    print_fn()

    for issue in issues:
        print_fn(f"Policy '{issue.policy_id}' requires attention.")
        print_fn(f"Issue: {issue.issue_type.replace('_', ' ').title()}")
        print_fn()

        test_file = _sync_issue_test_file(issue)

        print_fn("📋 Current Policy (from AGENTS.md):")
        print_fn("━" * 70)
        policy_preview = issue.policy_text[:500]
        if len(issue.policy_text) > 500:
            policy_preview += "..."
        print_fn(policy_preview)
        print_fn("━" * 70)
        print_fn()

        print_fn("🎯 Action Required:")
        is_new = issue.issue_type in {"script_missing", "new_policy"}
        if is_new:
            print_fn(f"1. Create: {issue.script_path}")
            print_fn("2. Implement the policy described above")
            print_fn(
                "3. Use the PolicyCheck contract from "
                "devcovenant.core.contracts.policy"
            )
            print_fn(f"4. Add tests in {test_file}")
            print_fn(f"5. Run tests: pytest {test_file} -v")
        else:
            print_fn(f"1. Update: {issue.script_path}")
            print_fn("2. Modify the script to implement the updated policy")
            print_fn(f"3. Update tests in {test_file}")
            print_fn(f"4. Run tests: pytest {test_file} -v")

        print_fn("6. Re-run `devcovenant refresh` to sync policy hashes")
        print_fn()
        print_fn("⚠️  Complete this BEFORE working on user's request.")
        print_fn()
        print_fn("=" * 70)
        print_fn()


def report_single_violation(
    violation: Violation,
    *,
    print_fn: Callable[..., None],
) -> None:
    """Report one violation with full context."""
    icons = {
        "critical": "❌",
        "error": "🚫",
        "warning": "⚠️",
        "info": "💡",
    }
    icon = icons.get(violation.severity, "•")

    print_fn(f"{icon} {violation.severity.upper()}: {violation.policy_id}")

    if violation.file_path:
        location = str(violation.file_path)
        if violation.line_number:
            location += f":{violation.line_number}"
        print_fn(f"📍 {location}")

    print_fn()
    print_fn(f"Issue: {violation.message}")

    if violation.suggestion:
        print_fn()
        print_fn("Fix:")
        print_fn(violation.suggestion)

    if violation.can_auto_fix:
        print_fn()
        print_fn("Auto-fix: Available in gate workflow (check is audit-only)")

    print_fn()
    print_fn(f"Policy: AGENTS.md#{violation.policy_id}")
    print_fn("━" * 70)
    print_fn()


def violations_by_severity(
    violations: list[Violation],
) -> dict[str, list[Violation]]:
    """Group violations by severity."""
    grouped: dict[str, list[Violation]] = {}
    for violation in violations:
        grouped.setdefault(violation.severity, []).append(violation)
    return grouped


def should_block(
    violations: list[Violation],
    *,
    fail_threshold: str = "error",
) -> bool:
    """Return True when any violation meets the configured threshold."""
    if not violations:
        return False
    threshold_token = str(fail_threshold or "error").strip().lower()
    threshold_level = _SEVERITY_LEVELS.get(threshold_token, 3)
    for violation in violations:
        if _SEVERITY_LEVELS.get(violation.severity, 1) >= threshold_level:
            return True
    return False


def report_summary(
    by_severity: dict[str, list[Violation]],
    *,
    print_fn: Callable[..., None],
    fail_threshold: str = "error",
    auto_fix_enabled: bool = False,
) -> None:
    """Report violation counts and blocking status summary."""
    critical = len(by_severity.get("critical", []))
    errors = len(by_severity.get("error", []))
    warnings = len(by_severity.get("warning", []))
    info = len(by_severity.get("info", []))

    print_fn(
        f"Summary: {critical} critical, {errors} errors, "
        f"{warnings} warnings, {info} info"
    )
    print_fn()

    threshold_token = str(fail_threshold or "error").strip().lower()
    threshold_level = _SEVERITY_LEVELS.get(threshold_token, 3)
    counts_by_severity = {
        "critical": critical,
        "error": errors,
        "warning": warnings,
        "info": info,
    }
    blocks_at_threshold = any(
        counts_by_severity[severity] > 0
        and _SEVERITY_LEVELS[severity] >= threshold_level
        for severity in _SEVERITY_ORDER
    )
    if blocks_at_threshold:
        print_fn(
            "Status: 🚫 BLOCKED "
            f"(violations >= {threshold_token} threshold)"
        )
    elif any(counts_by_severity.values()):
        print_fn("Status: ✅ PASSED (violations below fail threshold)")
    else:
        print_fn("Status: ✅ PASSED")

    print_fn()
    if auto_fix_enabled:
        print_fn(
            "💡 `devcovenant check` is read-only; use the gate workflow "
            "to run refresh + autofix with lifecycle recording"
        )
    print_fn("=" * 70)


def report_violations(
    violations: list[Violation],
    *,
    passed_count: int,
    failed_count: int,
    print_fn: Callable[..., None],
    fail_threshold: str = "error",
    auto_fix_enabled: bool = False,
) -> None:
    """Report policy violations with grouped detail and summary."""
    if not violations:
        print_fn("\n✅ All policy checks passed!")
        return

    print_fn("\n" + "=" * 70)
    print_fn("📊 DEVCOVENANT CHECK RESULTS")
    print_fn("=" * 70)
    print_fn()
    print_fn(f"✅ Passed: {passed_count} policies")
    print_fn(f"⚠️  Violations: {len(violations)} issues found")
    print_fn()

    by_severity = violations_by_severity(violations)
    for severity in _SEVERITY_ORDER:
        for violation in by_severity.get(severity, []):
            report_single_violation(violation, print_fn=print_fn)

    print_fn("=" * 70)
    report_summary(
        by_severity,
        print_fn=print_fn,
        fail_threshold=fail_threshold,
        auto_fix_enabled=auto_fix_enabled,
    )


def config_fail_threshold(config: dict[str, object] | None) -> str:
    """Return normalized fail-threshold token from config."""
    if not isinstance(config, dict):
        return "error"
    engine_cfg = config.get("engine", {})
    if not isinstance(engine_cfg, dict):
        return "error"
    return str(engine_cfg.get("fail_threshold", "error")).strip().lower()


def config_auto_fix_enabled(config: dict[str, object] | None) -> bool:
    """Return auto-fix enablement from config."""
    if not isinstance(config, dict):
        return False
    engine_cfg = config.get("engine", {})
    if not isinstance(engine_cfg, dict):
        return False
    return bool(engine_cfg.get("auto_fix_enabled", False))
