"""Mirrored tests for devcovenant.core.cli_support."""

from __future__ import annotations

import argparse
import importlib
import unittest
from types import SimpleNamespace

import devcovenant.core.cli_support as cli_args
from tests import MonkeyPatch


def _args_resolve_cli_output_mode_override_accepts_one_flag() -> None:
    """One output-mode flag should resolve to its configured mode."""
    assert (
        cli_args.resolve_cli_output_mode_override(
            ["--quiet", "check", "--all"]
        )
        == "quiet"
    )
    assert (
        cli_args.resolve_cli_output_mode_override(
            ["check", "--verbose", "--all"]
        )
        == "verbose"
    )


def _args_resolve_cli_output_mode_override_rejects_conflicts() -> None:
    """Conflicting output-mode flags should fail with a clear error."""
    try:
        cli_args.resolve_cli_output_mode_override(
            ["--quiet", "check", "--verbose"]
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError for conflicting flags.")
    assert "mutually exclusive" in message


def _args_strip_leading_output_mode_overrides_only() -> None:
    """Only leading root-level output-mode flags should be stripped."""
    assert cli_args.strip_leading_cli_output_mode_overrides(
        ["--quiet", "--verbose", "check", "--normal"]
    ) == ["check", "--normal"]
    assert cli_args.strip_leading_cli_output_mode_overrides(
        ["check", "--quiet"]
    ) == ["check", "--quiet"]


def _args_namespace_output_mode_helpers_round_trip() -> None:
    """Namespace helpers should read and apply one parsed override."""
    namespace = SimpleNamespace(output_mode_override="normal")
    captured: dict[str, object] = {}
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            cli_args.importlib,
            "import_module",
            lambda module_name: (
                SimpleNamespace(
                    configure_output_mode=lambda mode: captured.setdefault(
                        "mode", mode
                    )
                )
                if module_name == "devcovenant.core.execution"
                else None
            ),
        )
        assert (
            cli_args.output_mode_override_from_namespace(namespace) == "normal"
        )
        assert (
            cli_args.apply_output_mode_override_from_namespace(namespace)
            == "normal"
        )
    finally:
        monkeypatch.undo()
    assert captured["mode"] == "normal"


def _args_build_command_parser_uses_command_scoped_prog() -> None:
    """Command parser helper should keep stable scoped usage text."""
    parser = cli_args.build_command_parser("gate", "Gate help")
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "devcovenant gate"
    help_text = parser.format_help()
    assert "--quiet" in help_text
    assert "--normal" in help_text
    assert "--verbose" in help_text


class CliSupportCasesArgsTests(unittest.TestCase):
    """unittest wrappers for CLI argument helper tests."""

    def test_resolve_cli_output_mode_override_accepts_one_flag(self):
        """Run one-flag output-mode resolution coverage."""
        _args_resolve_cli_output_mode_override_accepts_one_flag()

    def test_resolve_cli_output_mode_override_rejects_conflicts(self):
        """Run conflicting output-mode resolution coverage."""
        _args_resolve_cli_output_mode_override_rejects_conflicts()

    def test_strip_leading_output_mode_overrides_only(self):
        """Run leading-output-mode stripping coverage."""
        _args_strip_leading_output_mode_overrides_only()

    def test_namespace_output_mode_helpers_round_trip(self):
        """Run namespace override apply/read coverage."""
        _args_namespace_output_mode_helpers_round_trip()

    def test_build_command_parser_uses_command_scoped_prog(self):
        """Run command parser usage-text coverage."""
        _args_build_command_parser_uses_command_scoped_prog()


MODULE = "devcovenant.core.cli_support"


def _output_module_importable() -> None:
    """Output helper module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _output_module_has_public_symbols() -> None:
    """Output helper module should expose public symbols."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _output_output_symbol_contract_is_stable() -> None:
    """Runtime output policy helpers should keep a stable symbol surface."""
    module = importlib.import_module(MODULE)
    expected = [
        "OutputMode",
        "ChildOutputChannel",
        "OUTPUT_MODE_DEFAULT",
        "OUTPUT_MODE_ALLOWED",
        "WAIT_PROGRESS_MESSAGE",
        "ChildOutputPlan",
        "normalize_output_mode",
        "resolve_child_output_plan",
        "channel_suppresses_child_output",
    ]
    for symbol in expected:
        assert hasattr(module, symbol), symbol


def _output_output_symbol_assertions_cover_public_api() -> None:
    """Output helper tests should assert explicit public symbols."""
    module = importlib.import_module(MODULE)
    assert module.OutputMode
    assert module.ChildOutputChannel
    assert module.OUTPUT_MODE_DEFAULT
    assert module.OUTPUT_MODE_ALLOWED
    assert module.WAIT_PROGRESS_MESSAGE
    assert module.ChildOutputPlan
    assert module.ChildOutputPlan.child_output_suppressed
    assert module.normalize_output_mode
    assert module.resolve_child_output_plan
    assert module.channel_suppresses_child_output


