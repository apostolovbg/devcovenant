"""Deploy command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

from devcovenant.core import install as install_core
from devcovenant.core.command_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for deploy command."""
    parser = argparse.ArgumentParser(
        description="Deploy managed docs/assets into a repository."
    )
    return parser


def _build_install_args(repo_root: Path) -> list[str]:
    """Return argv for core install.main in deploy mode."""
    install_args = [
        "--target",
        str(repo_root),
        "--deploy",
        "--require-non-generic",
        "--skip-core",
    ]
    return install_args


def run(args: argparse.Namespace) -> int:
    """Execute deploy command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)
    print_banner("DevCovenant run", "🚀")
    print_step("Command: deploy", "🧭")
    print_banner("Deploy DevCovenant", "🚀")

    install_core.main(argv=_build_install_args(repo_root))
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
