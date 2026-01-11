"""Tests for devcov-structure-guard policy."""

import tempfile
from pathlib import Path

from devcovenant.base import CheckContext
from devcovenant.common_policy_scripts.devcov_structure_guard import (
    DevCovenantStructureGuardCheck,
)


def test_structure_guard_passes_with_required_paths():
    """Guard should pass when required paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "devcovenant").mkdir()
        (repo_root / "devcovenant" / "common_policy_scripts").mkdir(
            parents=True
        )
        (repo_root / "devcovenant" / "custom_policy_scripts").mkdir(
            parents=True
        )
        (repo_root / "devcovenant" / "common_policy_patches").mkdir(
            parents=True
        )
        (repo_root / "devcovenant" / "registry.json").write_text("{}")
        (repo_root / "tools").mkdir()
        (repo_root / "tools" / "run_pre_commit.py").write_text("#")
        (repo_root / "tools" / "run_tests.py").write_text("#")
        for name in [
            "AGENTS.md",
            "DEVCOVENANT.md",
            "README.md",
            "VERSION",
            "CHANGELOG.md",
        ]:
            (repo_root / name).write_text("#")

        checker = DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        assert checker.check(context) == []


def test_structure_guard_reports_missing_paths():
    """Guard should flag missing structure entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        checker = DevCovenantStructureGuardCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert violations[0].policy_id == "devcov-structure-guard"
