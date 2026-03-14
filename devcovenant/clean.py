"""Clean command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from devcovenant.core.flow.clean import clean_repo
from devcovenant.core.runtime.execution import (
    build_command_parser,
    print_banner,
    print_step,
    resolve_repo_root,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the clean command."""
    parser = build_command_parser(
        "clean",
        "Remove disposable build or cache artifacts safely.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove both build/package and cache/test-output artifacts.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Remove build/package artifacts only.",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Remove cache/test-output artifacts only.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute clean command from parsed arguments."""
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: clean", "🧭")
    print_banner("Cleanup", "🧹")

    return clean_repo(
        repo_root,
        include_all=bool(args.all),
        include_build=bool(args.build),
        include_cache=bool(args.cache),
    )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.all and (args.build or args.cache):
        parser.error("`--all` cannot be combined with `--build` or `--cache`.")
    if not any((args.all, args.build, args.cache)):
        parser.error(
            "select at least one cleanup scope: `--all`, `--build`, or "
            "`--cache`."
        )
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
