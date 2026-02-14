#!/usr/bin/env python3
"""Check command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

from devcovenant.core.execution_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
    warn_version_mismatch,
)
from devcovenant.core.policy_runtime import DevCovenantEngine
from devcovenant.core.refresh_runtime import refresh_repo


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for check command."""
    parser = argparse.ArgumentParser(description="Run DevCovenant checks.")
    parser.add_argument(
        "--nofix",
        action="store_true",
        help="Disable auto-fixes for this run.",
    )
    parser.add_argument(
        "--norefresh",
        action="store_true",
        help="Skip the startup full refresh before policy checks.",
    )
    return parser


def _run_check(repo_root: Path, apply_fixes: bool, skip_refresh: bool) -> int:
    """Run policy checks through the engine."""
    print_banner("DevCovenant run", "🚀")
    print_step("Command: check", "🧭")
    print_step(f"Auto-fix: {'enabled' if apply_fixes else 'disabled'}", "🛠️")

    if skip_refresh:
        print_step("Skipping full refresh (--norefresh)", "⏭️")
    else:
        print_step("Running full refresh", "🔄")
        refresh_exit = refresh_repo(repo_root)
        if refresh_exit != 0:
            print_step("Full refresh failed", "🚫")
            return refresh_exit
        print_step("Full refresh complete", "✅")

    warn_version_mismatch(repo_root)

    print_step("Initializing engine", "🧠")
    engine = DevCovenantEngine(repo_root=repo_root)
    print_step("Engine ready", "✅")

    print_banner("Policy checks", "🔍")
    print_step("Running policy checks", "▶️")
    result = engine.check(mode="normal", apply_fixes=apply_fixes)
    print_step("Policy checks complete", "🏁")

    if result.should_block:
        return 1
    if result.has_sync_issues():
        return 1
    return 0


def run(args: argparse.Namespace) -> int:
    """Execute check command."""
    repo_root = resolve_repo_root(require_install=True)
    return _run_check(
        repo_root,
        apply_fixes=not args.nofix,
        skip_refresh=bool(args.norefresh),
    )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
