"""Unit tests for the managed-doc runtime service."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import yaml

import devcovenant.core.managed_docs as managed_docs
import devcovenant.core.project_governance as project_governance
from devcovenant import install
from tests import current_devcovenant_version, current_project_version

CURRENT_PROJECT_VERSION = current_project_version()
CURRENT_DEVCOVENANT_VERSION = current_devcovenant_version()


def _read_yaml(path: Path) -> dict[str, object]:
    """Load a YAML mapping payload from disk."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_demo_profile_descriptor(
    repo_root: Path,
    *,
    doc_name: str,
    title: str,
    doc_id: str,
) -> None:
    """Create one minimal custom managed-doc descriptor."""
    profile_root = (
        repo_root / "devcovenant" / "custom" / "profiles" / "mapsdemo"
    )
    assets_root = profile_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    (profile_root / "mapsdemo.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "profile": "mapsdemo",
                "category": "repo",
                "suffixes": [],
                "ignore_dirs": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    descriptor_path = assets_root / f"{Path(doc_name).stem}.yaml"
    descriptor_path.write_text(
        "\n".join(
            [
                f"title: {title}",
                f"target_path: {doc_name}",
                f"doc_id: {doc_id}",
                "doc_type: reference-map",
                "project_version: true",
                "last_updated: true",
                "devcovenant_version: true",
                "project_governance_headers: false",
                "import_seed: true",
                "authoritative_source: true",
                "managed_block: |-",
                "  This opening section is managed by DevCovenant.",
                (
                    "  Use `"
                    + doc_name
                    + "` for custom profile inventory below this block."
                ),
                "body: |-",
                "  ## Table of Contents",
                "  1. [Overview](#overview)",
                "",
                "  ## Overview",
                f"  Default body for {doc_name}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _configure_demo_profile(
    repo_root: Path,
    *,
    autogen: list[str],
) -> dict[str, object]:
    """Enable one temp custom profile and return the saved config payload."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = _read_yaml(config_path)
    profiles_block = payload.setdefault("profiles", {})
    assert isinstance(profiles_block, dict)
    profiles_block["active"] = ["mapsdemo"]
    doc_assets = payload.setdefault("doc_assets", {})
    assert isinstance(doc_assets, dict)
    doc_assets["autogen"] = autogen
    doc_assets["user"] = []
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return payload


class ManagedDocsTests(unittest.TestCase):
    """Direct coverage for the managed-doc runtime service."""

    def test_validate_descriptor_rejects_unknown_keys(self) -> None:
        """Managed-doc schema should fail explicit unknown descriptor keys."""
        descriptor = {
            "title": "README",
            "target_path": "README.md",
            "doc_id": "README",
            "doc_type": "repo-readme",
            "project_version": True,
            "last_updated": True,
            "devcovenant_version": True,
            "managed_block": "Block text.",
            "body": "Body text.",
            "unexpected_key": True,
        }
        raw_yaml = "\n".join(
            [
                "title: README",
                "target_path: README.md",
                "doc_id: README",
                "doc_type: repo-readme",
                "project_version: true",
                "last_updated: true",
                "devcovenant_version: true",
                "managed_block: |-",
                "  Block text.",
                "body: |-",
                "  Body text.",
                "unexpected_key: true",
                "",
            ]
        )

        with self.assertRaisesRegex(ValueError, "unsupported keys"):
            managed_docs.validate_managed_doc_descriptor(
                descriptor,
                descriptor_path_value=Path("README.yaml"),
                doc_name="README.md",
                raw_yaml=raw_yaml,
            )

    def test_validate_descriptor_requires_documented_key_order(self) -> None:
        """Managed-doc schema should fail for reordered descriptor keys."""
        descriptor = {
            "title": "README",
            "target_path": "README.md",
            "doc_id": "README",
            "doc_type": "repo-readme",
            "project_version": True,
            "last_updated": True,
            "devcovenant_version": True,
            "managed_block": "Block text.",
            "import_seed": True,
            "body": "Body text.",
        }
        raw_yaml = "\n".join(
            [
                "title: README",
                "target_path: README.md",
                "doc_id: README",
                "doc_type: repo-readme",
                "project_version: true",
                "last_updated: true",
                "devcovenant_version: true",
                "managed_block: |-",
                "  Block text.",
                "import_seed: true",
                "body: |-",
                "  Body text.",
                "",
            ]
        )

        with self.assertRaisesRegex(
            ValueError,
            "must declare keys in this order",
        ):
            managed_docs.validate_managed_doc_descriptor(
                descriptor,
                descriptor_path_value=Path("README.yaml"),
                doc_name="README.md",
                raw_yaml=raw_yaml,
            )

    def test_validate_descriptor_allows_license_without_tool_version(
        self,
    ) -> None:
        """License descriptors may omit the DevCovenant version header."""
        descriptor = {
            "title": "{{ PROJECT_NAME }} {{ PROJECT_VERSION }}",
            "target_path": "LICENSE",
            "doc_id": "LICENSE",
            "doc_type": "license",
            "project_version": False,
            "last_updated": False,
            "devcovenant_version": False,
            "managed_block": "",
            "body": "Permission text.\n",
        }
        raw_yaml = "\n".join(
            [
                'title: "{{ PROJECT_NAME }} {{ PROJECT_VERSION }}"',
                "target_path: LICENSE",
                "doc_id: LICENSE",
                "doc_type: license",
                "project_version: false",
                "last_updated: false",
                "devcovenant_version: false",
                "managed_block: ''",
                "body: |-",
                "  Permission text.",
                "",
            ]
        )

        managed_docs.validate_managed_doc_descriptor(
            descriptor,
            descriptor_path_value=Path("LICENSE.yaml"),
            doc_name="LICENSE",
            raw_yaml=raw_yaml,
        )

    def test_authoritative_entries_follow_descriptor_flags(self) -> None:
        """Authoritative doc coverage should come from descriptors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)

            entries = managed_docs.authoritative_managed_doc_entries(repo_root)
            docs = {str(entry["doc"]) for entry in entries}

            self.assertIn("AGENTS.md", docs)
            self.assertIn("README.md", docs)
            self.assertNotIn("devcovenant/README.md", docs)

    def test_managed_docs_from_config_excludes_user_docs(self) -> None:
        """User-owned docs should be excluded from the managed-doc list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            config_path = repo_root / "devcovenant" / "config.yaml"
            payload = _read_yaml(config_path)
            doc_assets = payload.setdefault("doc_assets", {})
            assert isinstance(doc_assets, dict)
            doc_assets["user"] = ["README.md", "PLAN.md"]
            config_path.write_text(
                yaml.safe_dump(payload, sort_keys=False),
                encoding="utf-8",
            )

            selected = managed_docs.managed_docs_from_config(payload)

            self.assertIn("AGENTS.md", selected)
            self.assertNotIn("README.md", selected)
            self.assertNotIn("PLAN.md", selected)

    def test_detect_importable_managed_docs_accepts_same_version_seed(
        self,
    ) -> None:
        """Same-version DevCovenant-shaped docs should be importable seeds."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            spec_path = repo_root / "SPEC.md"
            spec_path.write_text(
                "# Product Spec\n"
                "**Doc ID:** SPEC\n"
                "**Doc Type:** specification\n"
                "**Project Version:** 0.1.0\n"
                f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
                "Imported spec body.\n",
                encoding="utf-8",
            )

            imported = managed_docs.detect_importable_managed_docs(
                repo_root,
                install._source_package_dir(),
            )

            self.assertIn("SPEC.md", imported)

    def test_active_custom_profile_descriptors_are_resolved(self) -> None:
        """Enabled custom managed docs should resolve via profile assets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            _write_demo_profile_descriptor(
                repo_root,
                doc_name="PROFILE_MAP.md",
                title="Profile Map",
                doc_id="PROFILE_MAP",
            )
            payload = _configure_demo_profile(
                repo_root,
                autogen=["AGENTS.md", "PROFILE_MAP.md"],
            )

            entries = managed_docs.authoritative_managed_doc_entries(
                repo_root,
                config_payload=payload,
            )
            docs = {str(entry["doc"]) for entry in entries}

            self.assertIn("AGENTS.md", docs)
            self.assertIn("PROFILE_MAP.md", docs)
            self.assertNotIn("README.md", docs)

    def test_active_profile_descriptor_overrides_global_target(self) -> None:
        """Active profile docs should override same-target global docs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            profile_root = (
                repo_root / "devcovenant" / "custom" / "profiles" / "mapsdemo"
            )
            assets_root = profile_root / "assets"
            assets_root.mkdir(parents=True, exist_ok=True)
            (profile_root / "mapsdemo.yaml").write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "profile": "mapsdemo",
                        "category": "repo",
                        "suffixes": [],
                        "ignore_dirs": [],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (assets_root / "README.yaml").write_text(
                "\n".join(
                    [
                        "title: Repo Override",
                        "target_path: README.md",
                        "doc_id: README",
                        "doc_type: repo-readme",
                        "project_version: true",
                        "last_updated: true",
                        "devcovenant_version: true",
                        "project_governance_headers: false",
                        "import_seed: true",
                        "authoritative_source: true",
                        "managed_block: ''",
                        "body: |-",
                        "  Override body.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            payload = _configure_demo_profile(
                repo_root,
                autogen=["AGENTS.md", "README.md"],
            )

            resolved = managed_docs.descriptor_path(
                repo_root,
                "README.md",
                config_payload=payload,
            )
            runtime_state = project_governance.resolve_runtime_state(repo_root)
            rendered = managed_docs.render_doc(
                repo_root,
                "README.md",
                project_version="1.0.0",
                devcovenant_version="1.0.0",
                project_governance_state=runtime_state,
                config_payload=payload,
            )

            self.assertEqual(
                resolved,
                assets_root / "README.yaml",
            )
            self.assertIn("Override body.", rendered)

    def test_render_license_doc_uses_only_synced_title_header(self) -> None:
        """License docs should render one synced title and no metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            state = project_governance.resolve_runtime_state(repo_root)
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            rendered = managed_docs.render_doc(
                repo_root,
                "LICENSE",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
            )

            self.assertTrue(
                rendered.startswith(
                    f"# {state.project_name} {project_version}\n"
                )
            )
            self.assertNotIn("**Doc ID:**", rendered)
            self.assertNotIn("**Doc Type:**", rendered)
            self.assertNotIn("**Project Version:**", rendered)
            self.assertNotIn("**DevCovenant Version:**", rendered)
            self.assertNotIn("<!-- DEVCOV:BEGIN -->", rendered)
            self.assertIn(
                "Copyright (c) YEAR Legal Owner Name",
                rendered,
            )
            self.assertIn("The MIT License (MIT)", rendered)
            self.assertIn("All rights reserved.", rendered)
            self.assertIn("Permission is hereby granted", rendered)

    def test_sync_doc_preserves_authored_license_body(self) -> None:
        """License sync should refresh the title line and keep the body."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            license_path = repo_root / "LICENSE"
            license_path.write_text(
                "MIT License\n"
                "Project Version: 0.0.1\n\n"
                "Custom legal body.\n"
                "Second line.\n",
                encoding="utf-8",
            )

            state = project_governance.resolve_runtime_state(repo_root)
            project_version = "1.2.3"
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            changed = managed_docs.sync_doc(
                repo_root,
                "LICENSE",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = license_path.read_text(encoding="utf-8")
            self.assertTrue(changed)
            self.assertTrue(updated.startswith("# Project Name 1.2.3\n"))
            self.assertIn("Custom legal body.", updated)
            self.assertIn("Second line.", updated)
            self.assertNotIn("MIT License\n", updated)
            self.assertNotIn("Project Version:", updated)
            self.assertNotIn("<!-- DEVCOV:BEGIN -->", updated)

    def test_render_doc_uses_project_governance_identity(self) -> None:
        """Managed docs should render identity from governance state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            config_path = repo_root / "devcovenant" / "config.yaml"
            payload = _read_yaml(config_path)
            governance = payload.setdefault("project-governance", {})
            assert isinstance(governance, dict)
            governance["project_name"] = "Example Product"
            governance["project_description"] = (
                "Example Product keeps repository governance explicit."
            )
            config_path.write_text(
                yaml.safe_dump(payload, sort_keys=False),
                encoding="utf-8",
            )
            state = project_governance.resolve_runtime_state(repo_root)
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            rendered = managed_docs.render_doc(
                repo_root,
                "README.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
            )

            self.assertTrue(rendered.startswith("# Example Product\n"))
            self.assertIn(
                "Example Product keeps repository governance explicit.",
                rendered,
            )

    def test_sync_doc_uses_custom_profile_descriptor(self) -> None:
        """Custom managed docs should preserve real body content on sync."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            _write_demo_profile_descriptor(
                repo_root,
                doc_name="PROFILE_MAP.md",
                title="Profile Map",
                doc_id="PROFILE_MAP",
            )
            payload = _configure_demo_profile(
                repo_root,
                autogen=["AGENTS.md", "PROFILE_MAP.md"],
            )
            target_path = repo_root / "PROFILE_MAP.md"
            target_path.write_text(
                "# Profile Map\n\n"
                "## Purpose\n"
                "Keep this authored profile body.\n\n"
                "## Notes\n"
                "Do not replace this content.\n",
                encoding="utf-8",
            )

            state = project_governance.resolve_runtime_state(
                repo_root,
                config_payload=payload,
            )
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            changed = managed_docs.sync_doc(
                repo_root,
                "PROFILE_MAP.md",
                config_payload=payload,
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = target_path.read_text(encoding="utf-8")
            self.assertTrue(changed)
            self.assertIn("**Doc ID:** PROFILE_MAP", updated)
            self.assertIn("<!-- DEVCOV:BEGIN -->", updated)
            self.assertIn("Keep this authored profile body.", updated)
            self.assertIn("Do not replace this content.", updated)

    def test_sync_doc_preserves_non_placeholder_plan_body(self) -> None:
        """Sync should preserve a real authored PLAN body."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            plan_path = repo_root / "PLAN.md"
            plan_path.write_text(
                "# Development Plan\n"
                "**Doc ID:** PLAN\n"
                "**Doc Type:** plan\n"
                f"**Project Version:** {CURRENT_PROJECT_VERSION}\n"
                "**Last Updated:** 2026-03-01\n"
                f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
                "This is the real planning body.\n\n"
                "## Active Work\n"
                "1. [not done] Preserve authored docs.\n",
                encoding="utf-8",
            )

            state = project_governance.resolve_runtime_state(repo_root)
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            changed = managed_docs.sync_doc(
                repo_root,
                "PLAN.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = plan_path.read_text(encoding="utf-8")
            self.assertTrue(changed)
            self.assertIn("This is the real planning body.", updated)
            self.assertIn("Preserve authored docs.", updated)
            self.assertNotIn("Item placeholder.", updated)

    def test_sync_doc_ignores_last_updated_only_drift(self) -> None:
        """Sync should not rewrite docs when only Last Updated drifted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            state = project_governance.resolve_runtime_state(repo_root)
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            created = managed_docs.sync_doc(
                repo_root,
                "PLAN.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )
            self.assertTrue(created)

            plan_path = repo_root / "PLAN.md"
            current = plan_path.read_text(encoding="utf-8")
            today = date.fromisoformat(managed_docs.utc_today())
            yesterday = (today - timedelta(days=1)).isoformat()
            stale = current.replace(
                f"**Last Updated:** {today.isoformat()}",
                f"**Last Updated:** {yesterday}",
                1,
            )
            self.assertNotEqual(stale, current)
            plan_path.write_text(stale, encoding="utf-8")

            changed = managed_docs.sync_doc(
                repo_root,
                "PLAN.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = plan_path.read_text(encoding="utf-8")
            self.assertFalse(changed)
            self.assertEqual(updated, stale)

    def test_managed_docs_registry_payload_records_body_fingerprints(
        self,
    ) -> None:
        """Tracked registry payload should expose body-only fingerprints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)

            payload = managed_docs.managed_docs_registry_payload(repo_root)
            spec_entry = payload["descriptors"]["SPEC.md"]
            plan_entry = payload["descriptors"]["PLAN.md"]

            self.assertRegex(spec_entry["body_fingerprint"], r"^[0-9a-f]{64}$")
            self.assertNotIn(
                "legacy_generic_body_fingerprints",
                plan_entry,
            )
            self.assertNotIn(
                "legacy_generic_body_fingerprints",
                spec_entry,
            )

    def test_sync_doc_preserves_agents_editable_body(
        self,
    ) -> None:
        """AGENTS sync should preserve its user-owned editable body."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            agents_path = repo_root / "AGENTS.md"
            agents_path.write_text(
                "# DevCovenant Development Guide\n"
                "**Doc ID:** AGENTS\n"
                "**Doc Type:** policy-source\n"
                f"**Project Version:** {CURRENT_PROJECT_VERSION}\n"
                "**Project Stage:** stable\n"
                "**Maintenance Stance:** active\n"
                "**Compatibility Policy:** breaking-allowed\n"
                "**Versioning Mode:** versioned\n"
                "**Last Updated:** 2026-03-01\n"
                f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "old managed block\n"
                "<!-- DEVCOV:END -->\n\n"
                "# EDITABLE SECTION\n\n"
                "Keep this editable note.\n\n"
                "<!-- DEVCOV-WORKFLOW:BEGIN -->\n"
                "old workflow\n"
                "<!-- DEVCOV-WORKFLOW:END -->\n\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "old governance section\n"
                "<!-- DEVCOV:END -->\n\n"
                "<!-- DEVCOV-POLICIES:BEGIN -->\n"
                "keep policy text\n"
                "<!-- DEVCOV-POLICIES:END -->\n",
                encoding="utf-8",
            )

            state = project_governance.resolve_runtime_state(repo_root)
            project_version = state.displayed_project_version("")
            devcovenant_version = (
                (repo_root / "devcovenant" / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )

            changed = managed_docs.sync_doc(
                repo_root,
                "AGENTS.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = agents_path.read_text(encoding="utf-8")
            self.assertTrue(changed)
            self.assertIn("Keep this editable note.", updated)
            self.assertIn("## Project Governance", updated)
            self.assertIn("keep policy text", updated)
            self.assertNotIn("old managed block", updated)


if __name__ == "__main__":
    unittest.main()
