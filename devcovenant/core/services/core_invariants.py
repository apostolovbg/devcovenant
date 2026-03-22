"""Registry/runtime helpers for DevCovenant core invariants."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

import devcovenant.core.services.metadata as metadata_runtime
from devcovenant.core.contracts.invariant import (
    CoreInvariantCheck,
    CoreInvariantDefinition,
)
from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.policy_runtime_actions import (
    build_runtime_policy_option_views,
)
from devcovenant.core.services.registry import (
    PolicyDescriptor,
    policy_registry_path,
)

CORE_INVARIANTS_BEGIN = "<!-- DEVCOV-INVARIANTS:BEGIN -->"
CORE_INVARIANTS_END = "<!-- DEVCOV-INVARIANTS:END -->"


@dataclass(frozen=True)
class CoreInvariantLocation:
    """Resolved script and descriptor locations for one invariant."""

    invariant_id: str
    module: str
    path: Path
    descriptor_path: Path


@dataclass(frozen=True)
class ResolvedCoreInvariant:
    """Resolved metadata and registry-facing data for one invariant."""

    definition: CoreInvariantDefinition
    module_path: str
    descriptor_path: str
    metadata_resolution: Dict[str, Dict[str, Any]]
    metadata_warnings: List[Dict[str, Any]]
    runtime_option_views: Dict[str, Dict[str, Any]]


_CORE_INVARIANT_MODULES = {
    "devcov-integrity-guard": (
        "devcovenant.core.services.devcov_integrity_guard"
    ),
    "devcov-structure-guard": (
        "devcovenant.core.services.devcov_structure_guard"
    ),
    "devflow-run-gates": "devcovenant.core.services.devflow_run_gates",
}


def core_invariant_ids() -> list[str]:
    """Return the canonical ordered core invariant ids."""
    return sorted(_CORE_INVARIANT_MODULES)


def _script_name(invariant_id: str) -> str:
    """Return the filesystem-safe module stem for one invariant id."""
    return invariant_id.replace("-", "_")


def resolve_core_invariant_location(
    repo_root: Path,
    invariant_id: str,
) -> CoreInvariantLocation | None:
    """Return script/descriptor locations for one invariant id."""
    module_name = _CORE_INVARIANT_MODULES.get(invariant_id)
    if not module_name:
        return None
    script_name = _script_name(invariant_id)
    script_path = (
        repo_root / "devcovenant" / "core" / "services" / (f"{script_name}.py")
    )
    descriptor_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "contracts"
        / "invariants"
        / f"{script_name}.yaml"
    )
    return CoreInvariantLocation(
        invariant_id=invariant_id,
        module=module_name,
        path=script_path,
        descriptor_path=descriptor_path,
    )


def load_core_invariant_descriptor(
    repo_root: Path,
    invariant_id: str,
) -> PolicyDescriptor | None:
    """Load one core invariant descriptor from disk."""
    location = resolve_core_invariant_location(repo_root, invariant_id)
    if location is None or not location.descriptor_path.exists():
        return None
    try:
        payload = yaml_cache_service.load_yaml(location.descriptor_path)
    except yaml.YAMLError as exc:
        raise ValueError(
            "Invalid YAML in core invariant descriptor "
            f"{location.descriptor_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "Core invariant descriptor must contain a YAML mapping: "
            f"{location.descriptor_path}"
        )
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    runtime_actions = payload.get("runtime_actions", [])
    if not isinstance(runtime_actions, list):
        runtime_actions = []
    commands = payload.get("commands", [])
    if not isinstance(commands, list):
        commands = []
    return PolicyDescriptor(
        policy_id=str(payload.get("id", invariant_id)).strip() or invariant_id,
        text=str(payload.get("text", "") or ""),
        metadata=metadata,
        runtime_actions=runtime_actions,
        commands=commands,
    )


def load_core_invariant_check_instance(
    repo_root: Path,
    invariant_id: str,
) -> CoreInvariantCheck | None:
    """Import and instantiate one core invariant check class."""
    location = resolve_core_invariant_location(repo_root, invariant_id)
    if location is None or not location.path.exists():
        return None
    module = importlib.import_module(location.module)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, CoreInvariantCheck)
            and attr is not CoreInvariantCheck
        ):
            return attr()
    return None


def _normalize_config_override_value(key: str, value: Any) -> Any:
    """Normalize config override values using the policy-style path rules."""
    if not isinstance(value, list):
        return value
    token = str(key or "").strip().lower()
    if not token.endswith(
        ("_file", "_path", "_dir", "_root")
    ) or token.endswith(("_files", "_paths", "_dirs", "_roots")):
        return list(value)
    for entry in value:
        text = str(entry or "").strip()
        if text:
            return text
    return ""


def runtime_core_invariant_config_overrides(
    repo_root: Path,
    invariant_id: str,
) -> dict[str, Any]:
    """Return config metadata overrides for one invariant."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml_cache_service.load_yaml(config_path)
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, dict):
        return {}
    section = payload.get("core_invariants")
    if isinstance(section, dict):
        entry = section.get(invariant_id)
        if isinstance(entry, dict):
            normalized: dict[str, Any] = {}
            for key, value in entry.items():
                normalized[str(key)] = _normalize_config_override_value(
                    str(key),
                    value,
                )
            if normalized:
                return normalized
    context = CheckContext(repo_root=repo_root, config=payload)
    return context.get_policy_config(invariant_id)


