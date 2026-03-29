"""Unit tests for shared asset materialization helpers."""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from devcovenant import install

MODULE = "devcovenant.core.services.asset_materialization"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_yaml(path: Path) -> dict[str, object]:
    """Load a YAML mapping payload from disk."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_profile(
    repo_root: Path,
    *,
    profile_name: str,
    assets: list[dict[str, str]],
) -> None:
    """Create one minimal custom profile with concrete asset templates."""
    profile_root = (
        repo_root / "devcovenant" / "custom" / "profiles" / profile_name
    )
    assets_root = profile_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    for asset in assets:
        template_name = asset["template"]
        template_path = assets_root / template_name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(asset["content"], encoding="utf-8")
    manifest = {
        "version": 1,
        "profile": profile_name,
        "category": "repo",
        "suffixes": [],
        "ignore_dirs": [],
        "assets": [
            {"path": asset["path"], "template": asset["template"]}
            for asset in assets
        ],
    }
    (profile_root / f"{profile_name}.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )


def _set_active_profiles(repo_root: Path, names: list[str]) -> None:
    """Replace the active profile list in repo config."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = _load_yaml(config_path)
    profiles = payload.setdefault("profiles", {})
    assert isinstance(profiles, dict)
    profiles["active"] = list(names)
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


class GeneratedUnittestCases(unittest.TestCase):
    """Direct coverage for asset-materialization helpers."""

    def test_module_imports_cleanly(self) -> None:
        """The service module should import cleanly."""
        module = importlib.import_module(MODULE)
        self.assertIsNotNone(module)

    def test_public_symbol_contract_is_stable(self) -> None:
        """The public helper surface should stay callable."""
        module = importlib.import_module(MODULE)
        for symbol in (
            "MaterializableAssetCandidate",
            "MaterializedAssetResult",
            "materialize_named_asset",
            "render_profile_asset_template_text",
            "resolve_asset_output_path",
            "resolve_desktop_directory",
            "resolve_materializable_asset",
        ):
            self.assertTrue(hasattr(module, symbol))

    def test_output_path_resolution_uses_desktop_defaults(self) -> None:
        """Desktop output should use the original or renamed filename only."""
        module = importlib.import_module(MODULE)
        candidate = module.MaterializableAssetCandidate(
            kind="managed_doc",
            profile_name="global",
            active=True,
            profile_path="devcovenant/builtin/profiles/global",
            target_path="SPEC.md",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            desktop = Path(tmpdir) / "Desktop"
            with patch.dict(
                os.environ,
                {"XDG_DESKTOP_DIR": str(desktop)},
                clear=False,
            ):
                self.assertEqual(
                    module.resolve_asset_output_path(candidate, None),
                    desktop / "SPEC.md",
                )
                self.assertEqual(
                    module.resolve_asset_output_path(
                        candidate,
                        "OTHERNAME.md",
                    ),
                    desktop / "OTHERNAME.md",
                )

    def test_output_path_resolution_rejects_paths(self) -> None:
        """Output override should reject anything other than a filename."""
        module = importlib.import_module(MODULE)
        candidate = module.MaterializableAssetCandidate(
            kind="managed_doc",
            profile_name="global",
            active=True,
            profile_path="devcovenant/builtin/profiles/global",
            target_path="SPEC.md",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            desktop = Path(tmpdir) / "Desktop"
            with patch.dict(
                os.environ,
                {"XDG_DESKTOP_DIR": str(desktop)},
                clear=False,
            ):
                for token in (
                    "/tmp/OTHERNAME.md",
                    "nested/OTHERNAME.md",
                    "../OTHERNAME.md",
                    "./OTHERNAME.md",
                    r"nested\OTHERNAME.md",
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "plain filename|absolute path",
                    ):
                        module.resolve_asset_output_path(candidate, token)

    def test_resolve_materializable_asset_finds_managed_doc(self) -> None:
        """Managed docs should be materializable by basename."""
        module = importlib.import_module(MODULE)
        candidate = module.resolve_materializable_asset(REPO_ROOT, "SPEC.md")
        self.assertEqual(candidate.kind, "managed_doc")
        self.assertEqual(candidate.target_path, "SPEC.md")
        self.assertEqual(candidate.profile_name, "global")

    def test_active_profiles_win_same_name_resolution(self) -> None:
        """Active profiles should take precedence over inactive matches."""
        module = importlib.import_module(MODULE)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            install.install_repo(repo_root)
            _write_profile(
                repo_root,
                profile_name="alpha",
                assets=[
                    {
                        "path": "NOTICE.md",
                        "template": "NOTICE.md",
                        "content": "# Alpha\n",
                    }
                ],
            )
            _write_profile(
                repo_root,
                profile_name="beta",
                assets=[
                    {
                        "path": "NOTICE.md",
                        "template": "NOTICE.md",
                        "content": "# Beta\n",
                    }
                ],
            )
            _set_active_profiles(repo_root, ["beta"])

            candidate = module.resolve_materializable_asset(
                repo_root, "NOTICE.md"
            )

        self.assertEqual(candidate.profile_name, "beta")
        self.assertEqual(candidate.kind, "profile_asset")

    def test_same_profile_basename_ambiguity_requires_exact_target(
        self,
    ) -> None:
        """One winning profile with duplicate basenames should fail clearly."""
        module = importlib.import_module(MODULE)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            install.install_repo(repo_root)
            _write_profile(
                repo_root,
                profile_name="docsdemo",
                assets=[
                    {
                        "path": "docs/REFERENCE.md",
                        "template": "docs-spec.md",
                        "content": "# Docs Reference\n",
                    },
                    {
                        "path": "notes/REFERENCE.md",
                        "template": "notes-spec.md",
                        "content": "# Notes Reference\n",
                    },
                ],
            )
            _set_active_profiles(repo_root, ["docsdemo"])

            with self.assertRaisesRegex(
                ValueError,
                "Use an exact asset target path",
            ):
                module.resolve_materializable_asset(repo_root, "REFERENCE.md")

            candidate = module.resolve_materializable_asset(
                repo_root,
                "docs/REFERENCE.md",
            )

        self.assertEqual(candidate.target_path, "docs/REFERENCE.md")
        self.assertEqual(candidate.profile_name, "docsdemo")

    def test_materialize_named_asset_writes_managed_doc_to_desktop_name(
        self,
    ) -> None:
        """An optional output filename should write to Desktop."""
        module = importlib.import_module(MODULE)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            install.install_repo(repo_root)
            desktop = Path(tmpdir) / "Desktop"

            with patch.dict(
                os.environ,
                {"XDG_DESKTOP_DIR": str(desktop)},
                clear=False,
            ):
                result = module.materialize_named_asset(
                    repo_root,
                    "SPEC.md",
                    output_name="OTHERNAME.md",
                )

            output_text = (desktop / "OTHERNAME.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.candidate.kind, "managed_doc")
        self.assertEqual(result.output_path, desktop / "OTHERNAME.md")
        self.assertIn("**Doc ID:** SPEC", output_text)
