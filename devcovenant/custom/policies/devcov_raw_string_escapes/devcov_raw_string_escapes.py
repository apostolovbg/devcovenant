"""DevCovenant-specific raw-string-escapes policy."""

from devcovenant.core.policies.raw_string_escapes.raw_string_escapes import (
    RawStringEscapesCheck,
)


class DevcovRawStringEscapesCheck(RawStringEscapesCheck):
    """Warn on bare backslashes in DevCovenant repo strings."""

    policy_id = "devcov-raw-string-escapes"
    version = "1.0.0"
