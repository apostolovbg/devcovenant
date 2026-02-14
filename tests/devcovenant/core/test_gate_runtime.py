"""Unit tests for gate runtime helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.core import gate_runtime


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for gate runtime behavior."""

    def test_load_status_handles_invalid_payload(self):
        """_load_status should return {} for invalid JSON payloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "status.json"
            status_path.write_text("{bad", encoding="utf-8")
            self.assertEqual(gate_runtime._load_status(status_path), {})

    @patch("devcovenant.core.gate_runtime._utc_now")
    @patch("devcovenant.core.gate_runtime._git_diff")
    @patch("devcovenant.core.gate_runtime._run_command")
    def test_start_gate_records_status(
        self,
        run_command_mock,
        git_diff_mock,
        utc_now_mock,
    ):
        """run_pre_commit_gate(start) should execute and write status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            git_diff_mock.side_effect = ["", ""]

            start_time = gate_runtime._dt.datetime(
                2026,
                2,
                13,
                22,
                30,
                tzinfo=gate_runtime._dt.timezone.utc,
            )
            end_time = gate_runtime._dt.datetime(
                2026,
                2,
                13,
                22,
                31,
                tzinfo=gate_runtime._dt.timezone.utc,
            )
            utc_now_mock.side_effect = [start_time, end_time]

            captured = {}

            # Capture the env passed to the hook command call.
            def _capture(command: str, env: dict[str, str] | None = None):
                captured["command"] = command
                captured["phase"] = (env or {}).get("DEVCOV_DEVFLOW_PHASE")

            run_command_mock.side_effect = _capture
            result = gate_runtime.run_pre_commit_gate(
                repo_root,
                "start",
                command="python3 -m pre_commit run --all-files",
                notes="start notes",
            )

            self.assertEqual(result, 0)
            self.assertEqual(captured["phase"], "start")
            status_path = (
                gate_runtime.registry_runtime_module.test_status_path(
                    repo_root
                )
            )
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pre_commit_start_notes"], "start notes")
            self.assertEqual(
                payload["pre_commit_start_command"],
                "python3 -m pre_commit run --all-files",
            )

    @patch("devcovenant.core.gate_runtime._utc_now")
    @patch("devcovenant.core.gate_runtime._run_tests")
    @patch("devcovenant.core.gate_runtime._run_command")
    @patch("devcovenant.core.gate_runtime._git_diff")
    def test_end_gate_reruns_hooks_after_changes(
        self,
        git_diff_mock,
        run_command_mock,
        run_tests_mock,
        utc_now_mock,
    ):
        """End gate should rerun hooks when first hook pass changes tree."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            utc_now_mock.return_value = gate_runtime._dt.datetime(
                2026,
                2,
                13,
                22,
                35,
                tzinfo=gate_runtime._dt.timezone.utc,
            )
            git_diff_mock.side_effect = [
                "before",
                "after-hooks",
                "after-hooks",
                "after-hooks",
                "after-hooks",
            ]

            result = gate_runtime.run_pre_commit_gate(repo_root, "end")

            self.assertEqual(result, 0)
            self.assertEqual(run_command_mock.call_count, 2)
            run_tests_mock.assert_called_once()

    @patch("devcovenant.core.gate_runtime._run_tests")
    @patch("devcovenant.core.gate_runtime._run_command")
    @patch("devcovenant.core.gate_runtime._git_diff")
    def test_end_gate_fails_after_max_attempts(
        self,
        git_diff_mock,
        run_command_mock,
        run_tests_mock,
    ):
        """End gate should fail when tree stays dirty after five attempts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            git_diff_mock.side_effect = [
                "a",
                "b",
                "c",
                "c",
                "d",
                "e",
                "e",
                "f",
                "g",
                "g",
                "h",
                "i",
                "i",
                "j",
                "k",
            ]

            result = gate_runtime.run_pre_commit_gate(repo_root, "end")

            self.assertEqual(result, 1)
            self.assertEqual(run_command_mock.call_count, 5)
            self.assertEqual(run_tests_mock.call_count, 5)
