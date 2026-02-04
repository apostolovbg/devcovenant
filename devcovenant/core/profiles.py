"""Profile catalog helpers for DevCovenant."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import yaml

PROFILE_MANIFEST_FALLBACK = None
REGISTRY_CATALOG = Path("devcovenant/registry/local/profile_catalog.yaml")
CORE_PROFILE_ROOT = Path("devcovenant/core/profiles")
CUSTOM_PROFILE_ROOT = Path("devcovenant/custom/profiles")


def _utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _load_yaml(path: Path) -> dict:
    """Load YAML content from path when available."""
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _normalize_profile_name(raw: str) -> str:
    """Normalize a profile name for matching."""
    return str(raw or "").strip().lower()


def _iter_profile_dirs(root: Path) -> list[Path]:
    """Return profile directories beneath a root."""
    if not root.exists():
        return []
    return [entry for entry in root.iterdir() if entry.is_dir()]


def _relative_path(path: Path, base: Path) -> str:
    """Return a relative path when possible."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _profile_assets(profile_dir: Path, repo_root: Path) -> list[str]:
    """List asset files under a profile directory."""
    assets: list[str] = []
    assets_root = profile_dir / "assets"
    scan_root = assets_root if assets_root.exists() else profile_dir
    for entry in scan_root.rglob("*"):
        if not entry.is_file():
            continue
        if entry.name == f"{profile_dir.name}.yaml":
            continue
        assets.append(_relative_path(entry, repo_root))
    return sorted(assets)


def _manifest_path(profile_dir: Path) -> Path:
    """Return the preferred manifest path for a profile directory."""
    return profile_dir / f"{profile_dir.name}.yaml"


def load_profile(manifest_path: Path) -> dict:
    """Load a single profile manifest from disk."""
    return _load_yaml(manifest_path)


def discover_profiles(
    repo_root: Path,
    *,
    core_root: Path | None = None,
    custom_root: Path | None = None,
) -> Dict[str, Dict]:
    """Discover profiles from core/custom template roots."""
    catalog: Dict[str, Dict] = {}
    core_root = core_root or (repo_root / CORE_PROFILE_ROOT)
    custom_root = custom_root or (repo_root / CUSTOM_PROFILE_ROOT)

    for source, root in (("core", core_root), ("custom", custom_root)):
        for entry in _iter_profile_dirs(root):
            manifest_path = _manifest_path(entry)
            manifest = _load_yaml(manifest_path)
            meta = dict(manifest) if isinstance(manifest, dict) else {}
            name = _normalize_profile_name(meta.get("profile") or entry.name)
            if not name:
                continue
            meta.setdefault("profile", name)
            if "category" not in meta:
                meta["category"] = (
                    "custom" if source == "custom" else "unknown"
                )
            meta["source"] = source
            meta["path"] = _relative_path(entry, repo_root)
            meta["assets_available"] = _profile_assets(entry, repo_root)
            catalog[name] = meta
    return catalog


def build_profile_catalog(
    repo_root: Path,
    active_profiles: list[str] | None = None,
    *,
    core_root: Path | None = None,
    custom_root: Path | None = None,
) -> Dict[str, Dict]:
    """Build a profile catalog payload for registry output."""
    catalog = discover_profiles(
        repo_root, core_root=core_root, custom_root=custom_root
    )
    active = {
        _normalize_profile_name(name)
        for name in (active_profiles or [])
        if name
    }
    for name, meta in catalog.items():
        meta["active"] = name in active
    return {"generated_at": _utc_now(), "profiles": catalog}


def write_profile_catalog(repo_root: Path, catalog: Dict[str, Dict]) -> Path:
    """Write the profile catalog into the registry folder."""
    path = repo_root / REGISTRY_CATALOG
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(catalog, sort_keys=True, allow_unicode=False)
    path.write_text(payload, encoding="utf-8")
    return path


def _normalize_catalog(catalog: Dict[str, Dict]) -> Dict[str, Dict]:
    """Normalize profile catalogs that include a top-level profiles key."""
    if "profiles" in catalog and isinstance(catalog["profiles"], dict):
        return catalog["profiles"]
    return catalog


def load_profile_catalog(repo_root: Path) -> Dict[str, Dict]:
    """Load the merged profile catalog from registry or profile roots."""
    registry_path = repo_root / REGISTRY_CATALOG
    if registry_path.exists():
        catalog_data = _load_yaml(registry_path)
        if isinstance(catalog_data, dict) and catalog_data:
            return _normalize_catalog(catalog_data)
    return discover_profiles(repo_root)


def list_profiles(catalog: Dict[str, Dict]) -> List[str]:
    """Return a sorted list of profile names."""
    normalized = _normalize_catalog(catalog)
    return sorted(name for name in normalized.keys() if name)


def resolve_profile_suffixes(
    catalog: Dict[str, Dict], active_profiles: List[str]
) -> List[str]:
    """Return file suffixes associated with active profiles."""
    normalized_catalog = _normalize_catalog(catalog)
    suffixes: List[str] = []
    active = {
        _normalize_profile_name(name) for name in active_profiles if name
    }
    for name in active:
        meta = normalized_catalog.get(name, {})
        raw = meta.get("suffixes") or []
        for entry in raw:
            suffix_value = str(entry).strip()
            if not suffix_value or suffix_value == "__none__":
                continue
            suffixes.append(suffix_value)
    return suffixes


def resolve_profile_ignore_dirs(
    catalog: Dict[str, Dict], active_profiles: List[str]
) -> List[str]:
    """Return ignored directory names from active profiles."""
    normalized_catalog = _normalize_catalog(catalog)
    ignored: List[str] = []
    active = {
        _normalize_profile_name(name) for name in active_profiles if name
    }
    for name in active:
        meta = normalized_catalog.get(name, {})
        raw = meta.get("ignore_dirs") or []
        for entry in raw:
            dir_value = str(entry).strip()
            if not dir_value or dir_value == "__none__":
                continue
            ignored.append(dir_value)
    return ignored
