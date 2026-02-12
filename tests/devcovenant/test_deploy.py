"""Unit tests for deploy command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import deploy, install, refresh


def _set_generic_flag(repo_root: Path, enabled: bool) -> None:
    """Set install.generic_config in config.yaml."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    install_block = payload.get("install", {})
    if not isinstance(install_block, dict):
        install_block = {}
    install_block["generic_config"] = enabled
    payload["install"] = install_block
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _unit_test_deploy_blocks_when_config_is_generic() -> None:
    """deploy_repo should block if install.generic_config is true."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        try:
            deploy.deploy_repo(repo_root)
        except SystemExit as exc:
            assert "generic" in str(exc)
        else:
            raise AssertionError("deploy_repo should fail for generic config")


def _unit_test_deploy_runs_full_refresh_when_config_ready() -> None:
    """deploy_repo should run refresh and generate local registries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _set_generic_flag(repo_root, enabled=False)

        result = deploy.deploy_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        assert policy_registry.exists()


def _write_marker(path: Path) -> None:
    """Create a marker file and required parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("marker\n", encoding="utf-8")


def _unit_test_deploy_cleanup_is_deploy_only() -> None:
    """deploy_repo should remove user-mode paths; refresh should not."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _set_generic_flag(repo_root, enabled=False)

        policy_marker = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        tests_marker = (
            repo_root
            / "tests"
            / "devcovenant"
            / "core"
            / "demo"
            / "test_demo.py"
        )
        profile_marker = (
            repo_root
            / "devcovenant"
            / "custom"
            / "profiles"
            / "devcovrepo"
            / "demo.txt"
        )
        _write_marker(policy_marker)
        _write_marker(tests_marker)
        _write_marker(profile_marker)

        refresh_result = refresh.refresh_repo(repo_root)
        assert refresh_result == 0
        assert policy_marker.exists()
        assert tests_marker.exists()
        assert profile_marker.exists()

        deploy_result = deploy.deploy_repo(repo_root)
        assert deploy_result == 0
        assert not (repo_root / "devcovenant" / "custom" / "policies").exists()
        assert not (repo_root / "tests" / "devcovenant" / "core").exists()
        assert not (
            repo_root / "devcovenant" / "custom" / "profiles" / "devcovrepo"
        ).exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_deploy_blocks_when_config_is_generic(self):
        """Run test_deploy_blocks_when_config_is_generic."""
        _unit_test_deploy_blocks_when_config_is_generic()

    def test_deploy_runs_full_refresh_when_config_ready(self):
        """Run test_deploy_runs_full_refresh_when_config_ready."""
        _unit_test_deploy_runs_full_refresh_when_config_ready()

    def test_deploy_cleanup_is_deploy_only(self):
        """Run test_deploy_cleanup_is_deploy_only."""
        _unit_test_deploy_cleanup_is_deploy_only()
