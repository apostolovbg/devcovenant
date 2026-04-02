"""Tests for devcovenant.core.policy_registry."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from devcovenant.core.policy_metadata import PolicyDefinition

MODULE = "devcovenant.core.policy_registry"


def _registry_module_importable() -> None:
    """Registry module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _registry_registry_symbol_contract_is_stable() -> None:
    """Policy-registry contract symbols should remain stable."""
    module = importlib.import_module(MODULE)
    class_contract = [
        "PolicyDescriptor",
        "PolicyScriptLocation",
        "PolicySyncIssue",
        "PolicyRegistry",
    ]
    for symbol in class_contract:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))
        function_contract = [
            "iter_script_locations",
            "load_policy_descriptor",
            "resolve_script_location",
        ]
    for symbol in function_contract:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))
    registry_method_contract = [
        "calculate_full_hash",
        "check_policy_sync",
        "get_policy_hash",
        "get_policy_metadata_map",
        "get_policy_metadata_typed",
        "get_policy_runtime_state",
        "get_registry_metadata_value",
        "load",
        "save",
        "update_policy_runtime_state",
        "update_registry_metadata_value",
        "update_policy_entry",
    ]
    for symbol in registry_method_contract:
        assert hasattr(module.PolicyRegistry, symbol)
        assert callable(getattr(module.PolicyRegistry, symbol))


def _registry_registry_symbol_assertions_cover_public_api() -> None:
    """Policy-registry module should expose explicit public symbols."""
    module = importlib.import_module(MODULE)
    assert module.PolicyDescriptor
    assert module.PolicyScriptLocation
    assert module.PolicySyncIssue
    assert module.PolicyRegistry
    assert module.iter_script_locations
    assert module.load_policy_descriptor
    assert module.resolve_script_location
    assert module.PolicyRegistry.calculate_full_hash
    assert module.PolicyRegistry.check_policy_sync
    assert module.PolicyRegistry.get_policy_hash
    assert module.PolicyRegistry.get_policy_metadata_map
    assert module.PolicyRegistry.get_policy_metadata_typed
    assert module.PolicyRegistry.get_policy_runtime_state
    assert module.PolicyRegistry.get_registry_metadata_value
    assert module.PolicyRegistry.load
    assert module.PolicyRegistry.policy_ids
    assert module.PolicyRegistry.prune_policies
    assert module.PolicyRegistry.save
    assert module.PolicyRegistry.update_policy_runtime_state
    assert module.PolicyRegistry.update_registry_metadata_value
    assert module.PolicyRegistry.update_policy_entry


def _registry_registry_no_longer_owns_metadata_parse_helpers() -> None:
    """Registry module should no longer expose metadata parse helpers."""
    module = importlib.import_module(MODULE)
    assert not hasattr(module, "parse_policy_metadata_block")


def _registry_flat_core_surface_remains_importable() -> None:
    """Flat core modules should import directly without namespace shims."""
    core_module = importlib.import_module("devcovenant.core")
    exported = set(getattr(core_module, "__all__", []))
    assert exported in (set(),)
    assert "__getattr__" not in core_module.__dict__
    for module_name in (
        "devcovenant.core.policy_contract",
        "devcovenant.core.repository_paths",
        "devcovenant.core.policy_metadata",
        "devcovenant.core.policy_registry",
        "devcovenant.core.execution",
        "devcovenant.core.workflow_support",
    ):
        module = importlib.import_module(module_name)
        assert module is not None


def _registry_flat_core_root_stays_namespace_light() -> None:
    """Core root should stay a thin namespace marker, not an export shim."""
    module = importlib.import_module("devcovenant.core")
    exported = getattr(module, "__all__", None)
    assert exported in (None, [])
    assert "__getattr__" not in module.__dict__


