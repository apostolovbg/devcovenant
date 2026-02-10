"""Tests for the dependency-license-sync policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.dependency_license_sync import (
    dependency_license_sync,
)


def _setup_repo(tmp_path: Path) -> Path:
    """Create a minimal repo layout for license tracking tests."""
    tmp_path.joinpath("licenses").mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements.in").write_text("numpy==1.0\n", encoding="utf-8")
    (tmp_path / "requirements.lock").write_text(
        "numpy==1.0\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test'\n", encoding="utf-8"
    )
    (tmp_path / "THIRD_PARTY_LICENSES.md").write_text(
        "# Third-Party Licenses\n", encoding="utf-8"
    )
    (tmp_path / "licenses" / "BSD-3-Clause.txt").write_text(
        "BSD text\n", encoding="utf-8"
    )
    return tmp_path


def _build_checker() -> dependency_license_sync.DependencyLicenseSyncCheck:
    """Create a checker with dependency manifests configured."""
    checker = dependency_license_sync.DependencyLicenseSyncCheck()
    checker.set_options(
        metadata_options={
            "dependency_files": [
                "requirements.in",
                "requirements.lock",
                "pyproject.toml",
            ],
            "third_party_file": "THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        },
        config_overrides=None,
    )
    return checker


def _unit_test_requires_license_table_update(tmp_path: Path):
    """Dependency changes without touching the license table fail."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker()
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in"],
    )
    violations = checker.check(context)

    assert any("license table" in v.message.lower() for v in violations)


def _unit_test_passes_when_report_and_license_refreshed(tmp_path: Path):
    """The policy passes when the report mentions the changed files."""
    repo = _setup_repo(tmp_path)
    report = repo / "THIRD_PARTY_LICENSES.md"
    report.write_text(
        "# Third-Party Licenses\n\n## License Report\n"
        "- requirements.lock updated\n",
        encoding="utf-8",
    )
    # Create a new license snapshot
    new_license = repo / "licenses" / "example.txt"
    new_license.write_text("MIT\n", encoding="utf-8")

    checker = _build_checker()
    context = CheckContext(
        repo_root=repo,
        changed_files=[
            repo / "requirements.lock",
            report,
            new_license,
        ],
    )
    violations = checker.check(context)

    assert violations == []


def _unit_test_report_mentions_all_changed_files(tmp_path: Path):
    """Each dependency file needs a report line that cites it."""
    repo = _setup_repo(tmp_path)
    report = repo / "THIRD_PARTY_LICENSES.md"
    report.write_text(
        "# Third-Party Licenses\n\n## License Report\n"
        "- requirements.in added\n",
        encoding="utf-8",
    )

    checker = _build_checker()
    context = CheckContext(
        repo_root=repo,
        changed_files=[
            repo / "requirements.lock",
            report,
            repo / "licenses" / "BSD-3-Clause.txt",
        ],
    )
    violations = checker.check(context)

    assert any(
        "requirements.lock" in (v.context.get("missing_references") or [])
        for v in violations
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_requires_license_table_update(self):
        """Run test_requires_license_table_update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_requires_license_table_update(tmp_path=tmp_path)

    def test_passes_when_report_and_license_refreshed(self):
        """Run test_passes_when_report_and_license_refreshed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_passes_when_report_and_license_refreshed(
                tmp_path=tmp_path
            )

    def test_report_mentions_all_changed_files(self):
        """Run test_report_mentions_all_changed_files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_report_mentions_all_changed_files(tmp_path=tmp_path)
