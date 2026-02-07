#!/usr/bin/env python3
"""Remove deployed DevCovenant-managed artifacts without deleting core."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from devcovenant.core import cli_options
from devcovenant.core import manifest as manifest_module
from devcovenant.core import uninstall
from devcovenant.core.install import GITIGNORE_USER_BEGIN, GITIGNORE_USER_END
from devcovenant.core.refresh_all import _looks_generated_gitignore

_FALLBACK_DOC_BLOCKS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "devcovenant/README.md",
]


def _strip_managed_blocks(target_root: Path, doc_blocks: list[str]) -> None:
    """Strip managed blocks from the provided docs."""
    for rel_path in doc_blocks:
        uninstall._strip_block(target_root / rel_path)


def _extract_user_gitignore(text: str) -> str:
    """Return user-only entries from a managed gitignore."""
    if GITIGNORE_USER_BEGIN in text and GITIGNORE_USER_END in text:
        before, rest = text.split(GITIGNORE_USER_BEGIN, 1)
        _block, after = rest.split(GITIGNORE_USER_END, 1)
        user_lines = _block.strip("\n")
        return (user_lines + "\n") if user_lines else ""
    return ""


def _undeploy_gitignore(target_root: Path) -> None:
    """Remove managed gitignore fragments while preserving user entries."""
    gitignore_path = target_root / ".gitignore"
    if not gitignore_path.exists():
        return
    existing = gitignore_path.read_text(encoding="utf-8")
    user_text = _extract_user_gitignore(existing)
    if user_text:
        gitignore_path.write_text(user_text, encoding="utf-8")
        return
    if _looks_generated_gitignore(existing):
        gitignore_path.unlink()


def main(argv=None) -> None:
    """CLI entry point for undeploy."""
    parser = argparse.ArgumentParser(
        description=(
            "Remove deployed DevCovenant-managed docs/registries while "
            "keeping core files."
        )
    )
    cli_options.add_target_arg(parser)
    args = parser.parse_args(argv)

    target_root = Path(args.target).resolve()
    manifest = manifest_module.load_manifest(target_root, include_legacy=True)
    if manifest and "doc_blocks" in manifest:
        doc_blocks = list(manifest.get("doc_blocks", []))
    elif manifest and "docs" in manifest:
        docs = manifest.get("docs", {})
        doc_blocks = (
            docs.get("core", [])
            + docs.get("optional", [])
            + docs.get("custom", [])
        )
    else:
        doc_blocks = list(_FALLBACK_DOC_BLOCKS)

    _strip_managed_blocks(target_root, doc_blocks)

    registry_dir = target_root / "devcovenant" / "registry" / "local"
    if registry_dir.exists():
        shutil.rmtree(registry_dir)

    _undeploy_gitignore(target_root)


if __name__ == "__main__":
    main()
