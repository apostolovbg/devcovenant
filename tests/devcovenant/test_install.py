"""Unit tests for install command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core import manifest as manifest_module


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unit_test_install_writes_generic_config_and_manifest() -> None:
    """install_repo should copy core and seed generic config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        result = install.install_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        assert config_path.exists()
        config = _read_yaml(config_path)
        install_block = config.get("install", {})
        assert isinstance(install_block, dict)
        assert install_block.get("generic_config") is True

        manifest_path = manifest_module.manifest_path(repo_root)
        assert manifest_path.exists()


def _unit_test_install_preserves_existing_custom_tree() -> None:
    """install_repo should preserve custom policy/profile content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        custom_file = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_text("# custom\n", encoding="utf-8")

        result = install.install_repo(repo_root)
        assert result == 0
        assert custom_file.exists()
        assert custom_file.read_text(encoding="utf-8") == "# custom\n"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_install_writes_generic_config_and_manifest(self):
        """Run test_install_writes_generic_config_and_manifest."""
        _unit_test_install_writes_generic_config_and_manifest()

    def test_install_preserves_existing_custom_tree(self):
        """Run test_install_preserves_existing_custom_tree."""
        _unit_test_install_preserves_existing_custom_tree()
