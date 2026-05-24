"""Tests for the dependency-management policy."""

import importlib
import importlib.metadata as importlib_metadata
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.dependency_management import (
    dependency_lock_runtime,
    dependency_management,
)
from devcovenant.core.policy_contract import CheckContext


def _setup_repo(tmp_path: Path) -> Path:
    """Create a minimal repo layout for license tracking tests."""
    packaging_version = importlib_metadata.version("packaging")
    pytest_version = importlib_metadata.version("pytest")
    tmp_path.joinpath("licenses").mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements.in").write_text(
        "packaging>=26.0\npytest>=9.0.2\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.lock").write_text(
        f"packaging=={packaging_version}\n" f"pytest=={pytest_version}\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'test'\n"
        "dependencies = [\n"
        "  'packaging>=26.0',\n"
        "  'pytest>=9.0.2',\n"
        "]\n",
        encoding="utf-8",
    )
    (tmp_path / "licenses" / "THIRD_PARTY_LICENSES.md").write_text(
        "# Third-Party Licenses\n", encoding="utf-8"
    )
    (tmp_path / "licenses" / "BSD-3-Clause.txt").write_text(
        "BSD text\n", encoding="utf-8"
    )
    return tmp_path


def _build_checker() -> dependency_management.DependencyManagementCheck:
    """Create a checker with dependency manifests configured."""
    return _build_checker_with_options(
        {
            "surfaces": [
                _surface_options(
                    dependency_files=[
                        "requirements.in",
                        "pyproject.toml",
                    ]
                )
            ]
        }
    )


def _build_checker_with_options(
    options: dict[str, object],
) -> dependency_management.DependencyManagementCheck:
    """Create a checker with explicit metadata options."""
    checker = dependency_management.DependencyManagementCheck()
    checker.set_options(
        metadata_options=options,
        config_overrides=None,
    )
    return checker


def _surface_options(**overrides: object) -> dict[str, object]:
    """Return one dependency-management surface mapping for tests."""

    surface: dict[str, object] = {
        "id": "root_workspace",
        "lock_file": "requirements.lock",
        "direct_dependency_files": ["requirements.in"],
        "dependency_files": ["requirements.in"],
        "dependency_globs": [],
        "dependency_dirs": [],
        "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
        "licenses_dir": "licenses",
        "report_heading": "## License Report",
    }
    surface.update(overrides)
    return surface


def _surface_hash_targets() -> list[dict[str, object]]:
    """Return a small cross-platform target matrix for audit tests."""

    return [
        {
            "id": "linux-py311",
            "marker": 'sys_platform == "linux" and python_version == "3.11"',
            "pip": {
                "platform": "manylinux2014_x86_64",
                "implementation": "cp",
                "python_version": "3.11",
                "abi": "cp311",
            },
        },
        {
            "id": "windows-py311",
            "marker": 'sys_platform == "win32" and python_version == "3.11"',
            "pip": {
                "platform": "win_amd64",
                "implementation": "cp",
                "python_version": "3.11",
                "abi": "cp311",
            },
        },
    ]


def _vulnerability_payload(
    vulnerability_id: str,
    *,
    aliases: list[str] | None = None,
    fixed_in: list[str] | None = None,
    summary: str = "",
) -> list[dict[str, object]]:
    """Return one normalized vulnerability payload for audit tests."""

    return [
        {
            "id": vulnerability_id,
            "aliases": aliases or [],
            "fixed_in": fixed_in or [],
            "summary": summary,
        }
    ]


def _archive_bytes(members: dict[str, str]) -> bytes:
    """Return one in-memory tar.gz archive for override tests."""

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, text in members.items():
            payload = text.encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def _dist_without_license_files(name: str):
    """Return one fake distribution with no dist-info license files."""

    return type(
        "FakeDistribution",
        (),
        {
            "files": [],
            "metadata": {"Name": name},
        },
    )()


def _override_options(**overrides: object) -> list[dict[str, object]]:
    """Return one archive-backed license-source override mapping."""

    payload: dict[str, object] = {
        "id": "flet",
        "kind": "archive_url",
        "url": "https://example.invalid/releases/v{version}.tar.gz",
        "member_globs": ["*/sdk/python/packages/flet/LICENSE"],
    }
    payload.update(overrides)
    return [payload]


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
            "surfaces": [
                _surface_options(
                    dependency_files=[],
                    dependency_globs=["services/*/package.json"],
                )
            ]
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
            "surfaces": [
                _surface_options(
                    dependency_files=["requirements.in"],
                    third_party_file="docs/THIRD_PARTY_LICENSES.md",
                )
            ]
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


