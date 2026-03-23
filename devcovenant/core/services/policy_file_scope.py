"""File-scope and ignore-path helpers for policy-engine repository scans."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Any, Collection

from devcovenant.core.services.profile_registry import (
    resolve_profile_ignore_dirs,
    resolve_profile_suffixes,
)

_FALLBACK_CORE_EXCLUSION_PATHS = (
    "devcovenant/core",
    "devcovenant/builtin",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/check.py",
    "devcovenant/gate.py",
    "devcovenant/policy.py",
    "devcovenant/test.py",
    "devcovenant/install.py",
    "devcovenant/deploy.py",
    "devcovenant/upgrade.py",
    "devcovenant/refresh.py",
    "devcovenant/uninstall.py",
    "devcovenant/undeploy.py",
    "devcovenant/registry",
)


def _normalized_name_entries(raw_entries: object) -> list[str]:
    """Return stripped, non-empty names from scalar or list metadata."""
    if isinstance(raw_entries, str):
        candidates = [raw_entries]
    elif isinstance(raw_entries, list):
        candidates = raw_entries
    else:
        candidates = [raw_entries] if raw_entries else []
    names: list[str] = []
    for entry in candidates:
        name = str(entry).strip()
        if name:
            names.append(name)
    return names


def configured_ignore_dir_names(
    config: dict[str, Any] | None,
) -> list[str]:
    """Return extra ignored directory names from engine config."""
    engine_cfg = config.get("engine", {}) if isinstance(config, dict) else {}
    extra_dirs = engine_cfg.get("ignore_dirs", [])
    return _normalized_name_entries(extra_dirs)


def config_ignore_patterns(config: dict[str, Any] | None) -> list[str]:
    """Return normalized ignore glob patterns from config metadata."""
    ignore_cfg = config.get("ignore", {}) if isinstance(config, dict) else {}
    if isinstance(ignore_cfg, dict):
        raw_patterns = ignore_cfg.get("patterns", [])
    else:
        raw_patterns = []
    if isinstance(raw_patterns, str):
        candidates = [entry.strip() for entry in raw_patterns.split(",")]
    elif isinstance(raw_patterns, list):
        candidates = [str(entry).strip() for entry in raw_patterns]
    else:
        candidates = [str(raw_patterns).strip()] if raw_patterns else []
    patterns: list[str] = []
    for entry in candidates:
        pattern = entry.replace("\\", "/").lstrip("/")
        if not pattern or pattern.startswith("#"):
            continue
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/") + "/**"
        patterns.append(pattern)
    return patterns


def matches_config_ignore_pattern(
    repo_root: Path,
    candidate: Path,
    patterns: list[str],
) -> bool:
    """Return True when candidate matches configured ignore patterns."""
    if not patterns:
        return False
    try:
        rel_path = candidate.relative_to(repo_root)
    except ValueError:
        rel_path = candidate
    rel_posix = PurePosixPath(rel_path.as_posix())
    rel_text = rel_posix.as_posix()
    for pattern in patterns:
        if rel_posix.match(pattern):
            return True
        if pattern.endswith("/**"):
            dir_token = pattern[: -len("/**")].rstrip("/")
            if rel_text == dir_token:
                return True
    return False


def core_exclusion_paths(
    repo_root: Path,
    config: dict[str, Any] | None,
) -> list[Path]:
    """Return repo-rooted core exclusion paths based on config."""
    developer_mode = bool((config or {}).get("developer_mode", False))
    if developer_mode:
        return []
    profiles_cfg = (config or {}).get("profiles", {})
    if isinstance(profiles_cfg, dict):
        generated_cfg = profiles_cfg.get("generated", {})
    else:
        generated_cfg = {}
    if isinstance(generated_cfg, dict):
        core_paths = generated_cfg.get(
            "devcov_core_paths",
            list(_FALLBACK_CORE_EXCLUSION_PATHS),
        )
    else:
        core_paths = list(_FALLBACK_CORE_EXCLUSION_PATHS)
    entries = [core_paths] if isinstance(core_paths, str) else list(core_paths)
    results: list[Path] = []
    for entry in entries:
        rel = str(entry).strip()
        if rel:
            results.append(repo_root / rel)
    return results


def discover_custom_policy_overrides(repo_root: Path) -> set[str]:
    """Return policy ids overridden by custom policy scripts."""
    overrides: set[str] = set()
    custom_dir = repo_root / "devcovenant" / "custom" / "policies"
    if not custom_dir.exists():
        return overrides
    for policy_dir in custom_dir.iterdir():
        if not policy_dir.is_dir():
            continue
        script_path = policy_dir / f"{policy_dir.name}.py"
        if not script_path.exists():
            continue
        overrides.add(policy_dir.name.replace("_", "-"))
    return overrides


def is_ignored_path(
    candidate: Path,
    *,
    repo_root: Path,
    ignored_dirs: Collection[str],
    ignored_paths: list[Path],
    config_ignore_patterns: list[str],
) -> bool:
    """Return True when candidate hits ignore names, prefixes, or patterns."""
    if matches_config_ignore_pattern(
        repo_root, candidate, config_ignore_patterns
    ):
        return True
    for part in candidate.parts:
        if part in ignored_dirs:
            return True
    for root in ignored_paths:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def profile_ignored_dir_names(
    profile_registry: object,
    active_profiles: list[str],
) -> list[str]:
    """Return normalized ignored directory names from active profiles."""
    ignored = resolve_profile_ignore_dirs(profile_registry, active_profiles)
    return _normalized_name_entries(list(ignored))


def resolve_engine_file_suffixes(
    config: dict[str, Any] | None,
    profile_registry: object,
    active_profiles: list[str],
) -> list[str]:
    """Return configured + profile-provided file suffixes for scanning."""
    engine_cfg = config.get("engine", {}) if isinstance(config, dict) else {}
    suffixes = list(
        engine_cfg.get(
            "file_suffixes",
            [".py", ".md", ".yml", ".yaml"],
        )
    )
    suffixes.extend(
        resolve_profile_suffixes(profile_registry, active_profiles)
    )
    cleaned: list[str] = []
    for entry in suffixes:
        text = str(entry).strip()
        if text:
            cleaned.append(text)
    return cleaned


def should_descend_dir(
    candidate: Path,
    *,
    repo_root: Path,
    ignored_dirs: Collection[str],
    ignored_paths: list[Path],
    config_ignore_patterns: list[str],
) -> bool:
    """Return True when repository walk should recurse into candidate."""
    name = candidate.name
    if name in ignored_dirs:
        return False
    if is_ignored_path(
        candidate,
        repo_root=repo_root,
        ignored_dirs=ignored_dirs,
        ignored_paths=ignored_paths,
        config_ignore_patterns=config_ignore_patterns,
    ):
        return False
    if name.startswith("__pycache__"):
        return False
    return True


def collect_all_files(
    repo_root: Path,
    suffixes: set[str],
    *,
    ignored_dirs: Collection[str],
    ignored_paths: list[Path],
    config_ignore_patterns: list[str],
) -> list[Path]:
    """Collect files matching suffixes while honoring ignore rules."""
    matched: list[Path] = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            name
            for name in dirs
            if should_descend_dir(
                Path(root) / name,
                repo_root=repo_root,
                ignored_dirs=ignored_dirs,
                ignored_paths=ignored_paths,
                config_ignore_patterns=config_ignore_patterns,
            )
        ]
        for name in files:
            file_path = Path(root) / name
            if is_ignored_path(
                file_path,
                repo_root=repo_root,
                ignored_dirs=ignored_dirs,
                ignored_paths=ignored_paths,
                config_ignore_patterns=config_ignore_patterns,
            ):
                continue
            if file_path.suffix.lower() in suffixes:
                matched.append(file_path)
    return matched
