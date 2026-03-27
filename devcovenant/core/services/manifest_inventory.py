"""Tracked manifest inventory helpers for required repo structure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from devcovenant.core.runtime import registry as runtime_registry_module
from devcovenant.core.services import tracked_registry

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
    "devcovenant/builtin/profiles/global",
    "devcovenant/builtin/profiles/global/assets",
    "devcovenant/core",
    "devcovenant/core/contracts/invariants",
    "devcovenant/logs",
    REGISTRY_DIR,
]
DEFAULT_CORE_FILES = [
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/check.py",
    "devcovenant/gate.py",
    "devcovenant/run.py",
    "devcovenant/phase.py",
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
    "devcovenant/logs/README.md",
    f"{REGISTRY_DIR}/README.md",
    REGISTRY_REL_PATH,
    "devcovenant/builtin/profiles/global/assets/ci-and-test.yml",
    "devcovenant/builtin/profiles/global/assets/gitignore.yaml",
    "devcovenant/builtin/profiles/README.md",
    "devcovenant/builtin/policies/README.md",
    "devcovenant/core/contracts/invariant.py",
    "devcovenant/core/contracts/invariants/devcov_integrity_guard.yaml",
    "devcovenant/core/contracts/invariants/devcov_structure_guard.yaml",
    "devcovenant/core/contracts/invariants/devflow_run_gates.yaml",
    "devcovenant/core/services/core_invariant_block_refresh.py",
    "devcovenant/core/services/core_invariants.py",
    "devcovenant/core/services/integrity_validation.py",
    "devcovenant/core/services/manifest_inventory.py",
    "devcovenant/core/services/policy_commands.py",
    "devcovenant/core/services/policy_registry.py",
    "devcovenant/core/services/structure_validation.py",
    "devcovenant/core/services/tracked_registry.py",
    "devcovenant/core/services/workflow_contract.py",
    "devcovenant/core/flow/gate_status_validation.py",
    "devcovenant/core/flow/workflow_validation.py",
    "devcovenant/core/runtime/registry.py",
    "devcovenant/core/runtime/workflow_session.py",
]
DEFAULT_DOCS_CORE = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
]
DEFAULT_DOCS_OPTIONAL = [
    "SPEC.md",
    "PLAN.md",
]
DEFAULT_DOCS_CUSTOM: List[str] = []
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


def manifest_path(repo_root: Path) -> Path:
    """Return the tracked registry document path used for inventory data."""
    return tracked_registry.policy_registry_path(repo_root)


def build_manifest(
    *,
    options: Dict[str, Any] | None = None,
    installed: Dict[str, Any] | None = None,
    doc_blocks: List[str] | None = None,
) -> Dict[str, Any]:
    """Build a deterministic inventory payload for the tracked registry."""
    manifest: Dict[str, Any] = {
        "schema_version": 3,
        "core": {
            "dirs": list(DEFAULT_CORE_DIRS),
            "files": list(DEFAULT_CORE_FILES),
        },
        "docs": {
            "core": list(DEFAULT_DOCS_CORE),
            "optional": list(DEFAULT_DOCS_OPTIONAL),
            "custom": list(DEFAULT_DOCS_CUSTOM),
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
    manifest: Dict[str, Any],
) -> tuple[Dict[str, Any], bool]:
    """Normalize inventory sections to the current default inventories."""
    normalized = dict(manifest)
    changed = False
    defaults_manifest = build_manifest()
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
            payload = build_manifest()
        normalized, changed = _normalize_manifest_sections(payload)
        if changed:
            write_manifest(repo_root, normalized)
        return normalized
    if not (repo_root / tracked_registry.DEV_COVENANT_DIR).exists():
        return None
    manifest = build_manifest()
    write_manifest(repo_root, manifest)
    return manifest
