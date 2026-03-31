"""Unit tests for package-runtime-mirror policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.package_runtime_mirror import (
    package_runtime_mirror as mirror_module,
)

PackageRuntimeMirrorCheck = mirror_module.PackageRuntimeMirrorCheck


def _build_check() -> PackageRuntimeMirrorCheck:
    """Return one checker configured with test mirror pairs."""
    check = PackageRuntimeMirrorCheck()
    check.set_options(
        {
            "file_mirrors": [
                "requirements.lock=>devcovenant/requirements.lock"
            ],
            "dir_mirrors": ["licenses=>devcovenant/licenses"],
        },
        {},
    )
    return check


def _unit_test_reports_missing_file_and_dir_mirrors() -> None:
    """Checker should report missing packaged file and dir mirrors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "requirements.lock").write_text(
            "root lock\n", encoding="utf-8"
        )
        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "report\n",
            encoding="utf-8",
        )

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert len(violations) == 2
        assert all(violation.can_auto_fix for violation in violations)
        messages = {violation.message for violation in violations}
        assert any(
            "devcovenant/requirements.lock" in message for message in messages
        )
        assert any("devcovenant/licenses" in message for message in messages)


def _unit_test_accepts_exact_file_and_dir_mirrors() -> None:
    """Checker should pass when file and directory mirrors match exactly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "requirements.lock").write_text(
            "root lock\n", encoding="utf-8"
        )
        package_lock = repo_root / "devcovenant" / "requirements.lock"
        package_lock.parent.mkdir(parents=True, exist_ok=True)
        package_lock.write_text("root lock\n", encoding="utf-8")

        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "report\n",
            encoding="utf-8",
        )
        package_licenses = repo_root / "devcovenant" / "licenses"
        package_licenses.mkdir(parents=True, exist_ok=True)
        (package_licenses / "THIRD_PARTY_LICENSES.md").write_text(
            "report\n",
            encoding="utf-8",
        )

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert violations == []


def _unit_test_reports_changed_and_extra_dir_entries() -> None:
    """Checker should flag stale packaged directory mirror content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "requirements.lock").write_text(
            "root lock\n", encoding="utf-8"
        )
        package_lock = repo_root / "devcovenant" / "requirements.lock"
        package_lock.parent.mkdir(parents=True, exist_ok=True)
        package_lock.write_text("root lock\n", encoding="utf-8")

        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "report\n",
            encoding="utf-8",
        )
        package_licenses = repo_root / "devcovenant" / "licenses"
        package_licenses.mkdir(parents=True, exist_ok=True)
        (package_licenses / "THIRD_PARTY_LICENSES.md").write_text(
            "stale\n",
            encoding="utf-8",
        )
        (package_licenses / "EXTRA.txt").write_text(
            "extra\n", encoding="utf-8"
        )

        check = _build_check()
        violations = check.check(CheckContext(repo_root=repo_root))

        assert len(violations) == 1
        assert "devcovenant/licenses" in violations[0].message
        assert "changed" in violations[0].message
        assert "extra" in violations[0].message


def _unit_test_symbol_contract_is_stable() -> None:
    """Check symbol contract should stay explicit and importable."""
    assert PackageRuntimeMirrorCheck.__name__ == "PackageRuntimeMirrorCheck"
    assert hasattr(PackageRuntimeMirrorCheck, "check")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_reports_missing_file_and_dir_mirrors(self):
        """Run test_reports_missing_file_and_dir_mirrors."""
        _unit_test_reports_missing_file_and_dir_mirrors()

    def test_accepts_exact_file_and_dir_mirrors(self):
        """Run test_accepts_exact_file_and_dir_mirrors."""
        _unit_test_accepts_exact_file_and_dir_mirrors()

    def test_reports_changed_and_extra_dir_entries(self):
        """Run test_reports_changed_and_extra_dir_entries."""
        _unit_test_reports_changed_and_extra_dir_entries()

    def test_symbol_contract_is_stable(self):
        """Run test_symbol_contract_is_stable."""
        _unit_test_symbol_contract_is_stable()
