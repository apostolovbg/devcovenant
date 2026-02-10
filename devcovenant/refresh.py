"""Refresh command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

from devcovenant.core.command_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)
from devcovenant.core.refresh_all import refresh_all


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for refresh command."""
    parser = argparse.ArgumentParser(description="Run a full refresh.")
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute refresh command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)
    print_banner("DevCovenant run", "🚀")
    print_step("Command: refresh", "🧭")
    print_banner("Full refresh", "🔄")
    return refresh_all(
        repo_root,
        registry_only=False,
        backup_existing=False,
    )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
