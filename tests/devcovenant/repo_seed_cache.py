"""Cached repo seed helpers for integration-heavy tests.

These helpers preserve test fidelity (real install/refresh behavior) while
avoiding repeated baseline setup work across many tests in the same runner
process. Each test still receives an isolated copy.
"""

from __future__ import annotations

import shutil
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from devcovenant import install, refresh

_INSTALLED_CACHE_DIR: tempfile.TemporaryDirectory[str] | None = None
_INSTALLED_CACHE_ROOT: Path | None = None
_REFRESHED_CACHE_DIR: tempfile.TemporaryDirectory[str] | None = None
_REFRESHED_CACHE_ROOT: Path | None = None


def _build_installed_cache() -> Path:
    """Create and return the cached install baseline tree."""
    global _INSTALLED_CACHE_DIR, _INSTALLED_CACHE_ROOT
    if _INSTALLED_CACHE_ROOT is not None:
        return _INSTALLED_CACHE_ROOT

    cache_dir = tempfile.TemporaryDirectory()
    cache_root = Path(cache_dir.name) / "repo"
    with redirect_stderr(StringIO()):
        result = install.install_repo(cache_root)
    assert result == 0

    _INSTALLED_CACHE_DIR = cache_dir
    _INSTALLED_CACHE_ROOT = cache_root
    return cache_root


def _build_refreshed_cache() -> Path:
    """Create and return the cached install+refresh baseline tree."""
    global _REFRESHED_CACHE_DIR, _REFRESHED_CACHE_ROOT
    if _REFRESHED_CACHE_ROOT is not None:
        return _REFRESHED_CACHE_ROOT

    cache_dir = tempfile.TemporaryDirectory()
    cache_root = Path(cache_dir.name) / "repo"
    shutil.copytree(_build_installed_cache(), cache_root)
    result = refresh.refresh_repo(cache_root)
    assert result == 0

    _REFRESHED_CACHE_DIR = cache_dir
    _REFRESHED_CACHE_ROOT = cache_root
    return cache_root


def copy_installed_repo(repo_root: Path) -> None:
    """Copy a cached install baseline into ``repo_root``."""
    shutil.copytree(
        _build_installed_cache(),
        repo_root,
        dirs_exist_ok=True,
        copy_function=shutil.copy,
    )


def copy_refreshed_repo(repo_root: Path) -> None:
    """Copy a cached install+refresh baseline into ``repo_root``."""
    shutil.copytree(
        _build_refreshed_cache(),
        repo_root,
        dirs_exist_ok=True,
        copy_function=shutil.copy,
    )
