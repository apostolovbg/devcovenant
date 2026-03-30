"""Repository integrity validation for descriptors, registry, and gate data."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

import devcovenant.core.flow.gate_status_validation as status_validation
from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.policy_parse import (
    PolicyDefinition,
    PolicyParser,
)
from devcovenant.core.services.policy_registry import (
    PolicyRegistry,
    load_policy_descriptor,
)

CHECK_ID = "integrity-validation"
_DEFAULT_STATUS_PATH = (
    Path("devcovenant") / "registry" / "runtime" / "gate_status.json"
)
_DEFAULT_POLICY_DEFINITIONS = Path("AGENTS.md")
_DEFAULT_REGISTRY_FILE = Path("devcovenant/registry/registry.yaml")


def _load_config_payload_or_empty(repo_root: Path) -> dict[str, object]:
    """Load config when present, otherwise return an empty payload."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml_cache_service.load_yaml(config_path)
    except (OSError, yaml.YAMLError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _merged_section(
    repo_root: Path,
    context_config: dict[str, object],
    section_name: str,
) -> dict[str, object]:
    """Return one config section merged with in-context overrides."""
    merged: dict[str, object] = {}
    repo_payload = _load_config_payload_or_empty(repo_root)
    repo_section = repo_payload.get(section_name)
    if isinstance(repo_section, dict):
        merged.update(repo_section)
    context_section = context_config.get(section_name)
    if isinstance(context_section, dict):
        merged.update(context_section)
    return merged


def _relative_path_option(
    raw_mapping: dict[str, object],
    key: str,
    default: str | Path,
) -> Path:
    """Return one repo-relative path from string-or-list config values."""
    value = raw_mapping.get(key, default)
    if isinstance(value, (list, tuple)):
        for entry in value:
            token = str(entry or "").strip()
            if token:
                return Path(token)
        return Path(str(default))
    token = str(value or "").strip()
    if token:
        return Path(token)
    return Path(str(default))


def _string_list_option(
    raw_mapping: dict[str, object],
    key: str,
) -> list[str]:
    """Return one list-valued config option as cleaned strings."""
    raw_value = raw_mapping.get(key, [])
    if isinstance(raw_value, str):
        token = raw_value.strip()
        return [token] if token else []
    if not isinstance(raw_value, list):
        return []
    values: list[str] = []
    for entry in raw_value:
        token = str(entry or "").strip()
        if token:
            values.append(token)
    return values


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
    rel_path: Path,
    watched_roots: set[str],
    watched_files: set[str],
) -> bool:
    """Return True when rel_path should trigger a gate-status refresh."""
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


def _load_policies(
    agents_path: Path,
) -> tuple[list[PolicyDefinition], list[Violation]]:
    """Return parsed AGENTS policies or a blocking violation."""
    if not agents_path.exists():
        return [], [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=agents_path,
                message="Policy definitions file is missing.",
                suggestion="Restore AGENTS.md before running checks.",
            )
        ]
    parsed = PolicyParser(agents_path).parse_agents_md()
    return parsed, []


def _check_policy_text_integrity(
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
                    policy_id=CHECK_ID,
                    severity="error",
                    file_path=agents_path,
                    message=(
                        "Policy definitions must include descriptive text. "
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
                policy_id=CHECK_ID,
                severity="warning",
                file_path=agents_path,
                message=(
                    "Descriptor policy text differs from AGENTS. Policy "
                    f"'{policy.policy_id}' should match its descriptor text."
                ),
                suggestion=(
                    "Regenerate AGENTS from descriptors or update the "
                    "descriptor text to match the intended policy prose."
                ),
            )
        )
    return violations


def _check_registry_sync(
    context: CheckContext,
    registry_path: Path,
    policies: list[PolicyDefinition],
) -> list[Violation]:
    """Validate registry hash synchronization for discovered policies."""
    if not registry_path.exists():
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=registry_path,
                message="Policy registry file is missing.",
                suggestion="Run `devcovenant refresh`.",
            )
        ]

    registry = PolicyRegistry(registry_path, context.repo_root)
    sync_issues = registry.check_policy_sync(policies)
    violations: list[Violation] = []
    for issue in sync_issues:
        if issue.issue_type == "script_missing":
            message = f"Policy script missing for policy '{issue.policy_id}'."
            suggestion = "Add the policy script or remove the policy."
        else:
            message = (
                "Policy registry hash mismatch for policy "
                f"'{issue.policy_id}'."
            )
            suggestion = "Run `devcovenant refresh`."
        violations.append(
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=issue.script_path or registry_path,
                message=message,
                suggestion=suggestion,
            )
        )
    return violations


def _check_gate_status(
    context: CheckContext,
    status_relative: Path,
    watched_dirs: list[str],
    watched_files: list[str],
) -> list[Violation]:
    """Validate gate-status metadata when watched files are modified."""
    changed_paths: Iterable[Path] = context.changed_files or []
    watched_roots = set(watched_dirs)
    watched_file_names = {Path(entry).name for entry in watched_files}

    status_changed = False
    relevant_change = False
    for changed_path in changed_paths:
        try:
            rel_path = changed_path.relative_to(context.repo_root)
        except ValueError:
            continue
        if rel_path == status_relative:
            status_changed = True
        if _requires_status_update(
            rel_path, watched_roots, watched_file_names
        ):
            relevant_change = True

    if not relevant_change:
        return []

    status_path = context.repo_root / status_relative
    if not status_changed:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_path,
                line_number=1,
                message=(
                    "Code changes require a fresh gate status update. Run "
                    "`devcovenant run` so the workflow runs execute and "
                    "the status file is refreshed."
                ),
            )
        ]

    try:
        status_validation.validate_gate_status_payload(status_path)
    except ValueError as exc:
        return [
            Violation(
                policy_id=CHECK_ID,
                severity="error",
                file_path=status_path,
                line_number=1,
                message=f"{status_relative.as_posix()} is invalid: {exc}",
            )
        ]
    return []


def check_integrity(context: CheckContext) -> list[Violation]:
    """Run descriptor, registry, and gate-status integrity checks."""
    path_settings = _merged_section(context.repo_root, context.config, "paths")
    integrity_settings = _merged_section(
        context.repo_root,
        context.config,
        "integrity",
    )
    agents_relative = _relative_path_option(
        path_settings,
        "policy_definitions",
        _DEFAULT_POLICY_DEFINITIONS,
    )
    agents_path = context.repo_root / agents_relative
    policies, policy_load_violations = _load_policies(agents_path)
    if policy_load_violations:
        return policy_load_violations

    registry_relative = _relative_path_option(
        path_settings,
        "registry_file",
        _DEFAULT_REGISTRY_FILE,
    )
    status_relative = _relative_path_option(
        path_settings,
        "gate_status_file",
        _DEFAULT_STATUS_PATH,
    )

    violations: list[Violation] = []
    violations.extend(
        _check_policy_text_integrity(context, agents_path, policies)
    )
    violations.extend(
        _check_registry_sync(
            context,
            context.repo_root / registry_relative,
            policies,
        )
    )
    violations.extend(
        _check_gate_status(
            context,
            status_relative,
            watched_dirs=_string_list_option(integrity_settings, "watch_dirs"),
            watched_files=_string_list_option(
                integrity_settings,
                "watch_files",
            ),
        )
    )
    return violations
