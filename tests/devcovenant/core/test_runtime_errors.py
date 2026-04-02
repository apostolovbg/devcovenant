"""Mirrored tests for devcovenant.core.runtime_errors."""

from __future__ import annotations

import importlib
import unittest

MODULE = "devcovenant.core.runtime_errors"


def _contract_error_code_enum_contract() -> None:
    """Error code enum should keep stable token values."""
    module = importlib.import_module(MODULE)
    assert module.ErrorCode.INVALID_ARGUMENT.value == "invalid-argument"
    assert module.ErrorCode.MANAGED_ENVIRONMENT.value == "managed-environment"
    assert module.ErrorCode.COMMAND_RUNTIME.value == "command-runtime"
    assert module.ErrorCode.INTERNAL_ERROR.value == "internal-error"


def _contract_structured_error_renders_message_and_hint() -> None:
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


def _contract_error_exit_code_normalizes_non_positive_values() -> None:
    """Exit-code normalization should never return non-positive values."""
    module = importlib.import_module(MODULE)
    error = module.DevCovenantError(
        code=module.ErrorCode.INTERNAL_ERROR, message="boom", exit_code=0
    )
    assert error.exit_code == 1


def _contract_error_symbol_contract_is_stable() -> None:
    """Structured error symbols should remain explicit and importable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "DevCovenantError")
    assert module.DevCovenantError.__name__ == "DevCovenantError"
    assert hasattr(module.DevCovenantError, "to_display_message")


class RuntimeErrorsCasesContractTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_error_code_enum_contract(self):
        """Run ErrorCode token stability assertions."""
        _contract_error_code_enum_contract()

    def test_structured_error_renders_message_and_hint(self):
        """Run structured error rendering assertions."""
        _contract_structured_error_renders_message_and_hint()

    def test_error_exit_code_normalizes_non_positive_values(self):
        """Run error exit-code normalization assertions."""
        _contract_error_exit_code_normalizes_non_positive_values()

    def test_error_symbol_contract_is_stable(self):
        """Run structured error symbol contract assertions."""
        _contract_error_symbol_contract_is_stable()


MODULE = "devcovenant.core.runtime_errors"
CONTRACTS = "devcovenant.core.runtime_errors"


def _error_value_error_maps_to_invalid_argument() -> None:
    """ValueError should normalize to invalid-argument with exit code 2."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    normalized = runtime_module.normalize_unhandled_exception(
        ValueError("bad input")
    )
    assert normalized.code is contracts_module.ErrorCode.INVALID_ARGUMENT
    assert normalized.exit_code == 2
    assert "bad input" in normalized.message


def _error_os_error_maps_to_command_runtime() -> None:
    """OSError should normalize to command-runtime code."""
    runtime_module = importlib.import_module(MODULE)
    contracts_module = importlib.import_module(CONTRACTS)
    normalized = runtime_module.normalize_unhandled_exception(
        OSError("permission denied")
    )
    assert normalized.code is contracts_module.ErrorCode.COMMAND_RUNTIME
    assert normalized.exit_code == 1


def _error_existing_structured_error_passes_through() -> None:
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


def _error_render_error_uses_contract_renderer() -> None:
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


class RuntimeErrorsCasesErrorsTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_value_error_maps_to_invalid_argument(self):
        """Run ValueError normalization assertions."""
        _error_value_error_maps_to_invalid_argument()

    def test_os_error_maps_to_command_runtime(self):
        """Run OSError normalization assertions."""
        _error_os_error_maps_to_command_runtime()

    def test_existing_structured_error_passes_through(self):
        """Run pass-through assertions for structured errors."""
        _error_existing_structured_error_passes_through()

    def test_render_error_uses_contract_renderer(self):
        """Run runtime error render helper assertions."""
        _error_render_error_uses_contract_renderer()


MODULE = "devcovenant.core.runtime_errors"


class RuntimeErrorsTests(unittest.TestCase):
    """unittest wrappers for mirrored collector tests."""

    def test_module_importable(self) -> None:
        """Collector module should still point at the mirrored source."""
        assert importlib.import_module(MODULE) is not None
