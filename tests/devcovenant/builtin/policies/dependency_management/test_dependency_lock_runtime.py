"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import importlib.metadata as importlib_metadata
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = (
    "devcovenant.builtin.policies.dependency_management."
    "dependency_lock_runtime"
)
REPO_ROOT = Path(__file__).resolve().parents[5]


def _surface(module, **overrides):
    """Build one dependency surface object for runtime tests."""

    surface = module.dependency_management.DependencySurface(
        surface_id="root_workspace",
        enabled=True,
        active=True,
        lock_file="requirements.lock",
        direct_dependency_files=["requirements.in"],
        dependency_files=["requirements.in", "pyproject.toml"],
        dependency_globs=[],
        dependency_dirs=[],
        third_party_file="licenses/THIRD_PARTY_LICENSES.md",
        licenses_dir="licenses",
        report_heading=module.dependency_management.DEFAULT_REPORT_HEADING,
        manage_licenses_readme=True,
        generate_hashes=False,
        required_paths=[],
        hash_targets=[],
    )
    return module.dependency_management.DependencySurface(
        **{**surface.__dict__, **overrides}
    )


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_runtime_resolves_structured_surfaces_from_repo_metadata() -> (
    None
):
    """Runtime metadata resolution should keep structured surface mappings."""

    module = importlib.import_module(MODULE)
    payload = module._resolve_dependency_metadata(REPO_ROOT)
    surfaces = payload.get("surfaces")
    assert isinstance(surfaces, list)
    assert surfaces
    assert all(
        isinstance(
            surface,
            module.dependency_management.DependencySurface,
        )
        for surface in surfaces
    )
    assert {surface.surface_id for surface in surfaces} >= {
        "root_workspace",
        "devcovenant_runtime",
    }


