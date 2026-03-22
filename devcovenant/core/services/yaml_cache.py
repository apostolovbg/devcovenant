"""Run-scoped cached file and YAML loading helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def _path_signature(path: Path) -> tuple[str, bool, int, int]:
    """Return a stable cache key for one filesystem path."""
    resolved = Path(path).resolve(strict=False)
    try:
        stat_result = Path(path).stat()
    except FileNotFoundError:
        return (str(resolved), False, 0, 0)
    return (
        str(resolved),
        True,
        int(stat_result.st_mtime_ns),
        int(stat_result.st_size),
    )


@lru_cache(maxsize=512)
def _read_text_cached(
    signature: tuple[str, bool, int, int], encoding: str
) -> str:
    """Read one text file once per path signature."""
    path_text, exists, _mtime_ns, _size = signature
    if not exists:
        raise FileNotFoundError(path_text)
    return Path(path_text).read_text(encoding=encoding)


def read_text(path: Path, *, encoding: str = "utf-8") -> str:
    """Return cached text for one path."""
    return _read_text_cached(_path_signature(Path(path)), encoding)


@lru_cache(maxsize=512)
def _load_yaml_cached(
    signature: tuple[str, bool, int, int], encoding: str
) -> Any:
    """Load one YAML document once per path signature."""
    return yaml.safe_load(_read_text_cached(signature, encoding))


def load_yaml(path: Path, *, encoding: str = "utf-8") -> Any:
    """Return cached YAML content for one path."""
    return _load_yaml_cached(_path_signature(Path(path)), encoding)


def clear_yaml_cache() -> None:
    """Clear all cached file and YAML content."""
    _read_text_cached.cache_clear()
    _load_yaml_cached.cache_clear()
