"""Unit tests for the Python doc coverage adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.docstring_and_comment_coverage.adapters import (
    python as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Python adapter."""

    def test_flags_undocumented_function(self):
        """Functions without docs should be reported."""
        source = '"""module docs"""\n\ndef run_task():\n    return True\n'
        violations = adapter.check_file(
            path=Path("worker.py"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(3, violations[0].line_number)

    def test_accepts_comment_before_function(self):
        """A leading comment should satisfy the check."""
        source = (
            '"""module docs"""\n\n'
            "# explains run_task\n"
            "def run_task():\n"
            "    return True\n"
        )
        violations = adapter.check_file(
            path=Path("worker.py"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual([], violations)
