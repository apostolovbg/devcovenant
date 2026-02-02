"""Tests for manifest helpers."""

from pathlib import Path

from devcovenant.core import manifest as manifest_module


def test_ensure_manifest_returns_none_without_install(
    tmp_path: Path,
) -> None:
    """Manifest is not created when DevCovenant is absent."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert manifest_module.ensure_manifest(repo_root) is None


def test_ensure_manifest_creates_when_installed(
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


def test_append_notifications_creates_manifest(tmp_path: Path) -> None:
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
