"""Unit tests for the managed-doc runtime service."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core.services import managed_docs, project_governance


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


class GeneratedUnittestCases(unittest.TestCase):
    """Direct coverage for the managed-doc runtime service."""

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
                "**DevCovenant Version:** 1.0.0\n\n"
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
                "**Project Version:** 1.0.0\n"
                "**Last Updated:** 2026-03-01\n"
                "**DevCovenant Version:** 1.0.0\n\n"
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
                "**Project Version:** 1.0.0\n"
                "**Project Stage:** stable\n"
                "**Development Stance:** active-development\n"
                "**Versioning Mode:** versioned\n"
                "**Last Updated:** 2026-03-01\n"
                "**DevCovenant Version:** 1.0.0\n\n"
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
