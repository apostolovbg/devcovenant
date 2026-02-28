"""Typed error contracts for explicit DevCovenant runtime failures."""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class ErrorCode(str, Enum):
    """Stable error-code taxonomy for command/runtime boundaries."""

    INVALID_ARGUMENT = "invalid-argument"
    MANAGED_ENVIRONMENT = "managed-environment"
    COMMAND_RUNTIME = "command-runtime"
    INTERNAL_ERROR = "internal-error"


def _normalize_exit_code(raw_value: object) -> int:
    """Return a normalized non-zero process exit code for error paths."""
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return 1
    if value <= 0:
        return 1
    return value


class DevCovenantError(RuntimeError):
    """Structured error with stable code, optional hint, and exit code."""

    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        hint: str = "",
        exit_code: int = 1,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize one explicit DevCovenant error payload."""
        normalized_message = str(message).strip() or "Unknown error."
        super().__init__(normalized_message)
        self.code = code
        self.message = normalized_message
        self.hint = str(hint).strip()
        self.exit_code = _normalize_exit_code(exit_code)
        self.details = dict(details or {})

    def to_display_message(self) -> str:
        """Render deterministic user-facing error text."""
        lines = [f"Error [{self.code.value}]: {self.message}"]
        if self.hint:
            lines.append(f"Hint: {self.hint}")
        return "\n".join(lines)


__all__ = ["DevCovenantError", "ErrorCode"]
