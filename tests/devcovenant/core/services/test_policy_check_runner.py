"""Sanity checks for devcovenant.core.services.policy_check_runner."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.services.policy_parse import PolicyDefinition

MODULE = "devcovenant.core.services.policy_check_runner"


def _policy(
    policy_id: str,
    *,
    severity: str = "warning",
    enabled: bool = True,
    custom: bool = False,
    raw_metadata: dict[str, str] | None = None,
) -> PolicyDefinition:
    """Build a small policy definition fixture for helper tests."""
    return PolicyDefinition(
        policy_id=policy_id,
        name=policy_id,
        severity=severity,
        auto_fix=False,
        enabled=enabled,
        custom=custom,
        description="demo",
        raw_metadata=dict(raw_metadata or {}),
    )


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Policy-check runner seam functions should remain importable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "PolicyCheckRunResult",
        "critical_disable_attempted",
        "critical_disable_attempt_violation",
        "extract_policy_options",
        "run_policy_checks",
    ]:
        assert hasattr(module, symbol)


def _unit_test_symbol_assertions_cover_runner_seam() -> None:
    """Tests should assert the policy-check runner seam directly."""
    module = importlib.import_module(MODULE)
    assert module.PolicyCheckRunResult
    assert module.critical_disable_attempted
    assert module.critical_disable_attempt_violation
    assert module.extract_policy_options
    assert module.run_policy_checks


def _unit_test_critical_disable_attempted_uses_state_and_fallback_config() -> (
    None
):
    """Critical-disable helper should honor state and config fallback."""
    module = importlib.import_module(MODULE)
    critical_policy = _policy("critical-demo", severity="critical")
    warning_policy = _policy("warning-demo", severity="warning")

    assert (
        module.critical_disable_attempted(
            warning_policy,
            normalized_policy_state={"warning-demo": False},
            config={},
        )
        is False
    )
    assert (
        module.critical_disable_attempted(
            critical_policy,
            normalized_policy_state={"critical-demo": False},
            config={},
        )
        is True
    )
    assert (
        module.critical_disable_attempted(
            critical_policy,
            normalized_policy_state=None,
            config={"policy_state": {"critical-demo": False}},
        )
        is True
    )


def _unit_test_critical_disable_attempt_violation_messages_are_stable() -> (
    None
):
    """Critical-disable violation helper should preserve remediation text."""
    module = importlib.import_module(MODULE)
    builtin_violation = module.critical_disable_attempt_violation(
        _policy("critical-demo", severity="critical", custom=False),
        config_path=Path("devcovenant/config.yaml"),
    )
    custom_violation = module.critical_disable_attempt_violation(
        _policy("critical-demo", severity="critical", custom=True),
        config_path=Path("devcovenant/config.yaml"),
    )
    assert builtin_violation.severity == "critical"
    assert "remain enforced" in builtin_violation.message
    assert "copy the builtin policy" in str(builtin_violation.suggestion)
    assert "custom policy metadata" in str(custom_violation.suggestion)


def _unit_test_extract_policy_options_preserves_severity() -> None:
    """Option extractor should decode metadata while keeping severity."""
    module = importlib.import_module(MODULE)
    policy = _policy(
        "demo-policy",
        severity="error",
        raw_metadata={
            "header_scan_lines": "4",
            "required_globs": "README.md, AGENTS.md",
            "severity": "warning",
        },
    )
    options = module.extract_policy_options(
        policy,
        reserved_metadata_keys={"severity"},
    )
    assert options["severity"] == "error"
    assert options["header_scan_lines"] == 4
    assert options["required_globs"] == ["README.md", "AGENTS.md"]


def _unit_test_run_policy_checks_tracks_counts_for_forced_and_successful() -> (
    None
):
    """Runner helper should count forced-critical and successful checks."""
    module = importlib.import_module(MODULE)
    critical_policy = _policy(
        "critical-demo",
        severity="critical",
        enabled=False,
    )
    passing_policy = _policy("pass-demo", severity="warning", enabled=True)
    skipped_policy = _policy("skip-demo", severity="warning", enabled=False)
    calls: list[str] = []

    class _Checker:
        """Minimal checker stub for runner helper tests."""

        def __init__(self, policy_id: str) -> None:
            """Store policy id for assertions."""
            self.policy_id = policy_id
            self.options = ({}, {})

        def set_options(self, metadata_options, config_overrides) -> None:
            """Capture passed options."""
            self.options = (dict(metadata_options), dict(config_overrides))

        def check(self, context):
            """Return no violations and record execution order."""
            assert isinstance(context, CheckContext)
            calls.append(self.policy_id)
            return []

    def _load_policy_script(policy_id: str):
        """Return stubs for policies that should execute."""
        if policy_id == "skip-demo":
            raise AssertionError(
                "Disabled non-critical policy should not load."
            )
        return _Checker(policy_id)

    context = CheckContext(
        repo_root=Path("/tmp/devcovenant"),
        config={"user_metadata_overrides": {}},
    )
    result = module.run_policy_checks(
        [critical_policy, passing_policy, skipped_policy],
        context=context,
        load_policy_script=_load_policy_script,
        extract_policy_options_fn=lambda policy: {"severity": policy.severity},
        critical_disable_attempted_fn=(
            lambda policy: policy.policy_id == "critical-demo"
        ),
        critical_disable_attempt_violation_fn=lambda policy: Violation(
            policy_id=policy.policy_id,
            severity="critical",
            message="forced critical",
        ),
    )

    assert calls == ["critical-demo", "pass-demo"]
    assert result.passed_count == 1
    assert result.failed_count == 1
    assert len(result.violations) == 1
    assert result.violations[0].policy_id == "critical-demo"


def _unit_test_run_policy_checks_captures_checker_exceptions() -> None:
    """Runner helper should convert checker exceptions into violations."""
    module = importlib.import_module(MODULE)
    exploding_policy = _policy("explode-demo")
    context = CheckContext(repo_root=Path("/tmp/devcovenant"))

    def _load_policy_script(_policy_id: str):
        """Return a checker that raises when executed."""

        class _ExplodingChecker:
            """Minimal exploding checker."""

            def set_options(self, metadata_options, config_overrides) -> None:
                """Accept options before raising in check."""
                del metadata_options, config_overrides

            def check(self, _context):
                """Raise to exercise error-to-violation conversion."""
                raise RuntimeError("boom")

        return _ExplodingChecker()

    result = module.run_policy_checks(
        [exploding_policy],
        context=context,
        load_policy_script=_load_policy_script,
        extract_policy_options_fn=lambda policy: {"severity": policy.severity},
        critical_disable_attempted_fn=lambda _policy: False,
        critical_disable_attempt_violation_fn=lambda _policy: Violation(
            policy_id="unused",
            severity="critical",
            message="unused",
        ),
    )

    assert result.passed_count == 0
    assert result.failed_count == 1
    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.policy_id == "explode-demo"
    assert violation.severity == "error"
    assert "Policy execution failed: boom" in violation.message


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy-check-runner helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run policy-check-runner symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_runner_seam(self):
        """Run explicit policy-check-runner symbol assertions."""
        _unit_test_symbol_assertions_cover_runner_seam()

    def test_critical_disable_attempted_uses_state_and_fallback_config(self):
        """Run critical-disable state/fallback assertions."""
        _unit_test_critical_disable_attempted_uses_state_and_fallback_config()

    def test_critical_disable_attempt_violation_messages_are_stable(self):
        """Run critical-disable violation message assertions."""
        _unit_test_critical_disable_attempt_violation_messages_are_stable()

    def test_extract_policy_options_decodes_metadata_and_preserves_severity(
        self,
    ):
        """Run policy-option extraction/decoding assertions."""
        _unit_test_extract_policy_options_preserves_severity()

    def test_run_policy_checks_tracks_counts_for_forced_and_successful(
        self,
    ):
        """Run runner helper count/forced-policy assertions."""
        _unit_test_run_policy_checks_tracks_counts_for_forced_and_successful()

    def test_run_policy_checks_captures_checker_exceptions(self):
        """Run runner helper exception-to-violation assertions."""
        _unit_test_run_policy_checks_captures_checker_exceptions()
