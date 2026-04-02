"""Shared test support for the repository test suite."""

from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

_INSTALLED_SEED_DIR: tempfile.TemporaryDirectory[str] | None = None
_INSTALLED_SEED_ROOT: Path | None = None
_REFRESHED_SEED_DIR: tempfile.TemporaryDirectory[str] | None = None
_REFRESHED_SEED_ROOT: Path | None = None


class MonkeyPatch:
    """Minimal monkeypatch helper compatible with unittest workflows."""

    def __init__(self) -> None:
        """Initialize the patch stack used for cleanup."""
        self._patchers: list[object] = []

    def setattr(
        self,
        target: object | str,
        name_or_replacement: str | object,
        replacement_value: object | None = None,
    ) -> None:
        """Patch a dotted attribute path or object attribute."""
        if replacement_value is None:
            patcher = patch(str(target), name_or_replacement)
        else:
            patcher = patch.object(
                target, str(name_or_replacement), replacement_value
            )
        patcher.start()
        self._patchers.append(patcher)

    def setenv(self, key: str, env_value: str) -> None:
        """Patch one environment variable for the current process."""
        patcher = patch.dict(os.environ, {key: env_value})
        patcher.start()
        self._patchers.append(patcher)

    def undo(self) -> None:
        """Undo all active patches in reverse order."""
        while self._patchers:
            patcher = self._patchers.pop()
            patcher.stop()


def _build_installed_seed() -> Path:
    """Create and return the cached install baseline tree."""
    global _INSTALLED_SEED_DIR, _INSTALLED_SEED_ROOT
    if _INSTALLED_SEED_ROOT is not None:
        return _INSTALLED_SEED_ROOT

    from devcovenant import install

    seed_dir = tempfile.TemporaryDirectory()
    seed_root = Path(seed_dir.name) / "repo"
    with redirect_stderr(StringIO()):
        result = install.install_repo(seed_root)
    assert result == 0

    _INSTALLED_SEED_DIR = seed_dir
    _INSTALLED_SEED_ROOT = seed_root
    return seed_root


def _build_refreshed_seed() -> Path:
    """Create and return the cached install+refresh baseline tree."""
    global _REFRESHED_SEED_DIR, _REFRESHED_SEED_ROOT
    if _REFRESHED_SEED_ROOT is not None:
        return _REFRESHED_SEED_ROOT

    from devcovenant.core import refresh_runtime

    seed_dir = tempfile.TemporaryDirectory()
    seed_root = Path(seed_dir.name) / "repo"
    shutil.copytree(_build_installed_seed(), seed_root)
    result = refresh_runtime.refresh_repo(seed_root)
    assert result == 0

    _REFRESHED_SEED_DIR = seed_dir
    _REFRESHED_SEED_ROOT = seed_root
    return seed_root


def copy_installed_repo(repo_root: Path) -> None:
    """Copy one installed baseline into ``repo_root``."""
    shutil.copytree(
        _build_installed_seed(),
        repo_root,
        dirs_exist_ok=True,
        copy_function=shutil.copy,
    )


def copy_refreshed_repo(repo_root: Path) -> None:
    """Copy one refreshed baseline into ``repo_root``."""
    shutil.copytree(
        _build_refreshed_seed(),
        repo_root,
        dirs_exist_ok=True,
        copy_function=shutil.copy,
    )