def _unit_test_dependency_file_selector_is_exact_repo_relative_path(
    tmp_path: Path,
):
    """Bare dependency-files selectors should not match same-basename files."""
    repo = _setup_repo(tmp_path)
    asset_requirements = (
        repo
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "python"
        / "assets"
        / "requirements.in"
    )
    asset_requirements.parent.mkdir(parents=True, exist_ok=True)
    asset_requirements.write_text("packaging>=26.0\n", encoding="utf-8")
    checker = _build_checker()
    context = CheckContext(
        repo_root=repo,
        changed_files=[asset_requirements],
    )
    violations = checker.check(context)
    assert violations == []


def _unit_test_profile_asset_dependency_input_is_rejected(tmp_path: Path):
    """Profile-asset `requirements.in` should be rejected as input."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {
            "surfaces": [
                _surface_options(
                    direct_dependency_files=[
                        "devcovenant/builtin/profiles/python/assets/"
                        "requirements.in"
                    ],
                    dependency_files=[
                        "devcovenant/builtin/profiles/python/assets/"
                        "requirements.in"
                    ],
                )
            ]
        }
    )
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in"],
    )
    violations = checker.check(context)
    assert len(violations) == 1


def _setup_included_manifest_repo(tmp_path: Path) -> Path:
    """Create one repo layout with included lock manifests."""

    tmp_path.joinpath("licenses").mkdir(parents=True, exist_ok=True)
    tmp_path.joinpath("devcovenant").mkdir(parents=True, exist_ok=True)
    tmp_path.joinpath("package").mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements.in").write_text(
        "\n".join(
            [
                "-r devcovenant/runtime-requirements.lock",
                "-r package/runtime-requirements.lock",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "devcovenant" / "runtime-requirements.lock").write_text(
        "\n".join(
            [
                "build==1.4.2 \\",
                "    --hash=sha256:deadbeef",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "package" / "runtime-requirements.lock").write_text(
        "\n".join(
            [
                "ttkbootstrap==1.20.2 \\",
                "    --hash=sha256:feedface",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "requirements.lock").write_text(
        "\n".join(
            [
                "build==1.4.2",
                "ttkbootstrap==1.20.2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return tmp_path


def _unit_test_display_names_expand_requirement_includes(tmp_path: Path):
    """Included requirement manifests should contribute inventory names."""

    repo = _setup_included_manifest_repo(tmp_path)

    display_names = dependency_management._direct_dependency_display_names(
        repo,
        direct_dependency_files=["requirements.in"],
    )

    assert display_names == {
        "build": "build",
        "ttkbootstrap": "ttkbootstrap",
    }


def _unit_test_inventory_uses_packages_from_included_lockfiles(
    tmp_path: Path,
):
    """Included lock manifests should populate inventory entries."""

    repo = _setup_included_manifest_repo(tmp_path)

    original_find_distribution = dependency_management._find_distribution
    dependency_management._find_distribution = lambda _name: object()
    try:
        inventory = dependency_management._build_dependency_inventory(
            repo,
            licenses_dir_path=repo / "licenses",
            resolved_lock_file="requirements.lock",
            direct_dependency_files=["requirements.in"],
        )
    finally:
        dependency_management._find_distribution = original_find_distribution

    assert inventory == [
        {
            "normalized_name": "build",
            "package_name": "build",
            "version": "1.4.2",
            "relative_path": "build-1.4.2.txt",
        },
        {
            "normalized_name": "ttkbootstrap",
            "package_name": "ttkbootstrap",
            "version": "1.20.2",
            "relative_path": "ttkbootstrap-1.20.2.txt",
        },
    ]


def _unit_test_license_source_overrides_require_unique_package_ids():
    """Fallback license overrides should reject duplicate package ids."""

    try:
        dependency_management.resolve_license_source_overrides(
            [
                *_override_options(id="Flet"),
                *_override_options(id="flet"),
            ]
        )
    except ValueError as error:
        assert "duplicate id `flet`" in str(error)
    else:
        raise AssertionError("Duplicate override ids should fail.")


def _unit_test_license_source_symbols_stay_public():
    """License-source helper symbols should stay importable."""

    assert (
        dependency_management.DependencyLicenseSourceOverride.__name__
        == "DependencyLicenseSourceOverride"
    )
    assert (
        dependency_management.DependencyLicenseSourceBundle.__name__
        == "DependencyLicenseSourceBundle"
    )
    assert callable(dependency_management.resolve_license_source_overrides)


def _unit_test_archive_override_fills_missing_installed_license_files():
    """Archive overrides should supply license texts when metadata is empty."""

    fake_dist = _dist_without_license_files("flet")
    overrides = dependency_management.resolve_license_source_overrides(
        _override_options()
    )
    original_read_url_bytes = dependency_management._read_url_bytes
    dependency_management._read_url_bytes = lambda _url: _archive_bytes(
        {"flet-0.84.0/sdk/python/packages/flet/LICENSE": ("Apache License\n")}
    )
    try:
        bundle = dependency_management._resolve_dependency_license_bundle(
            package_name="flet",
            version="0.84.0",
            dist=fake_dist,
            license_source_overrides=overrides,
        )
    finally:
        dependency_management._read_url_bytes = original_read_url_bytes
        dependency_management._read_url_bytes.cache_clear()

    assert bundle.origin_description == (
        "source archive " "`https://example.invalid/releases/v0.84.0.tar.gz`"
    )
    assert bundle.sources == [
        (
            "flet-0.84.0/sdk/python/packages/flet/LICENSE",
            "Apache License\n",
        )
    ]


def _unit_test_installed_metadata_wins_before_archive_override(tmp_path: Path):
    """Installed dist-info licenses should win over configured fallbacks."""

    license_path = tmp_path / "flet-0.84.0.dist-info" / "LICENSE"
    license_path.parent.mkdir(parents=True, exist_ok=True)
    license_path.write_text("Installed license\n", encoding="utf-8")

    # The fake distribution keeps one dist-info license file on disk so
    # the installed-metadata path wins before any archive fallback is used.
    class _FakeDistribution:
        files = ["flet-0.84.0.dist-info/LICENSE"]
        metadata = {"Name": "flet"}

        def locate_file(self, _entry):
            """Return the on-disk path for the fake dist-info license."""
            return license_path

    overrides = dependency_management.resolve_license_source_overrides(
        _override_options()
    )
    original_read_url_bytes = dependency_management._read_url_bytes
    dependency_management._read_url_bytes = lambda _url: (_ for _ in ()).throw(
        AssertionError("unexpected fetch")
    )
    try:
        bundle = dependency_management._resolve_dependency_license_bundle(
            package_name="flet",
            version="0.84.0",
            dist=_FakeDistribution(),
            license_source_overrides=overrides,
        )
    finally:
        dependency_management._read_url_bytes = original_read_url_bytes
        dependency_management._read_url_bytes.cache_clear()

    assert bundle.origin_description == "installed distribution metadata"
    assert bundle.sources == [("LICENSE", "Installed license\n")]


def _unit_test_refresh_materializes_generic_license_readme(tmp_path: Path):
    """refresh_license_artifacts should create licenses/README.md."""
    repo = _setup_repo(tmp_path)
    modified = dependency_management.refresh_license_artifacts(
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
    dependency_management.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    report = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
    before_report = report.read_text(encoding="utf-8")
    licenses_readme = repo / "licenses" / "README.md"
    before_readme = licenses_readme.read_text(encoding="utf-8")
    packaging_version = importlib_metadata.version("packaging")
    pytest_version = importlib_metadata.version("pytest")
    before_packaging = (
        repo / "licenses" / f"packaging-{packaging_version}.txt"
    ).read_text(encoding="utf-8")
    before_pytest = (
        repo / "licenses" / f"pytest-{pytest_version}.txt"
    ).read_text(encoding="utf-8")

    modified = dependency_management.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )

    assert modified == []
    assert report.read_text(encoding="utf-8") == before_report
    assert licenses_readme.read_text(encoding="utf-8") == before_readme
    assert (
        repo / "licenses" / f"packaging-{packaging_version}.txt"
    ).read_text(encoding="utf-8") == before_packaging
    assert (repo / "licenses" / f"pytest-{pytest_version}.txt").read_text(
        encoding="utf-8"
    ) == before_pytest


def _unit_test_synced_artifacts_need_no_touch_churn_for_manifest_edit(
    tmp_path: Path,
):
    """Synced dependency artifacts should not require fake touch churn."""
    repo = _setup_repo(tmp_path)
    dependency_management.refresh_license_artifacts(
        repo,
        changed_dependency_files=["pyproject.toml"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    checker = _build_checker()
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "pyproject.toml"],
    )
    violations = checker.check(context)
    assert violations == []


def _unit_test_manifest_refresh_keeps_resolved_lock_in_report(
    tmp_path: Path,
):
    """Manifest-led refresh should still cite the resolved lock file."""
    repo = _setup_repo(tmp_path)
    dependency_management.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.in"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    report = (repo / "licenses" / "THIRD_PARTY_LICENSES.md").read_text(
        encoding="utf-8"
    )
    assert "- `requirements.in`" in report
    assert "- `requirements.lock`" in report


def _unit_test_refresh_uses_stable_report_entries(tmp_path: Path):
    """Report entries should stay deterministic and non-date-prefixed."""
    repo = _setup_repo(tmp_path)
    dependency_management.refresh_license_artifacts(
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
    packaging_version = importlib_metadata.version("packaging")
    report_path = repo / "licenses" / "THIRD_PARTY_LICENSES.md"
    stale_license = repo / "licenses" / "packaging-0.0.1.txt"
    stale_license.write_text("old\n", encoding="utf-8")
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
                "- `packaging==0.0.1`: `licenses/packaging-0.0.1.txt`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    dependency_management.refresh_license_artifacts(
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
    assert stale_license.exists() is False
    assert f"- `packaging=={packaging_version}`" in report


def _unit_test_refresh_materializes_inventory_and_license_texts(
    tmp_path: Path,
):
    """Refresh should build dependency inventory and upstream license texts."""
    repo = _setup_repo(tmp_path)
    modified = dependency_management.refresh_license_artifacts(
        repo,
        changed_dependency_files=["requirements.lock"],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading="## License Report",
    )
    packaging_version = importlib_metadata.version("packaging")
    pytest_version = importlib_metadata.version("pytest")
    report = (repo / "licenses" / "THIRD_PARTY_LICENSES.md").read_text(
        encoding="utf-8"
    )
    packaging_license = (
        repo / "licenses" / f"packaging-{packaging_version}.txt"
    )
    pytest_license = repo / "licenses" / f"pytest-{pytest_version}.txt"
    assert packaging_license in modified
    assert pytest_license in modified
    assert "## Dependency License Inventory" in report
    assert f"`packaging=={packaging_version}`" in report
    assert f"`pytest=={pytest_version}`" in report
    assert "LICENSE.APACHE" in packaging_license.read_text(encoding="utf-8")
    assert "# pytest " in pytest_license.read_text(encoding="utf-8")


def _unit_test_refresh_supports_archive_license_overrides(tmp_path: Path):
    """Refresh should generate license texts from archive overrides."""

    repo = tmp_path
    repo.joinpath("licenses").mkdir(parents=True, exist_ok=True)
    (repo / "requirements.in").write_text("flet>=0.84\n", encoding="utf-8")
    (repo / "requirements.lock").write_text(
        "flet==0.84.0\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        "[project]\n" "name = 'demo'\n" "dependencies = ['flet>=0.84']\n",
        encoding="utf-8",
    )
    fake_dist = _dist_without_license_files("flet")
    overrides = dependency_management.resolve_license_source_overrides(
        _override_options()
    )
    original_find_distribution = dependency_management._find_distribution
    original_read_url_bytes = dependency_management._read_url_bytes
    dependency_management._find_distribution = lambda _name: fake_dist
    dependency_management._read_url_bytes = lambda _url: _archive_bytes(
        {"flet-0.84.0/sdk/python/packages/flet/LICENSE": ("Apache License\n")}
    )
    try:
        dependency_management.refresh_license_artifacts(
            repo,
            changed_dependency_files=["requirements.lock"],
            third_party_file="licenses/THIRD_PARTY_LICENSES.md",
            licenses_dir="licenses",
            report_heading="## License Report",
            license_source_overrides=overrides,
        )
    finally:
        dependency_management._find_distribution = original_find_distribution
        dependency_management._read_url_bytes = original_read_url_bytes
        dependency_management._read_url_bytes.cache_clear()

    license_text = (repo / "licenses" / "flet-0.84.0.txt").read_text(
        encoding="utf-8"
    )
    report = (repo / "licenses" / "THIRD_PARTY_LICENSES.md").read_text(
        encoding="utf-8"
    )
    assert "Resolved from: source archive" in license_text
    assert "https://example.invalid/releases/v0.84.0.tar.gz" in license_text
    assert "Apache License" in license_text
    assert "`flet==0.84.0`" in report


def _unit_test_invalid_artifact_paths_raise_configuration_error(
    tmp_path: Path,
):
    """Outside-repo artifact targets should emit configuration violations."""
    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {
            "surfaces": [
                _surface_options(
                    dependency_files=["requirements.in"],
                    third_party_file="../outside.md",
                )
            ]
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
            "surfaces": [
                _surface_options(
                    dependency_files=[],
                    dependency_roles=[
                        "intent",
                        "resolved",
                        "package_manifest",
                    ],
                    dependency_role_files=["intent=>requirements.in"],
                )
            ]
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
            "surfaces": [
                _surface_options(
                    dependency_files=[],
                    dependency_roles=[
                        "intent",
                        "resolved",
                        "package_manifest",
                    ],
                    dependency_role_files=["resolved=>requirements.lock"],
                    dependency_role_globs=[
                        "package_manifest=>services/*/package.json"
                    ],
                )
            ]
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
            "surfaces": [
                _surface_options(
                    dependency_files=[],
                    dependency_roles=[
                        "intent",
                        "resolved",
                        "package_manifest",
                    ],
                    dependency_role_files=["unknown=>requirements.in"],
                )
            ]
        }
    )
    context = CheckContext(
        repo_root=repo,
        changed_files=[repo / "requirements.in"],
    )
    violations = checker.check(context)
    assert violations
    assert "outside configured `dependency_roles`" in violations[0].message


def _unit_test_vulnerability_audit_runs_without_changed_files(
    tmp_path: Path,
):
    """Surface-local vulnerability audit should run even without edits."""

    repo = _setup_repo(tmp_path)
    (repo / "requirements.lock").write_text(
        'testlockedpkg==1.2.3 ; sys_platform == "linux"\n',
        encoding="utf-8",
    )
    checker = _build_checker_with_options(
        {
            "surfaces": [
                _surface_options(
                    audit_service="pypi",
                    audit_ignore_ids=[],
                    hash_targets=_surface_hash_targets(),
                )
            ]
        }
    )
    original_query = dependency_lock_runtime._query_pypi_vulnerabilities
    dependency_lock_runtime._query_pypi_vulnerabilities = (
        lambda _name, _version: _vulnerability_payload(
            "CVE-2026-39892",
            fixed_in=["1.2.4"],
        )
    )
    try:
        violations = checker.check(CheckContext(repo_root=repo))
    finally:
        dependency_lock_runtime._query_pypi_vulnerabilities = original_query
    assert len(violations) == 1
    violation = violations[0]
    assert violation.can_auto_fix is True
    assert violation.context["changed_dependency_files"] == [
        "requirements.lock"
    ]
    assert violation.context["issue"] == "vulnerability_audit"
    assert "linux-py311" in violation.message
    assert "windows-py311" not in violation.message


def _unit_test_vulnerability_audit_respects_ignore_ids(tmp_path: Path):
    """Surface ignore ids should suppress matching advisories."""

    repo = _setup_repo(tmp_path)
    (repo / "requirements.lock").write_text(
        "testignoredpkg==2.0.0\n",
        encoding="utf-8",
    )
    checker = _build_checker_with_options(
        {
            "surfaces": [
                _surface_options(
                    audit_service="pypi",
                    audit_ignore_ids=["GHSA-TEST-0001"],
                )
            ]
        }
    )
    original_query = dependency_lock_runtime._query_pypi_vulnerabilities
    dependency_lock_runtime._query_pypi_vulnerabilities = (
        lambda _name, _version: _vulnerability_payload(
            "PYSEC-2026-1",
            aliases=["GHSA-test-0001"],
            fixed_in=["2.0.1"],
        )
    )
    try:
        violations = checker.check(CheckContext(repo_root=repo))
    finally:
        dependency_lock_runtime._query_pypi_vulnerabilities = original_query
    assert violations == []


def _unit_test_invalid_audit_service_reports_configuration_error(
    tmp_path: Path,
):
    """Unknown audit services should fail as configuration errors."""

    repo = _setup_repo(tmp_path)
    checker = _build_checker_with_options(
        {"surfaces": [_surface_options(audit_service="osv")]}
    )
    violations = checker.check(CheckContext(repo_root=repo))
    assert len(violations) == 1
    assert "audit_service" in violations[0].message


def _unit_test_policy_symbol_contract_is_stable():
    """Dependency-management symbol contract should stay stable."""
    module = dependency_management
    assert hasattr(module, "DependencyManagementCheck")
    assert hasattr(module, "DependencySurface")
    assert hasattr(module, "DependencySurfaceTarget")
    assert hasattr(module, "dependency_surface_lock_refresh_requested")
    assert hasattr(module, "dependency_surface_matches")
    assert hasattr(module, "dependency_surface_trigger_files")
    assert hasattr(module, "parse_role_selector_entries")
    assert hasattr(module, "refresh_license_artifacts")
    assert hasattr(module, "resolve_dependency_surfaces")
    assert hasattr(module, "resolve_dependency_roles")
    assert hasattr(module, "RUNTIME_ACTION_REFRESH_FORCE")
    assert hasattr(dependency_lock_runtime, "refresh_force")

    checker = module.DependencyManagementCheck()
    assert hasattr(checker, "run_runtime_action")


def _unit_test_runtime_action_dispatch_supports_force_refresh() -> None:
    """Runtime-action dispatch should accept `refresh-force`."""

    module_name = (
        "devcovenant.builtin.policies.dependency_management."
        "dependency_management"
    )
    module = importlib.import_module(module_name)
    captured: dict[str, object] = {}
    checker = module.DependencyManagementCheck()
    original_refresh_force = dependency_lock_runtime.refresh_force

    def _fake_refresh_force(repo_root, *, payload=None):
        """Capture the forced refresh payload for assertions."""

        captured["repo_root"] = repo_root
        captured["payload"] = payload
        return {"message": "forced"}

    dependency_lock_runtime.refresh_force = _fake_refresh_force
    try:
        result = checker.run_runtime_action(
            module.RUNTIME_ACTION_REFRESH_FORCE,
            repo_root=Path("/tmp/devcovenant"),
            payload={"changed_dependency_files": ["requirements.in"]},
        )
    finally:
        dependency_lock_runtime.refresh_force = original_refresh_force

    assert result == {"message": "forced"}
    assert captured["payload"] == {
        "changed_dependency_files": ["requirements.in"]
    }


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

    def test_dependency_file_selector_is_exact_repo_relative_path(self):
        """Run exact dependency-file selector regression assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_dependency_file_selector_is_exact_repo_relative_path(
                tmp_path=tmp_path
            )

    def test_profile_asset_dependency_input_is_rejected(self):
        """Run profile-asset dependency-input rejection assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_profile_asset_dependency_input_is_rejected(
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

    def test_synced_artifacts_need_no_touch_churn_for_manifest_edit(self):
        """Run synced-artifact no-touch-churn regression coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_synced_artifacts_need_no_touch_churn_for_manifest_edit(
                tmp_path=tmp_path
            )

    def test_manifest_refresh_keeps_resolved_lock_in_report(self):
        """Run manifest-led report rendering assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_manifest_refresh_keeps_resolved_lock_in_report(
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

    def test_refresh_materializes_inventory_and_license_texts(self):
        """Run inventory/license-text materialization assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_refresh_materializes_inventory_and_license_texts(
                tmp_path=tmp_path
            )

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

    def test_vulnerability_audit_runs_without_changed_files(self):
        """Run dependency vulnerability audit no-edit assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_vulnerability_audit_runs_without_changed_files(
                tmp_path=tmp_path
            )

    def test_vulnerability_audit_respects_ignore_ids(self):
        """Run dependency vulnerability ignore-id assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_vulnerability_audit_respects_ignore_ids(
                tmp_path=tmp_path
            )

    def test_invalid_audit_service_reports_configuration_error(self):
        """Run dependency vulnerability audit-service validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_invalid_audit_service_reports_configuration_error(
                tmp_path=tmp_path
            )

    def test_policy_symbol_contract_is_stable(self):
        """Run dependency-management symbol contract assertions."""
        _unit_test_policy_symbol_contract_is_stable()

    def test_runtime_action_dispatch_supports_force_refresh(self):
        """Run force-refresh runtime-action dispatch assertions."""
        _unit_test_runtime_action_dispatch_supports_force_refresh()

    def test_display_names_expand_requirement_includes(self):
        """Run included-manifest display-name expansion assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_display_names_expand_requirement_includes(
                tmp_path=tmp_path
            )

    def test_inventory_uses_packages_from_included_lockfiles(self):
        """Run included-lock inventory materialization assertions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_inventory_uses_packages_from_included_lockfiles(
                tmp_path=tmp_path
            )
