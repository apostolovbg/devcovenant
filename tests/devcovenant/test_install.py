"""Unit tests for install command behavior."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from devcovenant import install
from devcovenant.core.services import registry as manifest_module

REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_WHEEL_PATH_FRAGMENTS = (
    "__pycache__/",
    ".pyc",
    ".pyo",
    "devcovenant/core/policies/",
    "devcovenant/core/profiles/",
)
_WHEEL_ENTRIES_CACHE: dict[tuple[object, ...], list[str]] = {}


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unit_test_install_writes_config_reviewed_and_manifest() -> None:
    """install_repo should copy core and seed review-required config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        assert config_path.exists()
        config = _read_yaml(config_path)
        install_block = config.get("install", {})
        assert isinstance(install_block, dict)
        assert install_block.get("config_reviewed") is False
        assert config.get("developer_mode") is False

        profiles_block = config.get("profiles", {})
        assert isinstance(profiles_block, dict)
        assert profiles_block.get("active") == [
            "global",
            "defaults",
            "devcovuser",
            "python",
            "docs",
        ]

        ignore_block = config.get("ignore", {})
        assert isinstance(ignore_block, dict)
        ignore_patterns = ignore_block.get("patterns", [])
        assert isinstance(ignore_patterns, list)
        for expected in (
            ".vscode/**",
            ".idea/**",
            "*.egg-info/**",
            "pip-wheel-metadata/**",
            ".coverage.*",
            "devcovenant/registry/runtime/**",
        ):
            assert expected in ignore_patterns

        clean_block = config.get("clean", {})
        assert isinstance(clean_block, dict)
        assert clean_block.get("overlays") == {
            "build_dirs": [],
            "build_globs": [],
            "cache_dirs": [],
            "cache_globs": [],
            "runtime_registry_dirs": [],
            "runtime_registry_globs": [],
            "logs_dirs": [],
            "logs_globs": [],
            "protected_dirs": [],
            "protected_globs": [],
        }
        assert clean_block.get("overrides") == {}

        gitignore_block = config.get("gitignore", {})
        assert isinstance(gitignore_block, dict)
        assert gitignore_block.get("overlays") == []

        manifest_path = manifest_module.manifest_path(repo_root)
        assert manifest_path.exists()


def _unit_test_install_writes_tracked_registry_without_runtime_state() -> None:
    """install_repo should seed tracked registry.yaml without runtime state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0

        registry_root = repo_root / "devcovenant" / "registry"
        tracked_registry = registry_root / "registry.yaml"
        runtime_registry = registry_root / "runtime"

        assert registry_root.exists()
        assert tracked_registry.exists()
        assert not runtime_registry.exists()


def _unit_test_install_preserves_existing_custom_tree() -> None:
    """install_repo should preserve custom policy/profile content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        custom_file = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_text("# custom\n", encoding="utf-8")

        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0
        assert custom_file.exists()
        assert custom_file.read_text(encoding="utf-8") == "# custom\n"


def _unit_test_install_does_not_copy_repo_custom_payload() -> None:
    """install_repo should not copy repo-only custom payload into targets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            result = install.install_repo(repo_root)
        assert result == 0

        leaked_policy = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "devcov_raw_string_escapes"
        )
        leaked_profile = (
            repo_root / "devcovenant" / "custom" / "profiles" / "devcovrepo"
        )
        assert not leaked_policy.exists()
        assert not leaked_profile.exists()


def _unit_test_replace_core_package_ignores_source_runtime_outputs() -> None:
    """replace_core_package should skip source runtime logs and registry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        repo_root = temp_root / "target"
        source_dir = temp_root / "source" / "devcovenant"
        source_dir.mkdir(parents=True, exist_ok=True)

        (source_dir / "__init__.py").write_text("__all__ = []\n")
        (source_dir / "README.md").write_text("# package readme\n")

        registry_root = source_dir / "registry"
        (registry_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
        (registry_root / "README.md").write_text("# registry readme\n")
        (registry_root / "registry.yaml").write_text("tracked: true\n")
        runtime_root = registry_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "latest.json").write_text("{}\n")

        logs_root = source_dir / "logs"
        logs_root.mkdir(parents=True, exist_ok=True)
        (logs_root / "README.md").write_text("# logs readme\n")
        stale_run_dir = logs_root / "20260315T000000000000Z-test"
        stale_run_dir.mkdir(parents=True, exist_ok=True)
        (stale_run_dir / "run.json").write_text("{}\n")

        install.replace_core_package(repo_root, source_dir=source_dir)

        target_root = repo_root / "devcovenant"
        assert (target_root / "registry" / "README.md").exists()
        assert (target_root / "logs" / "README.md").exists()
        assert not (target_root / "registry" / "registry.yaml").exists()
        assert not (target_root / "registry" / "runtime").exists()
        assert not (target_root / "logs" / stale_run_dir.name).exists()


