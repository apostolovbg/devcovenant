"""Tests for the devcovenant module entry point."""

import unittest

import devcovenant.__main__ as entrypoint
from devcovenant import cli


def _unit_test_main_targets_cli_main() -> None:
    """Entrypoint should delegate to the CLI main function."""
    assert entrypoint.main is cli.main


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_main_targets_cli_main(self):
        """Run test_main_targets_cli_main."""
        _unit_test_main_targets_cli_main()
