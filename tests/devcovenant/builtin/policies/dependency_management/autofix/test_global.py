"""Unit tests for dependency-management global fixer."""

from __future__ import annotations

import unittest
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory

from devcovenant.core.policy_contract import Violation

DependencyManagementFixer = import_module(
    "devcovenant.builtin.policies.dependency_management.autofix.global"
).DependencyManagementFixer
_AUTOFIX_MODULE = import_module(
    "devcovenant.builtin.policies.dependency_management.autofix.global"
)


def _unit_test_can_fix_requires_changed_dependency_files() -> None:
    """Fixer should only run when dependency changes are present."""
    assert (
        DependencyManagementFixer is _AUTOFIX_MODULE.DependencyManagementFixer
    )
    fixer = DependencyManagementFixer()
    violation = Violation(
        policy_id="dependency-management",
        severity="error",
        message="sync",
        context={"changed_dependency_files": ["requirements.lock"]},
    )
    assert fixer.can_fix(violation) is True

    empty_context = Violation(
        policy_id="dependency-management",
        severity="error",
        message="sync",
        context={"changed_dependency_files": []},
    )
    assert fixer.can_fix(empty_context) is False


def _unit_test_fix_materializes_report_and_licenses_readme() -> None:
    """Fix should create report and generic licenses/README.md artifacts."""
    fixer = DependencyManagementFixer()
    captured: dict[str, object] = {}
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-management",
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
        original_runner = _AUTOFIX_MODULE.run_policy_runtime_action
        try:

            def _fake_runner(*_args, **_kwargs):
                """Capture runtime-action payload and return modified files."""
                captured.update(_kwargs)
                return {
                    "refreshed_artifacts": [
                        "licenses/THIRD_PARTY_LICENSES.md",
                        "licenses/README.md",
                    ]
                }

            _AUTOFIX_MODULE.run_policy_runtime_action = _fake_runner
            result = fixer.fix(violation)
        finally:
            _AUTOFIX_MODULE.run_policy_runtime_action = original_runner
        assert result.success is True
        assert result.files_modified == [
            Path("licenses/THIRD_PARTY_LICENSES.md"),
            Path("licenses/README.md"),
        ]
        assert captured["payload"] == {
            "changed_dependency_files": ["services/api/package.json"]
        }


def _unit_test_fix_uses_force_refresh_for_surface_definition_drift() -> None:
    """Fix should choose the forced runtime action when requested."""

    fixer = DependencyManagementFixer()
    captured: dict[str, object] = {}
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-management",
            severity="error",
            message="sync",
            context={
                "changed_dependency_files": ["requirements.lock"],
                "force_refresh": True,
                "issue": "third_party",
            },
        )
        original_runner = _AUTOFIX_MODULE.run_policy_runtime_action
        try:

            def _fake_runner(*_args, **_kwargs):
                """Capture the selected runtime action for assertions."""

                captured.update(_kwargs)
                return {"refreshed_artifacts": []}

            _AUTOFIX_MODULE.run_policy_runtime_action = _fake_runner
            result = fixer.fix(violation)
        finally:
            _AUTOFIX_MODULE.run_policy_runtime_action = original_runner

        assert result.success is True
        assert captured["action"] == "refresh-force"
        assert captured["payload"] == {
            "changed_dependency_files": ["requirements.lock"]
        }


def _unit_test_fix_noop_when_artifacts_are_already_synced() -> None:
    """Fix should be a no-op when all managed artifacts are synchronized."""
    fixer = DependencyManagementFixer()
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-management",
            severity="error",
            message="sync",
            context={
                "changed_dependency_files": ["requirements.lock"],
                "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
                "licenses_dir": "licenses",
                "report_heading": "## License Report",
                "issue": "missing_reference",
            },
        )
        original_runner = _AUTOFIX_MODULE.run_policy_runtime_action
        try:
            _AUTOFIX_MODULE.run_policy_runtime_action = (
                lambda *_args, **_kwargs: {"refreshed_artifacts": []}
            )
            result = fixer.fix(violation)
        finally:
            _AUTOFIX_MODULE.run_policy_runtime_action = original_runner
        assert result.success is True
        assert result.files_modified == []
        assert "already in sync" in result.message


def _unit_test_fix_rejects_outside_repo_targets() -> None:
    """Fix should fail cleanly for metadata paths outside repository root."""
    fixer = DependencyManagementFixer()
    with TemporaryDirectory() as tmp_dir:
        fixer.repo_root = Path(tmp_dir).resolve()
        violation = Violation(
            policy_id="dependency-management",
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
        original_runner = _AUTOFIX_MODULE.run_policy_runtime_action
        try:
            _AUTOFIX_MODULE.run_policy_runtime_action = (
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    ValueError(
                        "dependency-management metadata path must stay "
                        "inside the repository."
                    )
                )
            )
            result = fixer.fix(violation)
        finally:
            _AUTOFIX_MODULE.run_policy_runtime_action = original_runner
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

    def test_fix_uses_force_refresh_for_surface_definition_drift(self):
        """Run force-refresh runtime-action selection assertions."""
        _unit_test_fix_uses_force_refresh_for_surface_definition_drift()

    def test_fix_noop_when_artifacts_are_already_synced(self):
        """Run test_fix_noop_when_artifacts_are_already_synced."""
        _unit_test_fix_noop_when_artifacts_are_already_synced()

    def test_fix_rejects_outside_repo_targets(self):
        """Run test_fix_rejects_outside_repo_targets."""
        _unit_test_fix_rejects_outside_repo_targets()
