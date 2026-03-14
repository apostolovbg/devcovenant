"""Mirrored surface sanity checks."""

from __future__ import annotations

import unittest

from tests.devcovenant import module_surface_helpers as helpers

MODULE = "devcovenant.core.profiles.java.translator"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    helpers.assert_module_importable(MODULE)


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose public names."""
    helpers.assert_module_has_public_symbols(MODULE)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for mirrored module sanity checks."""

    def test_module_importable(self):
        """Run importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run public-symbol sanity check."""
        _unit_test_module_has_public_symbols()
