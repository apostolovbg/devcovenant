"""Mirrored surface sanity checks."""

from __future__ import annotations

import unittest

from tests.devcovenant import module_surface_helpers as helpers

RELATIVE_PATH = "devcovenant/core/profiles/objective-c/translator.py"
EXPECTED_TOKENS = ["translate", "can_handle"]


def _unit_test_python_file_parses() -> None:
    """Python source should parse without syntax errors."""
    helpers.assert_python_file_parses(RELATIVE_PATH)


def _unit_test_source_contains_expected_tokens() -> None:
    """Source should keep expected marker tokens."""
    helpers.assert_source_contains_tokens(RELATIVE_PATH, EXPECTED_TOKENS)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for mirrored source sanity checks."""

    def test_python_file_parses(self):
        """Run syntax-parse sanity check."""
        _unit_test_python_file_parses()

    def test_source_contains_expected_tokens(self):
        """Run source-token sanity check."""
        _unit_test_source_contains_expected_tokens()
