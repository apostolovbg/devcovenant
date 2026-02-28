"""Unit tests for core contract error types."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.contracts.errors"


def _unit_test_error_code_enum_contract() -> None:
    """Error code enum should keep stable token values."""
    module = importlib.import_module(MODULE)
    assert module.ErrorCode.INVALID_ARGUMENT.value == "invalid-argument"
    assert module.ErrorCode.MANAGED_ENVIRONMENT.value == "managed-environment"
    assert module.ErrorCode.COMMAND_RUNTIME.value == "command-runtime"
    assert module.ErrorCode.INTERNAL_ERROR.value == "internal-error"


def _unit_test_structured_error_renders_message_and_hint() -> None:
    """Structured errors should render deterministic output text."""
    module = importlib.import_module(MODULE)
    error = module.DevCovenantError(
        code=module.ErrorCode.INTERNAL_ERROR,
        message="boom",
        hint="inspect logs",
        exit_code=5,
        details={"foo": "bar"},
    )
    assert error.exit_code == 5
    assert error.details["foo"] == "bar"
    rendered = error.to_display_message()
    assert rendered.startswith("Error [internal-error]: boom")
    assert "Hint: inspect logs" in rendered


def _unit_test_error_exit_code_normalizes_non_positive_values() -> None:
    """Exit-code normalization should never return non-positive values."""
    module = importlib.import_module(MODULE)
    error = module.DevCovenantError(
        code=module.ErrorCode.INTERNAL_ERROR,
        message="boom",
        exit_code=0,
    )
    assert error.exit_code == 1


def _unit_test_error_symbol_contract_is_stable() -> None:
    """Structured error symbols should remain explicit and importable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "DevCovenantError")
    assert module.DevCovenantError.__name__ == "DevCovenantError"
    assert hasattr(module.DevCovenantError, "to_display_message")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_error_code_enum_contract(self):
        """Run ErrorCode token stability assertions."""
        _unit_test_error_code_enum_contract()

    def test_structured_error_renders_message_and_hint(self):
        """Run structured error rendering assertions."""
        _unit_test_structured_error_renders_message_and_hint()

    def test_error_exit_code_normalizes_non_positive_values(self):
        """Run error exit-code normalization assertions."""
        _unit_test_error_exit_code_normalizes_non_positive_values()

    def test_error_symbol_contract_is_stable(self):
        """Run structured error symbol contract assertions."""
        _unit_test_error_symbol_contract_is_stable()
