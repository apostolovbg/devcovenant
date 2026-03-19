"""
DevCovenant - Self-enforcing policy system.

This system parses policy definitions from AGENTS.md, maintains policy
scripts, and enforces policies automatically during development.
"""

from __future__ import annotations

import atexit
import os
import shutil
import sys
from pathlib import Path


def _source_checkout_root(
    package_file: str | Path | None = None,
) -> Path | None:
    """Return the repo root when this package is imported from source."""
    module_path = Path(package_file or __file__).resolve()
    package_dir = module_path.parent
    if package_dir.name != "devcovenant":
        return None
    repo_root = package_dir.parent
    if not (repo_root / ".git").exists():
        return None
    if not (package_dir / "__main__.py").exists():
        return None
    if not (package_dir / "cli.py").exists():
        return None
    return repo_root


def _disable_source_checkout_bytecode(
    package_file: str | Path | None = None,
) -> bool:
    """Disable Python cache-file writes when imported from source."""
    if _source_checkout_root(package_file) is None:
        return False
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    return True


def _cleanup_source_checkout_import_cache(
    package_file: str | Path | None = None,
) -> bool:
    """Remove source-package cache files that should not linger in repo."""
    repo_root = _source_checkout_root(package_file)
    if repo_root is None:
        return False
    cache_dir = repo_root / "devcovenant" / "__pycache__"
    if not cache_dir.exists():
        return False
    shutil.rmtree(cache_dir, ignore_errors=True)
    return True


def _register_source_checkout_import_cleanup(
    package_file: str | Path | None = None,
) -> bool:
    """Register exit-time cleanup for source-package import cache."""
    if _source_checkout_root(package_file) is None:
        return False
    atexit.register(_cleanup_source_checkout_import_cache, package_file)
    return True


_SOURCE_CHECKOUT_BYTECODE_DISABLED = _disable_source_checkout_bytecode()
_SOURCE_CHECKOUT_IMPORT_CACHE_CLEANED = _cleanup_source_checkout_import_cache()
_SOURCE_CHECKOUT_IMPORT_CACHE_CLEANUP_REGISTERED = (
    _register_source_checkout_import_cleanup()
)

__version__ = "1.0.0"
__all__ = ["__version__"]
