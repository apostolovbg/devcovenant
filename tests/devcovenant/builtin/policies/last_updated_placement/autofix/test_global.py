"""Unit tests for last-updated-placement global fixer."""

from __future__ import annotations

import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from devcovenant.core.contracts.policy import Violation

LastUpdatedPlacementFixer = import_module(
    "devcovenant.builtin.policies.last_updated_placement.autofix.global"
).LastUpdatedPlacementFixer


def _unit_test_can_fix_rejects_yaml_targets() -> None:
    """Fixer should refuse YAML paths and accept markdown paths."""
    fixer = LastUpdatedPlacementFixer()

    yaml_violation = Violation(
        policy_id="last-updated-placement",
        severity="error",
        message="yaml",
        file_path=Path("config.yaml"),
    )
    assert fixer.can_fix(yaml_violation) is False

    md_violation = Violation(
        policy_id="last-updated-placement",
        severity="error",
        message="doc",
        file_path=Path("README.md"),
    )
    assert fixer.can_fix(md_violation) is True


def _unit_test_fix_inserts_last_updated_marker() -> None:
    """Fixer should insert Last Updated marker near the top."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "README.md"
        target.write_text("# Title\n\nBody\n", encoding="utf-8")

        fixer = LastUpdatedPlacementFixer()
        violation = Violation(
            policy_id="last-updated-placement",
            severity="error",
            message="missing marker",
            file_path=target,
        )
        result = fixer.fix(violation)

        assert result.success is True
        content = target.read_text(encoding="utf-8")
        assert "**Last Updated:**" in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_can_fix_rejects_yaml_targets(self):
        """Run test_can_fix_rejects_yaml_targets."""
        _unit_test_can_fix_rejects_yaml_targets()

    def test_fix_inserts_last_updated_marker(self):
        """Run test_fix_inserts_last_updated_marker."""
        _unit_test_fix_inserts_last_updated_marker()
