"""Contract checks for tracked manifest inventory services."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.services.manifest_inventory"


def _unit_test_module_importable() -> None:
    """Manifest inventory module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_public_symbol_contract_is_stable() -> None:
    """Manifest inventory should expose the expected helper surface."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "DEFAULT_CORE_DIRS",
        "DEFAULT_CORE_FILES",
        "DEFAULT_DOCS_CORE",
        "DEFAULT_DOCS_OPTIONAL",
        "DEFAULT_CUSTOM_DIRS",
        "DEFAULT_CUSTOM_FILES",
        "DEFAULT_GENERATED_DIRS",
        "DEFAULT_GENERATED_FILES",
        "manifest_path",
        "build_manifest",
        "load_manifest",
        "write_manifest",
        "ensure_manifest",
    ]:
        assert hasattr(module, symbol)


def _unit_test_generated_manifest_includes_runtime_registry_artifacts() -> (
    None
):
    """Generated manifests should include runtime registry artifacts."""
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
        assert module.manifest_path(repo_root) == (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )


def _unit_test_ensure_manifest_persists_inventory() -> None:
    """ensure_manifest should create inventory when devcovenant exists."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "devcovenant").mkdir()
        manifest = module.ensure_manifest(repo_root)
        assert isinstance(manifest, dict)
        assert module.manifest_path(repo_root).exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for manifest-inventory service tests."""

    def test_module_importable(self):
        """Run manifest-inventory importability assertions."""
        _unit_test_module_importable()

    def test_public_symbol_contract_is_stable(self):
        """Run manifest-inventory public symbol assertions."""
        _unit_test_public_symbol_contract_is_stable()

    def test_generated_manifest_includes_runtime_registry_artifacts(self):
        """Run generated-manifest artifact assertions."""
        _unit_test_generated_manifest_includes_runtime_registry_artifacts()

    def test_ensure_manifest_persists_inventory(self):
        """Run manifest persistence assertions."""
        _unit_test_ensure_manifest_persists_inventory()
