"""Unit tests for the Java name clarity adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.name_clarity.adapters import java as adapter


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Java adapter."""

    def test_flags_generic_identifier(self):
        """Generic variable names should be reported."""
        source = "int tmp = 1;\n"
        violations = adapter.check_file(
            path=Path("Worker.java"),
            source=source,
            policy_id="name-clarity",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_honors_allow_comment(self):
        """Allowed lines should not emit violations."""
        source = "int tmp = 1; // name-clarity: allow\n"
        violations = adapter.check_file(
            path=Path("Worker.java"),
            source=source,
            policy_id="name-clarity",
        )
        self.assertEqual([], violations)