def runtime_core_invariant_metadata_options(
    repo_root: Path,
    invariant_id: str,
) -> dict[str, Any]:
    """Return resolved runtime metadata for one invariant."""
    registry_path = policy_registry_path(repo_root)
    if registry_path.exists():
        try:
            payload = yaml_cache_service.load_yaml(registry_path)
        except (OSError, yaml.YAMLError):
            payload = None
        if isinstance(payload, dict):
            invariants = payload.get("core-invariants")
            if isinstance(invariants, dict):
                entry = invariants.get(invariant_id)
                if isinstance(entry, dict):
                    typed = entry.get("runtime_metadata_options")
                    if isinstance(typed, dict):
                        return dict(typed)
                    metadata = entry.get("metadata")
                    if isinstance(metadata, dict):
                        return metadata_runtime.decode_metadata_options_map(
                            metadata
                        )
    descriptor = load_core_invariant_descriptor(repo_root, invariant_id)
    if descriptor is None:
        return {}
    return metadata_runtime.decode_metadata_options_map(descriptor.metadata)


def resolve_core_invariants(
    repo_root: Path,
    *,
    config_payload: dict[str, object] | None = None,
) -> list[ResolvedCoreInvariant]:
    """Resolve core invariant descriptors, metadata, and registry payloads."""
    if config_payload is None:
        config_path = repo_root / "devcovenant" / "config.yaml"
        if not config_path.exists():
            raise ValueError(f"Missing config file: {config_path}")
        try:
            loaded = yaml_cache_service.load_yaml(config_path)
        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML in config file {config_path}: {exc}"
            ) from exc
        if not isinstance(loaded, dict):
            raise ValueError(
                f"Config file must be a YAML mapping: {config_path}"
            )
        config_payload = loaded
    context = metadata_runtime.build_metadata_context_from_payload(
        repo_root,
        dict(config_payload),
    )
    resolved: list[ResolvedCoreInvariant] = []
    for invariant_id in core_invariant_ids():
        location = resolve_core_invariant_location(repo_root, invariant_id)
        if location is None or not location.path.exists():
            raise ValueError(
                f"Core invariant script missing for `{invariant_id}`."
            )
        descriptor = load_core_invariant_descriptor(repo_root, invariant_id)
        if descriptor is None:
            raise ValueError(
                f"Core invariant descriptor missing for `{invariant_id}`."
            )
        order = list(descriptor.metadata.keys())
        values = {
            key: metadata_runtime.metadata_value_list(
                descriptor.metadata.get(key)
            )
            for key in order
        }
        bundle = metadata_runtime.resolve_policy_metadata_bundle(
            invariant_id,
            order,
            values,
            descriptor,
            context,
            custom_policy=False,
        )
        resolved_metadata = {
            key: str(bundle.string_map.get(key, "")).strip()
            for key in bundle.order
        }
        runtime_option_views = build_runtime_policy_option_views(
            bundle.decode_options(),
            runtime_core_invariant_config_overrides(repo_root, invariant_id),
        )
        severity = resolved_metadata.get("severity") or "critical"
        name = (
            resolved_metadata.get("name")
            or invariant_id.replace("-", " ").title()
        )
        resolved.append(
            ResolvedCoreInvariant(
                definition=CoreInvariantDefinition(
                    invariant_id=invariant_id,
                    name=name,
                    severity=severity,
                    description=str(descriptor.text or "").strip(),
                    raw_metadata=dict(resolved_metadata),
                ),
                module_path=str(location.path.relative_to(repo_root)).replace(
                    "\\", "/"
                ),
                descriptor_path=str(
                    location.descriptor_path.relative_to(repo_root)
                ).replace("\\", "/"),
                metadata_resolution=bundle.resolution_trace,
                metadata_warnings=list(bundle.warnings),
                runtime_option_views=runtime_option_views,
            )
        )
    return resolved


