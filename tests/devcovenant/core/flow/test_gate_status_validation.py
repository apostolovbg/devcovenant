"""Tests for flow-owned gate-status validation helpers."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.flow.gate_status_validation"


def _write_status(path: Path, payload: object) -> None:
    """Write one gate-status payload fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _unit_test_valid_payload_passes() -> None:
    """Valid gate-status payloads should pass flow-owned validation."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status(
            status_path,
            {
                "last_run_utc": "2026-03-26T12:00:00+00:00",
                "commands": ["devcovenant run"],
            },
        )
        payload = module.validate_gate_status_payload(status_path)
        assert payload["commands"] == ["devcovenant run"]


def _unit_test_missing_timestamp_fails() -> None:
    """Missing `last_run_utc` should raise an explicit validation error."""
    module = importlib.import_module(MODULE)
    case = unittest.TestCase()
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status(status_path, {"commands": ["devcovenant run"]})
        with case.assertRaisesRegex(ValueError, "last_run_utc"):
            module.validate_gate_status_payload(status_path)


def _unit_test_empty_commands_fail() -> None:
    """Empty command lists should be rejected by validation."""
    module = importlib.import_module(MODULE)
    case = unittest.TestCase()
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status(
            status_path,
            {
                "last_run_utc": "2026-03-26T12:00:00+00:00",
                "commands": ["", "  "],
            },
        )
        with case.assertRaisesRegex(
            ValueError,
            "at least one executed workflow command",
        ):
            module.validate_gate_status_payload(status_path)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for flow-owned gate-status validation tests."""

    def test_valid_payload_passes(self):
        """Run valid gate-status payload assertions."""
        _unit_test_valid_payload_passes()

    def test_missing_timestamp_fails(self):
        """Run timestamp validation assertions."""
        _unit_test_missing_timestamp_fails()

    def test_empty_commands_fail(self):
        """Run commands validation assertions."""
        _unit_test_empty_commands_fail()
