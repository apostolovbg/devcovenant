"""Regression tests for command module placement."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_COMMAND_MODULES = (
    "check",
    "test",
    "install",
    "deploy",
    "upgrade",
    "refresh",
    "uninstall",
    "undeploy",
    "update_lock",
)
LEGACY_HELPER_MODULES = (
    "run_pre_commit",
    "run_tests",
    "update_test_status",
)
ASSET_SCRIPT_ROOT = (
    REPO_ROOT
    / "devcovenant"
    / "core"
    / "profiles"
    / "global"
    / "assets"
    / "devcovenant"
)


def _unit_test_root_command_modules_exist() -> None:
    """All CLI command modules should exist at package root."""
    for module_name in ROOT_COMMAND_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        assert root_path.exists(), str(root_path)


def _unit_test_legacy_helper_modules_removed_from_root() -> None:
    """Legacy helper scripts should be removed from package root."""
    for module_name in LEGACY_HELPER_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        assert not root_path.exists(), str(root_path)


def _unit_test_command_modules_not_duplicated_as_profile_assets() -> None:
    """Root command modules should not be duplicated in profile assets."""
    for module_name in ROOT_COMMAND_MODULES + LEGACY_HELPER_MODULES:
        duplicate_path = ASSET_SCRIPT_ROOT / f"{module_name}.py"
        assert not duplicate_path.exists(), str(duplicate_path)


def _unit_test_command_modules_support_file_path_help() -> None:
    """File-path invocation should work without PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for module_name in ROOT_COMMAND_MODULES:
        result = subprocess.run(
            [sys.executable, f"devcovenant/{module_name}.py", "--help"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_root_command_modules_exist(self):
        """Run test_root_command_modules_exist."""
        _unit_test_root_command_modules_exist()

    def test_legacy_helper_modules_removed_from_root(self):
        """Run test_legacy_helper_modules_removed_from_root."""
        _unit_test_legacy_helper_modules_removed_from_root()

    def test_command_modules_not_duplicated_as_profile_assets(self):
        """Run test_command_modules_not_duplicated_as_profile_assets."""
        _unit_test_command_modules_not_duplicated_as_profile_assets()

    def test_command_modules_support_file_path_help(self):
        """Run test_command_modules_support_file_path_help."""
        _unit_test_command_modules_support_file_path_help()
