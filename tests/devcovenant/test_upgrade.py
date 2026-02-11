"""Unit tests for upgrade command behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant import install, upgrade


def _source_version() -> str:
    """Return packaged source version for assertions."""
    version_path = Path(install.__file__).resolve().parent / "VERSION"
    return version_path.read_text(encoding="utf-8").strip()


def _unit_test_upgrade_replaces_when_target_is_older() -> None:
    """upgrade_repo should replace core when target version is older."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        version_path = repo_root / "devcovenant" / "VERSION"
        version_path.write_text("0.0.1\n", encoding="utf-8")

        result = upgrade.upgrade_repo(repo_root)
        assert result == 0
        assert (
            version_path.read_text(encoding="utf-8").strip()
            == _source_version()
        )


def _unit_test_upgrade_preserves_custom_tree() -> None:
    """upgrade_repo should preserve custom policies/profiles content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        custom_file = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_text("# keep\n", encoding="utf-8")

        result = upgrade.upgrade_repo(repo_root)
        assert result == 0
        assert custom_file.exists()
        assert custom_file.read_text(encoding="utf-8") == "# keep\n"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_upgrade_replaces_when_target_is_older(self):
        """Run test_upgrade_replaces_when_target_is_older."""
        _unit_test_upgrade_replaces_when_target_is_older()

    def test_upgrade_preserves_custom_tree(self):
        """Run test_upgrade_preserves_custom_tree."""
        _unit_test_upgrade_preserves_custom_tree()
