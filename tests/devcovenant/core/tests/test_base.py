"""Tests for core base helpers."""

from __future__ import annotations

from devcovenant.core.base import PolicyCheck


class DummyPolicy(PolicyCheck):
    """Minimal policy used for get_option tests."""

    def check(self, context):
        """Return no violations for the dummy policy."""
        return []


def test_get_option_empty_metadata_falls_back() -> None:
    """Empty metadata values should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": []}, None)
    assert policy.get_option("alpha", "default") == "default"


def test_get_option_empty_string_falls_back() -> None:
    """Empty strings should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ""}, None)
    assert policy.get_option("alpha", "default") == "default"


def test_get_option_non_empty_preserves_value() -> None:
    """Non-empty values should be returned as-is."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ["one", "two"]}, None)
    assert policy.get_option("alpha", "default") == ["one", "two"]
