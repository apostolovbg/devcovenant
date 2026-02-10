"""Upgrade command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

from devcovenant.core import upgrade as upgrade_core
from devcovenant.core.command_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for upgrade command."""
    parser = argparse.ArgumentParser(
        description="Upgrade DevCovenant core in a repository."
    )
    return parser


def _build_upgrade_args(repo_root: Path) -> list[str]:
    """Return argv for core upgrade.main."""
    upgrade_args = ["--target", str(repo_root)]
    return upgrade_args


def run(args: argparse.Namespace) -> int:
    """Execute upgrade command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)
    print_banner("DevCovenant run", "🚀")
    print_step("Command: upgrade", "🧭")
    print_banner("Upgrade DevCovenant", "⬆️")

    upgrade_core.main(argv=_build_upgrade_args(repo_root))
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
