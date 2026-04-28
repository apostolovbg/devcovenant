"""Tests for the fixed DevCovenant quickstart command."""

from __future__ import annotations

import argparse
import unittest
from contextlib import redirect_stdout
from io import StringIO

import devcovenant.quickstart as quickstart


def _unit_test_quickstart_parser_uses_command_scoped_prog() -> None:
    """Quickstart parser should expose stable command-scoped help text."""
    parser = quickstart._build_parser()
    assert parser.prog == "devcovenant quickstart"
    help_text = parser.format_help()
    assert "--quiet" in help_text
    assert "--normal" in help_text
    assert "--verbose" in help_text


def _unit_test_quickstart_prints_reminder() -> None:
    """Quickstart should print one fixed ordered reminder."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        result = quickstart.run(argparse.Namespace())
    assert result == 0
    text = buffer.getvalue()
    assert "DevCovenant quickstart reminder" in text
    assert "pipx install devcovenant" in text
    assert "devcovenant install" in text
    assert "devcovenant deploy" in text
    assert "always-active baseline" in text
    assert "userproject custom profile" in text
    assert "devcovenant gate --open" in text
    assert "devcovenant demo" in text
    assert (
        text.index("1. Install the CLI in an isolated machine environment.")
        < text.index(
            "2. Install DevCovenant into the repository you want to govern."
        )
        < text.index(
            "3. Review devcovenant/config.yaml, then deploy the reviewed "
            "setup."
        )
        < text.index(
            "4. If you want the real evaluation path, run the demo instead."
        )
        < text.index(
            "5. If you are already in a governed repository, run the normal"
        )
    )
    assert "This is a reminder, not the primary onboarding path." in text


def _unit_test_quickstart_main_prints_reminder() -> None:
    """Quickstart main should dispatch to the fixed reminder."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        try:
            quickstart.main([])
        except SystemExit as exc:
            assert exc.code == 0
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from quickstart.main().")
    text = buffer.getvalue()
    assert "DevCovenant quickstart reminder" in text
    assert "devcovenant gate --close" in text
    assert "devcovenant demo" in text


class QuickstartCommandTests(unittest.TestCase):
    """unittest wrappers for quickstart command coverage."""

    def test_quickstart_parser_uses_command_scoped_prog(self):
        """Run quickstart parser help coverage."""
        _unit_test_quickstart_parser_uses_command_scoped_prog()

    def test_quickstart_prints_reminder(self):
        """Run quickstart output coverage."""
        _unit_test_quickstart_prints_reminder()

    def test_quickstart_main_prints_reminder(self):
        """Run quickstart main coverage."""
        _unit_test_quickstart_main_prints_reminder()
