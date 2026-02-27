"""Sanity checks for devcovenant.core.contracts.policy."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.contracts.policy"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_contract_symbols_covered() -> None:
    """Core contract classes/methods should remain available."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "ChangeState")
    assert hasattr(module, "CheckContext")
    assert hasattr(module, "FixResult")
    assert hasattr(module, "PolicyCheck")
    assert hasattr(module, "PolicyFixer")
    assert hasattr(module, "Violation")

    assert hasattr(module.CheckContext, "get_policy_config")
    assert hasattr(module.CheckContext, "is_ignored")
    assert hasattr(module.PolicyCheck, "get_metadata")
    assert hasattr(module.PolicyCheck, "get_option")
    assert hasattr(module.PolicyCheck, "run_runtime_action")
    assert hasattr(module.PolicyCheck, "scoped_changed_files")
    assert hasattr(module.PolicyCheck, "set_options")
    assert hasattr(module.PolicyFixer, "can_fix")
    assert hasattr(module.PolicyFixer, "fix")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_contract_symbols_covered(self):
        """Run core policy contract symbol assertions."""
        _unit_test_contract_symbols_covered()
