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
        "audit_digest_json_path",
        "audit_digest_txt_path",
        "append_notifications",
        "build_manifest",
        "gate_status_path",
        "global_registry_root",
        "iter_script_locations",
        "load_policy_descriptor",
        "local_registry_root",
        "manifest_path",
        "policy_registry_path",
        "profile_registry_path",
        "resolve_script_location",
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
    assert module.audit_digest_json_path
    assert module.audit_digest_txt_path
    assert module.append_notifications
    assert module.build_manifest
    assert module.ensure_manifest
    assert module.gate_status_path
    assert module.global_registry_root
    assert module.iter_script_locations
    assert module.load_manifest
    assert module.load_policy_descriptor
    assert module.local_registry_root
    assert module.manifest_path
    assert module.parse_metadata_block
    assert module.policy_registry_path
    assert module.profile_registry_path
    assert module.resolve_script_location
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


def _unit_test_generated_manifest_includes_audit_digest_artifacts() -> None:
    """Manifest generated files should include audit-digest artifacts."""
    module = importlib.import_module(MODULE)
    manifest = module.build_manifest()
    generated = manifest.get("generated", {})
    files = generated.get("files", [])
    assert (
        f"{module.LOCAL_REGISTRY_DIR}/{module.AUDIT_DIGEST_JSON_FILENAME}"
        in files
    )
    assert (
        f"{module.LOCAL_REGISTRY_DIR}/{module.AUDIT_DIGEST_TXT_FILENAME}"
        in files
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        assert module.audit_digest_json_path(repo_root) == (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "audit_digest.json"
        )
        assert module.audit_digest_txt_path(repo_root) == (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "audit_digest.txt"
        )


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
    """Service package exports should stay on the stable module surface."""
    module = importlib.import_module("devcovenant.core.services")
    exported = set(getattr(module, "__all__", []))
    expected = {
        "event",
        "metadata",
        "policy_block_refresh",
        "policy_engine",
        "policy_parse",
        "profile_registry",
        "registry",
        "translator_engine",
    }
    assert exported == expected


def _unit_test_registry_metadata_typed_view_preserves_storage_contract() -> (
    None
):
    """Registry should store strings and expose a decoded typed view."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
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

    def test_generated_manifest_includes_audit_digest_artifacts(self):
        """Run generated-manifest audit-digest artifact assertions."""
        _unit_test_generated_manifest_includes_audit_digest_artifacts()

    def test_services_export_inventory_remains_intentionally_narrow(self):
        """Run services package export inventory guard assertions."""
        _unit_test_services_export_inventory_remains_intentionally_narrow()

    def test_registry_metadata_typed_view_preserves_storage_contract(self):
        """Run registry raw-vs-typed metadata contract assertions."""
        _unit_test_registry_metadata_typed_view_preserves_storage_contract()
