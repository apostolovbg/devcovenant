"""Unit tests for the Go security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import go as adapter


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Go adapter."""

    def test_flags_insecure_pattern(self):
        """exec.Command usage should be reported."""
        source = 'package main\n\nfunc runTask() { exec.Command("sh") }\n'
        violations = adapter.check_file(
            path=Path("worker.go"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(3, violations[0].line_number)

    def test_ignores_safe_source(self):
        """Sources without risky patterns should pass."""
        source = "package main\n\nfunc runTask() {}\n"
        violations = adapter.check_file(
            path=Path("worker.go"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
