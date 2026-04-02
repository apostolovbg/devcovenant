"""Unit tests for last-updated global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.policy_contract import Violation

LastUpdatedFixer = import_module(
    "devcovenant.builtin.policies.last_updated.autofix.global"
).LastUpdatedFixer


def _unit_test_can_fix_rejects_yaml_targets() -> None:
    """Fixer should refuse YAML paths and accept markdown paths."""
    fixer = LastUpdatedFixer()

    yaml_violation = Violation(
        policy_id="last-updated",
        severity="error",
        message="yaml",
        file_path=Path("config.yaml"),
    )
    assert fixer.can_fix(yaml_violation) is False

    md_violation = Violation(
        policy_id="last-updated",
        severity="error",
        message="doc",
        file_path=Path("README.md"),
    )
    assert fixer.can_fix(md_violation) is True


def _unit_test_fix_inserts_last_updated_marker() -> None:
    """Fixer should insert Last Updated marker in header zone."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "README.md"
        target.write_text("# Title\n\nBody\n", encoding="utf-8")

        fixer = LastUpdatedFixer()
        violation = Violation(
            policy_id="last-updated",
            severity="error",
            message="missing marker",
            file_path=target,
        )
        result = fixer.fix(violation)

        assert result.success is True
        content = target.read_text(encoding="utf-8")
        assert "**Last Updated:**" in content


def _unit_test_fixer_symbol_contract_is_stable() -> None:
    """Fixer symbol contract should stay explicit and importable."""
    assert LastUpdatedFixer.__name__ == "LastUpdatedFixer"
    assert hasattr(LastUpdatedFixer, "fix")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_can_fix_rejects_yaml_targets(self):
        """Run test_can_fix_rejects_yaml_targets."""
        _unit_test_can_fix_rejects_yaml_targets()

    def test_fix_inserts_last_updated_marker(self):
        """Run test_fix_inserts_last_updated_marker."""
        _unit_test_fix_inserts_last_updated_marker()

    def test_fixer_symbol_contract_is_stable(self):
        """Run test_fixer_symbol_contract_is_stable."""
        _unit_test_fixer_symbol_contract_is_stable()
