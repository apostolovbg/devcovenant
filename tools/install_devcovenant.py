#!/usr/bin/env python3
"""Install or update DevCovenant in a target repository."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CORE_PATHS = [
    "devcovenant",
    "devcovenant_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]

CONFIG_PATHS = [
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    ".gitignore",
]

DOC_PATHS = [
    "AGENTS.md",
    "README.md",
    "DEVCOVENANT.md",
    "CONTRIBUTING.md",
    "PLAN.md",
    "CHANGELOG.md",
    "VERSION",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
]

MANIFEST_PATH = ".devcovenant/install_manifest.json"
BLOCK_BEGIN = "<!-- DEVCOVENANT:BEGIN -->"
BLOCK_END = "<!-- DEVCOVENANT:END -->"

DOC_BLOCKS = {
    "README.md": (
        f"{BLOCK_BEGIN}\n"
        "**Read first:** `AGENTS.md` is the canonical source of truth. "
        "See `DEVCOVENANT.md` for architecture and lifecycle details.\n"
        f"{BLOCK_END}\n"
    ),
    "CONTRIBUTING.md": (
        f"{BLOCK_BEGIN}\n"
        "**Read first:** `AGENTS.md` is canonical. `DEVCOVENANT.md` explains "
        "the architecture and lifecycle.\n"
        f"{BLOCK_END}\n"
    ),
}


def _copy_path(source: Path, target: Path) -> None:
    """Copy a file or directory from source to target."""
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _install_paths(
    repo_root: Path,
    target_root: Path,
    paths: list[str],
    skip_existing: bool,
) -> list[str]:
    """Copy paths and return installed file list."""
    installed: list[str] = []
    for rel_path in paths:
        source = repo_root / rel_path
        target = target_root / rel_path
        if not source.exists():
            continue
        if skip_existing and target.exists():
            continue
        _copy_path(source, target)
        installed.append(rel_path)
    return installed


def _inject_block(path: Path, block: str) -> bool:
    """Insert or replace a DevCovenant block in a documentation file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, _rest = text.split(BLOCK_BEGIN, 1)
        _old_block, after = _rest.split(BLOCK_END, 1)
        updated = f"{before}{block}{after}"
        if updated == text:
            return False
        path.write_text(updated, encoding="utf-8")
        return True

    lines = text.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            insert_at = index + 1
            break
    lines.insert(insert_at, block)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Install or update DevCovenant in a target repository."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Overwrite docs and metadata on update.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite config files on update.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    target_root = Path(args.target).resolve()
    manifest_file = target_root / MANIFEST_PATH
    is_update = manifest_file.exists()

    installed: dict[str, list[str]] = {"core": [], "config": [], "docs": []}
    doc_blocks: list[str] = []

    installed["core"] = _install_paths(
        repo_root,
        target_root,
        CORE_PATHS,
        skip_existing=False,
    )

    installed["config"] = _install_paths(
        repo_root,
        target_root,
        CONFIG_PATHS,
        skip_existing=is_update and not args.force_config,
    )

    installed["docs"] = _install_paths(
        repo_root,
        target_root,
        DOC_PATHS,
        skip_existing=is_update and not args.force_docs,
    )

    for doc_name, block in DOC_BLOCKS.items():
        target = target_root / doc_name
        if _inject_block(target, block):
            doc_blocks.append(doc_name)

    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "mode": "update" if is_update else "install",
                "installed": installed,
                "doc_blocks": doc_blocks,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
