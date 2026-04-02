"""DevCovenant test mirror bootstrap."""

from __future__ import annotations

import atexit
import shutil
import sys
from pathlib import Path


def _repo_root(package_file: str | Path | None = None) -> Path | None:
    """Return the repository root when the test mirror runs from source."""
    module_path = Path(package_file or __file__).resolve()
    tests_package = module_path.parent
    tests_root = tests_package.parent
    repo_root = tests_root.parent
    if tests_package.name != "devcovenant":
        return None
    if tests_root.name != "tests":
        return None
    if not (repo_root / ".git").exists():
        return None
    if not (repo_root / "devcovenant" / "__init__.py").exists():
        return None
    return repo_root


def _owned_cache_roots(
    package_file: str | Path | None = None,
) -> tuple[Path, ...]:
    """Return the owned source trees that must stay free of Python caches."""
    repo_root = _repo_root(package_file)
    if repo_root is None:
        return ()
    return (
        repo_root / "devcovenant",
        repo_root / "tests" / "devcovenant",
    )


def _disable_owned_tree_bytecode(
    package_file: str | Path | None = None,
) -> bool:
    """Disable Python bytecode writes for the source-test process."""
    if not _owned_cache_roots(package_file):
        return False
    sys.dont_write_bytecode = True
    return True


def _cleanup_owned_tree_caches(
    package_file: str | Path | None = None,
) -> bool:
    """Remove owned-tree cache artifacts under the owned package/test trees."""
    removed = False
    for cache_root in _owned_cache_roots(package_file):
        if not cache_root.exists():
            continue
        for cache_dir in cache_root.rglob("__pycache__"):
            shutil.rmtree(cache_dir, ignore_errors=True)
            removed = True
        for compiled_file in cache_root.rglob("*.py[co]"):
            try:
                compiled_file.unlink()
            except OSError:
                continue
            removed = True
    return removed


def _register_owned_tree_cleanup(
    package_file: str | Path | None = None,
) -> bool:
    """Register exit-time cleanup for the owned source-test trees."""
    if not _owned_cache_roots(package_file):
        return False
    atexit.register(_cleanup_owned_tree_caches, package_file)
    return True


_OWNED_TREE_BYTECODE_DISABLED = _disable_owned_tree_bytecode()
_OWNED_TREE_CACHES_CLEANED = _cleanup_owned_tree_caches()
_OWNED_TREE_CLEANUP_REGISTERED = _register_owned_tree_cleanup()
