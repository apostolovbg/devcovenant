"""Sanity checks for devcovenant.core.services.metadata."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

import yaml

from devcovenant.core.services.policy_parse import PolicyParser
from devcovenant.core.services.registry import load_policy_descriptor

MODULE = "devcovenant.core.services.metadata"
REPO_ROOT = Path(__file__).resolve().parents[4]
INITIAL_CRITICAL_BUILTIN_POLICIES = (
    "devflow-run-gates",
    "devcov-integrity-guard",
    "devcov-structure-guard",
)


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_metadata_symbol_contract_is_stable() -> None:
    """Metadata service should expose stable helpers and model classes."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "PolicyControl")
    assert hasattr(module, "MetadataContext")
    assert hasattr(module, "ResolvedPolicyMetadata")
    assert hasattr(module, "apply_policy_control")
    assert hasattr(module, "build_metadata_context")
    assert hasattr(module, "collect_profile_overlays")
    assert hasattr(module, "decode_metadata_option_value")
    assert hasattr(module, "decode_metadata_options_map")
    assert hasattr(module, "descriptor_metadata_order_values")
    assert hasattr(module, "load_policy_control_config")
    assert hasattr(module, "metadata_value_list")
    assert hasattr(module, "normalize_policy_state")
    assert hasattr(module, "render_metadata_block")
    assert hasattr(module, "resolve_policy_metadata_bundle")
    assert hasattr(module, "resolve_policy_metadata_map")
    assert hasattr(module, "split_metadata_values")


def _unit_test_apply_policy_control_preserves_critical_enablement() -> None:
    """Config disable toggles should not disable critical severity metadata."""
    module = importlib.import_module(MODULE)
    order = ["severity", "enabled"]
    values = {"severity": ["critical"], "enabled": ["true"]}
    control = module.PolicyControl(policy_state={"demo-policy": False})

    _, updated_values = module.apply_policy_control(
        list(order),
        {key: list(entries) for key, entries in values.items()},
        "demo-policy",
        control,
    )

    assert updated_values["enabled"] == ["true"]


def _unit_test_apply_policy_control_allows_noncritical_disablement() -> None:
    """Non-critical policies should still honor config disable toggles."""
    module = importlib.import_module(MODULE)
    order = ["severity", "enabled"]
    values = {"severity": ["error"], "enabled": ["true"]}
    control = module.PolicyControl(policy_state={"demo-policy": False})

    _, updated_values = module.apply_policy_control(
        list(order),
        {key: list(entries) for key, entries in values.items()},
        "demo-policy",
        control,
    )

    assert updated_values["enabled"] == ["false"]


def _unit_test_initial_critical_builtin_set_is_marked_and_config_immune() -> (
    None
):
    """Selected builtin critical policies should be marked and stay enabled."""
    module = importlib.import_module(MODULE)
    control = module.PolicyControl(
        policy_state={
            policy_id: False for policy_id in INITIAL_CRITICAL_BUILTIN_POLICIES
        }
    )
    builtin_policies_root = REPO_ROOT / "devcovenant" / "builtin" / "policies"

    for policy_id in INITIAL_CRITICAL_BUILTIN_POLICIES:
        descriptor_path = (
            builtin_policies_root
            / policy_id.replace("-", "_")
            / f"{policy_id.replace('-', '_')}.yaml"
        )
        payload = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
        metadata_block = payload.get("metadata", {})
        assert metadata_block["severity"] == "critical"

        _, updated_values = module.apply_policy_control(
            ["severity", "enabled"],
            {"severity": ["critical"], "enabled": ["true"]},
            policy_id,
            control,
        )
        assert updated_values["enabled"] == ["true"]


def _unit_test_decode_metadata_option_value_normalizes_common_shapes() -> None:
    """Metadata decoder should normalize bool/list/int/float/string values."""
    module = importlib.import_module(MODULE)

    assert module.decode_metadata_option_value(None) == ""
    assert module.decode_metadata_option_value("true") is True
    assert module.decode_metadata_option_value("False") is False
    assert module.decode_metadata_option_value("4") == 4
    assert module.decode_metadata_option_value("3.5") == 3.5
    assert module.decode_metadata_option_value("a, b, c") == [
        "a",
        "b",
        "c",
    ]
    assert module.decode_metadata_option_value(["x", "y, z", ""]) == [
        "x",
        "y",
        "z",
    ]
    assert module.decode_metadata_option_value("plain-text") == "plain-text"


def _empty_context(module):
    """Return an empty metadata context for focused bundle tests."""
    return module.MetadataContext(
        control=module.PolicyControl(policy_state={}),
        profile_overlays={},
        autogen_overlays={},
        user_overlays={},
        autogen_overrides={},
        user_overrides={},
    )


