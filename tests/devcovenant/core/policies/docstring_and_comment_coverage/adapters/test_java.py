"""Unit tests for the Java doc coverage adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.docstring_and_comment_coverage.adapters import (
    java as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Java adapter."""

    def test_flags_undocumented_class(self):
        """Classes without comments should be reported."""
        source = "class Runner {}\n"
        violations = adapter.check_file(
            path=Path("Runner.java"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_accepts_leading_comment(self):
        """A leading comment should satisfy the check."""
        source = "/** Runner docs */\nclass Runner {}\n"
        violations = adapter.check_file(
            path=Path("Runner.java"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual([], violations)
