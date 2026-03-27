"""Contract checks for workflow-session runtime helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.runtime.workflow_session"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""

    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_workflow_session_round_trip_uses_runtime_registry() -> None:
    """Workflow-session payloads should round-trip through runtime storage."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
            "anchors": {"start": {"status": "passed"}},
            "phases": {"tests": {"status": "passed"}},
            "required_phase_ids": ["tests"],
        }

        written = module.write_workflow_session(repo_root, payload)
        loaded = module.load_workflow_session(repo_root)

        assert written == module.workflow_session_path(repo_root)
        assert written.exists()
        assert loaded["session_id"] == "demo-session"
        assert loaded["anchors"] == {"start": {"status": "passed"}}
        assert loaded["phases"] == {"tests": {"status": "passed"}}
        assert loaded["required_phase_ids"] == ["tests"]


def _unit_test_phase_snapshots_share_the_session_snapshot_file() -> None:
    """Phase snapshots should merge into and resolve from session snapshots."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
        }
        snapshot = {"sample.py": "hash\tsample.py"}

        snapshot_rel_path, merged_payload = module.merge_phase_snapshot(
            repo_root,
            payload,
            "tests",
            snapshot,
        )
        resolved = module.resolve_phase_snapshot(
            repo_root,
            merged_payload,
            "tests",
        )

        assert snapshot_rel_path.endswith("session_snapshot.json")
        assert resolved == snapshot


def _unit_test_workflow_session_write_normalizes_legacy_fields() -> None:
    """Workflow-session writes should collapse legacy duplicate fields."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
            "anchors": {
                "start": {
                    "status": "passed",
                    "last_run": "2026-03-26T12:00:00+00:00",
                    "command": "devcovenant gate --start",
                }
            },
            "phases": {
                "tests": {
                    "status": "passed",
                    "last_run": "2026-03-26T12:05:00+00:00",
                    "command": "pytest && python3 -m unittest discover -v",
                }
            },
            "required_phase_ids": ["tests"],
        }

        module.write_workflow_session(repo_root, payload)
        loaded = module.load_workflow_session(repo_root)

        assert loaded["anchors"]["start"]["last_run_utc"] == (
            "2026-03-26T12:00:00+00:00"
        )
        assert loaded["anchors"]["start"]["commands"] == [
            "devcovenant gate --start"
        ]
        assert "last_run" not in loaded["anchors"]["start"]
        assert "command" not in loaded["anchors"]["start"]
        assert loaded["phases"]["tests"]["last_run_utc"] == (
            "2026-03-26T12:05:00+00:00"
        )
        assert loaded["phases"]["tests"]["commands"] == [
            "pytest",
            "python3 -m unittest discover -v",
        ]
        assert "last_run" not in loaded["phases"]["tests"]
        assert "command" not in loaded["phases"]["tests"]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for workflow-session runtime checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""

        _unit_test_module_importable()

    def test_workflow_session_round_trip_uses_runtime_registry(self):
        """Run workflow-session persistence regression assertions."""

        _unit_test_workflow_session_round_trip_uses_runtime_registry()

    def test_phase_snapshots_share_the_session_snapshot_file(self):
        """Run workflow-session snapshot regression assertions."""

        _unit_test_phase_snapshots_share_the_session_snapshot_file()

    def test_workflow_session_write_normalizes_legacy_fields(self):
        """Run workflow-session normalization regression assertions."""

        _unit_test_workflow_session_write_normalizes_legacy_fields()
