"""Mirrored surface sanity checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core.services import core_invariant_block_refresh


def _unit_test_refresh_inserts_core_invariant_block_from_registry() -> None:
    """Refresh should scaffold and populate the AGENTS core invariant block."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        agents_path = repo_root / "AGENTS.md"
        agents_path.write_text(
            (
                "# AGENTS\n\n"
                "<!-- DEVCOV-POLICIES:BEGIN -->\n"
                "<!-- DEVCOV-POLICIES:END -->\n"
            ),
            encoding="utf-8",
        )
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "core-invariants": {
                        "devflow-run-gates": {
                            "name": "Devflow Run Gates",
                            "severity": "critical",
                            "description": (
                                "Require start, test, and end evidence."
                            ),
                            "metadata": {},
                        }
                    }
                },
                sort_keys=False,
                allow_unicode=False,
            ),
            encoding="utf-8",
        )

        result = (
            core_invariant_block_refresh.refresh_agents_core_invariant_block(
                agents_path,
                None,
                repo_root=repo_root,
            )
        )

        content = agents_path.read_text(encoding="utf-8")
        assert result.updated is True
        assert "Require start, test, and end evidence." in content
        assert "<!-- DEVCOV-INVARIANTS:BEGIN -->" in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_refresh_inserts_core_invariant_block_from_registry(self):
        """Run block refresh assertions."""
        _unit_test_refresh_inserts_core_invariant_block_from_registry()
