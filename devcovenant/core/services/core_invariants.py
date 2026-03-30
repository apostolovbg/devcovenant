"""Descriptor and registry helpers for DevCovenant core invariants."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

import devcovenant.core.services.profile_registry as profile_runtime
from devcovenant.core.contracts.invariant import (
    CoreInvariantCheck,
    CoreInvariantDefinition,
)
from devcovenant.core.contracts.policy import CheckContext, Violation
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.policy_registry import PolicyDescriptor
from devcovenant.core.services.tracked_registry import policy_registry_path


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


_CORE_INVARIANT_LOCATIONS = {
    "devcov-integrity-guard": {
        "module": "devcovenant.core.services.integrity_validation",
        "script_path": ("devcovenant/core/services/integrity_validation.py"),
    },
    "devcov-structure-guard": {
        "module": "devcovenant.core.services.structure_validation",
        "script_path": ("devcovenant/core/services/structure_validation.py"),
    },
    "devflow-run-gates": {
        "module": "devcovenant.core.flow.workflow_validation",
        "script_path": "devcovenant/core/flow/workflow_validation.py",
    },
}


def core_invariant_ids() -> list[str]:
    """Return the canonical ordered core invariant ids."""
    return sorted(_CORE_INVARIANT_LOCATIONS)


def _script_name(invariant_id: str) -> str:
    """Return the filesystem-safe module stem for one invariant id."""
    return invariant_id.replace("-", "_")


def resolve_core_invariant_location(
    repo_root: Path,
    invariant_id: str,
) -> CoreInvariantLocation | None:
    """Return script/descriptor locations for one invariant id."""
    location = _CORE_INVARIANT_LOCATIONS.get(invariant_id)
    if not location:
        return None
    module_name = str(location.get("module") or "").strip()
    script_name = _script_name(invariant_id)
    script_path = repo_root / str(location.get("script_path") or "").strip()
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


def _load_config_payload(repo_root: Path) -> dict[str, object]:
    """Load `devcovenant/config.yaml` into a dictionary."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        raise ValueError(f"Missing config file: {config_path}")
    try:
        payload = yaml_cache_service.load_yaml(config_path)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in config file {config_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must be a YAML mapping: {config_path}")
    return payload


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


def _normalize_invariant_metadata_values(raw_value: object) -> list[str]:
    """Normalize one invariant metadata value into a string list."""
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        cleaned: list[str] = []
        for entry in raw_value:
            token = str(entry or "").strip()
            if token:
                cleaned.append(token)
        return cleaned
    token = str(raw_value or "").strip()
    return [token] if token else []


def _split_metadata_tokens(raw_values: list[str]) -> list[str]:
    """Split comma-delimited metadata values into a flat string list."""
    items: list[str] = []
    for entry in raw_values:
        for part in str(entry or "").split(","):
            token = part.strip()
            if token:
                items.append(token)
    return items


def _decode_invariant_option_value(raw_value: object) -> Any:
    """Decode one invariant option into a common scalar/list shape."""
    if raw_value is None:
        return ""
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, float):
        return raw_value
    if isinstance(raw_value, (list, tuple, set)):
        return _split_metadata_tokens(
            [str(entry or "").strip() for entry in raw_value]
        )
    text = str(raw_value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if "," in text:
        return _split_metadata_tokens([text])
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _decode_invariant_options(
    raw_metadata: dict[str, object],
) -> dict[str, Any]:
    """Decode an invariant metadata map into typed runtime options."""
    return {
        str(key): _decode_invariant_option_value(value)
        for key, value in raw_metadata.items()
        if str(key).strip()
    }


def _option_value_is_empty(candidate: Any) -> bool:
    """Return True when a runtime option value is an empty placeholder."""
    if candidate is None:
        return True
    if isinstance(candidate, str):
        return candidate.strip() == ""
    if isinstance(candidate, dict):
        return not candidate
    if isinstance(candidate, (list, tuple, set)):
        if not candidate:
            return True
        return all(not str(item).strip() for item in candidate)
    return False


def _build_runtime_option_views(
    metadata_options: dict[str, Any],
    config_overrides: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build registry/debug views for invariant runtime options."""
    effective: dict[str, Any] = {}
    for key in list(metadata_options.keys()) + list(config_overrides.keys()):
        if key in effective:
            continue
        if key in config_overrides and not _option_value_is_empty(
            config_overrides[key]
        ):
            effective[key] = config_overrides[key]
            continue
        if key in metadata_options and not _option_value_is_empty(
            metadata_options[key]
        ):
            effective[key] = metadata_options[key]
    return {
        "runtime_metadata_options": dict(metadata_options),
        "runtime_config_overrides": dict(config_overrides),
        "runtime_effective_options": effective,
    }


def _record_resolution_values(
    trace: dict[str, dict[str, Any]],
    key: str,
    layer: str,
    values: list[str],
    *,
    behavior: str,
) -> None:
    """Record one invariant metadata resolution layer."""
    trace.setdefault(key, {})[layer] = {
        "values": [str(entry) for entry in values if str(entry).strip()],
        "behavior": behavior,
    }


def _record_effective_resolution(
    trace: dict[str, dict[str, Any]],
    key: str,
    values: list[str],
) -> None:
    """Record the final effective values for one invariant metadata key."""
    trace.setdefault(key, {})["effective"] = {
        "values": [str(entry) for entry in values if str(entry).strip()]
    }


def _merge_invariant_metadata_values(
    current: list[str],
    incoming: list[str],
) -> list[str]:
    """Append metadata values with de-duplication preserving order."""
    merged: list[str] = list(current)
    for entry in incoming:
        if entry not in merged:
            merged.append(entry)
    return merged


def _resolve_invariant_descriptor_metadata(
    repo_root: Path,
    config_payload: dict[str, object],
    invariant_id: str,
    descriptor: PolicyDescriptor,
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """Resolve invariant metadata from descriptor text and profile overlays."""
    values: dict[str, list[str]] = {}
    trace: dict[str, dict[str, Any]] = {}
    for key, raw_value in descriptor.metadata.items():
        key_name = str(key).strip()
        if not key_name:
            continue
        normalized = _normalize_invariant_metadata_values(raw_value)
        values[key_name] = normalized
        _record_resolution_values(
            trace,
            key_name,
            "descriptor",
            normalized,
            behavior="base",
        )

    active_profiles = profile_runtime.parse_active_profiles(
        config_payload,
        include_global=True,
    )
    registry = profile_runtime.load_profile_registry(repo_root)
    for profile_name in active_profiles:
        profile_payload = registry.get(profile_name)
        if not isinstance(profile_payload, dict):
            continue
        overlays = profile_payload.get("core_invariant_overlays")
        if not isinstance(overlays, dict):
            continue
        overlay = overlays.get(invariant_id)
        if not isinstance(overlay, dict):
            continue
        for key, raw_value in overlay.items():
            key_name = str(key).strip()
            if not key_name:
                continue
            normalized = _normalize_invariant_metadata_values(raw_value)
            if isinstance(raw_value, list):
                values[key_name] = _merge_invariant_metadata_values(
                    values.get(key_name, []), normalized
                )
                behavior = "append"
            else:
                values[key_name] = list(normalized)
                behavior = "replace"
            _record_resolution_values(
                trace,
                key_name,
                f"profile:{profile_name}",
                normalized,
                behavior=behavior,
            )

    rendered: dict[str, str] = {}
    for key, entries in values.items():
        rendered[key] = ", ".join(
            entry for entry in entries if str(entry).strip()
        )
        _record_effective_resolution(trace, key, entries)
    return rendered, trace


def _dedicated_core_invariant_config_overrides(
    payload: dict[str, Any],
    invariant_id: str,
) -> dict[str, Any]:
    """Return dedicated config overrides for one core invariant."""
    paths = payload.get("paths")
    if not isinstance(paths, dict):
        paths = {}
    workflow = payload.get("workflow")
    if not isinstance(workflow, dict):
        workflow = {}
    overrides: dict[str, Any] = {}
    if invariant_id == "devcov-integrity-guard":
        for key in ("policy_definitions", "registry_file", "gate_status_file"):
            if key in paths:
                overrides[key] = _normalize_config_override_value(
                    key, paths[key]
                )
        return overrides
    if invariant_id == "devflow-run-gates":
        for key in ("gate_status_file", "workflow_session_file"):
            if key in paths:
                overrides[key] = _normalize_config_override_value(
                    key, paths[key]
                )
        for key in ("pre_commit_command", "skipped_globs"):
            if key in workflow:
                overrides[key] = _normalize_config_override_value(
                    key, workflow[key]
                )
        return overrides
    return overrides


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
    overrides = _dedicated_core_invariant_config_overrides(
        payload, invariant_id
    )
    if overrides:
        return overrides
    return {}


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
                        return _decode_invariant_options(metadata)
    config_payload = _load_config_payload_or_empty(repo_root)
    descriptor = load_core_invariant_descriptor(repo_root, invariant_id)
    if descriptor is None:
        return {}
    resolved_metadata, _ = _resolve_invariant_descriptor_metadata(
        repo_root,
        config_payload,
        invariant_id,
        descriptor,
    )
    return _decode_invariant_options(resolved_metadata)


def resolve_core_invariants(
    repo_root: Path,
    *,
    config_payload: dict[str, object] | None = None,
) -> list[ResolvedCoreInvariant]:
    """Resolve core invariant descriptors, metadata, and registry payloads."""
    if config_payload is None:
        config_payload = _load_config_payload(repo_root)
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
        resolved_metadata, metadata_trace = (
            _resolve_invariant_descriptor_metadata(
                repo_root,
                dict(config_payload),
                invariant_id,
                descriptor,
            )
        )
        runtime_option_views = _build_runtime_option_views(
            _decode_invariant_options(resolved_metadata),
            runtime_core_invariant_config_overrides(repo_root, invariant_id),
        )
        name = (
            resolved_metadata.get("name")
            or invariant_id.replace("-", " ").title()
        )
        resolved.append(
            ResolvedCoreInvariant(
                definition=CoreInvariantDefinition(
                    invariant_id=invariant_id,
                    name=name,
                    description=str(descriptor.text or "").strip(),
                    raw_metadata=dict(resolved_metadata),
                ),
                module_path=str(location.path.relative_to(repo_root)).replace(
                    "\\", "/"
                ),
                descriptor_path=str(
                    location.descriptor_path.relative_to(repo_root)
                ).replace("\\", "/"),
                metadata_resolution=metadata_trace,
                metadata_warnings=[],
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
        }
        payload[definition.invariant_id] = entry
    return payload


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
