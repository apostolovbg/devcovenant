"""Unit tests for dependency-license-sync global fixer."""

from __future__ import annotations

import unittest
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory

from devcovenant.core.contracts.policy import Violation

DependencyLicenseSyncFixer = import_module(
    "devcovenant.builtin.policies.dependency_license_sync.autofix.global"
).DependencyLicenseSyncFixer
_DEPENDENCY_LICENSE_SYNC_MODULE = (
    "devcovenant.builtin.policies.dependency_license_sync."
    "dependency_license_sync"
)
DependencyLicenseSyncModule = import_module(_DEPENDENCY_LICENSE_SYNC_MODULE)


def _unit_test_can_fix_requires_changed_dependency_files() -> None:
    """Fixer should only run when dependency changes are present."""
    fixer = DependencyLicenseSyncFixer()
    violation = Violation(
        policy_id="dependency-license-sync",
        severity="error",
        message="sync",
        context={"changed_dependency_files": ["requirements.lock"]},
    )
    assert fixer.can_fix(violation) is True

    empty_context = Violation(
        policy_id="dependency-license-sync",
        severity="error",
        message="sync",
        context={"changed_dependency_files": []},
    )
    assert fixer.can_fix(empty_context) is False


def _unit_test_fix_materializes_report_and_licenses_readme() -> None:
    """Fix should create report and generic licenses/README.md artifacts."""
    fixer = DependencyLicenseSyncFixer()
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-license-sync",
            severity="error",
            message="sync",
            context={
                "changed_dependency_files": ["services/api/package.json"],
                "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
                "licenses_dir": "licenses",
                "report_heading": "## License Report",
                "issue": "third_party",
            },
        )
        result = fixer.fix(violation)
        assert result.success is True
        report = fixer.repo_root / "licenses" / "THIRD_PARTY_LICENSES.md"
        assert report.exists()
        licenses_readme = fixer.repo_root / "licenses" / "README.md"
        assert licenses_readme.exists()
        assert "services/api/package.json" in report.read_text(
            encoding="utf-8"
        )


def _unit_test_fix_noop_when_artifacts_are_already_synced() -> None:
    """Fix should be a no-op when report and README are synchronized."""
    fixer = DependencyLicenseSyncFixer()
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        licenses = fixer.repo_root / "licenses"
        licenses.mkdir(parents=True, exist_ok=True)
        report = licenses / "THIRD_PARTY_LICENSES.md"
        report.write_text(
            "# Third-Party Licenses\n\n## License Report\n"
            "- `services/api/package.json`\n",
            encoding="utf-8",
        )
        readme = licenses / "README.md"
        readme.write_text(
            DependencyLicenseSyncModule._render_licenses_readme(
                "licenses/THIRD_PARTY_LICENSES.md"
            ),
            encoding="utf-8",
        )

        violation = Violation(
            policy_id="dependency-license-sync",
            severity="error",
            message="sync",
            context={
                "changed_dependency_files": ["services/api/package.json"],
                "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
                "licenses_dir": "licenses",
                "report_heading": "## License Report",
                "issue": "missing_reference",
            },
        )
        result = fixer.fix(violation)
        assert result.success is True
        assert result.files_modified == []
        assert "already in sync" in result.message


def _unit_test_fix_rejects_outside_repo_targets() -> None:
    """Fix should fail cleanly for metadata paths outside repository root."""
    fixer = DependencyLicenseSyncFixer()
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-license-sync",
            severity="error",
            message="sync",
            context={
                "changed_dependency_files": ["requirements.lock"],
                "third_party_file": "../outside.md",
                "licenses_dir": "licenses",
                "report_heading": "## License Report",
                "issue": "third_party",
            },
        )
        result = fixer.fix(violation)
        assert result.success is False
        assert "must stay inside the repository" in result.message


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_can_fix_requires_changed_dependency_files(self):
        """Run test_can_fix_requires_changed_dependency_files."""
        _unit_test_can_fix_requires_changed_dependency_files()

    def test_fix_materializes_report_and_licenses_readme(self):
        """Run test_fix_materializes_report_and_licenses_readme."""
        _unit_test_fix_materializes_report_and_licenses_readme()

    def test_fix_noop_when_artifacts_are_already_synced(self):
        """Run test_fix_noop_when_artifacts_are_already_synced."""
        _unit_test_fix_noop_when_artifacts_are_already_synced()

    def test_fix_rejects_outside_repo_targets(self):
        """Run test_fix_rejects_outside_repo_targets."""
        _unit_test_fix_rejects_outside_repo_targets()
