"""Flow-session helpers exposed from runtime execution primitives."""

from __future__ import annotations

from devcovenant.core.runtime import execution as execution_runtime_module

capture_current_numstat_snapshot = (
    execution_runtime_module.capture_current_numstat_snapshot
)
capture_current_snapshot_paths = (
    execution_runtime_module.capture_current_snapshot_paths
)
session_delta_paths = execution_runtime_module.session_delta_paths
snapshot_paths_changed_since = (
    execution_runtime_module.snapshot_paths_changed_since
)
changed_numstat_paths = execution_runtime_module.changed_numstat_paths
snapshot_signature = execution_runtime_module.snapshot_signature
normalize_snapshot_rows = execution_runtime_module.normalize_snapshot_rows
snapshot_row_style = execution_runtime_module.snapshot_row_style

__all__ = [
    "capture_current_numstat_snapshot",
    "capture_current_snapshot_paths",
    "session_delta_paths",
    "snapshot_paths_changed_since",
    "changed_numstat_paths",
    "snapshot_signature",
    "normalize_snapshot_rows",
    "snapshot_row_style",
]
