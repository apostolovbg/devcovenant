"""Mirrored surface sanity checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core.runtime import policy_commands


def _seed_registry(repo_root: Path) -> None:
    """Write a minimal registry payload with one policy command."""
    registry_path = repo_root / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        yaml.safe_dump(
            {
                "policies": {
                    "dependency-management": {
                        "enabled": True,
                        "runtime_actions": [
                            {
                                "id": "refresh-all",
                                "description": "Refresh dependency artifacts.",
                                "mutates_repo": True,
                            }
                        ],
                        "commands": [
                            {
                                "name": "refresh-all",
                                "help": "Refresh dependency artifacts.",
                                "runtime_action": "refresh-all",
                                "mutates_repo": True,
                                "arguments": [
                                    {
                                        "flags": ["--scope"],
                                        "dest": "scope",
                                        "help": "Refresh scope.",
                                        "default": "full",
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            sort_keys=False,
            allow_unicode=False,
        ),
        encoding="utf-8",
    )


def _unit_test_find_policy_command_resolves_declared_name() -> None:
    """Command lookup should resolve the declared canonical name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        _seed_registry(repo_root)
        canonical = policy_commands.find_policy_command(
            repo_root,
            policy_id="dependency-management",
            command_name="refresh-all",
        )
        assert canonical is not None
        assert canonical.runtime_action == "refresh-all"


def _unit_test_parse_policy_command_payload_uses_declared_arguments() -> None:
    """Declared command arguments should parse into runtime payloads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        _seed_registry(repo_root)
        command = policy_commands.find_policy_command(
            repo_root,
            policy_id="dependency-management",
            command_name="refresh-all",
        )
        assert command is not None
        payload = policy_commands.parse_policy_command_payload(
            "dependency-management",
            command,
            ["--scope", "locks"],
        )
        assert payload == {"scope": "locks"}


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_find_policy_command_resolves_declared_name(self):
        """Run canonical command resolution assertions."""
        _unit_test_find_policy_command_resolves_declared_name()

    def test_parse_policy_command_payload_uses_declared_arguments(self):
        """Run argument parsing assertions."""
        _unit_test_parse_policy_command_payload_uses_declared_arguments()