def _output_normalize_output_mode_uses_default_for_invalid_values() -> None:
    """Invalid mode tokens should normalize to the configured default."""
    module = importlib.import_module(MODULE)
    assert module.normalize_output_mode(None) == "verbose"
    assert module.normalize_output_mode("normal") == "normal"
    assert module.normalize_output_mode("quiet") == "quiet"
    assert module.normalize_output_mode("VERBOSE") == "verbose"
    assert module.normalize_output_mode("invalid-token") == "verbose"
    assert (
        module.normalize_output_mode("invalid-token", default="normal")
        == "normal"
    )


def _output_normal_mode_suppresses_workflow_and_managed_child_output() -> None:
    """Normal mode should suppress noisy workflow/managed child output."""
    module = importlib.import_module(MODULE)
    workflow_plan = module.resolve_child_output_plan(
        "normal", "workflow_child"
    )
    managed_plan = module.resolve_child_output_plan("normal", "managed_child")
    assert workflow_plan.emit_console is False
    assert workflow_plan.child_output_suppressed is True
    assert workflow_plan.heartbeat_message == "Please wait. In progress..."
    assert managed_plan.emit_console is False
    assert managed_plan.child_output_suppressed is True
    assert managed_plan.heartbeat_message == "Please wait. In progress..."
    assert (
        module.channel_suppresses_child_output("normal", "workflow_child")
        is True
    )
    assert (
        module.channel_suppresses_child_output("normal", "managed_child")
        is True
    )


def _output_normal_mode_keeps_gate_and_generic_channels_visible() -> None:
    """Normal mode should keep gate and generic channels visible."""
    module = importlib.import_module(MODULE)
    gate_plan = module.resolve_child_output_plan("normal", "gate_child")
    generic_plan = module.resolve_child_output_plan("normal", "generic_child")
    assert gate_plan.emit_console is True
    assert gate_plan.child_output_suppressed is False
    assert gate_plan.heartbeat_message == "Please wait. In progress..."
    assert generic_plan.emit_console is True
    assert generic_plan.child_output_suppressed is False
    assert generic_plan.heartbeat_message == "Please wait. In progress..."
    assert (
        module.channel_suppresses_child_output("normal", "gate_child") is False
    )


def _output_quiet_mode_suppresses_all_child_channels() -> None:
    """Quiet mode should suppress all child output channels."""
    module = importlib.import_module(MODULE)
    for channel in (
        "gate_child",
        "workflow_child",
        "managed_child",
        "generic_child",
    ):
        plan = module.resolve_child_output_plan("quiet", channel)
        assert plan.emit_console is False, channel
        assert plan.child_output_suppressed is True, channel
        assert plan.heartbeat_message is None, channel
        assert (
            module.channel_suppresses_child_output("quiet", channel) is True
        ), channel


def _output_verbose_mode_keeps_all_child_channels_visible() -> None:
    """Verbose mode should emit all child output without heartbeat lines."""
    module = importlib.import_module(MODULE)
    for channel in (
        "gate_child",
        "workflow_child",
        "managed_child",
        "generic_child",
    ):
        plan = module.resolve_child_output_plan("verbose", channel)
        assert plan.emit_console is True, channel
        assert plan.child_output_suppressed is False, channel
        assert plan.heartbeat_message is None, channel
        assert (
            module.channel_suppresses_child_output("verbose", channel) is False
        ), channel


class CliSupportCasesOutputTests(unittest.TestCase):
    """unittest wrappers for runtime output helper tests."""

    def test_module_importable(self):
        """Run output helper module importability assertions."""
        _output_module_importable()

    def test_module_has_public_symbols(self):
        """Run output helper module symbol discovery assertions."""
        _output_module_has_public_symbols()

    def test_output_symbol_contract_is_stable(self):
        """Run output helper symbol-surface contract assertions."""
        _output_output_symbol_contract_is_stable()

    def test_output_symbol_assertions_cover_public_api(self):
        """Run explicit output helper symbol assertions."""
        _output_output_symbol_assertions_cover_public_api()

    def test_normalize_output_mode_uses_default_for_invalid_values(self):
        """Run output-mode normalization defaulting assertions."""
        _output_normalize_output_mode_uses_default_for_invalid_values()

    def test_normal_mode_suppresses_workflow_and_managed_child_output(self):
        """Run normal-mode suppression assertions for workflow channels."""
        _output_normal_mode_suppresses_workflow_and_managed_child_output()

    def test_normal_mode_keeps_gate_and_generic_channels_visible(self):
        """Run normal-mode visibility assertions for gate/generic channels."""
        _output_normal_mode_keeps_gate_and_generic_channels_visible()

    def test_quiet_mode_suppresses_all_child_channels(self):
        """Run quiet-mode suppression assertions for all child channels."""
        _output_quiet_mode_suppresses_all_child_channels()

    def test_verbose_mode_keeps_all_child_channels_visible(self):
        """Run verbose-mode visibility assertions for all channels."""
        _output_verbose_mode_keeps_all_child_channels_visible()


MODULE = "devcovenant.core.cli_support"


class CliSupportTests(unittest.TestCase):
    """unittest wrappers for mirrored collector tests."""

    def test_module_importable(self) -> None:
        """Collector module should still point at the mirrored source."""
        assert importlib.import_module(MODULE) is not None