def _unit_test_runtime_symbol_contract_is_stable() -> None:
    """Runtime helper dataclasses/functions should stay available."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "LockFilePieces")
    assert hasattr(module, "LockHandlerResult")
    assert hasattr(module, "refresh_all")


def _unit_test_refresh_runtime_updates_inventory_without_lock_change() -> None:
    """Lock refresh should still repair stale license inventory artifacts."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            f"packaging=={packaging_version}\n",
            encoding="utf-8",
        )
        (repo_root / "pyproject.toml").write_text(
            "[project]\n"
            "name = 'demo'\n"
            "dependencies = ['packaging>=26.0']\n",
            encoding="utf-8",
        )
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "# Third-Party Licenses\n\n"
            "## License Report\n"
            "- `requirements.lock`\n\n"
            "## Dependency License Inventory\n"
            "- `packaging==0.0.1`: `licenses/packaging-0.0.1.txt`\n",
            encoding="utf-8",
        )
        (licenses_dir / "packaging-0.0.1.txt").write_text(
            "stale\n",
            encoding="utf-8",
        )
        original_resolver = module._resolve_dependency_metadata
        original_compile = module._compile_requirements_lock
        module._resolve_dependency_metadata = lambda _repo_root: {
            "surfaces": [_surface(module)],
        }

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return the existing lock content without changing it."""

            return module.LockFilePieces([f"packaging=={packaging_version}"])

        module._compile_requirements_lock = _fake_compile
        try:
            payload = module.refresh_all(repo_root)
        finally:
            module._resolve_dependency_metadata = original_resolver
            module._compile_requirements_lock = original_compile

        results = payload["lock_results"]
        modified = payload["refreshed_artifacts"]
        assert results
        assert results[0]["changed"] is False
        assert any(
            Path(str(path)).name == f"packaging-{packaging_version}.txt"
            for path in modified
        )
        assert not (licenses_dir / "packaging-0.0.1.txt").exists()
        report = (licenses_dir / "THIRD_PARTY_LICENSES.md").read_text(
            encoding="utf-8"
        )
        assert f"`packaging=={packaging_version}`" in report


def _unit_test_refresh_runtime_preserves_changed_manifest_references() -> None:
    """Runtime refresh should keep all caller-supplied manifest references."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            f"packaging=={packaging_version}\n",
            encoding="utf-8",
        )
        (repo_root / "pyproject.toml").write_text(
            "[project]\n"
            "name = 'demo'\n"
            "dependencies = ['packaging>=26.0']\n",
            encoding="utf-8",
        )
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "# Third-Party Licenses\n\n"
            "## License Report\n"
            "- `requirements.lock`\n\n"
            "## Dependency License Inventory\n"
            f"- `packaging=={packaging_version}`: "
            f"`licenses/packaging-{packaging_version}.txt`\n",
            encoding="utf-8",
        )
        original_resolver = module._resolve_dependency_metadata
        original_compile = module._compile_requirements_lock
        module._resolve_dependency_metadata = lambda _repo_root: {
            "surfaces": [_surface(module)],
        }

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return one stable resolved dependency line for the report."""

            return module.LockFilePieces([f"packaging=={packaging_version}"])

        module._compile_requirements_lock = _fake_compile
        try:
            module.refresh_all(
                repo_root,
                payload={
                    "changed_dependency_files": [
                        "pyproject.toml",
                        "requirements.lock",
                    ]
                },
            )
        finally:
            module._resolve_dependency_metadata = original_resolver
            module._compile_requirements_lock = original_compile

        report = (licenses_dir / "THIRD_PARTY_LICENSES.md").read_text(
            encoding="utf-8"
        )
        assert "- `pyproject.toml`" in report
        assert "- `requirements.lock`" in report


def _unit_test_refresh_runtime_skips_compile_for_manifest_only() -> None:
    """Manifest-only refresh should not recompile requirements.lock."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            f"packaging=={packaging_version}\n",
            encoding="utf-8",
        )
        (repo_root / "pyproject.toml").write_text(
            "[project]\n"
            "name = 'demo'\n"
            "dependencies = ['packaging>=26.0']\n",
            encoding="utf-8",
        )
        (licenses_dir / "THIRD_PARTY_LICENSES.md").write_text(
            "# Third-Party Licenses\n\n"
            "## License Report\n"
            "- `requirements.lock`\n\n"
            "## Dependency License Inventory\n"
            f"- `packaging=={packaging_version}`: "
            f"`licenses/packaging-{packaging_version}.txt`\n",
            encoding="utf-8",
        )
        original_resolver = module._resolve_dependency_metadata
        original_compile = module._compile_requirements_lock
        module._resolve_dependency_metadata = lambda _repo_root: {
            "surfaces": [_surface(module)],
        }

        def _unexpected_compile(*_args, **_kwargs):
            """Fail the test if manifest-only refresh reaches pip-compile."""

            raise AssertionError("requirements.lock compile should be skipped")

        module._compile_requirements_lock = _unexpected_compile
        try:
            payload = module.refresh_all(
                repo_root,
                payload={"changed_dependency_files": ["pyproject.toml"]},
            )
        finally:
            module._resolve_dependency_metadata = original_resolver
            module._compile_requirements_lock = original_compile

        results = payload["lock_results"]
        assert results == [
            {
                "lock_file": "requirements.lock",
                "changed": False,
                "attempted": False,
                "message": "Skipped: no direct lock inputs changed.",
            }
        ]
        report = (licenses_dir / "THIRD_PARTY_LICENSES.md").read_text(
            encoding="utf-8"
        )
        assert "- `pyproject.toml`" in report


def _unit_test_refresh_runtime_ignores_environment_option_lines() -> None:
    """Environment-specific pip option lines should not count as lock drift."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            f"packaging=={packaging_version}\n",
            encoding="utf-8",
        )
        original_compile = module._compile_requirements_lock

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return one lock result with a private index option line."""

            return module.LockFilePieces(
                [
                    "--index-url https://mirror.example/simple",
                    f"packaging=={packaging_version}",
                ]
            )

        module._compile_requirements_lock = _fake_compile
        try:
            result = module._refresh_python_requirements_lock(repo_root)
        finally:
            module._compile_requirements_lock = original_compile

        assert result.attempted is True
        assert result.changed is False
        assert (repo_root / "requirements.lock").read_text(
            encoding="utf-8"
        ) == f"packaging=={packaging_version}\n"


