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
        source = repo_root / "LICENSE"
        target = repo_root / "devcovenant" / "licenses" / "LICENSE"
        source.write_text("root license\n", encoding="utf-8")

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
        assert target.read_text(encoding="utf-8") == "root license\n"


def _unit_test_fixer_symbol_contract_is_stable() -> None:
    """Fixer symbol contract should stay explicit and importable."""
    assert PackageArtifactMirrorFixer.__name__ == "PackageArtifactMirrorFixer"
    assert hasattr(PackageArtifactMirrorFixer, "fix")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_syncs_file_mirror(self):
        """Run test_syncs_file_mirror."""
        _unit_test_syncs_file_mirror()

    def test_fixer_symbol_contract_is_stable(self):
        """Run test_fixer_symbol_contract_is_stable."""
        _unit_test_fixer_symbol_contract_is_stable()
