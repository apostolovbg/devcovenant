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


OLD_GENERIC_SPEC_BODY = """This is a generic SPEC guide template.

Use `SPEC.md` only when your repository needs a durable specification layer.
If your repo does not need one, keep this file brief and route details to
your operational documentation.

## Table of Contents
1. [Overview](#overview)
2. [When To Use SPEC](#when-to-use-spec)
3. [Workflow](#workflow)
4. [Ownership Boundaries](#ownership-boundaries)
5. [Recommended Structure](#recommended-structure)
6. [Maintenance Rules](#maintenance-rules)
7. [Pointers](#pointers)

## Overview
`SPEC.md` is for durable repository-level contracts only.
Do not use it as a backlog, scratchpad, or temporary planning area.

## When To Use SPEC
- Use SPEC when your repo needs a stable internal contract document.
- Skip SPEC if AGENTS and operational docs already cover your needs.
- Keep it small, explicit, and implementation-facing.

## Workflow
- Follow your repo's required gate workflow before and after edits.
- Update SPEC only when durable contracts actually change.
- Update operational docs in the same work slice when behavior changes.

## Ownership Boundaries
- `AGENTS.md`: workflow law, policy source, and temporary editable notes.
- `PLAN.md`: active work backlog.
- `docs/*`: operational and user-facing behavior guides.
- `SPEC.md`: optional stable contract layer for this repository only.

## Recommended Structure
- Overview: what this repo treats as invariant.
- Functional requirements: stable behavior contracts.
- Non-functional requirements: quality, determinism, security baselines.
- Pointers: links to detailed operational docs.

If your repo needs architecture invariants, keep them in a dedicated
architecture doc and keep SPEC at the meta-contract level.

## Maintenance Rules
- Prefer one-way pointers from SPEC to docs.
- Do not make docs depend on SPEC to be understandable.
- Keep SPEC synchronized with runtime reality.
- Remove stale sections instead of keeping historical leftovers.
- If your repo stops using SPEC, keep this file as a short usage note only.

## Pointers
Add pointers to the docs that hold your runtime and operational contracts.
"""

OLD_GENERIC_PLAN_BODY = (
    "Use this plan to track active implementation work. Keep items\n"
    "dependency-ordered, factual, and current.\n\n"
    "## Table of Contents\n"
    "1. [Overview](#overview)\n"
    "2. [Workflow](#workflow)\n"
    "3. [Active Work](#active-work)\n"
    "4. [Validation Routine](#validation-routine)\n\n"
    "## Overview\n"
    "- Record durable requirements in `SPEC.md` when your repo uses SPEC.\n"
    "- Record change history in `CHANGELOG.md`.\n"
    "- Mark completed items as `[done]` and outstanding items as "
    "`[not done]`.\n\n"
    "## Workflow\n"
    "- Work in dependency order unless an explicit blocker requires "
    "reordering.\n"
    "- Keep each item concrete and testable.\n"
    "- Update status in the same session when work lands.\n\n"
    "## Active Work\n"
    "1. [not done] Item placeholder.\n"
    "2. [not done] Item placeholder.\n"
    "3. [done] Item placeholder.\n\n"
    "## Validation Routine\n"
    "- Verify checks and tests pass.\n"
    "- Verify generated artifacts are synchronized after refresh.\n"
    "- Verify documentation and changelog were updated where behavior "
    "changed.\n"
)


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

    def test_duplicate_descriptor_targets_fail(self) -> None:
        """Duplicate managed-doc targets should fail explicitly."""
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

            with self.assertRaisesRegex(
                ValueError,
                "Duplicate managed doc descriptor target `README.md`",
            ):
                managed_docs.descriptor_path(
                    repo_root,
                    "README.md",
                    config_payload=payload,
                )

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

    def test_sync_doc_replaces_legacy_generic_spec_body(self) -> None:
        """Sync should replace the exact legacy generic SPEC scaffold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            spec_path = repo_root / "SPEC.md"
            spec_path.write_text(
                "# DevCovenant Specification\n"
                "**Doc ID:** SPEC\n"
                "**Doc Type:** specification\n"
                "**Project Version:** 1.0.0\n"
                "**Project Stage:** stable\n"
                "**Maintenance Stance:** active\n"
                "**Compatibility Policy:** breaking-allowed\n"
                "**Versioning Mode:** versioned\n"
                "**Last Updated:** 2026-01-01\n"
                "**DevCovenant Version:** 1.0.0\n\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "This opening section is managed by DevCovenant.\n"
                "Use `SPEC.md` only for durable repository contracts below "
                "this block.\n"
                "<!-- DEVCOV:END -->\n\n" + OLD_GENERIC_SPEC_BODY,
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
                "SPEC.md",
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=state,
                import_managed_docs=set(),
            )

            updated = spec_path.read_text(encoding="utf-8")
            self.assertTrue(changed)
            self.assertNotIn("This is a generic SPEC guide template.", updated)
            self.assertIn("## Project Intent", updated)
            self.assertIn("## Acceptance Criteria", updated)

    def test_sync_doc_replaces_legacy_generic_plan_body(self) -> None:
        """Sync should replace the exact legacy generic PLAN scaffold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            install.install_repo(repo_root)
            plan_path = repo_root / "PLAN.md"
            plan_path.write_text(
                "# Development Plan\n"
                "**Doc ID:** PLAN\n"
                "**Doc Type:** plan\n"
                "**Project Version:** 1.0.0\n"
                "**Project Stage:** stable\n"
                "**Maintenance Stance:** active\n"
                "**Compatibility Policy:** breaking-allowed\n"
                "**Versioning Mode:** versioned\n"
                "**Last Updated:** 2026-01-01\n"
                "**DevCovenant Version:** 1.0.0\n\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "This opening section is managed by DevCovenant.\n"
                "Use `PLAN.md` to track active implementation work below "
                "this block.\n"
                "<!-- DEVCOV:END -->\n\n" + OLD_GENERIC_PLAN_BODY,
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
            self.assertNotIn("Item placeholder.", updated)
            self.assertIn("## Writing Direction", updated)
            self.assertIn("Completed item example.", updated)

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
            self.assertEqual(
                plan_entry["legacy_generic_body_fingerprints"],
                [
                    (
                        "9ca5f866398d1715312b39720b0c163674ce8b6e"
                        "2562201f3eacf5cc140fc894"
                    )
                ],
            )
            self.assertEqual(
                spec_entry["legacy_generic_body_fingerprints"],
                [
                    (
                        "5b3cac9d37293ae3f40dec269922fcbce264442a"
                        "67dc5a9642fadac6a0610043"
                    ),
                    (
                        "2fad01922c9ba1b30b1cc736c32041fbf2418aef"
                        "00349f6e7ffd28a67f547b37"
                    ),
                ],
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
                "**Project Version:** 1.0.0\n"
                "**Project Stage:** stable\n"
                "**Maintenance Stance:** active\n"
                "**Compatibility Policy:** breaking-allowed\n"
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
