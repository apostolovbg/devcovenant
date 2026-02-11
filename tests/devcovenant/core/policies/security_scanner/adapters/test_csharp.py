"""Unit tests for the C# security adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.security_scanner.adapters import (
    csharp as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the C# adapter."""

    def test_flags_insecure_pattern(self):
        """Process.Start usage should be reported."""
        source = 'Process.Start("cmd.exe");\n'
        violations = adapter.check_file(
            path=Path("Worker.cs"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_ignores_safe_source(self):
        """Sources without risky patterns should pass."""
        source = "class Worker {}\n"
        violations = adapter.check_file(
            path=Path("Worker.cs"),
            source=source,
            policy_id="security-scanner",
        )
        self.assertEqual([], violations)
