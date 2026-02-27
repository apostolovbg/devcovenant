"""Policy-check execution helpers extracted from `policy_engine`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.services import metadata as metadata_runtime
from devcovenant.core.services.policy_parse import PolicyDefinition


@dataclass
class PolicyCheckRunResult:
    """Counted results from one `run_policy_checks` execution pass."""

    violations: list[Violation]
    passed_count: int
    failed_count: int


def critical_disable_attempted(
    policy: PolicyDefinition,
    *,
    normalized_policy_state: dict[str, bool] | None,
    config: dict[str, Any] | None,
) -> bool:
    """Return True when config attempts to disable a critical policy."""
    severity_token = str(policy.severity or "").strip().lower()
    if severity_token != "critical":
        return False
    policy_state = normalized_policy_state
    if not isinstance(policy_state, dict):
        policy_state = metadata_runtime.normalize_policy_state(
            (config or {}).get("policy_state")
        )
    if policy.policy_id not in policy_state:
        return False
    return policy_state[policy.policy_id] is False


def critical_disable_attempt_violation(
    policy: PolicyDefinition,
    *,
    config_path: Path | None,
) -> Violation:
    """Build a deterministic violation for critical disable attempts."""
    if policy.custom:
        remediation = (
            "Update the custom policy metadata in tracked sources to "
            "change severity/enforcement, then refresh."
        )
    else:
        remediation = (
            "Change tracked policy metadata (or copy the builtin policy "
            "to a custom policy and change metadata there), then refresh."
        )
    return Violation(
        policy_id=policy.policy_id,
        severity="critical",
        file_path=config_path,
        message=(
            "Config `policy_state` attempted to disable a critical "
            f"policy (`{policy.policy_id}`), but critical policies "
            "remain enforced."
        ),
        suggestion=(
            f"Remove or set `policy_state.{policy.policy_id}: true` in "
            f"`devcovenant/config.yaml`. {remediation}"
        ),
        can_auto_fix=False,
    )


def extract_policy_options(
    policy: PolicyDefinition,
    *,
    reserved_metadata_keys: set[str],
) -> dict[str, Any]:
    """Pull custom metadata options from a policy definition."""
    options: dict[str, Any] = {"severity": policy.severity}
    options.update(
        metadata_runtime.decode_metadata_options_map(
            policy.raw_metadata,
            reserved_keys=reserved_metadata_keys,
        )
    )
    return options


def run_policy_checks(
    policies: list[PolicyDefinition],
    *,
    context: CheckContext,
    load_policy_script: Callable[[str], PolicyCheck | None],
    extract_policy_options_fn: Callable[[PolicyDefinition], dict[str, Any]],
    critical_disable_attempted_fn: Callable[[PolicyDefinition], bool],
    critical_disable_attempt_violation_fn: Callable[
        [PolicyDefinition], Violation
    ],
) -> PolicyCheckRunResult:
    """Load and run policy checks while tracking pass/fail counts."""
    violations: list[Violation] = []
    passed_count = 0
    failed_count = 0

    for policy in policies:
        policy_violations: list[Violation] = []
        forced_enabled = False
        if critical_disable_attempted_fn(policy):
            forced_enabled = True
            policy_violations.append(
                critical_disable_attempt_violation_fn(policy)
            )

        if not policy.enabled and not forced_enabled:
            continue

        try:
            checker = load_policy_script(policy.policy_id)
            if checker:
                options = extract_policy_options_fn(policy)
                config_overrides = context.get_policy_config(policy.policy_id)
                checker.set_options(options, config_overrides)
                checker_violations = checker.check(context)
                policy_violations.extend(checker_violations)
                violations.extend(policy_violations)
                if not policy_violations:
                    passed_count += 1
                else:
                    failed_count += 1
        except Exception as error:
            failed_count += 1
            violations.append(
                Violation(
                    policy_id=policy.policy_id,
                    severity="error",
                    message=f"Policy execution failed: {error}",
                    suggestion=(
                        "Fix the policy script/runtime error before "
                        "continuing."
                    ),
                )
            )

    return PolicyCheckRunResult(
        violations=violations,
        passed_count=passed_count,
        failed_count=failed_count,
    )
