"""Run-scoped cached file, YAML, and Python-AST loading helpers."""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


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
def _read_bytes_cached(signature: tuple[str, bool, int, int]) -> bytes:
    """Read one binary file once per path signature."""
    path_text, exists, _mtime_ns, _size = signature
    if not exists:
        raise FileNotFoundError(path_text)
    return Path(path_text).read_bytes()


def read_bytes(path: Path) -> bytes:
    """Return cached bytes for one path."""
    return _read_bytes_cached(_path_signature(Path(path)))


@lru_cache(maxsize=512)
def _load_yaml_cached(
    signature: tuple[str, bool, int, int], encoding: str
) -> Any:
    """Load one YAML document once per path signature."""
    return yaml.load(
        _read_text_cached(signature, encoding),
        Loader=_YAML_LOADER,
    )


def load_yaml(path: Path, *, encoding: str = "utf-8") -> Any:
    """Return cached YAML content for one path."""
    return _load_yaml_cached(_path_signature(Path(path)), encoding)


def load_yaml_text(text: str) -> Any:
    """Parse YAML text with the fastest available safe loader."""
    return yaml.load(text, Loader=_YAML_LOADER)


@lru_cache(maxsize=512)
def _parse_python_ast_cached(
    signature: tuple[str, bool, int, int], encoding: str
) -> ast.AST | None:
    """Parse one Python file once per path signature."""
    source = _read_text_cached(signature, encoding)
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def parse_python_ast(
    path: Path,
    *,
    encoding: str = "utf-8",
) -> ast.AST | None:
    """Return cached Python AST for one path."""
    return _parse_python_ast_cached(_path_signature(Path(path)), encoding)


def clear_yaml_cache() -> None:
    """Clear all cached file and YAML content."""
    _read_text_cached.cache_clear()
    _read_bytes_cached.cache_clear()
    _load_yaml_cached.cache_clear()
    _parse_python_ast_cached.cache_clear()
