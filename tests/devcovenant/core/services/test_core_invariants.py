"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

MODULE = "devcovenant.core.services.core_invariants"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_core_invariant_ids_are_stable() -> None:
    """Canonical invariant ids should remain present and ordered."""
    module = importlib.import_module(MODULE)
    assert module.core_invariant_ids() == [
        "devcov-integrity-guard",
        "devcov-structure-guard",
        "devflow-run-gates",
    ]


def _unit_test_load_core_invariant_descriptor_reads_real_descriptor() -> None:
    """Real repo descriptor loading should return the invariant metadata."""
    module = importlib.import_module(MODULE)
    descriptor = module.load_core_invariant_descriptor(
        REPO_ROOT, "devflow-run-gates"
    )
    assert descriptor is not None
    assert descriptor.policy_id == "devflow-run-gates"
    assert isinstance(descriptor.metadata, dict)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_core_invariant_ids_are_stable(self):
        """Run core invariant id contract assertions."""
        _unit_test_core_invariant_ids_are_stable()

    def test_load_core_invariant_descriptor_reads_real_descriptor(self):
        """Run real-descriptor loading assertions."""
        _unit_test_load_core_invariant_descriptor_reads_real_descriptor()