def _registry_registry_metadata_typed_view_preserves_storage_contract() -> (
    None
):
    """Registry should store strings and expose a decoded typed view."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry = module.PolicyRegistry(registry_path, repo_root)
        policy = PolicyDefinition(
            policy_id="demo-policy",
            name="Demo Policy",
            severity="warning",
            auto_fix=False,
            enabled=True,
            custom=False,
            description="demo policy text",
            raw_metadata={"id": "demo-policy"},
        )
        registry.update_policy_entry(
            policy,
            None,
            resolved_metadata={
                "enabled": "true",
                "header_scan_lines": "4",
                "required_globs": "README.md, AGENTS.md",
                "severity": "error",
            },
        )
        reloaded = module.PolicyRegistry(registry_path, repo_root)
        raw_map = reloaded.get_policy_metadata_map("demo-policy")
        typed_map = reloaded.get_policy_metadata_typed("demo-policy")
        assert raw_map["enabled"] == "true"
        assert raw_map["header_scan_lines"] == "4"
        stored = reloaded._data["policies"]["demo-policy"]["metadata"]
        assert isinstance(stored["enabled"], str)
        assert isinstance(stored["header_scan_lines"], str)
        assert typed_map["enabled"] is True
        assert typed_map["header_scan_lines"] == 4
        assert typed_map["required_globs"] == ["README.md", "AGENTS.md"]
        assert typed_map["severity"] == "error"


def _registry_registry_can_batch_entry_updates_before_save() -> None:
    """Policy registry should support in-memory entry batching before save."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry = module.PolicyRegistry(registry_path, repo_root)
        policy = PolicyDefinition(
            policy_id="demo-policy",
            name="Demo Policy",
            severity="warning",
            auto_fix=False,
            enabled=True,
            custom=False,
            description="demo policy text",
            raw_metadata={"id": "demo-policy"},
        )
        registry.update_policy_entry(
            policy, None, resolved_metadata={"enabled": "true"}, save=False
        )
        registry.update_registry_metadata_value(
            "policy_registry_input_hash", "demo", save=False
        )
        assert not registry_path.exists()
        registry.save()
        reloaded = module.PolicyRegistry(registry_path, repo_root)
        assert (
            reloaded.get_policy_metadata_map("demo-policy")["enabled"]
            == "true"
        )
        assert (
            reloaded.get_registry_metadata_value("policy_registry_input_hash")
            == "demo"
        )


def _registry_registry_preserves_policy_runtime_state_on_entry_refresh() -> (
    None
):
    """Refreshing one policy entry should keep its stored runtime state."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry = module.PolicyRegistry(registry_path, repo_root)
        policy = PolicyDefinition(
            policy_id="demo-policy",
            name="Demo Policy",
            severity="warning",
            auto_fix=False,
            enabled=True,
            custom=False,
            description="demo policy text",
            raw_metadata={"id": "demo-policy"},
        )
        runtime_state = {
            "surfaces": {"root_workspace": {"input_fingerprint": "abc123"}}
        }
        registry.update_policy_runtime_state("demo-policy", runtime_state)
        registry.update_policy_entry(
            policy, None, resolved_metadata={"enabled": "true"}
        )
        reloaded = module.PolicyRegistry(registry_path, repo_root)
        assert (
            reloaded.get_policy_runtime_state("demo-policy") == runtime_state
        )


class PolicyRegistryTests(unittest.TestCase):
    """unittest wrappers for layered policy-registry checks."""

    def test_module_importable(self):
        """Run registry module importability check."""
        _registry_module_importable()

    def test_registry_symbol_contract_is_stable(self):
        """Run registry symbol contract assertion."""
        _registry_registry_symbol_contract_is_stable()

    def test_registry_symbol_assertions_cover_public_api(self):
        """Run registry explicit symbol coverage assertions."""
        _registry_registry_symbol_assertions_cover_public_api()

    def test_flat_core_surface_remains_importable(self):
        """Run flat-core import assertions."""
        _registry_flat_core_surface_remains_importable()

    def test_registry_no_longer_owns_metadata_parse_helpers(self):
        """Run registry metadata-parser separation assertions."""
        _registry_registry_no_longer_owns_metadata_parse_helpers()

    def test_flat_core_root_stays_namespace_light(self):
        """Run thin flat-core root export assertions."""
        _registry_flat_core_root_stays_namespace_light()

    def test_registry_metadata_typed_view_preserves_storage_contract(self):
        """Run registry raw-vs-typed metadata contract assertions."""
        _registry_registry_metadata_typed_view_preserves_storage_contract()

    def test_registry_can_batch_entry_updates_before_save(self):
        """Run registry in-memory batching assertions."""
        _registry_registry_can_batch_entry_updates_before_save()

    def test_registry_preserves_policy_runtime_state_on_entry_refresh(self):
        """Run runtime-state preservation assertions."""
        _registry_registry_preserves_policy_runtime_state_on_entry_refresh()