def core_invariants_registry_payload(
    repo_root: Path,
    *,
    config_payload: dict[str, object] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return the registry payload for all resolved core invariants."""
    payload: dict[str, dict[str, Any]] = {}
    for resolved in resolve_core_invariants(
        repo_root,
        config_payload=config_payload,
    ):
        definition = resolved.definition
        entry: dict[str, Any] = {
            "severity": definition.severity,
            "description": definition.name,
            "invariant_text": definition.description,
            "metadata": dict(definition.raw_metadata),
            "metadata_resolution": dict(resolved.metadata_resolution),
            "metadata_warnings": list(resolved.metadata_warnings),
            "runtime_metadata_options": dict(
                resolved.runtime_option_views.get(
                    "runtime_metadata_options", {}
                )
            ),
            "runtime_config_overrides": dict(
                resolved.runtime_option_views.get(
                    "runtime_config_overrides", {}
                )
            ),
            "runtime_effective_options": dict(
                resolved.runtime_option_views.get(
                    "runtime_effective_options", {}
                )
            ),
            "module_path": resolved.module_path,
            "descriptor_path": resolved.descriptor_path,
            "customizable": False,
        }
        payload[definition.invariant_id] = entry
    return payload


def render_core_invariants_block(registry_payload: dict[str, object]) -> str:
    """Render the AGENTS core-invariants block from registry payload."""
    if not isinstance(registry_payload, dict) or not registry_payload:
        return ""
    sections: list[str] = ["## DevCovenant Core Invariants"]
    for invariant_id in sorted(registry_payload):
        entry = registry_payload.get(invariant_id, {})
        if not isinstance(entry, dict):
            continue
        sections.append("")
        heading = (
            str(entry.get("description", "")).strip()
            or invariant_id.replace("-", " ").title()
        )
        sections.append(f"### {heading}")
        sections.append("")
        sections.append("```core-invariant-def")
        sections.append(f"id: {invariant_id}")
        severity = str(entry.get("severity", "critical")).strip()
        if not severity:
            severity = "critical"
        sections.append(f"severity: {severity}")
        sections.append("customizable: false")
        metadata = entry.get("metadata", {})
        if isinstance(metadata, dict):
            for key, raw_value in metadata.items():
                if str(key).strip() in {
                    "id",
                    "severity",
                    "enabled",
                    "custom",
                    "auto_fix",
                }:
                    continue
                if isinstance(raw_value, list):
                    cleaned = [
                        str(item).strip()
                        for item in raw_value
                        if str(item).strip()
                    ]
                    if not cleaned:
                        sections.append(f"{key}:")
                        continue
                    sections.append(f"{key}: {cleaned[0]}")
                    for item in cleaned[1:]:
                        sections.append(f"  {item}")
                    continue
                token = str(raw_value).strip()
                if token:
                    sections.append(f"{key}: {token}")
                else:
                    sections.append(f"{key}:")
        sections.append("```")
        description = str(entry.get("invariant_text", "")).strip()
        if description:
            sections.append("")
            sections.append(description)
    body = "\n".join(sections).rstrip()
    return f"{CORE_INVARIANTS_BEGIN}\n{body}\n{CORE_INVARIANTS_END}"


def run_core_invariant_checks(
    repo_root: Path,
    *,
    context: CheckContext,
    config_payload: dict[str, object] | None = None,
) -> tuple[list[Violation], int, int]:
    """Run all configured core invariant checks."""
    violations: list[Violation] = []
    passed_count = 0
    failed_count = 0
    for resolved in resolve_core_invariants(
        repo_root,
        config_payload=config_payload,
    ):
        invariant_id = resolved.definition.invariant_id
        checker = load_core_invariant_check_instance(repo_root, invariant_id)
        if checker is None:
            failed_count += 1
            violations.append(
                Violation(
                    policy_id=invariant_id,
                    severity="critical",
                    message=(
                        "Core invariant script is missing or could not be "
                        f"loaded for `{invariant_id}`."
                    ),
                    suggestion="Restore the core invariant module and rerun.",
                )
            )
            continue
        checker.set_options(
            resolved.runtime_option_views.get("runtime_metadata_options", {}),
            resolved.runtime_option_views.get("runtime_config_overrides", {}),
        )
        try:
            invariant_violations = checker.check(context)
        except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
            failed_count += 1
            violations.append(
                Violation(
                    policy_id=invariant_id,
                    severity="critical",
                    message=f"Core invariant execution failed: {error}",
                    suggestion=(
                        "Fix the invariant implementation/runtime error "
                        "before continuing."
                    ),
                )
            )
            continue
        violations.extend(invariant_violations)
        if invariant_violations:
            failed_count += 1
        else:
            passed_count += 1
    return violations, passed_count, failed_count
