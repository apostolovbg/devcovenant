"""DevCovenant-specific raw-string-escapes policy."""

from devcovenant.builtin.policies.raw_string_escapes import raw_string_escapes


class DevcovRawStringEscapesCheck(raw_string_escapes.RawStringEscapesCheck):
    """Warn on bare backslashes in DevCovenant repo strings."""

    policy_id = "devcov-raw-string-escapes"
    version = "1.0.0"
