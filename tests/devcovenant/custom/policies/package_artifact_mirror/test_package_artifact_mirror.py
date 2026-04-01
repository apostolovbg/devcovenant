"""Unit tests for package-artifact-mirror policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.package_artifact_mirror import (
    package_artifact_mirror as mirror_module,
)

PackageArtifactMirrorCheck = mirror_module.PackageArtifactMirrorCheck


def _build_check() -> PackageArtifactMirrorCheck:
    """Return one checker configured with the repo's file mirror."""
    check = PackageArtifactMirrorCheck()
    check.set_options(
        {
            "file_mirrors": ["LICENSE=>devcovenant/licenses/LICENSE"],
            "dir_mirrors": [],
            "dir_skip_paths": [],
        },
        {},
    )
    return check


def _unit_test_reports_missing_file_mirror() -> None:
    """Checker should report missing packaged license mirror."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "LICENSE").write_text("root license\n", encoding="utf-8")

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert len(violations) == 1
        assert violations[0].can_auto_fix is True
        assert "devcovenant/licenses/LICENSE" in violations[0].message


def _unit_test_accepts_exact_file_mirror() -> None:
    """Checker should pass when the packaged license matches the root file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "LICENSE").write_text("root license\n", encoding="utf-8")
        package_license = repo_root / "devcovenant" / "licenses" / "LICENSE"
        package_license.parent.mkdir(parents=True, exist_ok=True)
        package_license.write_text("root license\n", encoding="utf-8")

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations == []


def _unit_test_reports_changed_file_mirror() -> None:
    """Checker should flag a divergent packaged license mirror."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "LICENSE").write_text("root license\n", encoding="utf-8")
        package_license = repo_root / "devcovenant" / "licenses" / "LICENSE"
        package_license.parent.mkdir(parents=True, exist_ok=True)
        package_license.write_text("stale\n", encoding="utf-8")

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert len(violations) == 1
        assert "diverges" in violations[0].message


def _unit_test_symbol_contract_is_stable() -> None:
    """Check symbol contract should stay explicit and importable."""
    assert PackageArtifactMirrorCheck.__name__ == "PackageArtifactMirrorCheck"
    assert hasattr(PackageArtifactMirrorCheck, "check")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_reports_missing_file_mirror(self):
        """Run test_reports_missing_file_mirror."""
        _unit_test_reports_missing_file_mirror()

    def test_accepts_exact_file_mirror(self):
        """Run test_accepts_exact_file_mirror."""
        _unit_test_accepts_exact_file_mirror()

    def test_reports_changed_file_mirror(self):
        """Run test_reports_changed_file_mirror."""
        _unit_test_reports_changed_file_mirror()

    def test_symbol_contract_is_stable(self):
        """Run test_symbol_contract_is_stable."""
        _unit_test_symbol_contract_is_stable()
