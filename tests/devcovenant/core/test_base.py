"""Tests for core base helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext, PolicyCheck


class DummyPolicy(PolicyCheck):
    """Minimal policy used for get_option tests."""

    def check(self, context):
        """Return no violations for the dummy policy."""
        return []


def _unit_test_get_option_empty_metadata_falls_back() -> None:
    """Empty metadata values should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": []}, None)
    assert policy.get_option("alpha", "default") == "default"


def _unit_test_get_option_empty_string_falls_back() -> None:
    """Empty strings should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ""}, None)
    assert policy.get_option("alpha", "default") == "default"


def _unit_test_get_option_non_empty_preserves_value() -> None:
    """Non-empty values should be returned as-is."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ["one", "two"]}, None)
    assert policy.get_option("alpha", "default") == ["one", "two"]


def _unit_test_get_policy_config_merges_autogen_and_user_overrides() -> None:
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


def _unit_test_get_policy_config_ignores_legacy_policies_block() -> None:
    """Legacy config.policies entries should not be used for overrides."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "policies": {"line-length-limit": {"max_length": 999}},
        },
    )
    assert context.get_policy_config("line-length-limit") == {}


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_get_option_empty_metadata_falls_back(self):
        """Run test_get_option_empty_metadata_falls_back."""
        _unit_test_get_option_empty_metadata_falls_back()

    def test_get_option_empty_string_falls_back(self):
        """Run test_get_option_empty_string_falls_back."""
        _unit_test_get_option_empty_string_falls_back()

    def test_get_option_non_empty_preserves_value(self):
        """Run test_get_option_non_empty_preserves_value."""
        _unit_test_get_option_non_empty_preserves_value()

    def test_get_policy_config_merges_autogen_and_user_overrides(self):
        """Run test_get_policy_config_merges_autogen_and_user_overrides."""
        _unit_test_get_policy_config_merges_autogen_and_user_overrides()

    def test_get_policy_config_ignores_legacy_policies_block(self):
        """Run test_get_policy_config_ignores_legacy_policies_block."""
        _unit_test_get_policy_config_ignores_legacy_policies_block()
