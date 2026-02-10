"""Uninstall command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

from devcovenant.core import uninstall as uninstall_core
from devcovenant.core.command_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for uninstall command."""
    parser = argparse.ArgumentParser(description="Remove DevCovenant.")
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute uninstall command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=False)
    print_banner("DevCovenant run", "🚀")
    print_step("Command: uninstall", "🧭")
    print_banner("Uninstall DevCovenant", "🧹")

    uninstall_core.main(argv=["--target", str(repo_root)])
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
