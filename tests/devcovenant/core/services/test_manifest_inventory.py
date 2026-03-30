"""Contract checks for tracked manifest inventory services."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install

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
        "DEFAULT_AVAILABLE_DOCS",
        "DEFAULT_ENABLED_DOCS",
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


def _unit_test_manifest_tracks_available_and_enabled_docs() -> None:
    """Manifest inventory should separate available from enabled docs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        install.install_repo(repo_root)

        manifest = module.ensure_manifest(repo_root)
        assert manifest is not None
        docs = manifest["docs"]

        assert "SECURITY.md" in docs["available"]
        assert "PRIVACY.md" in docs["available"]
        assert "SUPPORT.md" in docs["available"]
        assert "AGENTS.md" in docs["enabled"]
        assert "SECURITY.md" not in docs["enabled"]

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["doc_assets"] = {
            "autogen": ["AGENTS.md", "SECURITY.md"],
            "user": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        refreshed = module.ensure_manifest(repo_root)
        assert refreshed is not None
        assert refreshed["docs"]["enabled"] == ["AGENTS.md", "SECURITY.md"]


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

    def test_manifest_tracks_available_and_enabled_docs(self):
        """Run available-vs-enabled doc inventory assertions."""
        _unit_test_manifest_tracks_available_and_enabled_docs()
