"""Helpers for policy loading and runtime-action dispatch."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

from devcovenant.core.contracts.policy import CheckContext, PolicyCheck
from devcovenant.core.services import metadata as metadata_runtime
from devcovenant.core.services.registry import (
    load_policy_descriptor,
    policy_registry_path,
    resolve_script_location,
)


def load_policy_check_instance(
    repo_root: Path, policy_id: str
) -> PolicyCheck | None:
    """Load one policy script and return its `PolicyCheck` instance."""
    repo_root = Path(repo_root).resolve()
    location = resolve_script_location(repo_root, policy_id)
    if location is None:
        return None

    spec = importlib.util.spec_from_file_location(
        location.module, location.path
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, PolicyCheck)
            and attr is not PolicyCheck
        ):
            return attr()
    return None


def runtime_policy_config_overrides(
    repo_root: Path, policy_id: str
) -> dict[str, Any]:
    """Return merged config overrides for one policy runtime action."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, dict):
        return {}
    context = CheckContext(repo_root=repo_root, config=payload)
    return context.get_policy_config(policy_id)


def runtime_policy_metadata_options(
    repo_root: Path,
    policy_id: str,
    *,
    descriptor_loader: Callable[[Path, str], object | None] = (
        load_policy_descriptor
    ),
    registry_path_resolver: Callable[[Path], Path] = policy_registry_path,
) -> dict[str, Any]:
    """Return decoded runtime metadata options for one policy action."""
    registry_path = registry_path_resolver(repo_root)
    if registry_path.exists():
        try:
            registry_payload = yaml.safe_load(
                registry_path.read_text(encoding="utf-8")
            )
        except (OSError, yaml.YAMLError):
            registry_payload = None
        if isinstance(registry_payload, dict):
            policies = registry_payload.get("policies")
            if isinstance(policies, dict):
                entry = policies.get(policy_id)
                if isinstance(entry, dict):
                    metadata = entry.get("metadata")
                    if isinstance(metadata, dict):
                        return metadata_runtime.decode_metadata_options_map(
                            metadata
                        )
    descriptor = descriptor_loader(repo_root, policy_id)
    descriptor_metadata = getattr(descriptor, "metadata", None)
    if isinstance(descriptor_metadata, dict):
        return metadata_runtime.decode_metadata_options_map(
            descriptor_metadata
        )
    return {}


def run_policy_runtime_action(
    repo_root: Path,
    *,
    policy_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
    checker_loader: Callable[[Path, str], PolicyCheck | None] = (
        load_policy_check_instance
    ),
    metadata_loader: Callable[[Path, str], dict[str, Any]] = (
        runtime_policy_metadata_options
    ),
    config_loader: Callable[[Path, str], dict[str, Any]] = (
        runtime_policy_config_overrides
    ),
) -> Any:
    """Run one policy-owned runtime action through the policy contract."""
    repo_root = Path(repo_root).resolve()
    checker = checker_loader(repo_root, policy_id)
    if checker is None:
        raise ValueError(
            f"Policy script not found for runtime action: `{policy_id}`."
        )
    checker.set_options(
        metadata_loader(repo_root, policy_id),
        config_loader(repo_root, policy_id),
    )
    return checker.run_runtime_action(
        action,
        repo_root=repo_root,
        payload=payload or {},
    )
