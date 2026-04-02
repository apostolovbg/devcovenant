#!/usr/bin/env python3
"""Uninstall DevCovenant from the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import shutil
from pathlib import Path

import devcovenant.core.cli_support as cli_args_module


def uninstall_repo(repo_root: Path) -> int:
    """Remove DevCovenant package and managed artifacts from repo."""
    from devcovenant import undeploy
    from devcovenant.core.execution import print_step

    undeploy.undeploy_repo(repo_root)

    package_dir = repo_root / "devcovenant"
    if package_dir.exists():
        shutil.rmtree(package_dir)

    print_step("Removed devcovenant/ package", "✅")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for uninstall command."""
    return cli_args_module.build_command_parser(
        "uninstall",
        "Remove DevCovenant from the current repository.",
    )


def run(args: argparse.Namespace) -> int:
    """Execute uninstall command."""
    from devcovenant.core.execution import (
        print_banner,
        print_step,
        resolve_repo_root,
    )

    del args
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: uninstall", "🧭")
    print_banner("Uninstall", "🗑️")

    return uninstall_repo(repo_root)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    cli_args_module.apply_output_mode_override_from_namespace(args)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