def _unit_test_refresh_runtime_scrubs_environment_option_lines() -> None:
    """Existing environment-specific pip option lines should be removed."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            "--trusted-host mirror.example\n"
            f"packaging=={packaging_version}\n",
            encoding="utf-8",
        )
        original_compile = module._compile_requirements_lock

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return one preserved direct-conditional lock payload."""

            return module.LockFilePieces(
                module._preserve_direct_conditional_requirements(
                    [f"packaging=={packaging_version}"],
                    _requirements_in,
                )
            )

        module._compile_requirements_lock = _fake_compile
        try:
            result = module._refresh_python_requirements_lock(repo_root)
        finally:
            module._compile_requirements_lock = original_compile

        assert result.attempted is True
        assert result.changed is True
        assert result.message == (
            "Normalized requirements.lock by removing "
            "environment-specific pip option lines."
        )
        assert (repo_root / "requirements.lock").read_text(
            encoding="utf-8"
        ) == f"packaging=={packaging_version}\n"


def _unit_test_refresh_runtime_preserves_direct_conditional_requirements() -> (
    None
):
    """Direct exact conditional requirements should survive refresh."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        packaging_version = importlib_metadata.version("packaging")
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n" 'tomli==2.3.0; python_version < "3.11"\n',
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            f"packaging=={packaging_version}\n\n"
            'tomli==2.3.0 ; python_version < "3.11"\n'
            "    # via -r requirements.in\n",
            encoding="utf-8",
        )
        original_compile = module._compile_requirements_lock

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return one direct-conditional lock payload for refresh."""

            return module.LockFilePieces(
                module._preserve_direct_conditional_requirements(
                    [f"packaging=={packaging_version}"],
                    _requirements_in,
                )
            )

        module._compile_requirements_lock = _fake_compile
        try:
            result = module._refresh_python_requirements_lock(repo_root)
        finally:
            module._compile_requirements_lock = original_compile

        assert result.attempted is True
        assert result.changed is False
        assert (repo_root / "requirements.lock").read_text(
            encoding="utf-8"
        ) == (
            f"packaging=={packaging_version}\n\n"
            'tomli==2.3.0 ; python_version < "3.11"\n'
            "    # via -r requirements.in\n"
        )


def _unit_test_run_pip_compile_uses_private_cache_dir() -> None:
    """pip-compile should not inherit an unwritable user cache path."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        output_path = repo_root / "requirements.lock"
        requirements_in = repo_root / "requirements.in"
        requirements_in.write_text("packaging>=26.0\n", encoding="utf-8")
        captured: dict[str, object] = {}

        def _fake_run(command, **kwargs):
            """Capture subprocess env without executing pip-tools."""

            del command
            captured["env"] = dict(kwargs.get("env") or {})

            class _Result:
                """Minimal subprocess result stub for the captured call."""

                returncode = 0

            return _Result()

        with patch.dict(
            module.os.environ,
            {"PIP_TOOLS_CACHE_DIR": "/__devcov__/pip-tools-cache"},
            clear=False,
        ):
            with patch.object(
                module.importlib.util,
                "find_spec",
                return_value=object(),
            ):
                with patch.object(
                    module.subprocess, "run", side_effect=_fake_run
                ):
                    module._run_pip_compile(
                        repo_root,
                        requirements_in,
                        output_path,
                    )

        env = captured["env"]
        assert isinstance(env, dict)
        assert env["PIP_TOOLS_CACHE_DIR"]
        assert env["PIP_TOOLS_CACHE_DIR"] != "/__devcov__/pip-tools-cache"


def _unit_test_run_pip_compile_adds_generate_hashes_when_enabled() -> None:
    """Hash mode should forward `--generate-hashes` to pip-compile."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        output_path = repo_root / "requirements.lock"
        requirements_in = repo_root / "requirements.in"
        requirements_in.write_text("packaging>=26.0\n", encoding="utf-8")
        captured: dict[str, object] = {}

        def _fake_run(command, **kwargs):
            """Capture the pip-compile argv without executing it."""

            captured["command"] = list(command)
            captured["env"] = dict(kwargs.get("env") or {})

            class _Result:
                """Minimal subprocess result stub for the captured call."""

                returncode = 0

            return _Result()

        with patch.object(
            module.importlib.util,
            "find_spec",
            return_value=object(),
        ):
            with patch.object(module.subprocess, "run", side_effect=_fake_run):
                module._run_pip_compile(
                    repo_root,
                    requirements_in,
                    output_path,
                    generate_hashes=True,
                )

        command = captured["command"]
        assert isinstance(command, list)
        assert "--generate-hashes" in command


