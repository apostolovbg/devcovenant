"""Unit tests for metadata runtime resolution helpers."""

from __future__ import annotations

import unittest

from devcovenant.core import metadata_runtime
from devcovenant.core.registry_runtime import PolicyDescriptor


def _unit_test_policy_control_parses_boolean_strings() -> None:
    """Policy control parsing should normalize common bool spellings."""
    payload = {
        "policy_state": {
            "alpha": "true",
            "beta": "0",
            "gamma": "yes",
            "delta": "off",
        }
    }
    control = metadata_runtime.load_policy_control_config(payload)
    assert control.policy_state == {
        "alpha": True,
        "beta": False,
        "gamma": True,
        "delta": False,
    }


def _unit_test_policy_metadata_precedence_uses_user_last() -> None:
    """User overrides should win over descriptor, overlays, and autogen."""
    descriptor = PolicyDescriptor(
        policy_id="demo",
        text="Demo policy text.",
        metadata={
            "id": "demo",
            "severity": "warning",
            "enabled": "true",
            "include_globs": "*.py",
        },
    )
    context = metadata_runtime.MetadataContext(
        control=metadata_runtime.PolicyControl({"demo": True}),
        profile_overlays={
            "demo": {
                "severity": (["error"], False),
                "include_globs": (["src/**/*.py"], True),
            }
        },
        autogen_overrides={"demo": {"severity": ["info"]}},
        user_overrides={"demo": {"severity": ["critical"]}},
    )
    order, resolved = metadata_runtime.resolve_policy_metadata_map(
        "demo",
        current_order=["id", "severity", "enabled"],
        current_values={
            "id": ["demo"],
            "severity": ["warning"],
            "enabled": ["true"],
        },
        descriptor=descriptor,
        context=context,
        custom_policy=False,
    )
    assert "severity" in order
    assert resolved["severity"] == "critical"
    assert resolved["enabled"] == "true"
    assert "src/**/*.py" in resolved["include_globs"]


def _unit_test_selector_roles_are_materialized_from_legacy_keys() -> None:
    """Legacy include/exclude selectors should materialize role keys."""
    descriptor = PolicyDescriptor(
        policy_id="selectors-demo",
        text="Selector demo policy.",
        metadata={
            "id": "selectors-demo",
            "severity": "warning",
            "auto_fix": "false",
            "enforcement": "active",
            "enabled": "true",
            "custom": "false",
            "include_prefixes": "src",
            "exclude_suffixes": ".md",
        },
    )
    context = metadata_runtime.MetadataContext(
        control=metadata_runtime.PolicyControl({}),
        profile_overlays={},
        autogen_overrides={},
        user_overrides={},
    )
    _, resolved = metadata_runtime.resolve_policy_metadata_map(
        "selectors-demo",
        current_order=list(descriptor.metadata.keys()),
        current_values={
            key: metadata_runtime.metadata_value_list(value)
            for key, value in descriptor.metadata.items()
        },
        descriptor=descriptor,
        context=context,
        custom_policy=False,
    )
    roles = set(
        metadata_runtime.split_metadata_values([resolved["selector_roles"]])
    )
    assert {"include", "exclude"}.issubset(roles)
    assert "src/**" in resolved["include_globs"]
    assert "*.md" in resolved["exclude_globs"]


def _unit_test_render_metadata_block_supports_multiline_values() -> None:
    """Rendered metadata blocks should preserve multiline key formatting."""
    rendered = metadata_runtime.render_metadata_block(
        ["id", "include_globs"],
        {"id": ["demo"], "include_globs": ["*.py", "src/**/*.py"]},
    )
    assert rendered.splitlines() == [
        "id: demo",
        "include_globs: *.py",
        "  src/**/*.py",
    ]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for metadata-runtime helper behavior."""

    def test_policy_control_parses_boolean_strings(self):
        """Run test_policy_control_parses_boolean_strings."""
        _unit_test_policy_control_parses_boolean_strings()

    def test_policy_metadata_precedence_uses_user_last(self):
        """Run test_policy_metadata_precedence_uses_user_last."""
        _unit_test_policy_metadata_precedence_uses_user_last()

    def test_selector_roles_are_materialized_from_legacy_keys(self):
        """Run test_selector_roles_are_materialized_from_legacy_keys."""
        _unit_test_selector_roles_are_materialized_from_legacy_keys()

    def test_render_metadata_block_supports_multiline_values(self):
        """Run test_render_metadata_block_supports_multiline_values."""
        _unit_test_render_metadata_block_supports_multiline_values()
