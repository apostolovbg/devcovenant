"""Tests for devcov-structure-guard policy."""

import tempfile
from pathlib import Path

from devcovenant.core import manifest as manifest_module
from devcovenant.core.base import CheckContext
from devcovenant.core.policy_scripts.devcov_structure_guard import (
    DevCovenantStructureGuardCheck,
)


def test_structure_guard_passes_with_required_paths():
    """Guard should pass when required paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        for rel_path in manifest_module.DEFAULT_CORE_DIRS:
            (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
        for rel_path in manifest_module.DEFAULT_CORE_FILES:
            if rel_path == manifest_module.MANIFEST_REL_PATH:
                continue
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("#")
        for rel_path in manifest_module.DEFAULT_DOCS_CORE:
            (repo_root / rel_path).write_text("#")

        checker = DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        assert checker.check(context) == []
        assert (repo_root / manifest_module.MANIFEST_REL_PATH).exists()


def test_structure_guard_reports_missing_paths():
    """Guard should flag missing structure entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        checker = DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert violations[0].policy_id == "devcov-structure-guard"


def test_structure_guard_uses_manifest_docs() -> None:
    """Guard should use manifest doc lists when present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        manifest = manifest_module.build_manifest()
        manifest_module.write_manifest(repo_root, manifest)

        for rel_path in manifest["core"]["dirs"]:
            (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
        for rel_path in manifest["core"]["files"]:
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("#")

        docs = manifest["docs"]["core"]
        for rel_path in docs:
            if rel_path == "README.md":
                continue
            (repo_root / rel_path).write_text("#")

        checker = DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert "README.md" in violations[0].message