def _unit_test_hash_mode_semantics_include_hash_lines() -> None:
    """Hash mode should treat different hash sets as real lock drift."""

    module = importlib.import_module(MODULE)
    first = [
        "packaging==26.0 \\",
        "    --hash=sha256:aaa \\",
        "    --hash=sha256:bbb",
        "    # via -r requirements.in",
    ]
    second = [
        "packaging==26.0 \\",
        "    --hash=sha256:aaa \\",
        "    --hash=sha256:ccc",
        "    # via -r requirements.in",
    ]

    assert module._normalize_python_lock_semantics_for_mode(
        first,
        generate_hashes=True,
    ) != module._normalize_python_lock_semantics_for_mode(
        second,
        generate_hashes=True,
    )


def _unit_test_input_reference_comments_scrub_nested_tmp_paths() -> None:
    """Nested input-reference comments should use the configured label."""

    module = importlib.import_module(MODULE)
    normalized = module._normalise_input_reference_comments(
        [
            "packaging==26.0",
            "    # via",
            "    #   -r /tmp/runtime-requirements.in",
            "    #   build",
            "pre-commit==4.5.1",
            "    # via -r /tmp/runtime-requirements.in",
        ],
        input_name="pyproject.toml",
    )

    assert normalized == [
        "packaging==26.0",
        "    # via",
        "    #   -r pyproject.toml",
        "    #   build",
        "pre-commit==4.5.1",
        "    # via -r pyproject.toml",
    ]


