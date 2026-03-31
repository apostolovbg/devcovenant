"""Tracked manifest inventory helpers for required repo structure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from devcovenant.core.runtime import registry as runtime_registry_module
from devcovenant.core.services import managed_docs as managed_docs_service
from devcovenant.core.services import tracked_registry
from devcovenant.core.services import yaml_cache as yaml_cache_service

REGISTRY_DIR = tracked_registry.REGISTRY_DIR
REGISTRY_REL_PATH = tracked_registry.REGISTRY_REL_PATH
RUNTIME_REGISTRY_DIR = runtime_registry_module.RUNTIME_REGISTRY_DIR
GATE_STATUS_FILENAME = runtime_registry_module.GATE_STATUS_FILENAME
WORKFLOW_SESSION_FILENAME = runtime_registry_module.WORKFLOW_SESSION_FILENAME
LATEST_RUNTIME_FILENAME = runtime_registry_module.LATEST_RUNTIME_FILENAME
SESSION_SNAPSHOT_FILENAME = runtime_registry_module.SESSION_SNAPSHOT_FILENAME

DEFAULT_CORE_DIRS = [
    "devcovenant",
    "devcovenant/builtin",
    "devcovenant/builtin/policies",
    "devcovenant/builtin/profiles",
    "devcovenant/builtin/profiles/github",
    "devcovenant/builtin/profiles/github/assets",
    "devcovenant/builtin/profiles/global",
    "devcovenant/builtin/profiles/global/assets",
    "devcovenant/core",
    "devcovenant/licenses",
    "devcovenant/logs",
    REGISTRY_DIR,
]
DEFAULT_SCAN_EXCLUDED_CORE_PATHS = [
    "devcovenant/core",
    "devcovenant/builtin",
    "devcovenant/licenses",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/asset.py",
    "devcovenant/cli.py",
    "devcovenant/check.py",
    "devcovenant/clean.py",
    "devcovenant/gate.py",
    "devcovenant/run.py",
    "devcovenant/policy.py",
    "devcovenant/install.py",
    "devcovenant/deploy.py",
    "devcovenant/upgrade.py",
    "devcovenant/refresh.py",
    "devcovenant/uninstall.py",
    "devcovenant/undeploy.py",
    "devcovenant/requirements.lock",
    "devcovenant/registry",
]
DEFAULT_CORE_FILES = [
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/asset.py",
    "devcovenant/cli.py",
    "devcovenant/check.py",
    "devcovenant/gate.py",
    "devcovenant/run.py",
    "devcovenant/policy.py",
    "devcovenant/install.py",
    "devcovenant/deploy.py",
    "devcovenant/upgrade.py",
    "devcovenant/refresh.py",
    "devcovenant/uninstall.py",
    "devcovenant/undeploy.py",
    "devcovenant/config.yaml",
    "devcovenant/README.md",
    "devcovenant/VERSION",
    "devcovenant/requirements.lock",
    "devcovenant/licenses/README.md",
    "devcovenant/licenses/THIRD_PARTY_LICENSES.md",
    "devcovenant/logs/README.md",
    f"{REGISTRY_DIR}/README.md",
    REGISTRY_REL_PATH,
    "devcovenant/builtin/profiles/github/assets/ci.yml",
    "devcovenant/builtin/profiles/global/assets/gitignore.yaml",
    "devcovenant/builtin/profiles/README.md",
    "devcovenant/builtin/policies/README.md",
    "devcovenant/core/lib/agents_blocks.py",
    "devcovenant/core/services/asset_materialization.py",
    "devcovenant/core/services/integrity_validation.py",
    "devcovenant/core/services/manifest_inventory.py",
    "devcovenant/core/services/policy_registry.py",
    "devcovenant/core/services/structure_validation.py",
    "devcovenant/core/services/tracked_registry.py",
    "devcovenant/core/flow/gate_status_validation.py",
    "devcovenant/core/flow/workflow_contract.py",
    "devcovenant/core/flow/workflow_validation.py",
    "devcovenant/core/runtime/policy_commands.py",
    "devcovenant/core/runtime/policy_runtime_actions.py",
    "devcovenant/core/runtime/registry.py",
    "devcovenant/core/runtime/workflow_session.py",
]
DEFAULT_AVAILABLE_DOCS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SPEC.md",
    "PLAN.md",
    "SECURITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
    "LICENSE",
    "devcovenant/README.md",
]
DEFAULT_ENABLED_DOCS = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "devcovenant/README.md",
]
DEFAULT_CUSTOM_DIRS = [
    "devcovenant/custom",
    "devcovenant/custom/policies",
    "devcovenant/custom/profiles",
]
DEFAULT_CUSTOM_FILES = [
    "devcovenant/custom/profiles/README.md",
    "devcovenant/custom/policies/README.md",
]
DEFAULT_GENERATED_FILES = [
    f"{RUNTIME_REGISTRY_DIR}/{GATE_STATUS_FILENAME}",
    f"{RUNTIME_REGISTRY_DIR}/{LATEST_RUNTIME_FILENAME}",
    f"{RUNTIME_REGISTRY_DIR}/{WORKFLOW_SESSION_FILENAME}",
]
DEFAULT_GENERATED_DIRS: List[str] = [RUNTIME_REGISTRY_DIR]


def default_scan_excluded_core_paths() -> list[str]:
    """Return the canonical core paths hidden from normal repo scans."""
    return list(DEFAULT_SCAN_EXCLUDED_CORE_PATHS)


def manifest_path(repo_root: Path) -> Path:
    """Return the tracked registry document path used for inventory data."""
    return tracked_registry.policy_registry_path(repo_root)


def build_manifest(
    *,
    options: Dict[str, Any] | None = None,
    installed: Dict[str, Any] | None = None,
    doc_blocks: List[str] | None = None,
    available_docs: List[str] | None = None,
    enabled_docs: List[str] | None = None,
) -> Dict[str, Any]:
    """Build a deterministic inventory payload for the tracked registry."""
    manifest: Dict[str, Any] = {
        "schema_version": 3,
        "core": {
            "dirs": list(DEFAULT_CORE_DIRS),
            "files": list(DEFAULT_CORE_FILES),
        },
        "docs": {
            "available": list(available_docs or DEFAULT_AVAILABLE_DOCS),
            "enabled": list(enabled_docs or DEFAULT_ENABLED_DOCS),
        },
        "custom": {
            "dirs": list(DEFAULT_CUSTOM_DIRS),
            "files": list(DEFAULT_CUSTOM_FILES),
        },
        "generated": {
            "dirs": list(DEFAULT_GENERATED_DIRS),
            "files": list(DEFAULT_GENERATED_FILES),
        },
        "profiles": {
            "active": [],
            "resolved_pre_commit_hooks": [],
        },
    }
    if options is not None:
        manifest["options"] = options
    if installed is not None:
        manifest["installed"] = installed
    if doc_blocks is not None:
        manifest["doc_blocks"] = doc_blocks
    return manifest


def _resolved_docs_manifest(repo_root: Path) -> dict[str, list[str]]:
    """Return the available/enabled managed-doc inventory for one repo."""
    available_docs = list(DEFAULT_AVAILABLE_DOCS)
    enabled_docs = list(DEFAULT_ENABLED_DOCS)

    try:
        entries = managed_docs_service.managed_doc_descriptor_entries(
            repo_root
        )
    except ValueError:
        entries = []
    if entries:
        available_docs = [str(entry["doc"]) for entry in entries]

    config_path = repo_root / "devcovenant" / "config.yaml"
    if config_path.exists():
        try:
            config_payload = yaml_cache_service.load_yaml(config_path)
        except (OSError, yaml.YAMLError):
            config_payload = {}
        if isinstance(config_payload, dict):
            try:
                enabled_docs = managed_docs_service.managed_docs_from_config(
                    config_payload
                )
            except ValueError:
                pass

    return {
        "available": available_docs,
        "enabled": enabled_docs,
    }


def load_manifest(repo_root: Path) -> Dict[str, Any] | None:
    """Load the tracked inventory section if present, otherwise return None."""
    path = manifest_path(repo_root)
    payload = tracked_registry.load_registry_document(path)
    inventory = payload.get("inventory", {})
    return (
        dict(inventory) if isinstance(inventory, dict) and inventory else None
    )


def write_manifest(repo_root: Path, manifest: Dict[str, Any]) -> Path:
    """Write inventory data into the tracked registry document."""
    path = manifest_path(repo_root)
    payload = tracked_registry.load_registry_document(path)
    payload["inventory"] = dict(manifest)
    return tracked_registry.write_registry_document(path, payload)


def _normalize_manifest_sections(
    repo_root: Path,
    manifest: Dict[str, Any],
) -> tuple[Dict[str, Any], bool]:
    """Normalize inventory sections to the current default inventories."""
    normalized = dict(manifest)
    changed = False
    docs_manifest = _resolved_docs_manifest(repo_root)
    defaults_manifest = build_manifest(
        available_docs=docs_manifest["available"],
        enabled_docs=docs_manifest["enabled"],
    )
    for section_name in ("core", "docs", "custom", "generated"):
        defaults = defaults_manifest.get(section_name, {})
        current = normalized.get(section_name, {})
        if not isinstance(defaults, dict):
            continue
        if not isinstance(current, dict):
            normalized[section_name] = defaults
            changed = True
            continue
        merged = dict(current)
        for key, default_value in defaults.items():
            target_value = (
                list(default_value)
                if isinstance(default_value, list)
                else default_value
            )
            if merged.get(key) != target_value:
                merged[key] = target_value
                changed = True
        normalized[section_name] = merged
    return normalized, changed


def ensure_manifest(repo_root: Path) -> Dict[str, Any] | None:
    """Create the tracked inventory section when missing."""
    path = manifest_path(repo_root)
    if path.exists():
        payload = load_manifest(repo_root)
        if payload is None:
            docs_manifest = _resolved_docs_manifest(repo_root)
            payload = build_manifest(
                available_docs=docs_manifest["available"],
                enabled_docs=docs_manifest["enabled"],
            )
        normalized, changed = _normalize_manifest_sections(repo_root, payload)
        if changed:
            write_manifest(repo_root, normalized)
        return normalized
    if not (repo_root / tracked_registry.DEV_COVENANT_DIR).exists():
        return None
    docs_manifest = _resolved_docs_manifest(repo_root)
    manifest = build_manifest(
        available_docs=docs_manifest["available"],
        enabled_docs=docs_manifest["enabled"],
    )
    write_manifest(repo_root, manifest)
    return manifest
