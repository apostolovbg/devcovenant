"""Helpers for DevCovenant install/update manifest management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

DEV_COVENANT_DIR = "devcovenant"
MANIFEST_FILENAME = "manifest.json"
GLOBAL_REGISTRY_DIR = f"{DEV_COVENANT_DIR}/registry/global"
LOCAL_REGISTRY_DIR = f"{DEV_COVENANT_DIR}/registry/local"
MANIFEST_REL_PATH = f"{LOCAL_REGISTRY_DIR}/{MANIFEST_FILENAME}"
POLICY_REGISTRY_FILENAME = "policy_registry.yaml"
PROFILE_CATALOG_FILENAME = "profile_catalog.yaml"
POLICY_ASSETS_FILENAME = "policy_assets.yaml"
TEST_STATUS_FILENAME = "test_status.json"
LEGACY_MANIFEST_PATHS = [
    ".devcov/install_manifest.json",
    ".devcovenant/install_manifest.json",
    "devcovenant/manifest.json",
]

DEFAULT_CORE_DIRS = [
    "devcovenant",
    "devcovenant/core",
    "devcovenant/core/policies",
    "devcovenant/core/profiles",
    "devcovenant/core/profiles/global",
    "devcovenant/core/profiles/global/assets",
    GLOBAL_REGISTRY_DIR,
]

DEFAULT_CORE_FILES = [
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/config.yaml",
    "devcovenant/README.md",
    f"{GLOBAL_REGISTRY_DIR}/stock_policy_texts.yaml",
    f"{GLOBAL_REGISTRY_DIR}/policy_replacements.yaml",
    "devcovenant/core/cli_options.py",
    "devcovenant/core/profiles/global/assets/AGENTS.md",
    "devcovenant/core/profiles/global/assets/CONTRIBUTING.md",
    "devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt",
    "devcovenant/core/profiles/global/assets/VERSION",
    "devcovenant/core/profiles/global/assets/.pre-commit-config.yaml",
    "devcovenant/core/profiles/global/assets/.github/workflows/ci.yml",
    "devcovenant/core/profiles/global/assets/gitignore_base.txt",
    "devcovenant/core/profiles/global/assets/gitignore_os.txt",
    "devcovenant/core/profiles/global/assets/devcovenant/core/run_pre_commit.py",
    "devcovenant/core/profiles/global/assets/devcovenant/core/run_tests.py",
    "devcovenant/core/profiles/global/assets/devcovenant/core/update_test_status.py",
    "devcovenant/core/profiles/README.md",
    "devcovenant/core/policies/README.md",
    "devcovenant/core/run_pre_commit.py",
    "devcovenant/core/run_tests.py",
    "devcovenant/core/update_test_status.py",
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

DEFAULT_DOCS_CUSTOM: list[str] = []

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
    f"{LOCAL_REGISTRY_DIR}/{POLICY_REGISTRY_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{TEST_STATUS_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{MANIFEST_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{PROFILE_CATALOG_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{POLICY_ASSETS_FILENAME}",
]

DEFAULT_GENERATED_DIRS: list[str] = [LOCAL_REGISTRY_DIR]


def _registry_root(repo_root: Path, rel_dir: str) -> Path:
    return repo_root / rel_dir


def global_registry_root(repo_root: Path) -> Path:
    """Return the path to the global registry directory."""
    return _registry_root(repo_root, GLOBAL_REGISTRY_DIR)


def local_registry_root(repo_root: Path) -> Path:
    """Return the path to the local registry directory."""
    return _registry_root(repo_root, LOCAL_REGISTRY_DIR)


def policy_registry_path(repo_root: Path) -> Path:
    """Return the policy registry path inside the local registry."""
    return local_registry_root(repo_root) / POLICY_REGISTRY_FILENAME


def profile_catalog_path(repo_root: Path) -> Path:
    """Return the profile catalog path inside the local registry."""
    return local_registry_root(repo_root) / PROFILE_CATALOG_FILENAME


def policy_assets_path(repo_root: Path) -> Path:
    """Return the policy assets mapping path inside the local registry."""
    return local_registry_root(repo_root) / POLICY_ASSETS_FILENAME


def test_status_path(repo_root: Path) -> Path:
    """Return the test running status file path inside the local registry."""
    return local_registry_root(repo_root) / TEST_STATUS_FILENAME


def _utc_now() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(timezone.utc).isoformat()


def manifest_path(repo_root: Path) -> Path:
    """Return the manifest path for a repo."""
    return repo_root / MANIFEST_REL_PATH


def legacy_manifest_paths(repo_root: Path) -> list[Path]:
    """Return legacy manifest paths for a repo."""
    return [repo_root / rel for rel in LEGACY_MANIFEST_PATHS]


def build_manifest(
    *,
    options: Dict[str, Any] | None = None,
    installed: Dict[str, Any] | None = None,
    doc_blocks: list[str] | None = None,
    mode: str | None = None,
) -> Dict[str, Any]:
    """Build a default manifest payload."""
    manifest: Dict[str, Any] = {
        "schema_version": 2,
        "updated_at": _utc_now(),
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
            "catalog": [],
        },
        "policy_assets": {
            "global": [],
            "policies": {},
        },
    }
    if mode:
        manifest["mode"] = mode
    if options is not None:
        manifest["options"] = options
    if installed is not None:
        manifest["installed"] = installed
    if "notifications" not in manifest:
        manifest["notifications"] = []
    if doc_blocks is not None:
        manifest["doc_blocks"] = doc_blocks
    return manifest


def load_manifest(
    repo_root: Path, *, include_legacy: bool = False
) -> Dict[str, Any] | None:
    """Load the manifest if present, otherwise return None."""
    manifest = manifest_path(repo_root)
    if manifest.exists():
        return json.loads(manifest.read_text(encoding="utf-8"))
    if include_legacy:
        for legacy in legacy_manifest_paths(repo_root):
            if legacy.exists():
                legacy_data = json.loads(legacy.read_text(encoding="utf-8"))
                legacy_data["_legacy"] = True
                return legacy_data
    return None


def write_manifest(repo_root: Path, manifest: Dict[str, Any]) -> Path:
    """Write the manifest to disk and return its path."""
    path = manifest_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def ensure_manifest(repo_root: Path) -> Dict[str, Any] | None:
    """Create the manifest if missing and DevCovenant is installed."""
    path = manifest_path(repo_root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if not (repo_root / DEV_COVENANT_DIR).exists():
        return None
    manifest = build_manifest()
    write_manifest(repo_root, manifest)
    return manifest