def _unit_test_refresh_runtime_rewrites_normalized_comment_only_drift() -> (
    None
):
    """Comment-only normalization should still rewrite the lock file."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "requirements.in").write_text(
            "packaging>=26.0\n",
            encoding="utf-8",
        )
        (repo_root / "requirements.lock").write_text(
            "packaging==26.0\n"
            "    # via\n"
            "    #   -r /tmp/runtime-requirements.in\n"
            "    #   build\n",
            encoding="utf-8",
        )
        original_compile = module._compile_requirements_lock

        def _fake_compile(_repo_root, _requirements_in, **_kwargs):
            """Return the normalized comment form for the same resolved pin."""

            return module.LockFilePieces(
                [
                    "packaging==26.0",
                    "    # via",
                    "    #   -r requirements.in",
                    "    #   build",
                ]
            )

        module._compile_requirements_lock = _fake_compile
        try:
            result = module._refresh_python_requirements_lock(repo_root)
        finally:
            module._compile_requirements_lock = original_compile

        assert result.attempted is True
        assert result.changed is True
        assert result.message == (
            "Normalized requirements.lock without changing resolved pins."
        )
        assert (repo_root / "requirements.lock").read_text(
            encoding="utf-8"
        ) == (
            "packaging==26.0\n"
            "    # via\n"
            "    #   -r requirements.in\n"
            "    #   build\n"
        )


def _unit_test_refresh_runtime_passes_hash_mode_from_metadata() -> None:
    """Metadata-selected hash mode should reach the Python lock refresher."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        licenses_dir = repo_root / "licenses"
        licenses_dir.mkdir(parents=True, exist_ok=True)
        captured: dict[str, object] = {}
        original_resolver = module._resolve_dependency_metadata
        original_refresh = module._refresh_python_surface_lock
        original_license_refresh = (
            module.dependency_management.refresh_license_artifacts
        )
        module._resolve_dependency_metadata = lambda _repo_root: {
            "surfaces": [
                _surface(
                    module,
                    generate_hashes=True,
                    hash_targets=[
                        module.dependency_management.DependencySurfaceTarget(
                            target_id="linux-py311",
                            marker=(
                                'sys_platform == "linux" and '
                                'python_version == "3.11"'
                            ),
                            pip={
                                "platform": "manylinux2014_x86_64",
                                "implementation": "cp",
                                "python-version": "3.11",
                                "abi": "cp311",
                            },
                        )
                    ],
                )
            ],
        }

        def _fake_refresh(_repo_root, *, surface):
            """Capture the selected hash mode from refresh_all."""

            captured["generate_hashes"] = surface.generate_hashes
            return module.LockHandlerResult(
                "requirements.lock",
                changed=False,
                attempted=True,
                message="No change.",
            )

        module._refresh_python_surface_lock = _fake_refresh
        module.dependency_management.refresh_license_artifacts = (
            lambda *_args, **_kwargs: []
        )
        try:
            payload = module.refresh_all(repo_root)
        finally:
            module._resolve_dependency_metadata = original_resolver
            module._refresh_python_surface_lock = original_refresh
            module.dependency_management.refresh_license_artifacts = (
                original_license_refresh
            )

        assert payload["lock_results"]
        assert captured["generate_hashes"] is True


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_runtime_resolves_structured_surfaces_from_repo_metadata(self):
        """Run structured surface-resolution regression assertions."""
        _unit_test_runtime_resolves_structured_surfaces_from_repo_metadata()

    def test_runtime_symbol_contract_is_stable(self):
        """Run dependency lock runtime symbol contract assertions."""
        _unit_test_runtime_symbol_contract_is_stable()

    def test_refresh_runtime_updates_inventory_even_without_lock_change(self):
        """Run no-lock-change inventory repair assertions."""
        _unit_test_refresh_runtime_updates_inventory_without_lock_change()

    def test_refresh_runtime_preserves_changed_manifest_references(self):
        """Run changed-manifest reference preservation assertions."""
        _unit_test_refresh_runtime_preserves_changed_manifest_references()

    def test_refresh_runtime_skips_compile_for_manifest_only(self):
        """Run manifest-only lock-refresh skip assertions."""
        (_unit_test_refresh_runtime_skips_compile_for_manifest_only())

    def test_refresh_runtime_ignores_environment_option_lines(self):
        """Run environment-specific option-line drift assertions."""
        _unit_test_refresh_runtime_ignores_environment_option_lines()

    def test_refresh_runtime_scrubs_environment_option_lines(self):
        """Run environment-specific option-line cleanup assertions."""
        _unit_test_refresh_runtime_scrubs_environment_option_lines()

    def test_refresh_runtime_preserves_direct_conditional_requirements(self):
        """Run direct exact conditional requirement preservation assertions."""
        _unit_test_refresh_runtime_preserves_direct_conditional_requirements()

    def test_run_pip_compile_uses_private_cache_dir(self):
        """Run pip-tools cache-dir isolation assertions."""
        _unit_test_run_pip_compile_uses_private_cache_dir()

    def test_run_pip_compile_adds_generate_hashes_when_enabled(self):
        """Run pip-compile hash-mode argv assertions."""
        _unit_test_run_pip_compile_adds_generate_hashes_when_enabled()

    def test_hash_mode_semantics_include_hash_lines(self):
        """Run hash-aware lock semantics assertions."""
        _unit_test_hash_mode_semantics_include_hash_lines()

    def test_input_reference_comments_scrub_nested_tmp_paths(self):
        """Run nested input-reference comment normalization assertions."""
        _unit_test_input_reference_comments_scrub_nested_tmp_paths()

    def test_refresh_runtime_rewrites_normalized_comment_only_drift(self):
        """Run comment-only normalized lock rewrite assertions."""
        _unit_test_refresh_runtime_rewrites_normalized_comment_only_drift()

    def test_refresh_runtime_passes_hash_mode_from_metadata(self):
        """Run metadata-to-runtime hash-mode propagation assertions."""
        _unit_test_refresh_runtime_passes_hash_mode_from_metadata()
