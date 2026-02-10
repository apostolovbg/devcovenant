"""Tests for manifest helpers."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core import manifest as manifest_module


def _unit_test_ensure_manifest_returns_none_without_install(
    tmp_path: Path,
) -> None:
    """Manifest is not created when DevCovenant is absent."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert manifest_module.ensure_manifest(repo_root) is None


def _unit_test_ensure_manifest_creates_when_installed(
    tmp_path: Path,
) -> None:
    """Manifest is created when DevCovenant is installed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "devcovenant").mkdir()
    manifest = manifest_module.ensure_manifest(repo_root)
    assert manifest is not None
    assert (repo_root / manifest_module.MANIFEST_REL_PATH).exists()
    assert "core" in manifest


def _unit_test_append_notifications_creates_manifest(tmp_path: Path) -> None:
    """append_notifications creates manifest and records messages."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "devcovenant").mkdir()

    manifest_module.append_notifications(repo_root, ["hello world"])

    manifest = manifest_module.load_manifest(repo_root)
    assert manifest is not None
    notes = manifest.get("notifications", [])
    assert len(notes) == 1
    assert "hello world" in notes[0]["message"]


def _unit_test_ensure_manifest_normalizes_stale_default_sections(
    tmp_path: Path,
) -> None:
    """ensure_manifest should refresh stale default inventories."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "devcovenant").mkdir()
    stale = manifest_module.build_manifest()
    stale["core"]["files"] = [
        *stale["core"]["files"],
        "devcovenant/core/profiles/global/assets/AGENTS.md",
        "devcovenant/core/profiles/global/assets/CONTRIBUTING.md",
    ]
    manifest_module.write_manifest(repo_root, stale)

    manifest = manifest_module.ensure_manifest(repo_root)

    assert manifest is not None
    assert manifest["core"]["files"] == manifest_module.DEFAULT_CORE_FILES
    assert (
        "devcovenant/core/profiles/global/assets/AGENTS.md"
        not in manifest["core"]["files"]
    )
    assert (
        "devcovenant/core/profiles/global/assets/CONTRIBUTING.md"
        not in manifest["core"]["files"]
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_ensure_manifest_returns_none_without_install(self):
        """Run test_ensure_manifest_returns_none_without_install."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ensure_manifest_returns_none_without_install(
                tmp_path=tmp_path
            )

    def test_ensure_manifest_creates_when_installed(self):
        """Run test_ensure_manifest_creates_when_installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ensure_manifest_creates_when_installed(
                tmp_path=tmp_path
            )

    def test_append_notifications_creates_manifest(self):
        """Run test_append_notifications_creates_manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_append_notifications_creates_manifest(tmp_path=tmp_path)

    def test_ensure_manifest_normalizes_stale_default_sections(self):
        """Run test_ensure_manifest_normalizes_stale_default_sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ensure_manifest_normalizes_stale_default_sections(
                tmp_path=tmp_path
            )
