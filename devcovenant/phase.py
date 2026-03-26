"""Workflow-phase command implementation for DevCovenant."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from devcovenant.core.runtime.execution import (
    build_command_parser,
    print_banner,
    print_step,
    resolve_repo_root,
    run_and_record_workflow_phase,
    run_bootstrap_registry_refresh,
    warn_version_mismatch,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the phase command."""

    parser = build_command_parser(
        "phase",
        "Run a declared DevCovenant workflow phase.",
    )
    subparsers = parser.add_subparsers(dest="phase_command", required=True)
    run_parser = subparsers.add_parser(
        "run",
        help="Run one declared workflow phase.",
    )
    run_parser.add_argument("phase_id", help="Workflow phase id to run")
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the phase command from parsed arguments."""

    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant phase", "🚀")
    print_step("Command: phase", "🧭")
    run_bootstrap_registry_refresh(repo_root)
    warn_version_mismatch(repo_root)

    phase_command = str(getattr(args, "phase_command", "") or "").strip()
    if phase_command != "run":
        raise SystemExit(f"Unsupported phase subcommand: {phase_command}")
    phase_id = str(getattr(args, "phase_id", "") or "").strip()
    if not phase_id:
        raise SystemExit("Workflow phase id is required.")

    print_banner("DevCovenant workflow phase", "🧩")
    print_step(f"Running workflow phase `{phase_id}`", "▶️")
    return run_and_record_workflow_phase(repo_root, phase_id)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
