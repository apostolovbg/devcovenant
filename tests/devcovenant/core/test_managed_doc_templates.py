"""Regression checks for managed-document template sources."""

import unittest
from pathlib import Path

from devcovenant.core import manifest as manifest_module

REPO_ROOT = Path(__file__).resolve().parents[3]
ASSETS_ROOT = (
    REPO_ROOT / "devcovenant" / "core" / "profiles" / "global" / "assets"
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_managed_doc_descriptors_exist(self):
        """Run test_managed_doc_descriptors_exist."""
        _unit_test_managed_doc_descriptors_exist()

    def test_legacy_markdown_templates_are_absent(self):
        """Run test_legacy_markdown_templates_are_absent."""
        _unit_test_legacy_markdown_templates_are_absent()

    def test_manifest_core_files_skip_legacy_markdown_templates(self):
        """Run test_manifest_core_files_skip_legacy_markdown_templates."""
        _unit_test_manifest_core_files_skip_legacy_markdown_templates()
