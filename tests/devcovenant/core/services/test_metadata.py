"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from devcovenant.core.services.policy_parse import PolicyParser
from devcovenant.core.services.policy_registry import load_policy_descriptor

MODULE = "devcovenant.core.services.metadata"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
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

    assert updated_values["enabled"] == "true"


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

    assert updated_values["enabled"] == "false"


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
    """Typed bundle should match string-map resolver output."""
    module = importlib.import_module(MODULE)
    descriptor_module = importlib.import_module(
        "devcovenant.core.services.policy_registry"
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
    assert isinstance(bundle.resolution_trace, dict)
    assert isinstance(bundle.warnings, list)
    assert bundle.warning_messages() == []


def _unit_test_resolved_bundle_tracks_layer_trace_and_warnings() -> None:
    """Resolved bundles should expose layer trace and replacement warnings."""
    module = importlib.import_module(MODULE)
    descriptor_module = importlib.import_module(
        "devcovenant.core.services.policy_registry"
    )
    descriptor = descriptor_module.PolicyDescriptor(
        policy_id="demo-policy",
        text="demo",
        metadata={
            "severity": "error",
            "enabled": "true",
            "required_globs": ["README.md"],
            "header_scan_lines": "4",
        },
    )
    context = module.MetadataContext(
        control=module.PolicyControl(policy_state={"demo-policy": False}),
        profile_overlays={"demo-policy": {"required_globs": ["AGENTS.md"]}},
        autogen_overlays={},
        user_overlays={"demo-policy": {"required_globs": ["PLAN.md"]}},
        autogen_overrides={},
        user_overrides={"demo-policy": {"required_globs": ["SPEC.md"]}},
    )

    bundle = module.resolve_policy_metadata_bundle(
        "demo-policy",
        [],
        {},
        descriptor,
        context,
    )

    trace = bundle.resolution_trace["required_globs"]
    assert trace["descriptor"]["values"] == ["README.md"]
    assert trace["profile_overlays"]["values"] == ["AGENTS.md"]
    assert trace["profile_overlays"]["behavior"] == "append"
    assert trace["user_overlays"]["values"] == ["PLAN.md"]
    assert trace["user_overrides"]["values"] == ["SPEC.md"]
    assert trace["user_overrides"]["behavior"] == "replace"
    assert trace["user_overrides"]["replaced_inherited_values"] == [
        "README.md",
        "AGENTS.md",
        "PLAN.md",
    ]
    assert trace["effective"]["values"] == ["SPEC.md"]

    enabled_trace = bundle.resolution_trace["enabled"]
    assert enabled_trace["policy_state"]["values"] == ["false"]
    assert enabled_trace["effective"]["values"] == ["false"]

    assert bundle.warning_messages() == [
        "user_overrides replaces inherited metadata for "
        "`demo-policy.required_globs`; use overlays if you intended "
        "additive behavior."
    ]
    assert bundle.warnings[0]["key"] == "required_globs"
    assert bundle.warnings[0]["layer"] == "user_overrides"


def _unit_test_bundle_tracks_runtime_defaults_and_selector_derives() -> None:
    """Bundles should trace runtime defaults and selector-derived fields."""
    module = importlib.import_module(MODULE)
    descriptor_module = importlib.import_module(
        "devcovenant.core.services.policy_registry"
    )
    descriptor = descriptor_module.PolicyDescriptor(
        policy_id="demo-policy",
        text="demo",
        metadata={
            "watch_prefixes": ["docs"],
        },
    )

    bundle = module.resolve_policy_metadata_bundle(
        "demo-policy",
        [],
        {},
        descriptor,
        _empty_context(module),
    )

    severity_trace = bundle.resolution_trace["severity"]
    assert severity_trace["runtime_defaults"]["values"] == ["warning"]
    assert severity_trace["effective"]["values"] == ["warning"]

    watch_globs_trace = bundle.resolution_trace["watch_globs"]
    assert watch_globs_trace["derived_selectors"]["behavior"] == "derive"
    assert watch_globs_trace["effective"]["values"] == ["docs/**"]


def _unit_test_profile_overlays_collect_policy_sections() -> None:
    """Profile metadata collection should honor policy overlays only."""
    module = importlib.import_module(MODULE)
    original = module.profile_runtime.load_profile_registry
    try:
        module.profile_runtime.load_profile_registry = lambda repo_root: {
            "global": {
                "policy_overlays": {"demo-policy": {"header_scan_lines": "4"}},
            }
        }
        overlays = module.collect_profile_overlays(REPO_ROOT, ["global"])
    finally:
        module.profile_runtime.load_profile_registry = original

    assert overlays["demo-policy"]["header_scan_lines"] == "4"


def _unit_test_profile_overlays_preserve_structured_mapping_lists() -> None:
    """Structured overlay lists should stay structured and merge by id."""
    module = importlib.import_module(MODULE)
    original = module.profile_runtime.load_profile_registry
    try:
        module.profile_runtime.load_profile_registry = lambda repo_root: {
            "global": {
                "policy_overlays": {
                    "demo-policy": {
                        "surfaces": [
                            {
                                "id": "root_workspace",
                                "lock_file": "requirements.lock",
                            }
                        ]
                    }
                }
            },
            "custom": {
                "policy_overlays": {
                    "demo-policy": {
                        "surfaces": [
                            {
                                "id": "root_workspace",
                                "generate_hashes": "false",
                            },
                            {
                                "id": "package_runtime",
                                "lock_file": "pkg/runtime-requirements.lock",
                            },
                        ]
                    }
                }
            },
        }
        overlays = module.collect_profile_overlays(
            REPO_ROOT, ["global", "custom"]
        )
    finally:
        module.profile_runtime.load_profile_registry = original

    surfaces = overlays["demo-policy"]["surfaces"]
    assert isinstance(surfaces, list)
    assert surfaces[0]["id"] == "root_workspace"
    assert surfaces[0]["lock_file"] == "requirements.lock"
    assert surfaces[0]["generate_hashes"] == "false"
    assert surfaces[1]["id"] == "package_runtime"


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
        assert isinstance(bundle.resolution_trace, dict)
        assert isinstance(bundle.warnings, list)
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

    def test_decode_metadata_option_value_normalizes_common_shapes(self):
        """Run common metadata decoder shape assertions."""
        _unit_test_decode_metadata_option_value_normalizes_common_shapes()

    def test_resolve_policy_metadata_bundle_preserves_string_map_contract(
        self,
    ):
        """Run typed-bundle vs string-map compatibility assertions."""
        _unit_test_resolved_bundle_preserves_string_map_contract()

    def test_resolve_policy_metadata_bundle_tracks_layer_trace_and_warnings(
        self,
    ):
        """Run resolution-trace and override-warning assertions."""
        _unit_test_resolved_bundle_tracks_layer_trace_and_warnings()

    def test_resolve_policy_metadata_bundle_records_runtime_defaults(self):
        """Run runtime-default and derived-selector trace assertions."""
        _unit_test_bundle_tracks_runtime_defaults_and_selector_derives()

    def test_profile_overlays_collect_policy_sections(self):
        """Run policy-overlay collection assertions."""
        _unit_test_profile_overlays_collect_policy_sections()

    def test_active_policy_metadata_bundle_shapes_are_valid(self):
        """Run enabled-policy resolved-metadata shape assertions."""
        _unit_test_active_policy_metadata_bundle_shapes_are_valid()

    def test_profile_overlays_preserve_structured_mapping_lists(self):
        """Run structured overlay-list preservation assertions."""
        _unit_test_profile_overlays_preserve_structured_mapping_lists()
