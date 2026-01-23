"""Profile catalog helpers for DevCovenant."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

_PROFILE_CATALOG_FILE = "profile_catalog.yaml"


def _load_yaml(path: Path) -> dict:
    """Load YAML content from path when available."""
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def load_profile_catalog(repo_root: Path) -> Dict[str, Dict]:
    """Load the merged profile catalog from core and custom sources."""
    catalog: Dict[str, Dict] = {}
    core_path = (
        repo_root / "devcovenant" / "core" / _PROFILE_CATALOG_FILE
    )
    core_data = _load_yaml(core_path)
    for name, meta in (core_data.get("profiles") or {}).items():
        catalog[str(name).strip().lower()] = dict(meta or {})

    custom_path = (
        repo_root / "devcovenant" / "custom" / _PROFILE_CATALOG_FILE
    )
    custom_data = _load_yaml(custom_path)
    for name, meta in (custom_data.get("profiles") or {}).items():
        catalog[str(name).strip().lower()] = dict(meta or {})

    custom_dir = (
        repo_root
        / "devcovenant"
        / "custom"
        / "templates"
        / "profiles"
    )
    if custom_dir.exists():
        for entry in custom_dir.iterdir():
            if entry.is_dir():
                catalog.setdefault(entry.name.strip().lower(), {})

    return catalog


def list_profiles(catalog: Dict[str, Dict]) -> List[str]:
    """Return a sorted list of profile names."""
    return sorted(name for name in catalog.keys() if name)


def resolve_profile_suffixes(
    catalog: Dict[str, Dict], active_profiles: List[str]
) -> List[str]:
    """Return file suffixes associated with active profiles."""
    suffixes: List[str] = []
    normalized = {
        str(name).strip().lower()
        for name in active_profiles
        if name
    }
    for name in normalized:
        meta = catalog.get(name, {})
        raw = meta.get("suffixes") or []
        for entry in raw:
            suffix_value = str(entry).strip()
            if not suffix_value or suffix_value == "__none__":
                continue
            suffixes.append(suffix_value)
    return suffixes
