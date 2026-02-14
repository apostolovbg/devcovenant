"""Unit tests for devcovenant.core.execution_runtime helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from devcovenant.core import execution_runtime


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for execution helper behavior."""

    def test_find_git_root_detects_parent_repo(self):
        """find_git_root should resolve the nearest parent git root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            (repo_root / ".git").mkdir()
            nested = repo_root / "src" / "module"
            nested.mkdir(parents=True)
            resolved = execution_runtime.find_git_root(nested)
            self.assertEqual(resolved, repo_root)

    def test_read_local_version_returns_none_without_init(self):
        """read_local_version returns None when __init__.py is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            (repo_root / "devcovenant").mkdir()
            self.assertIsNone(execution_runtime.read_local_version(repo_root))

    def test_read_local_version_parses_version_string(self):
        """read_local_version parses __version__ from package __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            package_dir = repo_root / "devcovenant"
            package_dir.mkdir()
            init_path = package_dir / "__init__.py"
            init_path.write_text('__version__ = "9.9.9"\n', encoding="utf-8")
            self.assertEqual(
                execution_runtime.read_local_version(repo_root),
                "9.9.9",
            )

    def test_prioritizes_unittest_before_pytest(self):
        """unittest discover should run before pytest when both exist."""
        commands = [
            ("pytest", ["pytest"]),
            (
                "python3 -m unittest discover -v",
                ["python3", "-m", "unittest", "discover", "-v"],
            ),
            ("cargo test", ["cargo", "test"]),
        ]
        ordered = execution_runtime._prioritize_python_unit_then_pytest(
            commands
        )
        self.assertEqual(
            ordered,
            [
                (
                    "python3 -m unittest discover -v",
                    ["python3", "-m", "unittest", "discover", "-v"],
                ),
                ("pytest", ["pytest"]),
                ("cargo test", ["cargo", "test"]),
            ],
        )

    @patch(
        "devcovenant.core.execution_runtime."
        "registry_runtime_module.policy_registry_path"
    )
    @patch("yaml.safe_load")
    def test_registry_required_commands_reorders_python_pair(
        self,
        mock_safe_load,
        mock_registry_path,
    ):
        """Registry commands should normalize to unittest then pytest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            registry_path = repo_root / "policy_registry.yaml"
            registry_path.write_text("policies: {}\n", encoding="utf-8")
            mock_registry_path.return_value = registry_path
            mock_safe_load.return_value = {
                "policies": {
                    "devflow-run-gates": {
                        "metadata": {
                            "required_commands": [
                                "pytest",
                                "python3 -m unittest discover -v",
                            ]
                        }
                    }
                }
            }

            commands = execution_runtime.registry_required_commands(repo_root)

            self.assertEqual(commands[0][0], "python3 -m unittest discover -v")
            self.assertEqual(commands[1][0], "pytest")

    @patch("devcovenant.core.execution_runtime._current_sha")
    def test_record_test_status_writes_contract_schema(
        self,
        current_sha_mock,
    ):
        """record_test_status should emit the Tier-C state schema."""
        current_sha_mock.return_value = "a" * 40
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            execution_runtime.record_test_status(
                repo_root,
                "python3 -m unittest discover -v && pytest",
                notes="schema check",
            )

            status_path = (
                execution_runtime.registry_runtime_module.test_status_path(
                    repo_root
                )
            )
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["command"],
                "python3 -m unittest discover -v && pytest",
            )
            self.assertEqual(
                payload["commands"],
                ["python3 -m unittest discover -v", "pytest"],
            )
            self.assertEqual(payload["sha"], "a" * 40)
            self.assertEqual(payload["notes"], "schema check")
            self.assertIsInstance(payload["last_run"], str)
            self.assertIsInstance(payload["last_run_utc"], str)
            self.assertIsInstance(payload["last_run_epoch"], (int, float))
            datetime.fromisoformat(payload["last_run"])
            datetime.fromisoformat(payload["last_run_utc"])
