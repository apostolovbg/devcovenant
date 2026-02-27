"""Sanity checks for devcovenant.core.services.event."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.services.event"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_event_symbol_contract_is_stable() -> None:
    """Event service classes/functions should keep a stable surface."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "consume_test_event_adapter_warnings")
    assert hasattr(module, "load_test_event_adapters")
    assert hasattr(module, "python_test_event_adapter_factory")
    assert hasattr(module, "TestEvent")
    assert hasattr(module, "TestEventAdapter")
    assert hasattr(module, "GenericTestEventAdapter")
    assert hasattr(module, "PythonTestEventAdapter")
    assert hasattr(module, "TestEventManager")

    assert hasattr(module.TestEvent, "to_dict")
    assert hasattr(module.TestEventAdapter, "build_event")
    assert hasattr(module.TestEventAdapter, "handles")
    assert hasattr(module.TestEventManager, "record_command")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_event_symbol_contract_is_stable(self):
        """Run event service symbol contract assertions."""
        _unit_test_event_symbol_contract_is_stable()
