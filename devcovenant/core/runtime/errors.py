"""Runtime error normalization and rendering helpers."""

from __future__ import annotations

from devcovenant.core.contracts.errors import DevCovenantError, ErrorCode

_DEFAULT_INTERNAL_HINT = (
    "Inspect run logs for traceback details and failing command context."
)


def normalize_unhandled_exception(
    error: BaseException,
) -> DevCovenantError:
    """Normalize one unexpected runtime exception into typed error form."""
    if isinstance(error, DevCovenantError):
        return error

    if isinstance(error, ValueError):
        return DevCovenantError(
            code=ErrorCode.INVALID_ARGUMENT,
            message=str(error).strip() or "Invalid argument.",
            hint="Review command arguments and configuration values.",
            exit_code=2,
        )

    if isinstance(error, OSError):
        return DevCovenantError(
            code=ErrorCode.COMMAND_RUNTIME,
            message=str(error).strip() or "Command runtime failure.",
            hint=(
                "Verify file paths, permissions, and managed-environment "
                "state."
            ),
            exit_code=1,
        )

    message = str(error).strip()
    if message:
        message = f"Unexpected runtime failure: {message}"
    else:
        message = "Unexpected runtime failure."
    return DevCovenantError(
        code=ErrorCode.INTERNAL_ERROR,
        message=message,
        hint=_DEFAULT_INTERNAL_HINT,
        exit_code=1,
    )


def render_error(error: DevCovenantError) -> str:
    """Render one typed error for console output."""
    return error.to_display_message()


__all__ = ["normalize_unhandled_exception", "render_error"]
