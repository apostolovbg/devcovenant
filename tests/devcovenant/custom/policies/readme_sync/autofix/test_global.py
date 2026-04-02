"""Unit tests for readme-sync global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.policy_contract import Violation

ReadmeSyncFixer = import_module(
    "devcovenant.custom.policies.readme_sync.autofix.global"
).ReadmeSyncFixer


def _unit_test_syncs_expected_text_to_target() -> None:
    """Fixer should write expected content to the target README."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        target = repo_root / "devcovenant" / "README.md"

        fixer = ReadmeSyncFixer()
        violation = Violation(
            policy_id="readme-sync",
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
        """Readme-sync tests should assert the fixer symbol."""
        self.assertIsNotNone(ReadmeSyncFixer)
