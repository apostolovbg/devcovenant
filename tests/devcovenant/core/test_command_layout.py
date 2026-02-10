"""Regression tests for CLI command module placement."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMAND_MODULES = (
    "run_pre_commit",
    "run_tests",
    "update_lock",
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


def _unit_test_cli_command_modules_live_only_at_package_root() -> None:
    """CLI command modules should not be duplicated under core."""
    for module_name in COMMAND_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        core_path = REPO_ROOT / "devcovenant" / "core" / f"{module_name}.py"
        assert root_path.exists()
        assert not core_path.exists()


def _unit_test_cli_command_modules_are_not_forwarding_wrappers() -> None:
    """Root command modules should own their implementation."""
    for module_name in COMMAND_MODULES:
        root_path = REPO_ROOT / "devcovenant" / f"{module_name}.py"
        text = root_path.read_text(encoding="utf-8")
        wrapper_import = f"from devcovenant.core.{module_name} import main"
        assert wrapper_import not in text


def _unit_test_helper_scripts_are_not_duplicated_as_profile_assets() -> None:
    """Helper command scripts should not be duplicated in profile assets."""
    for module_name in COMMAND_MODULES:
        duplicate_path = ASSET_SCRIPT_ROOT / f"{module_name}.py"
        assert not duplicate_path.exists()


def _unit_test_cli_command_modules_support_file_path_help() -> None:
    """File-path invocation should work without PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for module_name in COMMAND_MODULES:
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

    def test_cli_command_modules_live_only_at_package_root(self):
        """Run test_cli_command_modules_live_only_at_package_root."""
        _unit_test_cli_command_modules_live_only_at_package_root()

    def test_cli_command_modules_are_not_forwarding_wrappers(self):
        """Run test_cli_command_modules_are_not_forwarding_wrappers."""
        _unit_test_cli_command_modules_are_not_forwarding_wrappers()

    def test_helper_scripts_are_not_duplicated_as_profile_assets(self):
        """Run test_helper_scripts_are_not_duplicated_as_profile_assets."""
        _unit_test_helper_scripts_are_not_duplicated_as_profile_assets()

    def test_cli_command_modules_support_file_path_help(self):
        """Run test_cli_command_modules_support_file_path_help."""
        _unit_test_cli_command_modules_support_file_path_help()
