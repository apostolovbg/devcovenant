"""Tests for the policy freeze helper."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core import parser, policy_freeze


def _policy_definition(
    policy_id: str, freeze: bool
) -> parser.PolicyDefinition:
    """Return a basic policy definition for freeze tests."""
    return parser.PolicyDefinition(
        policy_id=policy_id,
        name="Example",
        status="active",
        severity="warning",
        auto_fix=False,
        enabled=True,
        custom=False,
        description="Example policy",
        freeze=freeze,
    )


def _unit_test_copy_and_remove_freeze_override(tmp_path: Path) -> None:
    """Freeze copies the core policy tree and unfreeze removes it."""
    repo_root = tmp_path / "repo"
    core_dir = (
        repo_root / "devcovenant" / "core" / "policies" / "freeze_example"
    )
    core_dir.mkdir(parents=True, exist_ok=True)
    script_file = core_dir / "freeze_example.py"
    script_file.write_text("print('freeze')")
    fixer_dir = core_dir / "fixers"
    fixer_dir.mkdir()
    (fixer_dir / "global.py").write_text("# fixer")

    freeze_policy = _policy_definition("freeze-example", True)
    changed, messages = policy_freeze.apply_policy_freeze(
        repo_root, [freeze_policy]
    )
    custom_dir = (
        repo_root / "devcovenant" / "custom" / "policies" / "freeze_example"
    )
    assert changed is True
    assert messages
    assert custom_dir.exists()
    assert (custom_dir / "freeze_example.py").read_text() == "print('freeze')"
    assert (custom_dir / "fixers" / "global.py").exists()

    unfrozen_policy = _policy_definition("freeze-example", False)
    removed, removal_messages = policy_freeze.apply_policy_freeze(
        repo_root, [unfrozen_policy]
    )
    assert removed is True
    assert removal_messages
    assert not custom_dir.exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_copy_and_remove_freeze_override(self):
        """Run test_copy_and_remove_freeze_override."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_copy_and_remove_freeze_override(tmp_path=tmp_path)
