"""Unit tests for runtime error normalization helpers."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.runtime.errors"
CONTRACTS = "devcovenant.core.contracts.errors"


def _unit_test_value_error_maps_to_invalid_argument() -> None:
    """ValueError should normalize to invalid-argument with exit code 2."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    normalized = runtime_module.normalize_unhandled_exception(
        ValueError("bad input")
    )
    assert normalized.code is contracts_module.ErrorCode.INVALID_ARGUMENT
    assert normalized.exit_code == 2
    assert "bad input" in normalized.message


def _unit_test_os_error_maps_to_command_runtime() -> None:
    """OSError should normalize to command-runtime code."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    normalized = runtime_module.normalize_unhandled_exception(
        OSError("permission denied")
    )
    assert normalized.code is contracts_module.ErrorCode.COMMAND_RUNTIME
    assert normalized.exit_code == 1


def _unit_test_existing_structured_error_passes_through() -> None:
    """Existing structured errors should not be wrapped again."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    original = contracts_module.DevCovenantError(
        code=contracts_module.ErrorCode.MANAGED_ENVIRONMENT,
        message="managed mismatch",
        exit_code=9,
    )
    normalized = runtime_module.normalize_unhandled_exception(original)
    assert normalized is original


def _unit_test_render_error_uses_contract_renderer() -> None:
    """Render helper should delegate to contract display text."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    normalized = contracts_module.DevCovenantError(
        code=contracts_module.ErrorCode.INTERNAL_ERROR,
        message="boom",
        hint="inspect logs",
    )
    rendered = runtime_module.render_error(normalized)
    assert rendered.startswith("Error [internal-error]: boom")
    assert "Hint: inspect logs" in rendered


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_value_error_maps_to_invalid_argument(self):
        """Run ValueError normalization assertions."""
        _unit_test_value_error_maps_to_invalid_argument()

    def test_os_error_maps_to_command_runtime(self):
        """Run OSError normalization assertions."""
        _unit_test_os_error_maps_to_command_runtime()

    def test_existing_structured_error_passes_through(self):
        """Run pass-through assertions for structured errors."""
        _unit_test_existing_structured_error_passes_through()

    def test_render_error_uses_contract_renderer(self):
        """Run runtime error render helper assertions."""
        _unit_test_render_error_uses_contract_renderer()
