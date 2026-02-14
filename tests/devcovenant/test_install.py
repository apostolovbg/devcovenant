"""Unit tests for install command behavior."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from devcovenant import install
from devcovenant.core import registry_runtime as manifest_module


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unit_test_install_writes_generic_config_and_manifest() -> None:
    """install_repo should copy core and seed generic config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        assert config_path.exists()
        config = _read_yaml(config_path)
        install_block = config.get("install", {})
        assert isinstance(install_block, dict)
        assert install_block.get("generic_config") is True
        assert config.get("devcov_core_include") is False

        profiles_block = config.get("profiles", {})
        assert isinstance(profiles_block, dict)
        assert profiles_block.get("active") == install.DEFAULT_ACTIVE_PROFILES

        manifest_path = manifest_module.manifest_path(repo_root)
        assert manifest_path.exists()


def _unit_test_install_does_not_generate_local_registry() -> None:
    """install_repo should only leave manifest scaffold in registry/local."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0

        local_registry = repo_root / "devcovenant" / "registry" / "local"
        manifest_path = local_registry / "manifest.json"
        policy_registry = local_registry / "policy_registry.yaml"
        profile_registry = local_registry / "profile_registry.yaml"
        test_status = local_registry / "test_status.json"

        assert local_registry.exists()
        assert manifest_path.exists()
        assert not policy_registry.exists()
        assert not profile_registry.exists()
        assert not test_status.exists()


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

        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0
        assert custom_file.exists()
        assert custom_file.read_text(encoding="utf-8") == "# custom\n"


def _unit_test_install_run_requires_upgrade_when_present() -> None:
    """run() should refuse existing installs and point to upgrade."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            install.install_repo(repo_root)

        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            with patch(
                "devcovenant.install.resolve_repo_root",
                return_value=repo_root,
            ):
                with patch("devcovenant.install.install_repo") as install_mock:
                    result = install.run(SimpleNamespace())

        assert result == 1
        install_mock.assert_not_called()
        output = output_buffer.getvalue()
        assert "already present" in output
        assert "devcovenant upgrade" in output


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_install_writes_generic_config_and_manifest(self):
        """Run test_install_writes_generic_config_and_manifest."""
        _unit_test_install_writes_generic_config_and_manifest()

    def test_install_does_not_generate_local_registry(self):
        """Run test_install_does_not_generate_local_registry."""
        _unit_test_install_does_not_generate_local_registry()

    def test_install_preserves_existing_custom_tree(self):
        """Run test_install_preserves_existing_custom_tree."""
        _unit_test_install_preserves_existing_custom_tree()

    def test_install_run_requires_upgrade_when_present(self):
        """Run test_install_run_requires_upgrade_when_present."""
        _unit_test_install_run_requires_upgrade_when_present()
