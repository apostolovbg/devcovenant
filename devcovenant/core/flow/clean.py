"""Flow orchestration for the `devcovenant clean` command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import devcovenant.core.services.cleanup as cleanup_runtime
import devcovenant.core.services.registry as registry_runtime
from devcovenant.core.runtime.execution import (
    get_active_run_log_context,
    merge_active_run_log_metadata,
    print_step,
    runtime_print,
)


def clean_repo(
    repo_root: Path,
    *,
    include_all: bool,
    include_build: bool,
    include_cache: bool,
    include_registry: bool,
    include_logs: bool,
) -> int:
    """Run repository cleanup for the selected cleanup categories."""
    if _gate_session_is_open(repo_root):
        runtime_print(
            (
                "Error: Cannot run `clean` while a gate session is open. "
                "Run `devcovenant gate --end` first, then run `devcovenant "
                "clean ...` outside the active session."
            ),
            file=sys.stderr,
        )
        return 1
    selection = cleanup_runtime.resolve_clean_selection(
        include_all=include_all,
        include_build=include_build,
        include_cache=include_cache,
        include_registry=include_registry,
        include_logs=include_logs,
    )
    labels = ", ".join(selection.labels()) or "none"
    print_step(f"Cleanup scope: {labels}", "🧹")
    active_run_context = get_active_run_log_context()
    protected_run_dirs: tuple[Path, ...] = ()
    if active_run_context is not None:
        protected_run_dirs = (active_run_context.require_paths().run_dir,)

    result = cleanup_runtime.execute_cleanup(
        repo_root,
        selection,
        extra_protected_paths=protected_run_dirs,
    )
    merge_active_run_log_metadata(
        {
            "clean_summary": {
                "selected_scopes": list(selection.labels()),
                "removed_count": len(result.removed_paths),
                "removed_paths": list(result.removed_paths),
                "skipped_protected_count": len(result.skipped_protected_paths),
                "skipped_protected_match_count": (
                    result.skipped_protected_match_count
                ),
                "skipped_protected_paths": list(
                    result.skipped_protected_paths
                ),
            }
        }
    )
    if result.removed_paths:
        print_step(
            f"Removed {len(result.removed_paths)} cleanup target(s)",
            "✅",
        )
        for path in result.removed_paths:
            runtime_print(f"Removed: {path}", verbose_only=True)
    else:
        print_step("No cleanup targets matched", "✅")

    if result.skipped_protected_paths:
        print_step(
            (
                "Skipped protected cleanup target(s): "
                + ", ".join(result.skipped_protected_paths)
            ),
            "🛡️",
        )
    return 0


def _gate_session_is_open(repo_root: Path) -> bool:
    """Return True when the runtime gate status records an open session."""
    status_path = registry_runtime.gate_status_path(repo_root)
    if not status_path.exists():
        return False
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    return str(payload.get("session_state", "")).strip().lower() == "open"
