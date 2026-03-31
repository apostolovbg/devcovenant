"""Unit tests for package-artifact-mirror autofix."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.contracts.policy import Violation

PackageArtifactMirrorFixer = import_module(
    "devcovenant.custom.policies.package_artifact_mirror.autofix.global"
).PackageArtifactMirrorFixer


def _unit_test_syncs_file_mirror() -> None:
    """Fixer should copy one mirrored file from root to package."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        source = repo_root / "requirements.lock"
        target = repo_root / "devcovenant" / "requirements.lock"
        source.write_text("root lock\n", encoding="utf-8")

        fixer = PackageArtifactMirrorFixer()
        violation = Violation(
            policy_id="package-artifact-mirror",
            severity="error",
            message="sync",
            context={
                "kind": "file",
                "source_path": str(source),
                "target_path": str(target),
            },
        )

        result = fixer.fix(violation)

        assert result.success is True
        assert target.read_text(encoding="utf-8") == "root lock\n"


def _unit_test_syncs_dir_mirror_and_prunes_extra_files() -> None:
    """Fixer should rewrite one mirrored directory from the source tree."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        source = repo_root / "licenses"
        target = repo_root / "devcovenant" / "licenses"
        source.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        (source / "THIRD_PARTY_LICENSES.md").write_text(
            "fresh\n", encoding="utf-8"
        )
        (target / "LICENSE").write_text("root license\n", encoding="utf-8")
        (target / "THIRD_PARTY_LICENSES.md").write_text(
            "stale\n", encoding="utf-8"
        )
        (target / "EXTRA.txt").write_text("extra\n", encoding="utf-8")

        fixer = PackageArtifactMirrorFixer()
        violation = Violation(
            policy_id="package-artifact-mirror",
            severity="error",
            message="sync",
            context={
                "kind": "dir",
                "source_path": str(source),
                "target_path": str(target),
                "preserved_paths": ["LICENSE"],
            },
        )

        result = fixer.fix(violation)

        assert result.success is True
        assert (target / "THIRD_PARTY_LICENSES.md").read_text(
            encoding="utf-8"
        ) == "fresh\n"
        assert (target / "LICENSE").read_text(encoding="utf-8") == (
            "root license\n"
        )
        assert not (target / "EXTRA.txt").exists()


def _unit_test_fixer_symbol_contract_is_stable() -> None:
    """Fixer symbol contract should stay explicit and importable."""
    assert PackageArtifactMirrorFixer.__name__ == "PackageArtifactMirrorFixer"
    assert hasattr(PackageArtifactMirrorFixer, "fix")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_syncs_file_mirror(self):
        """Run test_syncs_file_mirror."""
        _unit_test_syncs_file_mirror()

    def test_syncs_dir_mirror_and_prunes_extra_files(self):
        """Run test_syncs_dir_mirror_and_prunes_extra_files."""
        _unit_test_syncs_dir_mirror_and_prunes_extra_files()

    def test_fixer_symbol_contract_is_stable(self):
        """Run test_fixer_symbol_contract_is_stable."""
        _unit_test_fixer_symbol_contract_is_stable()
