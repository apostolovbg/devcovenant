"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import importlib.metadata as importlib_metadata
import tempfile
import unittest
from pathlib import Path

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
    assert hasattr(module, "refresh_locks_and_licenses")


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
        module._resolve_dependency_metadata = lambda _repo_root: {
            "resolved_dependency_files": ["requirements.lock"],
            "third_party_file": "licenses/THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        }
        try:
            results, modified = module.refresh_locks_and_licenses(repo_root)
        finally:
            module._resolve_dependency_metadata = original_resolver

        assert results
        assert results[0].changed is False
        assert any(
            path.name == f"packaging-{packaging_version}.txt"
            for path in modified
        )
        assert not (licenses_dir / "packaging-0.0.1.txt").exists()
        report = (licenses_dir / "THIRD_PARTY_LICENSES.md").read_text(
            encoding="utf-8"
        )
        assert f"`packaging=={packaging_version}`" in report


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
