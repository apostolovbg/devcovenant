"""Flow orchestration for the `devcovenant clean` command."""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.runtime.execution import print_step, runtime_print
from devcovenant.core.services import cleanup as cleanup_runtime


def clean_repo(
    repo_root: Path,
    *,
    include_all: bool,
    include_build: bool,
    include_cache: bool,
) -> int:
    """Run repository cleanup for the selected cleanup categories."""
    selection = cleanup_runtime.resolve_clean_selection(
        include_all=include_all,
        include_build=include_build,
        include_cache=include_cache,
    )
    labels = ", ".join(selection.labels()) or "none"
    print_step(f"Cleanup scope: {labels}", "🧹")

    result = cleanup_runtime.execute_cleanup(repo_root, selection)
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
