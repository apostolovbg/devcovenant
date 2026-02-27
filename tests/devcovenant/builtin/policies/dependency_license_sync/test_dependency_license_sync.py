"""Tests for the dependency-license-sync policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.dependency_license_sync import (
    dependency_license_sync,
)
from devcovenant.core.contracts.policy import CheckContext


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
    (tmp_path / "licenses" / "THIRD_PARTY_LICENSES.md").write_text(
        "# Third-Party Licenses\n", encoding="utf-8"
    )
    (tmp_path / "licenses" / "BSD-3-Clause.txt").write_text(
        "BSD text\n", encoding="utf-8"
    )
    return tmp_path


def _build_checker() -> dependency_license_sync.DependencyLicenseSyncCheck:
    """Create a checker with dependency manifests configured."""
    return _build_checker_with_options(
        {
            "dependency_files": [
                "requirements.in",
                "requirements.lock",
                "pyproject.toml",
            ],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )


def _build_checker_with_options(
    options: dict[str, object],
) -> dependency_license_sync.DependencyLicenseSyncCheck:
    """Create a checker with explicit metadata options."""
    checker = dependency_license_sync.DependencyLicenseSyncCheck()
    checker.set_options(
        metadata_options=options,
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
    report = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
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
    report = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
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


def _unit_test_glob_metadata_matches_nested_manifest(tmp_path: Path):
    """dependency_globs should detect non-root manifests in mixed repos."""
    repo = _setup_repo(tmp_path)
    nested = repo / "services" / "api"
    nested.mkdir(parents=True, exist_ok=True)
    manifest = nested / "package.json"
    manifest.write_text('{"name": "api"}\n', encoding="utf-8")
    checker = _build_checker_with_options(
        {
            "dependency_files": [],
            "dependency_globs": ["services/*/package.json"],
            "dependency_dirs": [],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(repo_root=repo, changed_files=[manifest])
    violations = checker.check(context)
    assert any("license table" in v.message.lower() for v in violations)


def _unit_test_third_party_path_is_exact_not_name_only(tmp_path: Path):
    """Configured third_party_file path should be matched exactly."""
    repo = _setup_repo(tmp_path)
    nested_report = repo / "docs" / "THIRD_PARTY_LICENSES.md"
    nested_report.parent.mkdir(parents=True, exist_ok=True)
    nested_report.write_text(
        "# Third-Party Licenses\n\n## License Report\n",
        encoding="utf-8",
    )
    root_report = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
    checker = _build_checker_with_options(
        {
            "dependency_files": ["requirements.in"],
            "dependency_globs": [],
            "dependency_dirs": [],
            "third_party_file": "docs/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in", root_report],
    )
    violations = checker.check(context)
    assert any(
        str(v.file_path).endswith("docs/THIRD_PARTY_LICENSES.md")
        for v in violations
    )


def _unit_test_refresh_materializes_generic_license_readme(tmp_path: Path):
    """refresh_license_artifacts should create licenses/README.md."""
    repo = _setup_repo(tmp_path)
    modified = dependency_license_sync.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    readme = repo / "licenses" / "README.md"
    assert readme in modified
    assert "requirements.in" not in readme.read_text(encoding="utf-8")


def _unit_test_refresh_is_noop_when_artifacts_already_synced(
    tmp_path: Path,
):
    """refresh_license_artifacts should be idempotent for synced artifacts."""
    repo = _setup_repo(tmp_path)
    report = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
    report.write_text(
        "# Third-Party Licenses\n\n## License Report\n"
        "- `requirements.lock`\n",
        encoding="utf-8",
    )
    licenses_readme = repo / "licenses" / "README.md"
    licenses_readme.write_text(
        dependency_license_sync._render_licenses_readme(
            "licenses/THIRD_PARTY_LICENSES.md"
        ),
        encoding="utf-8",
    )
    before_report = report.read_text(encoding="utf-8")
    before_readme = licenses_readme.read_text(encoding="utf-8")

    modified = dependency_license_sync.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )

    assert modified == []
    assert report.read_text(encoding="utf-8") == before_report
    assert licenses_readme.read_text(encoding="utf-8") == before_readme


def _unit_test_refresh_uses_stable_report_entries(tmp_path: Path):
    """Report entries should stay deterministic and non-date-prefixed."""
    repo = _setup_repo(tmp_path)
    dependency_license_sync.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    report = (repo / "licenses" / "THIRD_PARTY_LICENSES.md").read_text(
        encoding="utf-8"
    )
    assert "- `requirements.lock`" in report
    assert "Recorded dependency update" not in report


def _unit_test_refresh_prunes_stale_report_entries(tmp_path: Path):
    """Refresh should rewrite report section and prune stale references."""
    repo = _setup_repo(tmp_path)
    report_path = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
    report_path.write_text(
        "\n".join(
            [
                "# Third-Party Licenses",
                "",
                "## License Report",
                "- `requirements.in`",
                (
                    "- `devcovenant/builtin/profiles/python/assets/"
                    "requirements.in`"
                ),
                "",
                "## Dependency License Inventory",
                "- `pytest==9.0.2`: `licenses/pytest-9.0.2.txt`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    dependency_license_sync.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    report = report_path.read_text(encoding="utf-8")
    assert (
        "devcovenant/builtin/profiles/python/assets/requirements.in"
        not in (report)
    )
    expected_section = "\n".join(
        [
            "## License Report",
            "- `requirements.lock`",
        ]
    )
    assert expected_section in report


def _unit_test_invalid_artifact_paths_raise_configuration_error(
    tmp_path: Path,
):
    """Outside-repo artifact targets should emit configuration violations."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {
            "dependency_files": ["requirements.in"],
            "dependency_globs": [],
            "dependency_dirs": [],
            "third_party_file": "../outside.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(
        repo_root=repo, changed_files=[repo / "requirements.in"]
    )
    violations = checker.check(context)
    assert len(violations) == 1
    assert "must stay inside the repository" in violations[0].message


