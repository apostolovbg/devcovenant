"""Unit tests for cleanup target resolution and deletion helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.devcovenant import repo_seed_cache

MODULE = "devcovenant.core.services.cleanup"


def _unit_test_module_importable() -> None:
    """Cleanup service module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Cleanup service should expose its public helpers."""
    module = importlib.import_module(MODULE)
    assert module.CleanConfig
    assert module.CleanSelection
    assert module.CleanResult
    assert module.execute_cleanup
    assert module.resolve_clean_config
    assert module.resolve_clean_selection
    for symbol in [
        "CleanConfig",
        "CleanSelection",
        "CleanResult",
        "execute_cleanup",
        "resolve_clean_config",
        "resolve_clean_selection",
    ]:
        assert hasattr(module, symbol)


def _unit_test_resolve_clean_selection_defaults_to_all() -> None:
    """No explicit clean flags should resolve to all cleanup categories."""
    module = importlib.import_module(MODULE)
    selection = module.resolve_clean_selection(
        include_all=False,
        include_build=False,
        include_cache=False,
    )
    assert selection.include_build is True
    assert selection.include_cache is True
    assert selection.labels() == ("build", "cache")


def _unit_test_resolve_clean_config_merges_profiles_and_config_layers() -> (
    None
):
    """Clean config should merge profile overlays and config layers."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["profiles"]["active"] = ["global", "python", "typescript"]
        payload["clean"] = {
            "overlays": {
                "build_dirs": ["custom-build"],
                "protected_dirs": ["scratch/protected"],
            },
            "overrides": {
                "cache_globs": ["cache-only.override"],
            },
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        resolved = module.resolve_clean_config(repo_root)

        assert "build" in resolved.build_dirs
        assert "custom-build" in resolved.build_dirs
        assert ".pytype" in resolved.cache_dirs
        assert ".turbo" in resolved.cache_dirs
        assert resolved.cache_globs == ("cache-only.override",)
        assert "scratch/protected" in resolved.protected_dirs
        assert ".git" in resolved.protected_dirs
        assert "devcovenant/logs/**" in resolved.protected_globs


def _unit_test_execute_cleanup_preserves_protected() -> None:
    """Cleanup execution should remove artifacts safely."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        (repo_root / "build").mkdir()
        (repo_root / "dist").mkdir()
        (repo_root / "pkg" / "__pycache__").mkdir(parents=True)
        (repo_root / ".coverage").write_text("coverage\n", encoding="utf-8")
        (repo_root / "pkg.egg-info").mkdir()
        (repo_root / "scratch").mkdir()
        (repo_root / "scratch" / "protected").mkdir()
        (repo_root / "scratch" / "protected" / "keep.txt").write_text(
            "keep\n",
            encoding="utf-8",
        )

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["clean"] = {
            "overlays": {
                "protected_dirs": ["scratch/protected"],
            },
            "overrides": {},
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        selection = module.resolve_clean_selection(
            include_all=False,
            include_build=False,
            include_cache=True,
        )
        result = module.execute_cleanup(repo_root, selection)

        assert (repo_root / "build").exists()
        assert (repo_root / "dist").exists()
        assert not (repo_root / "pkg" / "__pycache__").exists()
        assert not (repo_root / ".coverage").exists()
        assert (repo_root / "devcovenant" / "logs").exists()
        assert (repo_root / "devcovenant" / "registry" / "local").exists()
        assert (repo_root / "scratch" / "protected").exists()
        assert result.selection.include_build is False
        assert result.selection.include_cache is True
        assert result.removed_paths
        assert result.skipped_protected_paths == ()

        all_selection = module.resolve_clean_selection(
            include_all=True,
            include_build=False,
            include_cache=False,
        )
        all_result = module.execute_cleanup(repo_root, all_selection)
        assert not (repo_root / "build").exists()
        assert not (repo_root / "dist").exists()
        assert not (repo_root / "pkg.egg-info").exists()
        assert all_result.selection.labels() == ("build", "cache")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for cleanup service regression coverage."""

    def test_module_importable(self):
        """Run cleanup service importability coverage."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run cleanup service symbol contract coverage."""
        _unit_test_module_has_public_symbols()

    def test_resolve_clean_selection_defaults_to_all(self):
        """Run clean-selection default behavior coverage."""
        _unit_test_resolve_clean_selection_defaults_to_all()

    def test_resolve_clean_config_merges_profiles_and_config_layers(self):
        """Run clean-config merge behavior coverage."""
        _unit_test_resolve_clean_config_merges_profiles_and_config_layers()

    def test_execute_cleanup_removes_selected_targets_and_preserves_protected(
        self,
    ):
        """Run cleanup execution protection coverage."""
        _unit_test_execute_cleanup_preserves_protected()
