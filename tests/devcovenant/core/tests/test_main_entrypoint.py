"""Tests for the devcovenant module entry point."""

import devcovenant.__main__ as entrypoint
from devcovenant import cli


def test_main_targets_cli_main() -> None:
    """Entrypoint should delegate to the CLI main function."""
    assert entrypoint.main is cli.main
