#!/usr/bin/env python3
"""Gate command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from devcovenant.core.flow.gate import run_pre_commit_gate, show_gate_status
from devcovenant.core.runtime.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for gate command."""
    parser = argparse.ArgumentParser(
        description="Run DevCovenant gate session lifecycle commands."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--start",
        action="store_true",
        help="Run pre-commit and record gate session start evidence.",
    )
    group.add_argument(
        "--end",
        action="store_true",
        help="Run pre-commit and record gate session end evidence.",
    )
    group.add_argument(
        "--mid",
        action="store_true",
        help=(
            "Run a non-lifecycle mid-session pre-commit sweep "
            "(mutating checks/autofix may apply)."
        ),
    )
    group.add_argument(
        "--status",
        action="store_true",
        help=(
            "Show short gate session status without mutating lifecycle state."
        ),
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute gate command."""
    repo_root = resolve_repo_root(require_install=True)
    if getattr(args, "status", False):
        return show_gate_status(repo_root)

    if getattr(args, "start", False):
        phase = "start"
    elif getattr(args, "mid", False):
        phase = "mid"
    else:
        phase = "end"

    print_banner("Devflow gate", "🚦")
    print_step(f"Running `{phase}` pre-commit gate", "▶️")
    exit_code = run_pre_commit_gate(repo_root, phase)
    if exit_code == 0:
        if phase == "mid":
            print_step("Mid gate completed", "✅")
        else:
            print_step(f"{phase.capitalize()} gate recorded", "✅")
    return exit_code


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
