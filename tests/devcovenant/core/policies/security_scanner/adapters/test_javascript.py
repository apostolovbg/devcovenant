"""Unit tests for the JavaScript security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import (
    javascript as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the JavaScript adapter."""

    def test_flags_insecure_pattern(self):
        """eval usage should be reported."""
        source = "eval(input);\n"
        violations = adapter.check_file(
            path=Path("worker.js"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_honors_allow_comment(self):
        """Allow comments should suppress flagged lines."""
        source = "eval(input); // security-scanner: allow\n"
        violations = adapter.check_file(
            path=Path("worker.js"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
