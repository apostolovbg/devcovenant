"""Unit tests for internal gate status helper functions."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.flow.gate_status_helpers"


def _write_status(repo_root: Path, payload: dict[str, object]) -> Path:
    """Write one gate status payload under the local registry path."""
    status_path = (
        repo_root / "devcovenant" / "registry" / "local" / "gate_status.json"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return status_path


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_load_status_rejects_non_mapping_payload() -> None:
    """Status loader should reject non-object JSON payloads."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "gate_status.json"
        path.write_text("[1, 2, 3]\n", encoding="utf-8")
        with unittest.TestCase().assertRaises(ValueError):
            module._load_status(path)


def _unit_test_latest_pointer_skips_active_status_run() -> None:
    """Pointer resolver should skip the active `gate --status` run."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        run_logging = (
            module.execution_runtime_module.run_logging_runtime_module
        )
        run_logging.create_run_log_context(
            repo_root,
            "test",
            ["devcovenant", "test"],
        )
        current = run_logging.create_run_log_context(
            repo_root,
            "gate",
            ["devcovenant", "gate", "--status"],
        )
        module.execution_runtime_module.set_active_run_log_context(current)
        try:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
        finally:
            module.execution_runtime_module.clear_active_run_log_context()
        assert pointer is None


def _unit_test_gate_status_summary_lines_report_open_session() -> None:
    """Summary lines should include open-session fields and latest pointer."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_status(
            repo_root,
            {
                "session_id": "open-1",
                "session_state": "open",
                "pre_commit_start_epoch": 10.0,
                "pre_commit_start_utc": "2026-02-27T06:00:00+00:00",
                "last_run_epoch": 20.0,
                "last_run_utc": "2026-02-27T06:05:00+00:00",
            },
        )
        logs_root = repo_root / "devcovenant" / "logs"
        run_dir = logs_root / "20260227T060500000000Z-test"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "test",
                    "status": "success",
                    "artifacts": {
                        "summary_txt": (
                            f"devcovenant/logs/{run_dir.name}/summary.txt"
                        ),
                        "summary_json": (
                            f"devcovenant/logs/{run_dir.name}/summary.json"
                        ),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_root / "latest.json").write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "test",
                    "status": "success",
                    "run_dir": f"devcovenant/logs/{run_dir.name}",
                    "summary_txt": (
                        f"devcovenant/logs/{run_dir.name}/summary.txt"
                    ),
                    "summary_json": (
                        f"devcovenant/logs/{run_dir.name}/summary.json"
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = module._gate_status_summary_lines(repo_root)
        assert "Gate Status: open" in lines
        assert "Session ID: open-1" in lines
        assert "Last Phase: test" in lines
        assert "Session Start: 2026-02-27T06:00:00+00:00" in lines
        assert "Last Test Run: 2026-02-27T06:05:00+00:00" in lines
        assert any(
            "Latest Relevant Logs: devcovenant/logs/" in line for line in lines
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run importability sanity check."""
        _unit_test_module_importable()

    def test_load_status_rejects_non_mapping_payload(self):
        """Run status-loader payload-shape validation assertions."""
        _unit_test_load_status_rejects_non_mapping_payload()

    def test_latest_pointer_skips_active_status_run(self):
        """Run latest-pointer strict-pointer assertions for active runs."""
        _unit_test_latest_pointer_skips_active_status_run()

    def test_gate_status_summary_lines_report_open_session(self):
        """Run gate-status summary line assertions for open sessions."""
        _unit_test_gate_status_summary_lines_report_open_session()
