"""Tests for runtime output-mode policy helpers."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.runtime.output"


def _unit_test_module_importable() -> None:
    """Output helper module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Output helper module should expose public symbols."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_output_symbol_contract_is_stable() -> None:
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


def _unit_test_output_symbol_assertions_cover_public_api() -> None:
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


def _unit_test_normalize_output_mode_uses_default_for_invalid_values() -> None:
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


def _unit_test_normal_mode_suppresses_test_and_managed_child_output() -> None:
    """Normal mode should suppress noisy test/managed child command output."""
    module = importlib.import_module(MODULE)
    test_plan = module.resolve_child_output_plan("normal", "test_child")
    managed_plan = module.resolve_child_output_plan(
        "normal",
        "managed_child",
    )
    assert test_plan.emit_console is False
    assert test_plan.child_output_suppressed is True
    assert test_plan.heartbeat_message == "Please wait. In progress..."
    assert managed_plan.emit_console is False
    assert managed_plan.child_output_suppressed is True
    assert managed_plan.heartbeat_message == "Please wait. In progress..."
    assert (
        module.channel_suppresses_child_output("normal", "test_child") is True
    )
    assert (
        module.channel_suppresses_child_output("normal", "managed_child")
        is True
    )


def _unit_test_normal_mode_keeps_gate_and_generic_channels_visible() -> None:
    """Normal mode should keep gate and generic channels visible."""
    module = importlib.import_module(MODULE)
    gate_plan = module.resolve_child_output_plan(
        "normal",
        "gate_child",
    )
    generic_plan = module.resolve_child_output_plan(
        "normal",
        "generic_child",
    )
    assert gate_plan.emit_console is True
    assert gate_plan.child_output_suppressed is False
    assert gate_plan.heartbeat_message == "Please wait. In progress..."
    assert generic_plan.emit_console is True
    assert generic_plan.child_output_suppressed is False
    assert generic_plan.heartbeat_message == "Please wait. In progress..."
    assert (
        module.channel_suppresses_child_output("normal", "gate_child") is False
    )


def _unit_test_quiet_mode_suppresses_all_child_channels() -> None:
    """Quiet mode should suppress all child output channels."""
    module = importlib.import_module(MODULE)
    for channel in (
        "gate_child",
        "test_child",
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


def _unit_test_verbose_mode_keeps_all_child_channels_visible() -> None:
    """Verbose mode should emit all child output without heartbeat lines."""
    module = importlib.import_module(MODULE)
    for channel in (
        "gate_child",
        "test_child",
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for runtime output helper tests."""

    def test_module_importable(self):
        """Run output helper module importability assertions."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run output helper module symbol discovery assertions."""
        _unit_test_module_has_public_symbols()

    def test_output_symbol_contract_is_stable(self):
        """Run output helper symbol-surface contract assertions."""
        _unit_test_output_symbol_contract_is_stable()

    def test_output_symbol_assertions_cover_public_api(self):
        """Run explicit output helper symbol assertions."""
        _unit_test_output_symbol_assertions_cover_public_api()

    def test_normalize_output_mode_uses_default_for_invalid_values(self):
        """Run output-mode normalization defaulting assertions."""
        _unit_test_normalize_output_mode_uses_default_for_invalid_values()

    def test_normal_mode_suppresses_test_and_managed_child_output(self):
        """Run normal-mode suppression assertions for test/managed channels."""
        _unit_test_normal_mode_suppresses_test_and_managed_child_output()

    def test_normal_mode_keeps_gate_and_generic_channels_visible(self):
        """Run normal-mode visibility assertions for gate/generic channels."""
        _unit_test_normal_mode_keeps_gate_and_generic_channels_visible()

    def test_quiet_mode_suppresses_all_child_channels(self):
        """Run quiet-mode suppression assertions for all child channels."""
        _unit_test_quiet_mode_suppresses_all_child_channels()

    def test_verbose_mode_keeps_all_child_channels_visible(self):
        """Run verbose-mode visibility assertions for all channels."""
        _unit_test_verbose_mode_keeps_all_child_channels_visible()
