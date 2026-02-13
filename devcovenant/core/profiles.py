"""Profile registry helpers for DevCovenant."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import yaml

PROFILE_MANIFEST_FALLBACK = None
REGISTRY_PROFILE = Path("devcovenant/registry/local/profile_registry.yaml")
CORE_PROFILE_ROOT = Path("devcovenant/core/profiles")
CUSTOM_PROFILE_ROOT = Path("devcovenant/custom/profiles")
LANGUAGE_CATEGORY = "language"


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


def _normalize_translator_extensions(
    raw_value: object,
    *,
    profile_name: str,
    translator_id: str,
    source_label: str,
) -> list[str]:
    """Normalize translator extension lists."""
    if not isinstance(raw_value, list):
        raise ValueError(
            f"{source_label} translator '{translator_id}' in profile "
            f"'{profile_name}' must define extensions as a list."
        )
    normalized: list[str] = []
    for raw_entry in raw_value:
        token = str(raw_entry or "").strip().lower()
        if not token:
            continue
        if not token.startswith("."):
            token = f".{token}"
        if token not in normalized:
            normalized.append(token)
    if not normalized:
        raise ValueError(
            f"{source_label} translator '{translator_id}' in profile "
            f"'{profile_name}' must declare at least one extension."
        )
    return normalized


def _normalize_translator_strategy(
    raw_value: object,
    *,
    profile_name: str,
    translator_id: str,
    section: str,
    source_label: str,
) -> dict[str, object]:
    """Normalize a translator strategy block."""
    if not isinstance(raw_value, dict):
        raise ValueError(
            f"{source_label} translator '{translator_id}' in profile "
            f"'{profile_name}' must define {section} as a mapping."
        )
    normalized = dict(raw_value)
    strategy = str(normalized.get("strategy", "")).strip().lower()
    entrypoint = str(normalized.get("entrypoint", "")).strip()
    if not strategy:
        raise ValueError(
            f"{source_label} translator '{translator_id}' in profile "
            f"'{profile_name}' must define {section}.strategy."
        )
    if not entrypoint:
        raise ValueError(
            f"{source_label} translator '{translator_id}' in profile "
            f"'{profile_name}' must define {section}.entrypoint."
        )
    normalized["strategy"] = strategy
    normalized["entrypoint"] = entrypoint
    return normalized


def _normalize_profile_translators(
    profile_name: str,
    profile_meta: dict[str, object],
    *,
    source_label: str,
) -> None:
    """Normalize translator declarations for one profile."""
    category = str(profile_meta.get("category", "")).strip().lower()
    raw_translators = profile_meta.get("translators")
    if raw_translators in (None, "__none__"):
        return
    if category != LANGUAGE_CATEGORY:
        raise ValueError(
            f"{source_label} profile '{profile_name}' declares translators "
            "but is not category: language."
        )
    if not isinstance(raw_translators, list):
        raise ValueError(
            f"{source_label} profile '{profile_name}' must define "
            "translators as a list."
        )
    normalized_entries: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for raw_entry in raw_translators:
        if not isinstance(raw_entry, dict):
            raise ValueError(
                f"{source_label} profile '{profile_name}' has non-mapping "
                "translator entries."
            )
        entry = dict(raw_entry)
        translator_id = str(entry.get("id", "")).strip().lower()
        if not translator_id:
            raise ValueError(
                f"{source_label} profile '{profile_name}' has a translator "
                "without id."
            )
        if translator_id in seen_ids:
            raise ValueError(
                f"{source_label} profile '{profile_name}' has duplicate "
                f"translator id '{translator_id}'."
            )
        seen_ids.add(translator_id)
        entry["id"] = translator_id
        entry["extensions"] = _normalize_translator_extensions(
            entry.get("extensions"),
            profile_name=profile_name,
            translator_id=translator_id,
            source_label=source_label,
        )
        entry["can_handle"] = _normalize_translator_strategy(
            entry.get("can_handle"),
            profile_name=profile_name,
            translator_id=translator_id,
            section="can_handle",
            source_label=source_label,
        )
        entry["translate"] = _normalize_translator_strategy(
            entry.get("translate"),
            profile_name=profile_name,
            translator_id=translator_id,
            section="translate",
            source_label=source_label,
        )
        normalized_entries.append(entry)
    profile_meta["translators"] = normalized_entries


def _normalize_registry_profiles(
    registry: Dict[str, Dict], *, source_label: str
) -> Dict[str, Dict]:
    """Validate and normalize profile registry entries in place."""
    for profile_name, raw_meta in list(registry.items()):
        if not isinstance(raw_meta, dict):
            registry[profile_name] = {}
            continue
        meta = dict(raw_meta)
        category = str(meta.get("category", "")).strip().lower()
        if not category:
            category = "unknown"
        meta["category"] = category
        _normalize_profile_translators(
            profile_name,
            meta,
            source_label=source_label,
        )
        registry[profile_name] = meta
    return registry


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
    registry: Dict[str, Dict] = {}
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
            _normalize_profile_translators(
                name,
                meta,
                source_label=str(manifest_path),
            )
            meta["source"] = source
            meta["path"] = _relative_path(entry, repo_root)
            meta["assets_available"] = _profile_assets(entry, repo_root)
            registry[name] = meta
    return registry


def build_profile_registry(
    repo_root: Path,
    active_profiles: list[str] | None = None,
    *,
    core_root: Path | None = None,
    custom_root: Path | None = None,
) -> Dict[str, Dict]:
    """Build a profile registry payload for registry output."""
    registry = discover_profiles(
        repo_root, core_root=core_root, custom_root=custom_root
    )
    active = {
        _normalize_profile_name(name)
        for name in (active_profiles or [])
        if name
    }
    for name, meta in registry.items():
        meta["active"] = name in active
    return {"generated_at": _utc_now(), "profiles": registry}


def write_profile_registry(repo_root: Path, registry: Dict[str, Dict]) -> Path:
    """Write the profile registry into the registry folder."""
    path = repo_root / REGISTRY_PROFILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(registry, sort_keys=True, allow_unicode=False)
    path.write_text(payload, encoding="utf-8")
    return path


def _normalize_registry(registry: Dict[str, Dict]) -> Dict[str, Dict]:
    """Normalize profile registries that include a top-level profiles key."""
    if "profiles" in registry and isinstance(registry["profiles"], dict):
        return _normalize_registry_profiles(
            registry["profiles"], source_label=str(REGISTRY_PROFILE)
        )
    return _normalize_registry_profiles(
        registry, source_label="profile-registry"
    )


def load_profile_registry(repo_root: Path) -> Dict[str, Dict]:
    """Load the merged profile registry from registry or profile roots."""
    registry_path = repo_root / REGISTRY_PROFILE
    if registry_path.exists():
        registry_data = _load_yaml(registry_path)
        if isinstance(registry_data, dict) and registry_data:
            return _normalize_registry(registry_data)
    return discover_profiles(repo_root)


def list_profiles(registry: Dict[str, Dict]) -> List[str]:
    """Return a sorted list of profile names."""
    normalized = _normalize_registry(registry)
    return sorted(name for name in normalized.keys() if name)


def resolve_profile_suffixes(
    registry: Dict[str, Dict], active_profiles: List[str]
) -> List[str]:
    """Return file suffixes associated with active profiles."""
    normalized_registry = _normalize_registry(registry)
    suffixes: List[str] = []
    active_names: List[str] = []
    for profile_name in active_profiles:
        normalized_name = _normalize_profile_name(profile_name)
        if not normalized_name or normalized_name in active_names:
            continue
        active_names.append(normalized_name)

    for name in active_names:
        meta = normalized_registry.get(name, {})
        raw = meta.get("suffixes") or []
        for entry in raw:
            suffix_value = str(entry).strip()
            if not suffix_value or suffix_value == "__none__":
                continue
            suffixes.append(suffix_value)
    return suffixes


def resolve_profile_ignore_dirs(
    registry: Dict[str, Dict], active_profiles: List[str]
) -> List[str]:
    """Return ignored directory names from active profiles."""
    normalized_registry = _normalize_registry(registry)
    ignored: List[str] = []
    active_names: List[str] = []
    for profile_name in active_profiles:
        normalized_name = _normalize_profile_name(profile_name)
        if not normalized_name or normalized_name in active_names:
            continue
        active_names.append(normalized_name)

    for name in active_names:
        meta = normalized_registry.get(name, {})
        raw = meta.get("ignore_dirs") or []
        for entry in raw:
            dir_value = str(entry).strip()
            if not dir_value or dir_value == "__none__":
                continue
            ignored.append(dir_value)
    return ignored
