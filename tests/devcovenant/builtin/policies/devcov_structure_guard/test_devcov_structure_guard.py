"""Tests for devcov-structure-guard policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.devcov_structure_guard import (
    devcov_structure_guard,
)
from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.services import registry as manifest_module


def _seed_required_structure(repo_root: Path) -> None:
    """Create required core/docs paths for structure guard."""
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


def _write_active_profiles(repo_root: Path, profiles: list[str]) -> None:
    """Write a minimal config with specified active profiles."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "profiles:\n  active:\n"
    for profile in profiles:
        payload += f"  - {profile}\n"
    config_path.write_text(payload, encoding="utf-8")


def _unit_test_structure_guard_passes_with_required_paths():
    """Guard should pass when required paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)

        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        assert checker.check(context) == []
        assert (repo_root / manifest_module.MANIFEST_REL_PATH).exists()


def _unit_test_structure_guard_reports_missing_paths():
    """Guard should flag missing structure entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert violations[0].policy_id == "devcov-structure-guard"


def _unit_test_structure_guard_uses_manifest_docs() -> None:
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

        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert "README.md" in violations[0].message


def _unit_test_structure_guard_reports_repo_bytecode() -> None:
    """Guard should flag repo-local bytecode when devcovrepo is active."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)
        _write_active_profiles(repo_root, ["devcovrepo"])

        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")

        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert "bytecode" in violations[0].message


def _unit_test_structure_guard_skips_repo_bytecode_without_profile() -> None:
    """Guard should ignore bytecode when devcovrepo is inactive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)
        _write_active_profiles(repo_root, ["global"])

        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")

        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations == []


def _unit_test_structure_guard_requires_logs_readme() -> None:
    """Guard should require the tracked logs README skeleton."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)

        logs_readme = repo_root / "devcovenant" / "logs" / "README.md"
        logs_readme.unlink()

        checker = devcov_structure_guard.DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert "devcovenant/logs/README.md" in violations[0].message


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_structure_guard_passes_with_required_paths(self):
        """Run test_structure_guard_passes_with_required_paths."""
        _unit_test_structure_guard_passes_with_required_paths()

    def test_structure_guard_reports_missing_paths(self):
        """Run test_structure_guard_reports_missing_paths."""
        _unit_test_structure_guard_reports_missing_paths()

    def test_structure_guard_uses_manifest_docs(self):
        """Run test_structure_guard_uses_manifest_docs."""
        _unit_test_structure_guard_uses_manifest_docs()

    def test_structure_guard_reports_repo_bytecode(self):
        """Run test_structure_guard_reports_repo_bytecode."""
        _unit_test_structure_guard_reports_repo_bytecode()

    def test_structure_guard_skips_repo_bytecode_without_profile(self):
        """Run test_structure_guard_skips_repo_bytecode_without_profile."""
        _unit_test_structure_guard_skips_repo_bytecode_without_profile()

    def test_structure_guard_requires_logs_readme(self):
        """Run test_structure_guard_requires_logs_readme."""
        _unit_test_structure_guard_requires_logs_readme()
