"""Unit tests for the Rust security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import rust as adapter


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Rust adapter."""

    def test_flags_insecure_pattern(self):
        """unsafe blocks should be reported."""
        source = "unsafe { run_task(); }\n"
        violations = adapter.check_file(
            path=Path("worker.rs"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_ignores_safe_source(self):
        """Sources without risky patterns should pass."""
        source = "fn run_task() {}\n"
        violations = adapter.check_file(
            path=Path("worker.rs"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
