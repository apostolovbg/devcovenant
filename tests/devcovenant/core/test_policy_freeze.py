"""Unit tests for devcovenant.core.policy_freeze and replacements."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install, upgrade
from devcovenant.core import parser, policy_freeze


def _policy_definition(
    policy_id: str,
    freeze: bool,
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


def _write_replacements(repo_root: Path) -> None:
    """Write replacement metadata to registry/global."""
    path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "global"
        / "policy_replacements.yaml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "replacements": {
            "old-policy": {"replaced_by": "new-policy"},
        }
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _write_agents(repo_root: Path) -> None:
    """Write AGENTS with one policy block for replacement testing."""
    agents = repo_root / "AGENTS.md"
    agents.write_text(
        "# AGENTS\n\n"
        "<!-- DEVCOV-POLICIES:BEGIN -->\n"
        "## Policy: Old Policy\n\n"
        "```policy-def\n"
        "id: old-policy\n"
        "status: active\n"
        "custom: false\n"
        "enabled: true\n"
        "```\n\n"
        "Old text.\n"
        "<!-- DEVCOV-POLICIES:END -->\n",
        encoding="utf-8",
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_copy_and_remove_freeze_override(self):
        """Freeze should copy override tree, then unfreeze should remove it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            core_dir = (
                repo_root
                / "devcovenant"
                / "core"
                / "policies"
                / "freeze_example"
            )
            core_dir.mkdir(parents=True, exist_ok=True)
            script_file = core_dir / "freeze_example.py"
            script_file.write_text("print('freeze')")
            fixer_dir = core_dir / "fixers"
            fixer_dir.mkdir()
            (fixer_dir / "global.py").write_text("# fixer")

            freeze_policy = _policy_definition("freeze-example", True)
            changed, messages = policy_freeze.apply_policy_freeze(
                repo_root,
                [freeze_policy],
            )
            custom_dir = (
                repo_root
                / "devcovenant"
                / "custom"
                / "policies"
                / "freeze_example"
            )
            self.assertTrue(changed)
            self.assertTrue(messages)
            self.assertTrue(custom_dir.exists())
            self.assertEqual(
                (custom_dir / "freeze_example.py").read_text(),
                "print('freeze')",
            )
            self.assertTrue((custom_dir / "fixers" / "global.py").exists())

            unfrozen_policy = _policy_definition("freeze-example", False)
            removed, removal_messages = policy_freeze.apply_policy_freeze(
                repo_root,
                [unfrozen_policy],
            )
            self.assertTrue(removed)
            self.assertTrue(removal_messages)
            self.assertFalse(custom_dir.exists())

    def test_load_policy_replacements_reads_mapping(self):
        """Replacement loader should parse registry/global mapping payloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "devcovenant").mkdir(parents=True, exist_ok=True)
            _write_replacements(repo_root)

            loaded = policy_freeze.load_policy_replacements(repo_root)
            self.assertIn("old-policy", loaded)
            self.assertEqual(
                loaded["old-policy"].replaced_by,
                "new-policy",
            )

    def test_apply_replacements_marks_policy_deprecated_custom(self):
        """Upgrade replacement pass should rewrite AGENTS policy metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            _write_replacements(repo_root)
            _write_agents(repo_root)

            replaced = upgrade._apply_policy_replacements(repo_root)
            self.assertEqual(replaced, ["old-policy"])

            updated_agents = (repo_root / "AGENTS.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("status: deprecated", updated_agents)
            self.assertIn("custom: true", updated_agents)
