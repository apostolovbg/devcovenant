"""Unit tests for the Python security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import (
    python as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Python adapter."""

    def test_flags_insecure_pattern(self):
        """eval usage should be reported."""
        source = "def run_task(value):\n    return eval(value)\n"
        violations = adapter.check_file(
            path=Path("worker.py"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(2, violations[0].line_number)

    def test_honors_allow_comment(self):
        """Allow comments should suppress flagged lines."""
        source = (
            "def run_task(value):\n"
            "    # security-scanner: allow\n"
            "    return eval(value)\n"
        )
        violations = adapter.check_file(
            path=Path("worker.py"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
