#!/usr/bin/env python3
"""Uninstall DevCovenant from a target repository."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from devcovenant.core import manifest as manifest_module

FALLBACK_CORE_PATHS = [
    "devcovenant",
    "devcov_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]
FALLBACK_CONFIG_PATHS = [
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
]
FALLBACK_DOC_BLOCKS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
]

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"


def _remove_path(target: Path) -> None:
    """Remove a file or directory if it exists."""
    if target.is_dir():
        shutil.rmtree(target)
        return
    if target.exists():
        target.unlink()


def _strip_block(path: Path) -> bool:
    """Remove DevCovenant block markers from a file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN not in text or BLOCK_END not in text:
        return False
    before, rest = text.split(BLOCK_BEGIN, 1)
    _block, after = rest.split(BLOCK_END, 1)
    path.write_text(f"{before}{after}", encoding="utf-8")
    return True


def main(argv=None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Uninstall DevCovenant using its install manifest."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--remove-docs",
        action="store_true",
        help="Delete doc files that were installed by DevCovenant.",
    )
    args = parser.parse_args(argv)

    target_root = Path(args.target).resolve()
    manifest = manifest_module.load_manifest(target_root, include_legacy=True)
    installed = manifest.get("installed", {}) if manifest else {}
    if manifest and "core" in manifest:
        core = manifest.get("core", {})
        core_paths = core.get("dirs", []) + core.get("files", [])
    else:
        core_paths = (
            installed.get("core", []) if manifest else FALLBACK_CORE_PATHS
        )
    config_paths = (
        installed.get("config", []) if manifest else FALLBACK_CONFIG_PATHS
    )
    if manifest and "doc_blocks" in manifest:
        doc_blocks = manifest.get("doc_blocks", [])
    elif manifest and "docs" in manifest:
        docs = manifest.get("docs", {})
        doc_blocks = (
            docs.get("core", [])
            + docs.get("optional", [])
            + docs.get("custom", [])
        )
    else:
        doc_blocks = FALLBACK_DOC_BLOCKS

    for rel_path in core_paths:
        _remove_path(target_root / rel_path)

    for rel_path in config_paths:
        _remove_path(target_root / rel_path)

    for rel_path in doc_blocks:
        _strip_block(target_root / rel_path)

    if args.remove_docs and manifest:
        for rel_path in installed.get("docs", []):
            _remove_path(target_root / rel_path)

    manifest_path = manifest_module.manifest_path(target_root)
    if manifest_path.exists():
        _remove_path(manifest_path)
    for legacy_path in manifest_module.legacy_manifest_paths(target_root):
        if legacy_path.exists():
            _remove_path(legacy_path)


if __name__ == "__main__":
    main()
