"""Tests for tracked-registry path and document helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.services.tracked_registry"


def _unit_test_module_importable() -> None:
    """Tracked registry module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_public_symbol_contract_is_stable() -> None:
    """Tracked registry should expose the tracked-registry helper surface."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "DEV_COVENANT_DIR",
        "REGISTRY_DIR",
        "REGISTRY_FILENAME",
        "REGISTRY_REL_PATH",
        "registry_root",
        "policy_registry_path",
        "profile_registry_path",
        "base_registry_document",
        "load_registry_document",
        "write_registry_document",
    ]:
        assert hasattr(module, symbol)


def _unit_test_path_helpers_resolve_tracked_locations() -> None:
    """Tracked registry helpers should resolve tracked paths only."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        assert module.registry_root(repo_root) == (
            repo_root / "devcovenant" / "registry"
        )
        assert module.policy_registry_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        assert module.profile_registry_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )


def _unit_test_document_helpers_round_trip_registry_payload() -> None:
    """Tracked registry should round-trip the normalized document payload."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        path = module.policy_registry_path(repo_root)
        payload = module.base_registry_document()
        payload["profiles"] = {"demo": {"active": True}}
        module.write_registry_document(path, payload)
        loaded = module.load_registry_document(path)
        assert loaded["profiles"] == {"demo": {"active": True}}
        assert loaded["metadata"]["schema_version"] == 1


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run tracked-registry importability assertions."""
        _unit_test_module_importable()

    def test_public_symbol_contract_is_stable(self):
        """Run tracked-registry public symbol assertions."""
        _unit_test_public_symbol_contract_is_stable()

    def test_path_helpers_resolve_tracked_locations(self):
        """Run tracked-registry path resolution assertions."""
        _unit_test_path_helpers_resolve_tracked_locations()

    def test_document_helpers_round_trip_registry_payload(self):
        """Run tracked-registry document round-trip assertions."""
        _unit_test_document_helpers_round_trip_registry_payload()