def _unit_test_install_run_requires_upgrade_when_present() -> None:
    """run() should refuse existing installs and point to upgrade."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with redirect_stderr(StringIO()):
            install.install_repo(repo_root)

        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            with patch(
                "devcovenant.install.resolve_repo_root",
                return_value=repo_root,
            ):
                with patch("devcovenant.install.install_repo") as install_mock:
                    result = install.run(SimpleNamespace())

        assert result == 1
        install_mock.assert_not_called()
        output = output_buffer.getvalue()
    assert "already present" in output
    assert "devcovenant upgrade" in output


def _build_wheel(
    repo_root: Path,
    output_dir: Path,
    *,
    include_local_build_tree: bool = False,
    prepare_build_root: Callable[[Path], None] | None = None,
    clean_before_build: bool = False,
) -> Path:
    """Build a wheel artifact and return its path."""
    build_root = output_dir / "build-root"
    ignored_patterns = [
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "dist",
        "devcovenant.egg-info",
    ]
    if not include_local_build_tree:
        ignored_patterns.append("build")

    ignore = shutil.ignore_patterns(*ignored_patterns)
    shutil.copytree(
        repo_root,
        build_root,
        ignore=ignore,
        copy_function=shutil.copy,
    )
    if prepare_build_root is not None:
        prepare_build_root(build_root)
    if clean_before_build:
        _clean_local_build_artifacts(build_root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(build_root),
            "--no-deps",
            "-w",
            str(output_dir),
        ],
        cwd=build_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "Wheel build failed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    wheels = sorted(output_dir.glob("*.whl"))
    assert wheels, "Wheel build succeeded but no wheel artifact was produced."
    return wheels[0]


def _read_wheel_entries(wheel_path: Path) -> list[str]:
    """Return wheel entry names for content assertions."""
    with zipfile.ZipFile(wheel_path) as wheel:
        return wheel.namelist()


def _cached_wheel_entries(
    *,
    include_local_build_tree: bool = False,
    prepare_build_root: Callable[[Path], None] | None = None,
    clean_before_build: bool = False,
) -> list[str]:
    """Build and cache wheel entries for repeated packaging assertions."""
    cache_key = (
        include_local_build_tree,
        clean_before_build,
        "" if prepare_build_root is None else prepare_build_root.__name__,
    )
    cached = _WHEEL_ENTRIES_CACHE.get(cache_key)
    if cached is not None:
        return list(cached)

    with tempfile.TemporaryDirectory() as temp_dir:
        wheel_path = _build_wheel(
            REPO_ROOT,
            Path(temp_dir),
            include_local_build_tree=include_local_build_tree,
            prepare_build_root=prepare_build_root,
            clean_before_build=clean_before_build,
        )
        entries = _read_wheel_entries(wheel_path)

    _WHEEL_ENTRIES_CACHE[cache_key] = list(entries)
    return list(entries)


def _assert_no_forbidden_wheel_entries(entries: list[str]) -> None:
    """Assert wheel entries do not include stale artifacts or legacy paths."""
    violations: dict[str, list[str]] = {}
    for marker in FORBIDDEN_WHEEL_PATH_FRAGMENTS:
        matches = [entry for entry in entries if marker in entry]
        if matches:
            violations[marker] = matches

    assert not violations, (
        "Wheel contains forbidden entries.\n" f"violations={violations}"
    )


def _assert_runtime_outputs_excluded_from_wheel(entries: list[str]) -> None:
    """Assert tracked/runtime registry and logs obey wheel packaging rules."""
    forbidden_entries = [
        "devcovenant/registry/registry.yaml",
        "devcovenant/registry/runtime/latest.json",
        "devcovenant/registry/runtime/gate_status.json",
        "devcovenant/registry/runtime/session_snapshot.json",
        "devcovenant/logs/20260225T000000000000Z-test/run.json",
        "devcovenant/logs/20260225T000000000000Z-test/summary.json",
        "devcovenant/logs/20260225T000000000000Z-test/summary.txt",
        "devcovenant/logs/20260225T000000000000Z-test/tail.txt",
    ]
    for entry in forbidden_entries:
        assert entry not in entries, (
            "Wheel leaked runtime log artifact: " f"{entry}"
        )
    assert "devcovenant/logs/README.md" in entries
    assert "devcovenant/registry/README.md" in entries


def _seed_stale_build_tree(build_root: Path) -> None:
    """Write stale local build artifacts to prove packaging exclusions."""
    stale_policy = (
        build_root
        / "build"
        / "lib"
        / "devcovenant"
        / "core"
        / "policies"
        / "stale_policy.py"
    )
    stale_profile = (
        build_root
        / "build"
        / "lib"
        / "devcovenant"
        / "core"
        / "profiles"
        / "legacy"
        / "legacy.yaml"
    )
    stale_pyc = (
        build_root
        / "build"
        / "lib"
        / "devcovenant"
        / "__pycache__"
        / "stale.cpython-314.pyc"
    )

    stale_policy.parent.mkdir(parents=True, exist_ok=True)
    stale_profile.parent.mkdir(parents=True, exist_ok=True)
    stale_pyc.parent.mkdir(parents=True, exist_ok=True)
    stale_policy.write_text("# stale legacy policy\n", encoding="utf-8")
    stale_profile.write_text("id: legacy\n", encoding="utf-8")
    stale_pyc.write_bytes(b"stale-pyc")


def _seed_runtime_logs_tree(build_root: Path) -> None:
    """Write runtime log artifacts in source tree to prove exclusions."""
    run_dir = (
        build_root / "devcovenant" / "logs" / "20260225T000000000000Z-test"
    )
    runtime_registry = build_root / "devcovenant" / "registry" / "runtime"
    run_dir.mkdir(parents=True, exist_ok=True)
    runtime_registry.mkdir(parents=True, exist_ok=True)
    (runtime_registry / "latest.json").write_text(
        '{"run_dir": "devcovenant/logs/20260225T000000000000Z-test"}\n',
        encoding="utf-8",
    )
    (run_dir / "run.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "summary.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "summary.txt").write_text("summary\n", encoding="utf-8")
    (run_dir / "tail.txt").write_text("tail\n", encoding="utf-8")


def _seed_stale_and_runtime_tree(build_root: Path) -> None:
    """Seed stale build plus runtime logs for one shared wheel cache key."""
    _seed_stale_build_tree(build_root)
    _seed_runtime_logs_tree(build_root)


def _clean_local_build_artifacts(repo_root: Path) -> None:
    """Remove local build outputs before packaging to enforce determinism."""
    for rel_path in ("build", "dist", ".pytest_cache", ".ruff_cache"):
        shutil.rmtree(repo_root / rel_path, ignore_errors=True)

    for egg_info in repo_root.glob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info, ignore_errors=True)
        elif egg_info.exists():
            egg_info.unlink()


def _unit_test_pyproject_uses_pep639_license_metadata() -> None:
    """pyproject.toml should declare packaging/license metadata cleanly."""
    pyproject_data = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text("utf-8")
    )
    build_system = pyproject_data.get("build-system", {})
    assert build_system.get("build-backend") == "setuptools.build_meta"
    build_requires = build_system.get("requires")
    assert isinstance(build_requires, list)
    assert "setuptools>=77" in build_requires
    assert "wheel" in build_requires
    project_data = pyproject_data.get("project", {})
    assert project_data.get("license") == "MIT"
    readme_value = project_data.get("readme")
    assert isinstance(readme_value, dict)
    assert readme_value.get("file") == "devcovenant/README.md"
    assert readme_value.get("content-type") == "text/markdown"
    license_files = project_data.get("license-files")
    assert isinstance(license_files, list)
    for required in [
        "LICENSE",
        "licenses/THIRD_PARTY_LICENSES.md",
        "licenses/*.txt",
    ]:
        assert required in license_files


def _unit_test_manifest_includes_license_artifacts() -> None:
    """MANIFEST.in should include third-party license source artifacts."""
    content = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "include LICENSE" in content
    assert "include licenses/THIRD_PARTY_LICENSES.md" in content
    assert "recursive-include licenses *.txt" in content
    assert "recursive-exclude devcovenant/logs *" in content
    assert "include devcovenant/logs/README.md" in content
    assert "include devcovenant/registry/README.md" in content
    assert "exclude devcovenant/registry/registry.yaml" in content
    assert "recursive-exclude devcovenant/registry/runtime *" in content


def _unit_test_wheel_contains_required_license_artifacts() -> None:
    """Wheel must include required files under dist-info/licenses."""
    expected = ["LICENSE", "licenses/THIRD_PARTY_LICENSES.md"]
    licenses_dir = REPO_ROOT / "licenses"
    for path in sorted(licenses_dir.glob("*.txt")):
        if path.is_file():
            expected.append(f"licenses/{path.name}")

    names = _cached_wheel_entries()

    payloads = {
        name.split("dist-info/licenses/", 1)[1]
        for name in names
        if "dist-info/licenses/" in name
    }
    for required in expected:
        assert required in payloads, (
            "Missing required license artifact in wheel metadata: "
            f"{required}"
        )


def _unit_test_wheel_excludes_forbidden_artifacts() -> None:
    """Wheel should exclude bytecode and removed legacy policy trees."""
    entries = _cached_wheel_entries()

    _assert_no_forbidden_wheel_entries(entries)


def _unit_test_dirty_build_tree_does_not_leak_into_wheel() -> None:
    """Wheel should stay clean after dirty trees are pre-cleaned."""
    entries = _cached_wheel_entries(
        include_local_build_tree=True,
        prepare_build_root=_seed_stale_and_runtime_tree,
        clean_before_build=True,
    )

    _assert_no_forbidden_wheel_entries(entries)
    assert not any("stale_policy.py" in entry for entry in entries)
    assert not any("legacy.yaml" in entry for entry in entries)


def _unit_test_wheel_excludes_runtime_logs_but_keeps_logs_readme() -> None:
    """Wheel should exclude runtime outputs while keeping tracked READMEs."""
    entries = _cached_wheel_entries(
        include_local_build_tree=True,
        prepare_build_root=_seed_stale_and_runtime_tree,
        clean_before_build=True,
    )

    _assert_runtime_outputs_excluded_from_wheel(entries)


def _unit_test_install_symbol_contract_is_stable() -> None:
    """Install module should keep key command symbols stable."""
    assert hasattr(install, "replace_core_package")
    assert callable(install.replace_core_package)
    assert hasattr(install, "main")
    assert callable(install.main)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_install_writes_config_reviewed_and_manifest(self):
        """Run test_install_writes_config_reviewed_and_manifest."""
        _unit_test_install_writes_config_reviewed_and_manifest()

    def test_install_writes_tracked_registry_without_runtime_state(self):
        """Run test_install_writes_tracked_registry_without_runtime_state."""
        _unit_test_install_writes_tracked_registry_without_runtime_state()

    def test_install_preserves_existing_custom_tree(self):
        """Run test_install_preserves_existing_custom_tree."""
        _unit_test_install_preserves_existing_custom_tree()

    def test_install_does_not_copy_repo_custom_payload(self):
        """Run install repo-only custom-payload exclusion assertions."""
        _unit_test_install_does_not_copy_repo_custom_payload()

    def test_replace_core_package_ignores_source_runtime_outputs(self):
        """Run source-runtime-output exclusion assertions for install."""
        _unit_test_replace_core_package_ignores_source_runtime_outputs()

    def test_install_run_requires_upgrade_when_present(self):
        """Run test_install_run_requires_upgrade_when_present."""
        _unit_test_install_run_requires_upgrade_when_present()

    def test_pyproject_uses_pep639_license_metadata(self):
        """Run test_pyproject_uses_pep639_license_metadata."""
        _unit_test_pyproject_uses_pep639_license_metadata()

    def test_manifest_includes_license_artifacts(self):
        """Run test_manifest_includes_license_artifacts."""
        _unit_test_manifest_includes_license_artifacts()

    def test_wheel_contains_required_license_artifacts(self):
        """Run test_wheel_contains_required_license_artifacts."""
        _unit_test_wheel_contains_required_license_artifacts()

    def test_wheel_excludes_forbidden_artifacts(self):
        """Run test_wheel_excludes_forbidden_artifacts."""
        _unit_test_wheel_excludes_forbidden_artifacts()

    def test_dirty_build_tree_does_not_leak_into_wheel(self):
        """Run test_dirty_build_tree_does_not_leak_into_wheel."""
        _unit_test_dirty_build_tree_does_not_leak_into_wheel()

    def test_wheel_excludes_runtime_logs_but_keeps_logs_readme(self):
        """Run test_wheel_excludes_runtime_logs_but_keeps_logs_readme."""
        _unit_test_wheel_excludes_runtime_logs_but_keeps_logs_readme()

    def test_install_symbol_contract_is_stable(self):
        """Run test_install_symbol_contract_is_stable."""
        _unit_test_install_symbol_contract_is_stable()
