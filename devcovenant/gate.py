#!/usr/bin/env python3
"""Gate command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from devcovenant.core.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)
from devcovenant.core.gates import run_pre_commit_gate


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for gate command."""
    parser = argparse.ArgumentParser(description="Run DevCovenant gate hooks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--start",
        action="store_true",
        help="Run pre-commit and record start gate metadata.",
    )
    group.add_argument(
        "--end",
        action="store_true",
        help="Run pre-commit and record end gate metadata.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute gate command."""
    repo_root = resolve_repo_root(require_install=True)
    phase = "start" if args.start else "end"

    print_banner("Devflow gate", "🚦")
    print_step(f"Running `{phase}` pre-commit gate", "▶️")
    exit_code = run_pre_commit_gate(repo_root, phase)
    if exit_code == 0:
        print_step(f"{phase.capitalize()} gate recorded", "✅")
    return exit_code


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
