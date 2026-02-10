"""Check command implementation for DevCovenant."""

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
    run_bootstrap_registry_refresh,
    warn_version_mismatch,
)
from devcovenant.core.engine import DevCovenantEngine
from devcovenant.core.gates import run_pre_commit_gate


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the check command."""
    parser = argparse.ArgumentParser(description="Run DevCovenant checks.")
    parser.add_argument(
        "--nofix",
        action="store_true",
        help="Disable auto-fixes for check.",
    )
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument(
        "--start",
        action="store_true",
        help="Run full pre-commit and record the start gate.",
    )
    gate_group.add_argument(
        "--end",
        action="store_true",
        help="Run full pre-commit and record the end gate.",
    )
    parser.add_argument(
        "--mode",
        choices=["startup", "lint", "pre-commit", "normal"],
        default="normal",
        help=argparse.SUPPRESS,
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute check command from parsed arguments."""
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)

    if (args.start or args.end) and args.mode != "normal":
        raise SystemExit("--mode cannot be combined with --start or --end.")

    if args.start or args.end:
        phase = "start" if args.start else "end"
        print_banner("Devflow gate", "🚦")
        print_step(f"Running `{phase}` pre-commit gate", "▶️")
        exit_code = run_pre_commit_gate(repo_root, phase)
        if exit_code == 0:
            print_step(f"{phase.capitalize()} gate recorded", "✅")
        return exit_code

    print_banner("DevCovenant run", "🚀")
    print_step("Command: check", "🧭")
    print_step(f"Auto-fix: {'disabled' if args.nofix else 'enabled'}", "🛠️")

    run_bootstrap_registry_refresh(repo_root)
    warn_version_mismatch(repo_root)

    print_step("Initializing engine", "🧠")
    engine = DevCovenantEngine(repo_root=repo_root)
    print_step("Engine ready", "✅")
    print_banner("Policy checks", "🔍")
    print_step("Running policy checks", "▶️")
    result = engine.check(mode=args.mode, apply_fixes=not args.nofix)
    print_step("Policy checks complete", "🏁")

    if result.should_block or result.has_sync_issues():
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
