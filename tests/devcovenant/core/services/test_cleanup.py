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


def _unit_test_resolve_clean_selection_requires_explicit_scope() -> None:
    """No explicit clean flags should be rejected."""
    module = importlib.import_module(MODULE)
    try:
        module.resolve_clean_selection(
            include_all=False,
            include_build=False,
            include_cache=False,
            include_registry=False,
            include_logs=False,
        )
    except ValueError as error:
        assert "Select at least one cleanup scope" in str(error)
    else:
        raise AssertionError("Expected explicit-scope validation failure.")


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
        assert "devcovenant/registry/runtime" in resolved.runtime_registry_dirs
        assert "devcovenant/logs/*" in resolved.logs_globs
        assert resolved.cache_globs == ("cache-only.override",)
        assert "scratch/protected" in resolved.protected_dirs
        assert ".git" in resolved.protected_dirs
        assert "devcovenant/registry/registry.yaml" in resolved.protected_globs
        assert "devcovenant/logs/README.md" in resolved.protected_globs


def _unit_test_all_empty_clean_override_block_clears_lists() -> None:
    """All-empty override blocks should now clear inherited clean lists."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["profiles"]["active"] = ["global", "python", "typescript"]
        payload["clean"]["overrides"] = {
            "build_dirs": [],
            "build_globs": [],
            "cache_dirs": [],
            "cache_globs": [],
            "runtime_registry_dirs": [],
            "runtime_registry_globs": [],
            "logs_dirs": [],
            "logs_globs": [],
            "protected_dirs": [],
            "protected_globs": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        resolved = module.resolve_clean_config(repo_root)

        assert resolved.build_dirs == ()
        assert resolved.build_globs == ()
        assert resolved.cache_dirs == ()
        assert resolved.cache_globs == ()
        assert resolved.runtime_registry_dirs == ()
        assert resolved.runtime_registry_globs == ()
        assert resolved.logs_dirs == ()
        assert resolved.logs_globs == ()


def _unit_test_explicit_empty_clean_override_clears_selected_key() -> None:
    """Explicit per-key empty overrides should clear resolved values."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["profiles"]["active"] = ["global", "python", "typescript"]
        payload["clean"]["overrides"] = {"cache_dirs": []}
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        resolved = module.resolve_clean_config(repo_root)

        assert resolved.cache_dirs == ()
        assert ".coverage.*" in resolved.cache_globs


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
        runtime_registry_dir = (
            repo_root / "devcovenant" / "registry" / "runtime"
        )
        runtime_registry_dir.mkdir(parents=True, exist_ok=True)
        (runtime_registry_dir / "gate_status.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        logs_root = repo_root / "devcovenant" / "logs"
        logs_root.mkdir(parents=True, exist_ok=True)
        (logs_root / "README.md").write_text("tracked\n", encoding="utf-8")
        run_dir = logs_root / "20260315T000000000000Z-clean-test"
        run_dir.mkdir()
        (run_dir / "summary.txt").write_text("run\n", encoding="utf-8")

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
            include_registry=False,
            include_logs=False,
        )
        result = module.execute_cleanup(repo_root, selection)

        assert (repo_root / "build").exists()
        assert (repo_root / "dist").exists()
        assert not (repo_root / "pkg" / "__pycache__").exists()
        assert not (repo_root / ".coverage").exists()
        assert (repo_root / "devcovenant" / "logs").exists()
        assert (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        ).is_file()
        assert runtime_registry_dir.exists()
        assert run_dir.exists()
        assert (repo_root / "scratch" / "protected").exists()
        assert result.selection.include_build is False
        assert result.selection.include_cache is True
        assert result.selection.include_runtime_registry is False
        assert result.selection.include_logs is False
        assert result.removed_paths
        assert result.skipped_protected_paths == ()

        registry_selection = module.resolve_clean_selection(
            include_all=False,
            include_build=False,
            include_cache=False,
            include_registry=True,
            include_logs=False,
        )
        registry_result = module.execute_cleanup(repo_root, registry_selection)
        assert not runtime_registry_dir.exists()
        assert (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        ).is_file()
        assert registry_result.selection.labels() == ("registry",)

        logs_selection = module.resolve_clean_selection(
            include_all=False,
            include_build=False,
            include_cache=False,
            include_registry=False,
            include_logs=True,
        )
        logs_result = module.execute_cleanup(repo_root, logs_selection)
        assert not run_dir.exists()
        assert (logs_root / "README.md").is_file()
        assert logs_result.selection.labels() == ("logs",)

        runtime_registry_dir.mkdir(parents=True, exist_ok=True)
        (runtime_registry_dir / "latest.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        run_dir.mkdir()
        (run_dir / "summary.txt").write_text("run\n", encoding="utf-8")
        all_selection = module.resolve_clean_selection(
            include_all=True,
            include_build=False,
            include_cache=False,
            include_registry=False,
            include_logs=False,
        )
        all_result = module.execute_cleanup(repo_root, all_selection)
        assert not (repo_root / "build").exists()
        assert not (repo_root / "dist").exists()
        assert not (repo_root / "pkg.egg-info").exists()
        assert not runtime_registry_dir.exists()
        assert not run_dir.exists()
        assert (logs_root / "README.md").is_file()
        assert (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        ).is_file()
        assert all_result.selection.labels() == (
            "build",
            "cache",
            "registry",
            "logs",
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for cleanup service regression coverage."""

    def test_module_importable(self):
        """Run cleanup service importability coverage."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run cleanup service symbol contract coverage."""
        _unit_test_module_has_public_symbols()

    def test_resolve_clean_selection_requires_explicit_scope(self):
        """Run explicit-scope validation coverage."""
        _unit_test_resolve_clean_selection_requires_explicit_scope()

    def test_resolve_clean_config_merges_profiles_and_config_layers(self):
        """Run clean-config merge behavior coverage."""
        _unit_test_resolve_clean_config_merges_profiles_and_config_layers()

    def test_all_empty_clean_override_block_clears_lists(self):
        """Run all-empty clean override replacement coverage."""
        _unit_test_all_empty_clean_override_block_clears_lists()

    def test_explicit_empty_clean_override_clears_selected_key(self):
        """Run explicit empty-list clean override coverage."""
        _unit_test_explicit_empty_clean_override_clears_selected_key()

    def test_execute_cleanup_removes_selected_targets_and_preserves_protected(
        self,
    ):
        """Run cleanup execution protection coverage."""
        _unit_test_execute_cleanup_preserves_protected()
