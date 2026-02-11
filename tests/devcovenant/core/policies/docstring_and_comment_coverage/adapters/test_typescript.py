"""Unit tests for the TypeScript doc coverage adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.docstring_and_comment_coverage.adapters import (
    typescript as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the TypeScript adapter."""

    def test_flags_undocumented_function(self):
        """Functions without comments should be reported."""
        source = "function runTask(): void {\n  return;\n}\n"
        violations = adapter.check_file(
            path=Path("worker.ts"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_accepts_leading_comment(self):
        """A leading comment should satisfy the check."""
        source = (
            "// explains runTask\n"
            "function runTask(): void {\n"
            "  return;\n"
            "}\n"
        )
        violations = adapter.check_file(
            path=Path("worker.ts"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual([], violations)