def _unit_test_role_selectors_match_dependency_file(tmp_path: Path):
    """Role-based file selectors should match dependency changes."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {
            "dependency_files": [],
            "dependency_globs": [],
            "dependency_dirs": [],
            "dependency_roles": ["intent", "resolved", "package_manifest"],
            "dependency_role_files": ["intent=>requirements.in"],
            "dependency_role_globs": [],
            "dependency_role_dirs": [],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in"],
    )
    violations = checker.check(context)
    assert any("license table" in v.message.lower() for v in violations)


def _unit_test_role_selectors_support_mixed_role_entries(tmp_path: Path):
    """Role selectors should support mixed file/glob mapping."""
    repo = _setup_repo(tmp_path)
    nested = repo / "services" / "api"
    nested.mkdir(parents=True, exist_ok=True)
    manifest = nested / "package.json"
    manifest.write_text('{"name":"api"}\n', encoding="utf-8")
    checker = _build_checker_with_options(
        {
            "dependency_files": [],
            "dependency_globs": [],
            "dependency_dirs": [],
            "dependency_roles": ["intent", "resolved", "package_manifest"],
            "dependency_role_files": ["resolved=>requirements.lock"],
            "dependency_role_globs": [
                "package_manifest=>services/*/package.json"
            ],
            "dependency_role_dirs": [],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(repo_root=repo, changed_files=[manifest])
    violations = checker.check(context)
    assert any("license table" in v.message.lower() for v in violations)


def _unit_test_role_selector_invalid_role_reports_configuration_error(
    tmp_path: Path,
):
    """Unknown roles in role-selector metadata should raise config errors."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {
            "dependency_files": [],
            "dependency_globs": [],
            "dependency_dirs": [],
            "dependency_roles": ["intent", "resolved", "package_manifest"],
            "dependency_role_files": ["unknown=>requirements.in"],
            "dependency_role_globs": [],
            "dependency_role_dirs": [],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
    )
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in"],
    )
    violations = checker.check(context)
    assert violations
    assert "outside configured `dependency_roles`" in violations[0].message


def _unit_test_policy_symbol_contract_is_stable():
    """Dependency-license-sync symbol contract should stay stable."""
    module = dependency_license_sync
    assert hasattr(module, "DependencyLicenseSyncCheck")
    assert hasattr(module, "parse_role_selector_entries")
    assert hasattr(module, "refresh_license_artifacts")
    assert hasattr(module, "resolve_dependency_roles")

    checker = module.DependencyLicenseSyncCheck()
    assert hasattr(checker, "run_runtime_action")


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

    def test_glob_metadata_matches_nested_manifest(self):
        """Run test_glob_metadata_matches_nested_manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_glob_metadata_matches_nested_manifest(tmp_path=tmp_path)

    def test_third_party_path_is_exact_not_name_only(self):
        """Run test_third_party_path_is_exact_not_name_only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_third_party_path_is_exact_not_name_only(
                tmp_path=tmp_path
            )

    def test_refresh_materializes_generic_license_readme(self):
        """Run test_refresh_materializes_generic_license_readme."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_refresh_materializes_generic_license_readme(
                tmp_path=tmp_path
            )

    def test_refresh_is_noop_when_artifacts_already_synced(self):
        """Run test_refresh_is_noop_when_artifacts_already_synced."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_refresh_is_noop_when_artifacts_already_synced(
                tmp_path=tmp_path
            )

    def test_refresh_uses_stable_report_entries(self):
        """Run test_refresh_uses_stable_report_entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_refresh_uses_stable_report_entries(tmp_path=tmp_path)

    def test_invalid_artifact_paths_raise_configuration_error(self):
        """Run test_invalid_artifact_paths_raise_configuration_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_invalid_artifact_paths_raise_configuration_error(
                tmp_path=tmp_path
            )

    def test_refresh_prunes_stale_report_entries(self):
        """Run test_refresh_prunes_stale_report_entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_refresh_prunes_stale_report_entries(tmp_path=tmp_path)

    def test_role_selectors_match_dependency_file(self):
        """Run test_role_selectors_match_dependency_file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_role_selectors_match_dependency_file(tmp_path=tmp_path)

    def test_role_selectors_support_mixed_role_entries(self):
        """Run test_role_selectors_support_mixed_role_entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_role_selectors_support_mixed_role_entries(
                tmp_path=tmp_path
            )

    def test_role_selector_invalid_role_reports_configuration_error(self):
        """Run test_role_selector_invalid_role_reports_configuration_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_role_selector_invalid_role_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_policy_symbol_contract_is_stable(self):
        """Run dependency-license-sync symbol contract assertions."""
        _unit_test_policy_symbol_contract_is_stable()
