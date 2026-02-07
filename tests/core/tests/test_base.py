"""Tests for core base helpers."""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.base import CheckContext, PolicyCheck


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


def test_get_policy_config_merges_autogen_and_user_overrides() -> None:
    """User overrides should win over autogen values."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "autogen_metadata_overrides": {
                "line-length-limit": {"max_length": 79, "severity": "warning"}
            },
            "user_metadata_overrides": {
                "line-length-limit": {"severity": "error"}
            },
        },
    )
    assert context.get_policy_config("line-length-limit") == {
        "max_length": 79,
        "severity": "error",
    }


def test_get_policy_config_ignores_legacy_policies_block() -> None:
    """Legacy config.policies entries should not be used for overrides."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "policies": {"line-length-limit": {"max_length": 999}},
        },
    )
    assert context.get_policy_config("line-length-limit") == {}
