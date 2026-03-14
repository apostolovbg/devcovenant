"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.lib.selectors"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()
