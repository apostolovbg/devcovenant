#!/usr/bin/env python3
"""Uninstall DevCovenant from a target repository."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

MANIFEST_PATH = ".devcovenant/install_manifest.json"


def _remove_path(target: Path) -> None:
    """Remove a file or directory if it exists."""
    if target.is_dir():
        shutil.rmtree(target)
        return
    if target.exists():
        target.unlink()


def main() -> None:
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
        "--preserve-docs",
        action="store_true",
        help="Preserve README/AGENTS/metadata files.",
    )
    args = parser.parse_args()

    target_root = Path(args.target).resolve()
    manifest_file = target_root / MANIFEST_PATH
    if not manifest_file.exists():
        raise SystemExit(
            f"Install manifest not found at {manifest_file}."
        )

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    installed = manifest.get("installed", {})

    for rel_path in installed.get("core", []):
        _remove_path(target_root / rel_path)

    for rel_path in installed.get("config", []):
        _remove_path(target_root / rel_path)

    if not args.preserve_docs:
        for rel_path in installed.get("docs", []):
            _remove_path(target_root / rel_path)

    _remove_path(manifest_file)


if __name__ == "__main__":
    main()
