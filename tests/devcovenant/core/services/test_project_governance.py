"""Unit tests for the project-governance runtime service."""

from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core.services import project_governance

ProjectGovernanceState = project_governance.ProjectGovernanceState
render_identity_placeholders = project_governance.render_identity_placeholders
resolve_release_headings = project_governance.resolve_release_headings
resolve_runtime_state = project_governance.resolve_runtime_state
validate_changelog_contract = project_governance.validate_changelog_contract


def _write_project_governance_config(
    repo_root: Path,
    **updates: object,
) -> None:
    """Update the top-level project-governance config block."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    block = payload.setdefault("project-governance", {})
    if not isinstance(block, dict):
        block = {}
        payload["project-governance"] = block
    block.update(updates)
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for project-governance service behavior."""

    def test_runtime_state_defaults_to_unversioned_governance(self):
        """Fresh installs should default to explicit unversioned governance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            state = resolve_runtime_state(repo_root)
            self.assertTrue(state.enabled)
            self.assertTrue(state.is_unversioned)
            self.assertEqual(state.project_name, "Project Name")
            self.assertIn(
                "Describe the project this repository ships",
                state.project_description,
            )
            self.assertEqual(state.stage, "prototype")
            self.assertEqual(state.maintenance_stance, "active")
            self.assertEqual(state.compatibility_policy, "unspecified")
            self.assertEqual(
                state.displayed_project_version("1.2.3"), "Unversioned"
            )
            self.assertIn(
                "**Project Stage:** prototype", state.governance_header_lines()
            )

    def test_runtime_state_requires_direct_config_block(self):
        """Runtime resolution should fail when project-governance is absent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            config_path = repo_root / "devcovenant" / "config.yaml"
            payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            payload.pop("project-governance", None)
            config_path.write_text(
                yaml.safe_dump(payload, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "project-governance"):
                resolve_runtime_state(repo_root)

    def test_unversioned_release_headings_require_unreleased_heading(self):
        """Unversioned repos should enforce the configured heading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            changelog = repo_root / "CHANGELOG.md"
            changelog.write_text(
                "# Changelog\n\n## Log changes here\n\n## Version 1.0.0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "top changelog heading"):
                validate_changelog_contract(repo_root)

    def test_release_heading_resolution_uses_unreleased_heading(self):
        """Release headings should follow the resolved changelog contract."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            changelog = repo_root / "CHANGELOG.md"
            changelog.write_text(
                "# Changelog\n\n## Log changes here\n\n## Unreleased\n",
                encoding="utf-8",
            )
            self.assertEqual(
                resolve_release_headings(repo_root), ["## Unreleased"]
            )

    def test_versioned_runtime_state_requires_declared_version(self):
        """Versioned repos should reject fake fallback versions."""
        state = ProjectGovernanceState(versioning_mode="versioned")
        with self.assertRaisesRegex(
            ValueError, "missing a declared project version"
        ):
            state.displayed_project_version("")

    def test_service_registry_payload_is_deterministic(self):
        """Registry payload should surface the resolved governance state."""
        state = ProjectGovernanceState(
            project_name="DevCovenant",
            project_description=(
                "DevCovenant is a Repository Governance Framework."
            ),
            stage="stable",
            maintenance_stance="active",
            compatibility_policy="breaking-allowed",
            versioning_mode="versioned",
            codename="Atlas",
            build_identity="2026.03.20.1",
        )
        payload = state.registry_payload("1.2.3")
        self.assertEqual(payload["project_name"], "DevCovenant")
        self.assertEqual(
            payload["project_description"],
            "DevCovenant is a Repository Governance Framework.",
        )
        self.assertEqual(payload["project_version"], "1.2.3")
        self.assertEqual(payload["stage"], "stable")
        self.assertEqual(payload["maintenance_stance"], "active")
        self.assertEqual(
            payload["compatibility_policy"],
            "breaking-allowed",
        )
        self.assertEqual(payload["versioning_mode"], "versioned")
        self.assertEqual(payload["codename"], "Atlas")
        self.assertEqual(payload["build_identity"], "2026.03.20.1")

    def test_render_identity_placeholders_wraps_project_description(self):
        """Wrapped identity placeholders should preserve the full meaning."""
        state = ProjectGovernanceState(
            project_description=(
                "Describe the project this repository ships: what it does, "
                "who it helps, and what problem it solves."
            )
        )
        rendered = render_identity_placeholders(
            "{{ PROJECT_DESCRIPTION_PARAGRAPH }}",
            state,
        )
        self.assertIn("\n", rendered)
        self.assertEqual(
            " ".join(rendered.split()),
            state.project_description,
        )

    def test_render_identity_placeholders_formats_toml_description(self):
        """TOML placeholder rendering should preserve the description."""
        state = ProjectGovernanceState(
            project_description=(
                "Describe the project this repository ships: what it does, "
                "who it helps, and what problem it solves."
            )
        )
        rendered = render_identity_placeholders(
            "description = {{ PROJECT_DESCRIPTION_TOML }}\n",
            state,
        )
        self.assertGreaterEqual(rendered.count("\n"), 2)
        self.assertEqual(
            tomllib.loads(rendered)["description"],
            state.project_description,
        )
