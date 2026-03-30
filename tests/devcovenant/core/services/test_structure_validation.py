"""Tests for repository structure validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.services import manifest_inventory as manifest_module
from devcovenant.core.services import structure_validation


def _seed_required_structure(repo_root: Path) -> None:
    """Create required core/docs paths for structure checks."""
    for rel_path in manifest_module.DEFAULT_CORE_DIRS:
        (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
    for rel_path in manifest_module.DEFAULT_CORE_FILES:
        if rel_path == manifest_module.REGISTRY_REL_PATH:
            continue
        path = repo_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("#\n", encoding="utf-8")
    for rel_path in manifest_module.DEFAULT_ENABLED_DOCS:
        path = repo_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#\n", encoding="utf-8")


def _write_active_profiles(repo_root: Path, profiles: list[str]) -> None:
    """Write a minimal config with specified active profiles."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "profiles:\n  active:\n"
    for profile in profiles:
        payload += f"  - {profile}\n"
    config_path.write_text(payload, encoding="utf-8")


def _unit_test_structure_check_passes_with_required_paths() -> None:
    """Structure check should pass when required paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)

        context = CheckContext(repo_root=repo_root)
        assert structure_validation.check_structure(context) == []
        assert (repo_root / manifest_module.REGISTRY_REL_PATH).exists()


def _unit_test_structure_check_reports_missing_paths() -> None:
    """Structure check should flag missing structure entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)

        assert violations
        assert violations[0].policy_id == "structure-validation"


def _unit_test_structure_check_uses_manifest_docs() -> None:
    """Structure check should use enabled doc lists when present."""
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
                path.write_text("#\n", encoding="utf-8")

        docs = manifest["docs"]["enabled"]
        for rel_path in docs:
            if rel_path == "README.md":
                continue
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#\n", encoding="utf-8")

        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)

        assert violations
        assert "README.md" in violations[0].message


def _unit_test_structure_check_reports_repo_bytecode() -> None:
    """Structure check should flag repo-local bytecode for devcovrepo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)
        _write_active_profiles(repo_root, ["devcovrepo"])

        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")

        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)

        assert violations
        assert "bytecode" in violations[0].message


def _unit_test_structure_check_skips_repo_bytecode_without_profile() -> None:
    """Structure check should ignore bytecode when devcovrepo is inactive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)
        _write_active_profiles(repo_root, ["global"])

        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")

        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)

        assert violations == []


def _unit_test_structure_check_requires_logs_readme() -> None:
    """Structure check should require the tracked logs README skeleton."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _seed_required_structure(repo_root)

        logs_readme = repo_root / "devcovenant" / "logs" / "README.md"
        logs_readme.unlink()

        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)

        assert violations
        assert "devcovenant/logs/README.md" in violations[0].message


def _unit_test_structure_check_ignores_available_but_disabled_docs() -> None:
    """Structure check should ignore docs that are only available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        manifest = manifest_module.build_manifest(
            available_docs=["AGENTS.md", "SECURITY.md"],
            enabled_docs=["AGENTS.md"],
        )
        manifest_module.write_manifest(repo_root, manifest)

        for rel_path in manifest["core"]["dirs"]:
            (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
        for rel_path in manifest["core"]["files"]:
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("#\n", encoding="utf-8")

        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.write_text(
            "doc_assets:\n" "  autogen:\n" "    - AGENTS.md\n" "  user: []\n",
            encoding="utf-8",
        )
        (repo_root / "AGENTS.md").write_text("#\n", encoding="utf-8")

        context = CheckContext(repo_root=repo_root)
        assert structure_validation.check_structure(context) == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_structure_check_passes_with_required_paths(self):
        """Run structure pass assertions."""
        _unit_test_structure_check_passes_with_required_paths()

    def test_structure_check_reports_missing_paths(self):
        """Run missing-path structure assertions."""
        _unit_test_structure_check_reports_missing_paths()

    def test_structure_check_uses_manifest_docs(self):
        """Run enabled-doc structure assertions."""
        _unit_test_structure_check_uses_manifest_docs()

    def test_structure_check_reports_repo_bytecode(self):
        """Run repo-bytecode structure assertions."""
        _unit_test_structure_check_reports_repo_bytecode()

    def test_structure_check_skips_repo_bytecode_without_profile(self):
        """Run non-devcovrepo bytecode assertions."""
        _unit_test_structure_check_skips_repo_bytecode_without_profile()

    def test_structure_check_requires_logs_readme(self):
        """Run logs README structure assertions."""
        _unit_test_structure_check_requires_logs_readme()

    def test_structure_check_ignores_available_but_disabled_docs(self):
        """Run available-but-disabled doc structure assertions."""
        _unit_test_structure_check_ignores_available_but_disabled_docs()


if __name__ == "__main__":
    unittest.main()
