"""Unit tests for the Java security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import java as adapter


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Java adapter."""

    def test_flags_insecure_pattern(self):
        """Runtime.exec usage should be reported."""
        source = "Runtime.getRuntime().exec(cmd);\n"
        violations = adapter.check_file(
            path=Path("Worker.java"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_ignores_safe_source(self):
        """Sources without risky patterns should pass."""
        source = "class Worker {}\n"
        violations = adapter.check_file(
            path=Path("Worker.java"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
