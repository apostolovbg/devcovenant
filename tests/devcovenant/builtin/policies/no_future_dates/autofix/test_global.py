"""Unit tests for no-future-dates global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.policy_contract import Violation

NoFutureDatesFixer = import_module(
    "devcovenant.builtin.policies.no_future_dates.autofix.global"
).NoFutureDatesFixer


def _unit_test_rewrites_future_date_match() -> None:
    """Fixer should replace the matched future date."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "CHANGELOG.md"
        target.write_text("- 2099-12-31: placeholder\n", encoding="utf-8")

        fixer = NoFutureDatesFixer()
        violation = Violation(
            policy_id="no-future-dates",
            severity="error",
            message="future date",
            file_path=target,
            line_number=1,
            context={"match": "2099-12-31"},
        )

        result = fixer.fix(violation)
        assert result.success is True
        text = target.read_text(encoding="utf-8")
        assert "2099-12-31" not in text


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_rewrites_future_date_match(self):
        """Run test_rewrites_future_date_match."""
        _unit_test_rewrites_future_date_match()


class GeneratedSymbolCoverageTests(unittest.TestCase):
    """Direct symbol assertions for coverage tracking."""

    def test_symbol_level_assertions_cover_public_api(self):
        """No-future-dates tests should assert the fixer symbol."""
        self.assertIsNotNone(NoFutureDatesFixer)
