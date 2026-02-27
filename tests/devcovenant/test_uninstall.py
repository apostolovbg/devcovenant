"""Unit tests for uninstall command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant import install, refresh, uninstall


def _unit_test_uninstall_removes_devcovenant_package() -> None:
    """uninstall_repo should remove the repository devcovenant directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        package_dir = repo_root / "devcovenant"
        assert package_dir.exists()

        result = uninstall.uninstall_repo(repo_root)
        assert result == 0
        assert not package_dir.exists()


def _unit_test_uninstall_recovers_when_config_is_invalid() -> None:
    """uninstall_repo should remove package even with invalid config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        refresh.refresh_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.write_text(":\n", encoding="utf-8")

        package_dir = repo_root / "devcovenant"
        assert package_dir.exists()

        result = uninstall.uninstall_repo(repo_root)
        assert result == 0
        assert not package_dir.exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_uninstall_removes_devcovenant_package(self):
        """Run test_uninstall_removes_devcovenant_package."""
        _unit_test_uninstall_removes_devcovenant_package()

    def test_uninstall_recovers_when_config_is_invalid(self):
        """Run test_uninstall_recovers_when_config_is_invalid."""
        _unit_test_uninstall_recovers_when_config_is_invalid()
