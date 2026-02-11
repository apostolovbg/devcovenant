"""Unit tests for the TypeScript security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import (
    typescript as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the TypeScript adapter."""

    def test_flags_insecure_pattern(self):
        """eval usage should be reported."""
        source = "eval(input);\n"
        violations = adapter.check_file(
            path=Path("worker.ts"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_honors_allow_comment(self):
        """Allow comments should suppress flagged lines."""
        source = "eval(input); // security-scanner: allow\n"
        violations = adapter.check_file(
            path=Path("worker.ts"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
