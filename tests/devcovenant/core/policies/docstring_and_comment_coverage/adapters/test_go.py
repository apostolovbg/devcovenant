"""Unit tests for the Go doc coverage adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.docstring_and_comment_coverage.adapters import (
    go as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Go adapter."""

    def test_flags_undocumented_function(self):
        """Functions without comments should be reported."""
        source = "package main\n\nfunc RunTask() {}\n"
        violations = adapter.check_file(
            path=Path("worker.go"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(3, violations[0].line_number)

    def test_accepts_leading_comment(self):
        """A leading comment should satisfy the check."""
        source = (
            "package main\n\n"
            "// RunTask explains behavior\n"
            "func RunTask() {}\n"
        )
        violations = adapter.check_file(
            path=Path("worker.go"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual([], violations)
