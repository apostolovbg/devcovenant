"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest
from types import SimpleNamespace

MODULE = "devcovenant.core.services.policy_block_refresh"


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
