"""Unit tests for package-doc-sync global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.policy_contract import Violation

PackageDocSyncFixer = import_module(
    "devcovenant.builtin.policies.package_doc_sync.autofix.global"
).PackageDocSyncFixer


def _unit_test_syncs_expected_text_to_target() -> None:
    """Fixer should write expected content to the target README."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        target = repo_root / "devcovenant" / "README.md"

        fixer = PackageDocSyncFixer()
        violation = Violation(
            policy_id="package-doc-sync",
            severity="error",
            message="sync",
            context={
                "expected_text": "# Mirror\n",
                "target_path": str(target),
            },
        )

        result = fixer.fix(violation)

        assert result.success is True
        assert target.read_text(encoding="utf-8") == "# Mirror\n"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_syncs_expected_text_to_target(self):
        """Run test_syncs_expected_text_to_target."""
        _unit_test_syncs_expected_text_to_target()


class GeneratedSymbolCoverageTests(unittest.TestCase):
    """Direct symbol assertions for coverage tracking."""

    def test_symbol_level_assertions_cover_public_api(self):
        """Package-doc-sync tests should assert the fixer symbol."""
        self.assertIsNotNone(PackageDocSyncFixer)
