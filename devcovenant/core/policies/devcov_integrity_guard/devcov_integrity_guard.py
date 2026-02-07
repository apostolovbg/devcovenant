"""Unified integrity checks for DevCovenant policy metadata and state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyDefinition, PolicyParser
from devcovenant.core.policy_descriptor import load_policy_descriptor
from devcovenant.core.registry import PolicyRegistry
from devcovenant.core.selector_helpers import build_watchlists

_DEFAULT_STATUS_PATH = (
    Path("devcovenant") / "registry" / "local" / "test_status.json"
)


def _normalize_policy_text(text_value: str) -> str:
    """Normalize policy text for descriptor comparisons."""
    return "\n".join(line.rstrip() for line in text_value.strip().splitlines())


def _has_meaningful_description(description: str) -> bool:
    """Return True when the policy description is non-empty and useful."""
    if not description:
        return False
    normalized = description.strip()
    if not normalized:
        return False
    if normalized.lower().startswith("<!-- devcov:"):
        return False
    if all(line.strip() in {"---", ""} for line in normalized.splitlines()):
        return False
    return True


def _requires_status_update(
    rel_path: Path, watched_roots: set[str], watched_files: set[str]
) -> bool:
    """Return True when *rel_path* should trigger a test-status refresh."""
    if not rel_path.parts:
        return False
    if rel_path == _DEFAULT_STATUS_PATH:
        return False
    first_segment = rel_path.parts[0]
    if first_segment in watched_roots:
        return True
    if rel_path.name in watched_files:
        return True
    return False


def _validate_status_payload(status_path: Path) -> None:
    """Raise ValueError when the stored test-status payload is malformed."""
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive parse handling
        raise ValueError(f"Unable to parse {status_path}: {exc}") from exc

    last_run = payload.get("last_run") or ""
    try:
        datetime.fromisoformat(last_run.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            "Field 'last_run' must be an ISO-8601 timestamp."
        ) from exc

    command = payload.get("command") or ""
    if not command.strip():
        raise ValueError(
            "Field 'command' must record the executed test command."
        )

    commit_sha = (payload.get("sha") or "").strip()
    if len(commit_sha) < 8:
        raise ValueError(
            "Field 'sha' must contain the git commit recorded for the run."
        )


class DevcovIntegrityGuardCheck(PolicyCheck):
    """Run consolidated integrity checks for policy definitions."""

    policy_id = "devcov-integrity-guard"
    version = "1.0.0"

    def _load_policies(
        self, context: CheckContext, agents_path: Path
    ) -> tuple[list[PolicyDefinition], list[Violation]]:
        """Return parsed AGENTS policies or a blocking violation."""
        if not agents_path.exists():
            return [], [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=agents_path,
                    message="Policy definitions file is missing.",
                    suggestion="Restore AGENTS.md before running checks.",
                )
            ]
        parsed = PolicyParser(agents_path).parse_agents_md()
        return parsed, []

    def _check_policy_text_integrity(
        self,
        context: CheckContext,
        agents_path: Path,
        policies: list[PolicyDefinition],
    ) -> list[Violation]:
        """Validate descriptor parity and non-empty policy descriptions."""
        violations: list[Violation] = []
        for policy in policies:
            description = policy.description.strip()
            if not _has_meaningful_description(description):
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=agents_path,
                        message=(
                            "Policy definitions must include descriptive "
                            "text. "
                            f"Missing text for policy '{policy.policy_id}'."
                        ),
                        suggestion=(
                            "Add meaningful prose immediately after the "
                            f"`policy-def` block for '{policy.policy_id}'."
                        ),
                    )
                )

            descriptor = load_policy_descriptor(
                context.repo_root, policy.policy_id
            )
            if not descriptor or not descriptor.text:
                continue
            if _normalize_policy_text(description) == _normalize_policy_text(
                descriptor.text
            ):
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="warning",
                    file_path=agents_path,
                    message=(
                        "Descriptor policy text differs from AGENTS. "
                        f"Policy '{policy.policy_id}' should match its "
                        "descriptor text."
                    ),
                    suggestion=(
                        "Regenerate AGENTS from descriptors or update the "
                        "descriptor text to match the intended policy prose."
                    ),
                )
            )
        return violations

    def _check_registry_sync(
        self,
        context: CheckContext,
        registry_path: Path,
        policies: list[PolicyDefinition],
    ) -> list[Violation]:
        """Validate registry hash synchronization for discovered policies."""
        if not registry_path.exists():
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=registry_path,
                    message="Policy registry file is missing.",
                    suggestion="Run `devcovenant update-policy-registry`.",
                )
            ]

        registry = PolicyRegistry(registry_path, context.repo_root)
        sync_issues = registry.check_policy_sync(policies)
        violations: list[Violation] = []
        for issue in sync_issues:
            if issue.issue_type == "script_missing":
                message = (
                    f"Policy script missing for policy '{issue.policy_id}'."
                )
                suggestion = "Add the policy script or remove the policy."
            elif issue.issue_type == "new_policy":
                message = (
                    "Policy registry missing entry for policy "
                    f"'{issue.policy_id}'."
                )
                suggestion = "Run `devcovenant update-policy-registry`."
            else:
                message = (
                    "Policy registry hash mismatch for policy "
                    f"'{issue.policy_id}'."
                )
                suggestion = "Run `devcovenant update-policy-registry`."
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=issue.script_path or registry_path,
                    message=message,
                    suggestion=suggestion,
                )
            )
        return violations

    def _check_test_status(
        self, context: CheckContext, status_relative: Path
    ) -> list[Violation]:
        """Validate test-status metadata when watched files are modified."""
        changed_paths: Iterable[Path] = context.changed_files or []
        watch_files, watch_dirs = build_watchlists(self, defaults={})
        watched_roots = set(watch_dirs)
        watched_files = {Path(entry).name for entry in watch_files}

        status_changed = False
        relevant_change = False
        for changed_path in changed_paths:
            try:
                rel_path = changed_path.relative_to(context.repo_root)
            except ValueError:
                continue
            if rel_path == status_relative:
                status_changed = True
            if _requires_status_update(rel_path, watched_roots, watched_files):
                relevant_change = True

        if not relevant_change:
            return []

        status_path = context.repo_root / status_relative
        if not status_changed:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_path,
                    line_number=1,
                    message=(
                        "Code changes require a fresh test status update. "
                        "Run `python3 devcovenant/run_tests.py` so the suite "
                        "executes and the status file is refreshed."
                    ),
                )
            ]

        try:
            _validate_status_payload(status_path)
        except ValueError as exc:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=status_path,
                    line_number=1,
                    message=(
                        f"{status_relative.as_posix()} is invalid: {exc}"
                    ),
                )
            ]
        return []

    def check(self, context: CheckContext) -> List[Violation]:
        """Run the consolidated integrity checks."""
        agents_relative = Path(
            self.get_option("policy_definitions", "AGENTS.md")
        )
        agents_path = context.repo_root / agents_relative
        policies, policy_load_violations = self._load_policies(
            context, agents_path
        )
        if policy_load_violations:
            return policy_load_violations

        registry_relative = Path(
            self.get_option(
                "registry_file",
                "devcovenant/registry/local/policy_registry.yaml",
            )
        )
        status_relative = Path(
            self.get_option("test_status_file", str(_DEFAULT_STATUS_PATH))
        )

        violations: list[Violation] = []
        violations.extend(
            self._check_policy_text_integrity(context, agents_path, policies)
        )
        violations.extend(
            self._check_registry_sync(
                context, context.repo_root / registry_relative, policies
            )
        )
        violations.extend(self._check_test_status(context, status_relative))
        return violations
