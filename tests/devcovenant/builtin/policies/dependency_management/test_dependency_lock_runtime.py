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


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


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
            "resolved_dependency_files": ["requirements.lock"],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
        module._compile_requirements_lock = (
            lambda _repo_root, _requirements_in: module.LockFilePieces(
                [f"packaging=={packaging_version}"]
            )
        )
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
            "resolved_dependency_files": ["requirements.lock"],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
        module._compile_requirements_lock = (
            lambda _repo_root, _requirements_in: module.LockFilePieces(
                [f"packaging=={packaging_version}"]
            )
        )
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
            "resolved_dependency_files": ["requirements.lock"],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
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
        module._compile_requirements_lock = (
            lambda _repo_root, _requirements_in: module.LockFilePieces(
                [
                    "--index-url https://mirror.example/simple",
                    f"packaging=={packaging_version}",
                ]
            )
        )
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
        module._compile_requirements_lock = (
            lambda _repo_root, _requirements_in: module.LockFilePieces(
                module._preserve_exact_marker_pins(
                    [f"packaging=={packaging_version}"],
                    _requirements_in,
                )
            )
        )
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


def _unit_test_refresh_runtime_preserves_exact_marker_pins() -> None:
    """Exact conditional pins should survive refresh on newer interpreters."""

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
        module._compile_requirements_lock = (
            lambda _repo_root, _requirements_in: module.LockFilePieces(
                module._preserve_exact_marker_pins(
                    [f"packaging=={packaging_version}"],
                    _requirements_in,
                )
            )
        )
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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

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

    def test_refresh_runtime_preserves_exact_marker_pins(self):
        """Run exact conditional backport pin preservation assertions."""
        _unit_test_refresh_runtime_preserves_exact_marker_pins()

    def test_run_pip_compile_uses_private_cache_dir(self):
        """Run pip-tools cache-dir isolation assertions."""
        _unit_test_run_pip_compile_uses_private_cache_dir()
