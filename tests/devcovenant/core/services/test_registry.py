"""Sanity and contract checks for devcovenant.core.services.registry."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from devcovenant.core.services.policy_parse import PolicyDefinition

MODULE = "devcovenant.core.services.registry"


def _unit_test_module_importable() -> None:
    """Registry module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_registry_symbol_contract_is_stable() -> None:
    """Registry contract symbols should remain available and callable."""
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
        "build_manifest",
        "gate_status_path",
        "iter_script_locations",
        "latest_runtime_path",
        "load_policy_descriptor",
        "manifest_path",
        "policy_registry_path",
        "profile_registry_path",
        "registry_root",
        "resolve_script_location",
        "runtime_registry_root",
        "write_manifest",
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
        "load",
        "save",
        "update_policy_entry",
    ]
    for symbol in registry_method_contract:
        assert hasattr(module.PolicyRegistry, symbol)
        assert callable(getattr(module.PolicyRegistry, symbol))


def _unit_test_registry_symbol_assertions_cover_public_api() -> None:
    """Registry module should expose explicit public symbols."""
    module = importlib.import_module(MODULE)
    assert module.PolicyDescriptor
    assert module.PolicyScriptLocation
    assert module.PolicySyncIssue
    assert module.PolicyRegistry
    assert module.build_manifest
    assert module.ensure_manifest
    assert module.gate_status_path
    assert module.iter_script_locations
    assert module.latest_runtime_path
    assert module.load_manifest
    assert module.load_policy_descriptor
    assert module.manifest_path
    assert module.parse_metadata_block
    assert module.policy_registry_path
    assert module.profile_registry_path
    assert module.registry_root
    assert module.resolve_script_location
    assert module.runtime_registry_root
    assert module.write_manifest
    assert module.PolicyRegistry.calculate_full_hash
    assert module.PolicyRegistry.check_policy_sync
    assert module.PolicyRegistry.get_policy_hash
    assert module.PolicyRegistry.get_policy_metadata_map
    assert module.PolicyRegistry.get_policy_metadata_typed
    assert module.PolicyRegistry.load
    assert module.PolicyRegistry.policy_ids
    assert module.PolicyRegistry.prune_policies
    assert module.PolicyRegistry.save
    assert module.PolicyRegistry.update_policy_entry


def _unit_test_generated_manifest_includes_runtime_registry_artifacts() -> (
    None
):
    """Inventory generated files should include runtime registry artifacts."""
    module = importlib.import_module(MODULE)
    manifest = module.build_manifest()
    generated = manifest.get("generated", {})
    files = generated.get("files", [])
    assert (
        f"{module.RUNTIME_REGISTRY_DIR}/{module.GATE_STATUS_FILENAME}" in files
    )
    assert (
        f"{module.RUNTIME_REGISTRY_DIR}/{module.LATEST_RUNTIME_FILENAME}"
        in files
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        assert module.registry_root(repo_root) == (
            repo_root / "devcovenant" / "registry"
        )
        assert module.runtime_registry_root(repo_root) == (
            repo_root / "devcovenant" / "registry" / "runtime"
        )
        assert module.policy_registry_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        assert module.profile_registry_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        assert module.gate_status_path(repo_root) == (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        assert module.latest_runtime_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "runtime" / "latest.json"
        )
        assert module.manifest_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )


def _unit_test_parse_metadata_block_preserves_colon_continuations() -> None:
    """Registry metadata parser should keep indented values with colons."""
    module = importlib.import_module(MODULE)
    block = """
id: demo-policy
url_prefixes: http://
  https://
long_lines_contain: marker://
  token:with:colon
"""
    order, values = module.parse_metadata_block(block.strip())
    assert order == ["id", "url_prefixes", "long_lines_contain"]
    assert values["url_prefixes"] == ["http://", "https://"]
    assert values["long_lines_contain"] == ["marker://", "token:with:colon"]


def _unit_test_layered_core_namespaces_remain_importable() -> None:
    """Layered core namespaces should remain exported from root package."""
    core_module = importlib.import_module("devcovenant.core")
    exported = set(getattr(core_module, "__all__", []))

    for namespace in ["contracts", "flow", "lib", "runtime", "services"]:
        assert namespace in exported
        importlib.import_module(f"devcovenant.core.{namespace}")


def _unit_test_services_export_inventory_remains_intentionally_narrow() -> (
    None
):
    """Service package should stay a namespace marker, not an export shim."""
    module = importlib.import_module("devcovenant.core.services")
    exported = getattr(module, "__all__", None)
    assert exported in (None, [])
    assert "__getattr__" not in module.__dict__


def _unit_test_registry_metadata_typed_view_preserves_storage_contract() -> (
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered registry checks."""

    def test_module_importable(self):
        """Run registry module importability check."""
        _unit_test_module_importable()

    def test_registry_symbol_contract_is_stable(self):
        """Run registry symbol contract assertion."""
        _unit_test_registry_symbol_contract_is_stable()

    def test_registry_symbol_assertions_cover_public_api(self):
        """Run registry explicit symbol coverage assertions."""
        _unit_test_registry_symbol_assertions_cover_public_api()

    def test_layered_core_namespaces_remain_importable(self):
        """Run root namespace export/importability check."""
        _unit_test_layered_core_namespaces_remain_importable()

    def test_generated_manifest_includes_runtime_registry_artifacts(self):
        """Run inventory runtime-registry artifact assertions."""
        _unit_test_generated_manifest_includes_runtime_registry_artifacts()

    def test_parse_metadata_block_preserves_colon_continuations(self):
        """Run registry metadata-continuation parser assertions."""
        _unit_test_parse_metadata_block_preserves_colon_continuations()

    def test_services_export_inventory_remains_intentionally_narrow(self):
        """Run services package export inventory guard assertions."""
        _unit_test_services_export_inventory_remains_intentionally_narrow()

    def test_registry_metadata_typed_view_preserves_storage_contract(self):
        """Run registry raw-vs-typed metadata contract assertions."""
        _unit_test_registry_metadata_typed_view_preserves_storage_contract()
