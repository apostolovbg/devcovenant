"""Unit tests for devcovenant.core.policy_descriptor helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core import policy_descriptor


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for descriptor helpers."""

    def test_loads_changelog_descriptor(self):
        """Descriptor loader should return changelog-coverage metadata."""
        repo_root = Path(__file__).resolve().parents[3]
        descriptor = policy_descriptor.load_policy_descriptor(
            repo_root,
            "changelog-coverage",
        )

        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor.policy_id, "changelog-coverage")
        self.assertEqual(
            descriptor.metadata.get("severity"),
            "error",
        )
        self.assertEqual(
            descriptor.metadata.get("main_changelog"),
            ["CHANGELOG.md"],
        )

    def test_descriptors_do_not_define_activation_scope_keys(self):
        """Descriptors should not expose retired scope metadata keys."""
        repo_root = Path(__file__).resolve().parents[3]
        forbidden = {"profile_scopes", "policy_scopes"}

        for policy_root in (
            repo_root / "devcovenant" / "core" / "policies",
            repo_root / "devcovenant" / "custom" / "policies",
        ):
            for policy_dir in policy_root.iterdir():
                if not policy_dir.is_dir() or policy_dir.name.startswith("_"):
                    continue
                descriptor_path = policy_dir / f"{policy_dir.name}.yaml"
                payload = yaml.safe_load(
                    descriptor_path.read_text(encoding="utf-8")
                )
                metadata = payload.get("metadata", {})
                present = forbidden.intersection(metadata.keys())
                self.assertFalse(
                    present,
                    (
                        f"{descriptor_path} contains retired scope keys: "
                        f"{sorted(present)}"
                    ),
                )

    def test_parse_metadata_block_reads_order_and_multiline_values(self):
        """Metadata parsing should preserve key order and folded entries."""
        block = (
            "id: sample\n"
            "severity: error\n"
            "required_files:\n"
            "  README.md\n"
            "  PLAN.md\n"
        )
        order, values = policy_descriptor.parse_metadata_block(block)
        self.assertEqual(order, ["id", "severity", "required_files"])
        self.assertEqual(values["required_files"], ["README.md", "PLAN.md"])

    def test_resolve_script_location_prefers_custom_policy(self):
        """Resolver should prefer custom policy scripts over core scripts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            custom_script = (
                repo_root
                / "devcovenant"
                / "custom"
                / "policies"
                / "sample_policy"
                / "sample_policy.py"
            )
            core_script = (
                repo_root
                / "devcovenant"
                / "core"
                / "policies"
                / "sample_policy"
                / "sample_policy.py"
            )
            custom_script.parent.mkdir(parents=True, exist_ok=True)
            core_script.parent.mkdir(parents=True, exist_ok=True)
            custom_script.write_text("# custom\n", encoding="utf-8")
            core_script.write_text("# core\n", encoding="utf-8")

            resolved = policy_descriptor.resolve_script_location(
                repo_root,
                "sample-policy",
            )

            self.assertIsNotNone(resolved)
            self.assertEqual(resolved.kind, "custom")
            self.assertEqual(resolved.path, custom_script)
