"""Sanity checks for devcovenant.core.flow.refresh."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.flow.refresh"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_refresh_symbol_contract_is_stable() -> None:
    """Refresh flow module should expose key orchestration symbols."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "refresh_policy_registry")
    assert hasattr(module, "refresh_repo")


def _unit_test_refresh_symbol_assertions_cover_public_api() -> None:
    """Refresh flow tests should assert explicit public helper symbols."""
    module = importlib.import_module(MODULE)
    assert module.refresh_policy_registry
    assert module.refresh_repo
    assert module.refresh_agents_policy_block


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_refresh_symbol_contract_is_stable(self):
        """Run refresh module symbol contract assertions."""
        _unit_test_refresh_symbol_contract_is_stable()

    def test_refresh_symbol_assertions_cover_public_api(self):
        """Run refresh module explicit symbol assertions."""
        _unit_test_refresh_symbol_assertions_cover_public_api()
