"""Tests for manifest helpers and managed-doc descriptor assets."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core import manifest as manifest_module

REPO_ROOT = Path(__file__).resolve().parents[3]
ASSETS_ROOT = (
    REPO_ROOT / "devcovenant" / "core" / "profiles" / "global" / "assets"
)


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


def _unit_test_managed_doc_descriptors_exist() -> None:
    """Managed docs should be backed by YAML descriptors."""
    required = (
        ASSETS_ROOT / "AGENTS.yaml",
        ASSETS_ROOT / "README.yaml",
        ASSETS_ROOT / "SPEC.yaml",
        ASSETS_ROOT / "PLAN.yaml",
        ASSETS_ROOT / "CHANGELOG.yaml",
        ASSETS_ROOT / "CONTRIBUTING.yaml",
        ASSETS_ROOT / "devcovenant" / "README.yaml",
    )
    for descriptor_path in required:
        assert descriptor_path.exists()


def _unit_test_legacy_markdown_templates_are_absent() -> None:
    """Legacy managed-doc markdown templates should not exist."""
    assert not (ASSETS_ROOT / "AGENTS.md").exists()
    assert not (ASSETS_ROOT / "CONTRIBUTING.md").exists()


def _unit_test_legacy_gpl_template_is_absent() -> None:
    """Retired GPL template asset should not exist."""
    assert not (ASSETS_ROOT / "LICENSE_GPL-3.0.txt").exists()


def _unit_test_manifest_excludes_no_devcov_state_path() -> None:
    """MANIFEST.in should not keep retired .devcov-state rules."""
    manifest_path = REPO_ROOT / "MANIFEST.in"
    contents = manifest_path.read_text(encoding="utf-8")
    assert ".devcov-state" not in contents


def _unit_test_manifest_excludes_root_managed_docs() -> None:
    """MANIFEST.in should not include root managed docs."""
    manifest_path = REPO_ROOT / "MANIFEST.in"
    contents = manifest_path.read_text(encoding="utf-8")
    forbidden_includes = (
        "include AGENTS.md",
        "include CONTRIBUTING.md",
        "include SPEC.md",
        "include PLAN.md",
        "include CHANGELOG.md",
    )
    for entry in forbidden_includes:
        assert entry not in contents


def _unit_test_manifest_core_files_skip_legacy_markdown_templates() -> None:
    """Manifest defaults should not list removed markdown templates."""
    assert (
        "devcovenant/core/profiles/global/assets/AGENTS.md"
        not in manifest_module.DEFAULT_CORE_FILES
    )
    assert (
        "devcovenant/core/profiles/global/assets/CONTRIBUTING.md"
        not in manifest_module.DEFAULT_CORE_FILES
    )
    assert (
        "devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt"
        not in manifest_module.DEFAULT_CORE_FILES
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

    def test_managed_doc_descriptors_exist(self):
        """Run test_managed_doc_descriptors_exist."""
        _unit_test_managed_doc_descriptors_exist()

    def test_legacy_markdown_templates_are_absent(self):
        """Run test_legacy_markdown_templates_are_absent."""
        _unit_test_legacy_markdown_templates_are_absent()

    def test_legacy_gpl_template_is_absent(self):
        """Run test_legacy_gpl_template_is_absent."""
        _unit_test_legacy_gpl_template_is_absent()

    def test_manifest_excludes_no_devcov_state_path(self):
        """Run test_manifest_excludes_no_devcov_state_path."""
        _unit_test_manifest_excludes_no_devcov_state_path()

    def test_manifest_excludes_root_managed_docs(self):
        """Run test_manifest_excludes_root_managed_docs."""
        _unit_test_manifest_excludes_root_managed_docs()

    def test_manifest_core_files_skip_legacy_markdown_templates(self):
        """Run test_manifest_core_files_skip_legacy_markdown_templates."""
        _unit_test_manifest_core_files_skip_legacy_markdown_templates()