def _unit_test_resolved_bundle_preserves_string_map_contract() -> None:
    """Typed bundle should match legacy string-map resolver output."""
    module = importlib.import_module(MODULE)
    descriptor_module = importlib.import_module(
        "devcovenant.core.services.registry"
    )
    descriptor = descriptor_module.PolicyDescriptor(
        policy_id="demo-policy",
        text="demo",
        metadata={
            "severity": "error",
            "enabled": "true",
            "auto_fix": "false",
            "custom": "false",
            "header_scan_lines": "4",
            "required_globs": ["README.md", "AGENTS.md"],
        },
    )
    bundle = module.resolve_policy_metadata_bundle(
        "demo-policy",
        [],
        {},
        descriptor,
        _empty_context(module),
    )
    legacy_order, legacy_map = module.resolve_policy_metadata_map(
        "demo-policy",
        [],
        {},
        descriptor,
        _empty_context(module),
    )

    assert bundle.order == legacy_order
    assert bundle.string_map == legacy_map
    assert bundle.decode_options()["header_scan_lines"] == 4
    assert bundle.decode_options()["required_globs"] == [
        "README.md",
        "AGENTS.md",
    ]


def _unit_test_active_policy_metadata_bundle_shapes_are_valid() -> None:
    """Resolved metadata for enabled policies should keep stable shapes."""
    module = importlib.import_module(MODULE)
    parser = PolicyParser(REPO_ROOT / "AGENTS.md")
    context = module.build_metadata_context(REPO_ROOT)
    enabled_bundles = {}

    for policy in parser.parse_agents_md():
        if not policy.enabled:
            continue
        current_order = list(policy.raw_metadata.keys())
        current_values = {
            key: module.metadata_value_list(value)
            for key, value in policy.raw_metadata.items()
        }
        descriptor = load_policy_descriptor(REPO_ROOT, policy.policy_id)
        bundle = module.resolve_policy_metadata_bundle(
            policy.policy_id,
            current_order,
            current_values,
            descriptor,
            context,
            custom_policy=policy.custom,
        )
        enabled_bundles[policy.policy_id] = bundle

        assert bundle.order
        assert len(bundle.order) == len(set(bundle.order))
        assert set(bundle.order) == set(bundle.list_map.keys())
        assert set(bundle.order) == set(bundle.string_map.keys())
        assert "id" in bundle.string_map
        assert "severity" in bundle.string_map
        for values in bundle.list_map.values():
            assert isinstance(values, list)
            assert all(isinstance(item, str) for item in values)
        for value in bundle.string_map.values():
            assert isinstance(value, str)

    changelog_bundle = enabled_bundles["changelog-coverage"]
    changelog_typed = changelog_bundle.decode_options()
    assert isinstance(changelog_typed["header_scan_lines"], int)
    assert isinstance(changelog_typed["required_globs"], list)
    assert changelog_typed["header_scan_lines"] >= 1

    docs_bundle = enabled_bundles["documentation-growth-tracking"]
    docs_typed = docs_bundle.decode_options()
    assert isinstance(docs_typed["require_toc"], bool)
    assert isinstance(docs_typed["min_section_count"], int)
    assert isinstance(docs_typed["user_facing_suffixes"], list)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_metadata_symbol_contract_is_stable(self):
        """Run metadata service symbol contract assertions."""
        _unit_test_metadata_symbol_contract_is_stable()

    def test_apply_policy_control_preserves_critical_enablement(self):
        """Run critical-severity policy-state immunity assertions."""
        _unit_test_apply_policy_control_preserves_critical_enablement()

    def test_apply_policy_control_allows_noncritical_disablement(self):
        """Run non-critical policy-state disable assertions."""
        _unit_test_apply_policy_control_allows_noncritical_disablement()

    def test_initial_critical_builtin_set_is_marked_and_config_immune(self):
        """Run selected builtin critical-policy rollout assertions."""
        _unit_test_initial_critical_builtin_set_is_marked_and_config_immune()

    def test_decode_metadata_option_value_normalizes_common_shapes(self):
        """Run common metadata decoder shape assertions."""
        _unit_test_decode_metadata_option_value_normalizes_common_shapes()

    def test_resolve_policy_metadata_bundle_preserves_string_map_contract(
        self,
    ):
        """Run typed-bundle vs legacy string-map compatibility assertions."""
        _unit_test_resolved_bundle_preserves_string_map_contract()

    def test_active_policy_metadata_bundle_shapes_are_valid(self):
        """Run enabled-policy resolved-metadata shape assertions."""
        _unit_test_active_policy_metadata_bundle_shapes_are_valid()
