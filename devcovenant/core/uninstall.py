#!/usr/bin/env python3
"""Uninstall DevCovenant from a target repository."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

MANIFEST_PATH = ".devcov/install_manifest.json"
LEGACY_MANIFEST_PATH = ".devcovenant/install_manifest.json"
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
    manifest_file = target_root / MANIFEST_PATH
    legacy_manifest = target_root / LEGACY_MANIFEST_PATH
    if not manifest_file.exists() and not legacy_manifest.exists():
        raise SystemExit(
            "Install manifest not found at "
            f"{manifest_file} or {legacy_manifest}."
        )
    if not manifest_file.exists():
        manifest_file = legacy_manifest

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    installed = manifest.get("installed", {})

    for rel_path in installed.get("core", []):
        _remove_path(target_root / rel_path)

    for rel_path in installed.get("config", []):
        _remove_path(target_root / rel_path)

    doc_blocks = manifest.get("doc_blocks", [])
    for rel_path in doc_blocks:
        _strip_block(target_root / rel_path)

    if args.remove_docs:
        for rel_path in installed.get("docs", []):
            _remove_path(target_root / rel_path)

    _remove_path(manifest_file)
    if legacy_manifest.exists():
        _remove_path(legacy_manifest)


if __name__ == "__main__":
    main()
