"""Sanity checks for dependency lock runtime policy helper module."""

from __future__ import annotations

import importlib
import unittest

MODULE = (
    "devcovenant.builtin.policies.dependency_license_sync."
    "dependency_lock_runtime"
)


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_runtime_symbol_contract_is_stable() -> None:
    """Runtime helper dataclasses/functions should stay available."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "LockFilePieces")
    assert hasattr(module, "LockHandlerResult")
    assert hasattr(module, "refresh_locks_and_licenses")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_runtime_symbol_contract_is_stable(self):
        """Run dependency lock runtime symbol contract assertions."""
        _unit_test_runtime_symbol_contract_is_stable()
