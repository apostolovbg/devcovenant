"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

MODULE = "devcovenant.core.lib.agents_blocks"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_descriptor_text_contract_requires_non_empty_text() -> None:
    """Policy descriptors should fail when the prose text is empty."""
    module = importlib.import_module(MODULE)
    try:
        module._descriptor_text_or_error(
            SimpleNamespace(text=""),
            "demo-policy",
        )
    except ValueError as error:
        assert "Set the `text` field" in str(error)
    else:
        raise AssertionError("Expected empty policy text to fail.")


def _unit_test_descriptor_text_contract_returns_canonical_text() -> None:
    """Policy descriptor prose should return trimmed canonical text."""
    module = importlib.import_module(MODULE)
    result = module._descriptor_text_or_error(
        SimpleNamespace(text="  Demo policy prose.  "),
        "demo-policy",
    )
    assert result == "Demo policy prose."


def _unit_test_refresh_inserts_core_invariant_block_from_registry() -> None:
    """Refresh should scaffold and populate the AGENTS invariant block."""
    module = importlib.import_module(MODULE)
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
                            "description": (
                                "Require start, test, and end evidence."
                            ),
                            "metadata": {
                                "gate_status_file": (
                                    "devcovenant/registry/runtime/"
                                    "gate_status.json"
                                )
                            },
                        }
                    }
                },
                sort_keys=False,
                allow_unicode=False,
            ),
            encoding="utf-8",
        )

        result = module.refresh_agents_core_invariant_block(
            agents_path,
            None,
            repo_root=repo_root,
        )

        content = agents_path.read_text(encoding="utf-8")
        assert result.updated is True
        assert "Require start, test, and end evidence." in content
        assert module.CORE_INVARIANTS_BEGIN in content
        assert "severity:" not in content
        assert "customizable:" not in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_descriptor_text_contract_requires_non_empty_text(self):
        """Run empty-policy-text contract assertions."""
        _unit_test_descriptor_text_contract_requires_non_empty_text()

    def test_descriptor_text_contract_returns_canonical_text(self):
        """Run canonical-policy-text contract assertions."""
        _unit_test_descriptor_text_contract_returns_canonical_text()

    def test_refresh_inserts_core_invariant_block_from_registry(self):
        """Run core-invariant block refresh assertions."""
        _unit_test_refresh_inserts_core_invariant_block_from_registry()
