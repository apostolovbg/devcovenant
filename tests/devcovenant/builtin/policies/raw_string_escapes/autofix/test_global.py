"""Unit tests for raw-string-escapes global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.contracts.policy import Violation

RawStringEscapesFixer = import_module(
    "devcovenant.builtin.policies.raw_string_escapes.autofix.global"
).RawStringEscapesFixer


def _unit_test_doubles_escapes_in_target_literal() -> None:
    """Fixer should double bare backslashes in targeted token span."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "sample.py"
        source = r'value = "C:\folder\q"' + "\n"
        target.write_text(source, encoding="utf-8")

        start = (1, source.index('"'))
        end = (1, source.rindex('"') + 1)
        violation = Violation(
            policy_id="raw-string-escapes",
            severity="warning",
            message="escape",
            file_path=target,
            context={"start": start, "end": end},
        )

        fixer = RawStringEscapesFixer()
        result = fixer.fix(violation)
        assert result.success is True
        updated = target.read_text(encoding="utf-8")
        assert r"\\q" in updated


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_doubles_escapes_in_target_literal(self):
        """Run test_doubles_escapes_in_target_literal."""
        _unit_test_doubles_escapes_in_target_literal()
