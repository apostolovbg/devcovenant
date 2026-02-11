"""Unit tests for the Rust doc coverage adapter."""

import unittest
from pathlib import Path

from devcovenant.core.policies.docstring_and_comment_coverage.adapters import (
    rust as adapter,
)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for the Rust adapter."""

    def test_flags_undocumented_struct(self):
        """Structs without doc comments should be reported."""
        source = "struct Runner {}\n"
        violations = adapter.check_file(
            path=Path("worker.rs"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual(1, len(violations))
        self.assertEqual(1, violations[0].line_number)

    def test_accepts_leading_doc_comment(self):
        """A leading doc comment should satisfy the check."""
        source = "/// Runner docs\nstruct Runner {}\n"
        violations = adapter.check_file(
            path=Path("worker.rs"),
            source=source,
            policy_id="docstring-and-comment-coverage",
        )
        self.assertEqual([], violations)
