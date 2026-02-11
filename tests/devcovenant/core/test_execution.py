"""Unit tests for devcovenant.core.execution helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devcovenant.core import execution


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for execution helper behavior."""

    def test_find_git_root_detects_parent_repo(self):
        """find_git_root should resolve the nearest parent git root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            (repo_root / ".git").mkdir()
            nested = repo_root / "src" / "module"
            nested.mkdir(parents=True)
            resolved = execution.find_git_root(nested)
            self.assertEqual(resolved, repo_root)

    def test_read_local_version_returns_none_without_init(self):
        """read_local_version returns None when __init__.py is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            (repo_root / "devcovenant").mkdir()
            self.assertIsNone(execution.read_local_version(repo_root))

    def test_read_local_version_parses_version_string(self):
        """read_local_version parses __version__ from package __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            package_dir = repo_root / "devcovenant"
            package_dir.mkdir()
            init_path = package_dir / "__init__.py"
            init_path.write_text('__version__ = "9.9.9"\n', encoding="utf-8")
            self.assertEqual(execution.read_local_version(repo_root), "9.9.9")

    def test_prioritizes_unittest_before_pytest(self):
        """unittest discover should run before pytest when both exist."""
        commands = [
            ("pytest", ["pytest"]),
            (
                "python3 -m unittest discover",
                ["python3", "-m", "unittest", "discover"],
            ),
            ("cargo test", ["cargo", "test"]),
        ]
        ordered = execution._prioritize_python_unit_then_pytest(commands)
        self.assertEqual(
            ordered,
            [
                (
                    "python3 -m unittest discover",
                    ["python3", "-m", "unittest", "discover"],
                ),
                ("pytest", ["pytest"]),
                ("cargo test", ["cargo", "test"]),
            ],
        )

    @patch("devcovenant.core.execution.manifest_module.policy_registry_path")
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
                                "python3 -m unittest discover",
                            ]
                        }
                    }
                }
            }

            commands = execution.registry_required_commands(repo_root)

            self.assertEqual(commands[0][0], "python3 -m unittest discover")
            self.assertEqual(commands[1][0], "pytest")
