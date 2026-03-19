"""
DevCovenant - Self-enforcing policy system.

This system parses policy definitions from AGENTS.md, maintains policy
scripts, and enforces policies automatically during development.
"""

from __future__ import annotations

import os
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


_SOURCE_CHECKOUT_BYTECODE_DISABLED = _disable_source_checkout_bytecode()

__version__ = "1.0.0"
__all__ = ["__version__"]
