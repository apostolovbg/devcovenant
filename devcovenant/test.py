"""Test command implementation for DevCovenant."""

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
    run_and_record_tests,
    run_bootstrap_registry_refresh,
    warn_version_mismatch,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the test command."""
    parser = argparse.ArgumentParser(description="Run the DevCovenant tests.")
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute test command from parsed arguments."""
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: test", "🧭")
    run_bootstrap_registry_refresh(repo_root)
    warn_version_mismatch(repo_root)

    print_banner("DevCovenant tests", "🧪")
    print_step("Running unittest discover + pytest", "▶️")
    return run_and_record_tests(repo_root, notes="")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
