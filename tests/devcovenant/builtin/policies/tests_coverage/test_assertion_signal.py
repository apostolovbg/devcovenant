"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import inspect
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.builtin.policies.tests_coverage.assertion_signal"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_analyze_assertion_signal_tracks_python_asserts() -> None:
    """Public helpers should expose assertion results for Python tests."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_example.py"
        path.write_text(
            "def test_example():\n"
            "    assert helper_name == helper_name\n"
            "    assert helper_name == 3\n",
            encoding="utf-8",
        )
        analysis = module.analyze_assertion_signal(
            path,
            language="python",
            symbol_names=("helper_name",),
        )
        assert hasattr(module, "analyze_assertion_signal")
        assert module.has_assertion_signal(path) is True
        assert isinstance(analysis, module.AssertionSignalAnalysis)
        assert analysis.has_assertion_signal is True
        assert "helper_name" in analysis.covered_symbols


def _unit_test_python_visitor_contract_stays_explicit() -> None:
    """The Python analyzer should keep its named visitor hooks explicit."""
    module = importlib.import_module(MODULE)
    source = inspect.getsource(module._analyze_python)
    assert "visit_Assert" in source
    assert "visit_Call" in source


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_analyze_assertion_signal_tracks_python_asserts(self):
        """Run Python assertion-signal analysis sanity check."""
        _unit_test_analyze_assertion_signal_tracks_python_asserts()

    def test_python_visitor_contract_stays_explicit(self):
        """Run Python visitor-contract sanity check."""
        _unit_test_python_visitor_contract_stays_explicit()
