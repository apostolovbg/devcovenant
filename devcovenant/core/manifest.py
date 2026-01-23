"""Helpers for DevCovenant install/update manifest management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

DEV_COVENANT_DIR = "devcovenant"
MANIFEST_FILENAME = "manifest.json"
MANIFEST_REL_PATH = f"{DEV_COVENANT_DIR}/{MANIFEST_FILENAME}"
LEGACY_MANIFEST_PATHS = [
    ".devcov/install_manifest.json",
    ".devcovenant/install_manifest.json",
]

DEFAULT_CORE_DIRS = [
    "devcovenant",
    "devcovenant/core",
    "devcovenant/core/policy_scripts",
    "devcovenant/core/fixers",
    "devcovenant/core/templates",
    "devcovenant/core/templates/global",
    "devcovenant/core/templates/profiles",
    "devcovenant/core/templates/policies",
]

DEFAULT_CORE_FILES = [
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/config.yaml",
    "devcovenant/registry.json",
    "devcovenant/README.md",
    "devcovenant/manifest.json",
    "devcovenant/core/stock_policy_texts.yaml",
    "devcovenant/core/policy_replacements.yaml",
    "devcovenant/core/cli_options.py",
    "devcovenant/core/profile_catalog.yaml",
    "devcovenant/core/policy_assets.yaml",
    "devcovenant/core/templates/global/AGENTS.md",
    "devcovenant/core/templates/global/CONTRIBUTING.md",
    "devcovenant/core/templates/global/LICENSE_GPL-3.0.txt",
    "devcovenant/core/templates/global/VERSION",
    "devcovenant/core/templates/global/.pre-commit-config.yaml",
    "devcovenant/core/templates/global/.github/workflows/ci.yml",
    "devcovenant/core/templates/global/tools/run_pre_commit.py",
    "devcovenant/core/templates/global/tools/run_tests.py",
    "devcovenant/core/templates/global/tools/update_test_status.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
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
    "devcovenant/custom/policy_scripts",
    "devcovenant/custom/fixers",
    "devcovenant/custom/templates",
    "devcovenant/custom/templates/global",
    "devcovenant/custom/templates/profiles",
    "devcovenant/custom/templates/policies",
]

DEFAULT_CUSTOM_FILES: list[str] = []

DEFAULT_GENERATED_FILES = [
    "devcovenant/registry.json",
    "devcovenant/test_status.json",
]

DEFAULT_GENERATED_DIRS: list[str] = []


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
            "profiles": {},
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
