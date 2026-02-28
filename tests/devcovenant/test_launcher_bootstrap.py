"""Tests for lightweight launcher bootstrap pycache-prefix behavior."""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.launcher_bootstrap"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_launcher_bootstrap_symbol_contract_is_stable() -> None:
    """Launcher bootstrap helpers should keep a stable public surface."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "apply_repo_pycache_prefix_from_cwd")
    assert hasattr(module, "apply_repo_pycache_prefix_from_start_path")
    assert hasattr(module, "default_repo_pycache_prefix")
    assert hasattr(module, "find_git_root_for_launcher_bootstrap")
    assert hasattr(module, "resolve_repo_pycache_prefix_from_config")


def _restore_pycache_state(
    module,
    previous_env: str | None,
    previous_prefix: object,
) -> None:
    """Restore env/runtime pycache-prefix state after bootstrap tests."""
    if previous_env is None:
        os.environ.pop("PYTHONPYCACHEPREFIX", None)
    else:
        os.environ["PYTHONPYCACHEPREFIX"] = previous_env
    try:
        module.sys.pycache_prefix = previous_prefix
    except (AttributeError, TypeError):
        pass


def _unit_test_resolve_repo_pycache_prefix_uses_repo_profile_default() -> None:
    """Repo profile should seed enabled pycache routing for launcher reads."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "profiles:\n"
            "  active:\n"
            "  - devcovrepo\n"
            "engine:\n"
            "  output_mode: normal\n",
            encoding="utf-8",
        )
        enabled, prefix = module.resolve_repo_pycache_prefix_from_config(
            repo_root
        )
        assert enabled is True
        assert prefix
        assert "/devcovenant-pycache/" in prefix.replace("\\", "/")


def _unit_test_resolve_repo_pycache_prefix_honors_disable_flag() -> None:
    """Explicit disable should win over repo-profile default enablement."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "profiles:\n"
            "  active:\n"
            "  - devcovrepo\n"
            "engine:\n"
            "  pycache_prefix_enabled: false\n",
            encoding="utf-8",
        )
        enabled, prefix = module.resolve_repo_pycache_prefix_from_config(
            repo_root
        )
        assert enabled is False
        assert prefix is None


def _unit_test_resolve_repo_pycache_prefix_honors_relative_path() -> None:
    """Relative prefix values should resolve against the repo root."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "engine:\n"
            "  pycache_prefix_enabled: true\n"
            "  pycache_prefix: .cache/pycache\n",
            encoding="utf-8",
        )
        enabled, prefix = module.resolve_repo_pycache_prefix_from_config(
            repo_root
        )
        assert enabled is True
        assert prefix == str(repo_root / ".cache" / "pycache")


def _unit_test_apply_repo_pycache_prefix_sets_env_and_runtime_prefix() -> None:
    """Bootstrap apply should set env and runtime prefix for launcher path."""
    module = importlib.import_module(MODULE)
    previous_env = os.environ.get("PYTHONPYCACHEPREFIX")
    previous_prefix = getattr(module.sys, "pycache_prefix", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".git").mkdir()
            start_dir = repo_root / "nested" / "dir"
            start_dir.mkdir(parents=True, exist_ok=True)
            config_path = repo_root / "devcovenant" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                "engine:\n"
                "  pycache_prefix_enabled: true\n"
                "  pycache_prefix: ''\n",
                encoding="utf-8",
            )
            applied = module.apply_repo_pycache_prefix_from_start_path(
                start_dir
            )
            assert applied is True
            resolved = os.environ.get("PYTHONPYCACHEPREFIX")
            assert resolved
            assert getattr(module.sys, "pycache_prefix", None) == resolved
            assert Path(resolved).is_dir()
    finally:
        _restore_pycache_state(module, previous_env, previous_prefix)


def _unit_test_apply_repo_pycache_prefix_returns_false_without_repo() -> None:
    """Bootstrap apply should no-op outside git repositories."""
    module = importlib.import_module(MODULE)
    previous_env = os.environ.get("PYTHONPYCACHEPREFIX")
    previous_prefix = getattr(module.sys, "pycache_prefix", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            applied = module.apply_repo_pycache_prefix_from_start_path(
                Path(tmpdir)
            )
            assert applied is False
    finally:
        _restore_pycache_state(module, previous_env, previous_prefix)


def _unit_test_cli_and_main_use_shared_launcher_bootstrap() -> None:
    """Entry points should import the shared launcher bootstrap helper."""
    cli_text = (REPO_ROOT / "devcovenant" / "cli.py").read_text(
        encoding="utf-8"
    )
    main_text = (REPO_ROOT / "devcovenant" / "__main__.py").read_text(
        encoding="utf-8"
    )
    assert "apply_repo_pycache_prefix_from_cwd" in cli_text
    assert "apply_repo_pycache_prefix_from_cwd" in main_text
    assert "def _config_requests_pycache_prefix" not in cli_text
    assert "def _config_requests_pycache_prefix" not in main_text
    assert "def _default_repo_pycache_prefix" not in cli_text
    assert "def _default_repo_pycache_prefix" not in main_text


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for launcher bootstrap regressions."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_launcher_bootstrap_symbol_contract_is_stable(self):
        """Run launcher-bootstrap public symbol contract assertions."""
        _unit_test_launcher_bootstrap_symbol_contract_is_stable()

    def test_resolve_repo_pycache_prefix_uses_repo_profile_default(self):
        """Run repo-profile default pycache-prefix bootstrap assertions."""
        _unit_test_resolve_repo_pycache_prefix_uses_repo_profile_default()

    def test_resolve_repo_pycache_prefix_honors_disable_flag(self):
        """Run explicit disable pycache-prefix bootstrap assertions."""
        _unit_test_resolve_repo_pycache_prefix_honors_disable_flag()

    def test_resolve_repo_pycache_prefix_honors_relative_path(self):
        """Run relative pycache-prefix bootstrap path resolution assertions."""
        _unit_test_resolve_repo_pycache_prefix_honors_relative_path()

    def test_apply_repo_pycache_prefix_sets_env_and_runtime_prefix(self):
        """Run launcher bootstrap apply env/runtime-prefix assertions."""
        _unit_test_apply_repo_pycache_prefix_sets_env_and_runtime_prefix()

    def test_apply_repo_pycache_prefix_returns_false_without_repo(self):
        """Run launcher bootstrap no-repo no-op assertions."""
        _unit_test_apply_repo_pycache_prefix_returns_false_without_repo()

    def test_cli_and_main_use_shared_launcher_bootstrap(self):
        """Run source checks for shared launcher bootstrap usage."""
        _unit_test_cli_and_main_use_shared_launcher_bootstrap()


if __name__ == "__main__":
    unittest.main()
