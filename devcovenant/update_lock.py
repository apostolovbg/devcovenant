#!/usr/bin/env python3
"""CLI command to refresh dependency lockfiles and license artifacts."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError  # nosec B404
from typing import Sequence

from devcovenant.core.runtime.execution import (
    build_command_parser,
    resolve_repo_root,
    runtime_print,
)
from devcovenant.core.services import (
    policy_commands as policy_commands_service,
)
from devcovenant.core.services.policy_engine import run_policy_runtime_action

_DEPENDENCY_POLICY_ID = "dependency-management"
_REFRESH_ACTION_ID = "refresh-all"


@dataclass(frozen=True)
class LockFilePieces:
    """Describe the body of a generated lock snapshot."""

    body: list[str]


@dataclass(frozen=True)
class LockHandlerResult:
    """Outcome from one lockfile refresh strategy."""

    lock_file: str
    changed: bool
    attempted: bool
    message: str


def refresh_locks_and_licenses(
    repo_root: Path,
) -> tuple[list[LockHandlerResult], list[Path]]:
    """Run dependency refresh through the active policy runtime."""
    payload = run_policy_runtime_action(
        repo_root,
        policy_id=_DEPENDENCY_POLICY_ID,
        action=_REFRESH_ACTION_ID,
        payload={},
    )
    if not isinstance(payload, dict):
        raise ValueError(
            "dependency-management runtime action returned invalid payload."
        )
    raw_results = payload.get("lock_results")
    raw_license_files = payload.get("refreshed_artifacts")
    if not isinstance(raw_results, list) or not isinstance(
        raw_license_files, list
    ):
        raise ValueError(
            "dependency-management runtime action returned invalid lists."
        )

    results: list[LockHandlerResult] = []
    for raw in raw_results:
        if isinstance(raw, dict):
            lock_file = raw.get("lock_file")
            changed = raw.get("changed")
            attempted = raw.get("attempted")
            message = raw.get("message")
        else:
            lock_file = getattr(raw, "lock_file", None)
            changed = getattr(raw, "changed", None)
            attempted = getattr(raw, "attempted", None)
            message = getattr(raw, "message", None)
        if lock_file is None or message is None:
            raise ValueError(
                "dependency-management runtime returned malformed lock "
                "result entries."
            )
        results.append(
            LockHandlerResult(
                lock_file=str(lock_file),
                changed=bool(changed),
                attempted=bool(attempted),
                message=str(message),
            )
        )

    license_files = [Path(entry) for entry in raw_license_files]
    return results, license_files


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for update_lock command."""

    return build_command_parser(
        "update_lock",
        (
            "Refresh dependency lockfiles for active profiles and keep "
            "license artifacts in sync."
        ),
    )


def _print_results(
    results: list[LockHandlerResult], license_files: list
) -> None:
    """Print refresh summary for CLI users."""

    changed = [entry for entry in results if entry.changed]
    attempted = [entry for entry in results if entry.attempted]
    skipped = [entry for entry in results if not entry.attempted]

    runtime_print("Lock refresh results:", file=sys.stdout)
    for entry in results:
        runtime_print(f"- {entry.lock_file}: {entry.message}", file=sys.stdout)

    if changed:
        changed_names = ", ".join(entry.lock_file for entry in changed)
        runtime_print(f"Updated lockfiles: {changed_names}", file=sys.stdout)
    else:
        runtime_print("No lockfile content changed.", file=sys.stdout)

    if license_files:
        refreshed = ", ".join(str(path) for path in license_files)
        runtime_print(
            f"Refreshed license artifacts: {refreshed}", file=sys.stdout
        )

    if not attempted and skipped:
        runtime_print(
            "All handlers skipped due missing prerequisites/tools.",
            file=sys.stdout,
        )


def run(args: argparse.Namespace) -> int:
    """Execute the update_lock command."""

    del args
    repo_root = resolve_repo_root(require_install=True)
    runtime_print(
        (
            "Compatibility command `update_lock` is deprecated. Prefer "
            "`"
            + policy_commands_service.canonical_policy_command_invocation(
                _DEPENDENCY_POLICY_ID,
                "refresh-all",
            )
            + "`."
        ),
        verbose_only=True,
    )
    try:
        results, license_files = refresh_locks_and_licenses(repo_root)
    except CalledProcessError as exc:
        runtime_print(
            (
                "Lock refresh failed while running: "
                f"{' '.join(exc.cmd)} (exit {exc.returncode})"
            ),
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        runtime_print(str(exc), file=sys.stderr)
        return 1
    if not results:
        runtime_print(
            "No metadata-selected lockfiles are configured for this repo.",
            file=sys.stdout,
        )
        return 0

    _print_results(results, license_files)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
