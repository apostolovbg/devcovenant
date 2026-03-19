"""Unit tests for refresh command behavior."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from devcovenant import install, refresh
from tests.devcovenant import repo_seed_cache


def _unit_test_refresh_builds_tracked_registry_and_agents() -> None:
    """refresh_repo should build tracked registry content and render AGENTS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        profile_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        agents_path = repo_root / "AGENTS.md"

        assert policy_registry.exists()
        assert profile_registry.exists()
        assert agents_path.exists()
        changelog_path = repo_root / "CHANGELOG.md"
        spec_path = repo_root / "SPEC.md"
        assert changelog_path.exists()
        assert "## Unreleased" in changelog_path.read_text(encoding="utf-8")
        spec_text = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** prototype" in spec_text
        assert "**Versioning Mode:** unversioned" in spec_text


def _unit_test_refresh_updates_managed_block_only() -> None:
    """refresh_repo should update managed block without replacing full doc."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        readme = repo_root / "README.md"
        readme.write_text(
            "# User README\n\n"
            "<!-- DEVCOV:BEGIN -->\nold\n<!-- DEVCOV:END -->\n\n"
            "User body\n",
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = readme.read_text(encoding="utf-8")
        assert "User body" in updated
        assert "Doc ID:" in updated


def _unit_test_refresh_imports_same_version_header_only_spec_doc() -> None:
    """refresh_repo should adopt a same-version preauthored SPEC body."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        spec_path = repo_root / "SPEC.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            "# Product Spec\n"
            "**Doc ID:** SPEC\n"
            "**Doc Type:** specification\n"
            "**Project Version:** 9.9.9\n"
            "**DevCovenant Version:** 1.0.0\n\n"
            "Custom imported spec body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** prototype" in updated
        assert "**Versioning Mode:** unversioned" in updated
        assert "Custom imported spec body." in updated


def _unit_test_refresh_imports_same_version_header_only_plan_doc() -> None:
    """refresh_repo should adopt a same-version preauthored PLAN body."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        plan_path = repo_root / "PLAN.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(
            "# App Plan\n"
            "**Doc ID:** PLAN\n"
            "**Doc Type:** plan\n"
            "**Project Version:** 9.9.9\n"
            "**DevCovenant Version:** 1.0.0\n\n"
            "Custom imported planning body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = plan_path.read_text(encoding="utf-8")
        assert "Custom imported planning body." in updated
        assert "**DevCovenant Version:** 1.0.0" in updated


def _unit_test_refresh_preserves_existing_non_placeholder_plan_body() -> None:
    """refresh_repo should preserve existing non-placeholder PLAN content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

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

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = plan_path.read_text(encoding="utf-8")
        assert "This is the real planning body." in updated
        assert "Preserve authored docs." in updated
        assert "Item placeholder." not in updated


def _unit_test_refresh_replaces_older_header_only_spec_doc() -> None:
    """refresh_repo should replace older DevCovenant SPEC seeds."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        spec_path = repo_root / "SPEC.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            "# Product Spec\n"
            "**Doc ID:** SPEC\n"
            "**Doc Type:** specification\n"
            "**Project Version:** 9.9.9\n"
            "**DevCovenant Version:** 0.9.0\n\n"
            "Old imported body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = spec_path.read_text(encoding="utf-8")
        assert "Old imported body." not in updated
        assert "This is a generic SPEC guide template." in updated


def _unit_test_refresh_imports_same_version_managed_block_doc() -> None:
    """refresh_repo should adopt same-version managed-block docs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        readme_path = repo_root / "README.md"
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text(
            "# Seed README\n"
            "**Doc ID:** README\n"
            "**Doc Type:** repo-readme\n"
            "**Project Version:** 0.1.0\n"
            "**DevCovenant Version:** 1.0.0\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "stale block\n"
            "<!-- DEVCOV:END -->\n\n"
            "Imported README body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = readme_path.read_text(encoding="utf-8")
        assert "Imported README body." in updated
        assert "stale block" not in updated
        assert "**DevCovenant Version:** 1.0.0" in updated


def _unit_test_refresh_updates_all_managed_blocks() -> None:
    """refresh_repo should normalize AGENTS managed/workflow/policy blocks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        agents.write_text(
            "# AGENTS\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old top block\n"
            "<!-- DEVCOV:END -->\n\n"
            "# EDITABLE SECTION\n\n"
            "keep me\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old secondary block\n"
            "<!-- DEVCOV:END -->\n\n"
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "<!-- DEVCOV-POLICIES:END -->\n",
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = agents.read_text(encoding="utf-8")
        assert "old top block" not in updated
        assert "old secondary block" not in updated
        assert "keep me" in updated
        assert "## THE DEV COVENANT" in updated
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" in updated
        assert "<!-- DEVCOV-WORKFLOW:END -->" in updated
        assert updated.count("<!-- DEVCOV:BEGIN -->") == 1


def _unit_test_refresh_writes_ruff_cache_gitignore() -> None:
    """refresh_repo should include .ruff_cache in generated gitignore."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert ".ruff_cache/" in content


def _unit_test_refresh_writes_devcovenant_logs_gitignore_rules() -> None:
    """refresh_repo should ignore runtime logs but keep logs README tracked."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert "devcovenant/logs/**" in content
        assert "!devcovenant/logs/" in content
        assert "!devcovenant/logs/README.md" in content


def _unit_test_refresh_writes_global_artifact_ignore_defaults() -> None:
    """refresh_repo should seed shared editor/build/runtime ignore globs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        patterns = payload["ignore"]["patterns"]
        for expected in (
            ".vscode/**",
            ".idea/**",
            "*.egg-info/**",
            "pip-wheel-metadata/**",
            ".coverage.*",
            "devcovenant/logs/**",
            "devcovenant/registry/runtime/**",
        ):
            assert expected in patterns


def _unit_test_refresh_writes_clean_config_section() -> None:
    """refresh_repo should render the clean config contract and defaults."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        clean_block = payload.get("clean", {})

        assert isinstance(clean_block, dict)
        assert clean_block.get("overlays") == {
            "build_dirs": [],
            "build_globs": [],
            "cache_dirs": [],
            "cache_globs": [],
            "runtime_registry_dirs": [],
            "runtime_registry_globs": [],
            "logs_dirs": [],
            "logs_globs": [],
            "protected_dirs": [],
            "protected_globs": [],
        }
        assert clean_block.get("overrides") == {}


def _unit_test_refresh_renders_devcov_managed_doc_intros() -> None:
    """refresh_repo should render doc-specific DevCovenant intro text."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        readme = (repo_root / "README.md").read_text(encoding="utf-8")
        package_readme = (repo_root / "devcovenant" / "README.md").read_text(
            encoding="utf-8"
        )
        contributing = (repo_root / "CONTRIBUTING.md").read_text(
            encoding="utf-8"
        )
        changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")

        assert "**Contributor note:** this repository is managed by " not in (
            readme
        )
        assert "<!-- DEVCOV:BEGIN -->\n\n<!-- DEVCOV:END -->" in readme
        assert "Describe the project this repository ships" in readme
        assert "If you already drafted DevCovenant-shaped docs" in readme
        assert "**Managed runtime note:** this `devcovenant/` folder" in (
            package_readme
        )
        assert (
            "DevCovenant is a Repository Governance Framework."
            in package_readme
        )
        assert "This opening section is managed by DevCovenant." in (
            contributing
        )
        assert "## Workflow" in contributing
        assert "<!-- DEVCOV:END -->\n\n## Repository Notes" in contributing
        assert "## DevCovenant Change Logging Rules" in changelog


def _unit_test_refresh_writes_global_artifact_gitignore_rules() -> None:
    """refresh_repo should write universal editor/build/runtime gitignores."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        for expected in (
            ".vscode/",
            ".idea/",
            "*.egg-info/",
            "pip-wheel-metadata/",
            ".coverage",
            ".coverage.*",
            "htmlcov/",
        ):
            assert expected in content


def _unit_test_refresh_policy_registry_origin_metadata() -> None:
    """refresh_repo should record builtin/custom policy origins."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        payload = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policies = payload.get("policies", {})
        assert policies["changelog-coverage"]["origin"] == "builtin"
        assert "readme-sync" not in policies
        assert "core" not in policies["changelog-coverage"]


def _unit_test_refresh_policy_registry_records_metadata_resolution() -> None:
    """refresh_repo should persist per-key metadata resolution trace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        payload = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policy_entry = payload["policies"]["changelog-coverage"]
        resolution = policy_entry["metadata_resolution"]["skipped_globs"]

        assert resolution["effective"]["values"]
        assert any(key != "effective" for key in resolution)
        assert isinstance(policy_entry["metadata_warnings"], list)
        assert isinstance(policy_entry["runtime_metadata_options"], dict)
        assert isinstance(policy_entry["runtime_config_overrides"], dict)
        assert isinstance(policy_entry["runtime_effective_options"], dict)


def _unit_test_refresh_records_override_replacement_warning() -> None:
    """refresh_repo should record warnings for destructive overrides."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["user_metadata_overrides"] = {
            "changelog-coverage": {"skipped_globs": ["README.md"]}
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        refreshed = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policy_entry = refreshed["policies"]["changelog-coverage"]
        warnings = policy_entry["metadata_warnings"]
        assert warnings
        assert warnings[0]["layer"] == "user_overrides"
        assert warnings[0]["key"] == "skipped_globs"
        resolution = policy_entry["metadata_resolution"]["skipped_globs"]
        assert resolution["user_overrides"]["values"] == ["README.md"]
        assert "README.md" in resolution["effective"]["values"]
        assert policy_entry["runtime_config_overrides"]["skipped_globs"] == [
            "README.md"
        ]
        assert (
            "README.md"
            in policy_entry["runtime_effective_options"]["skipped_globs"]
        )


def _unit_test_refresh_preserves_existing_gate_status() -> None:
    """refresh_repo should leave an open gate status file untouched."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        gate_status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        gate_status_path.parent.mkdir(parents=True, exist_ok=True)
        expected_payload = {
            "session_id": "refresh-open-session",
            "session_state": "open",
            "pre_commit_start_utc": "2026-03-01T10:00:00+00:00",
        }
        gate_status_path.write_text(
            json.dumps(expected_payload, indent=2) + "\n",
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        assert gate_status_path.exists()
        actual_payload = json.loads(
            gate_status_path.read_text(encoding="utf-8")
        )
        assert actual_payload == expected_payload


def _unit_test_refresh_recreates_missing_tracked_registry_only() -> None:
    """refresh_repo should rebuild tracked registry without runtime state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        tracked_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        runtime_registry = repo_root / "devcovenant" / "registry" / "runtime"
        if runtime_registry.exists():
            raise AssertionError(
                "Seeded repo should not include runtime state."
            )
        tracked_registry.unlink()
        assert not tracked_registry.exists()

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        assert tracked_registry.exists()
        assert not runtime_registry.exists()


def _unit_test_refresh_defaults_autofix_disabled_globally() -> None:
    """refresh_repo should default `engine.auto_fix_enabled` to false."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert payload["engine"]["auto_fix_enabled"] is False
        assert payload["engine"]["pycache_prefix_enabled"] is False
        assert payload["engine"]["pycache_prefix"] == ""


def _unit_test_refresh_seeds_autofix_for_devcovrepo_when_unset() -> None:
    """refresh_repo should seed autofix for active `devcovrepo` when unset."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload.setdefault("profiles", {})
        payload["profiles"]["active"] = [
            "global",
            "defaults",
            "devcovrepo",
            "devcovuser",
            "python",
            "docs",
        ]
        payload.setdefault("engine", {})
        payload["engine"].pop("auto_fix_enabled", None)
        payload["engine"].pop("pycache_prefix_enabled", None)
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        updated = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert updated["engine"]["auto_fix_enabled"] is True
        assert updated["engine"]["pycache_prefix_enabled"] is True


def _unit_test_refresh_rejects_missing_version_for_versioned_repo() -> None:
    """refresh_repo should fail when versioned repos lack a real version."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        version_path = repo_root / "VERSION"
        if version_path.exists():
            version_path.unlink()

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload.setdefault("policy_state", {})
        payload["policy_state"]["project-governance"] = True
        payload.setdefault("user_metadata_overlays", {})
        payload["user_metadata_overlays"]["project-governance"] = {
            "stage": "stable",
            "development_stance": "active-development",
            "versioning_mode": "versioned",
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 1


def _unit_test_refresh_allows_unversioned_repo_without_version_file() -> None:
    """refresh_repo should allow missing version file for unversioned repos."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)
        version_path = repo_root / "VERSION"
        if version_path.exists():
            version_path.unlink()

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload.setdefault("policy_state", {})
        payload["policy_state"]["project-governance"] = True
        payload.setdefault("user_metadata_overlays", {})
        payload["user_metadata_overlays"]["project-governance"] = {
            "stage": "beta",
            "development_stance": "active-development",
            "versioning_mode": "unversioned",
            "unversioned_label": "Unversioned",
            "unreleased_heading": "## Unreleased",
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        spec_path = repo_root / "SPEC.md"
        spec_text = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** beta" in spec_text
        assert "**Versioning Mode:** unversioned" in spec_text


def _unit_test_refresh_renders_canonical_workflow_triggers() -> None:
    """refresh_repo should render canonical GitHub trigger syntax."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        workflow_path = (
            repo_root / ".github" / "workflows" / "governance-and-test.yml"
        )
        content = workflow_path.read_text(encoding="utf-8")
        assert "\non:\n" in content
        assert "'on':" not in content
        assert '"on":' not in content
        assert "push: null" not in content
        assert "pull_request: null" not in content
        assert re.search(r"(?m)^  push:$", content)
        assert re.search(r"(?m)^  pull_request:$", content)


def _unit_test_refresh_rejects_multiline_non_block_doc_descriptor() -> None:
    """refresh_repo should fail when multiline doc fields skip block style."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "README.yaml"
        )
        descriptor_path.write_text(
            "\n".join(
                [
                    "title: README",
                    "doc_id: README",
                    "doc_type: repo-readme",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: true",
                    "managed_block: |-",
                    "  block text",
                    'body: "Line one\\nLine two"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        output = StringIO()
        with redirect_stdout(output):
            result = refresh.refresh_repo(repo_root)
        assert result == 1
        assert "must use YAML literal block style" in output.getvalue()


def _unit_test_refresh_rejects_invalid_doc_descriptor_schema() -> None:
    """refresh_repo should fail when managed doc descriptor schema is wrong."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "README.yaml"
        )
        descriptor_path.write_text(
            "\n".join(
                [
                    "title: README",
                    "doc_id: README",
                    "doc_type: repo-readme",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: false",
                    "managed_block: |-",
                    "  block text",
                    "body: |-",
                    "  Body text",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        output = StringIO()
        with redirect_stdout(output):
            result = refresh.refresh_repo(repo_root)
        assert result == 1
        assert "field `devcovenant_version` must be true" in output.getvalue()


def _unit_test_refresh_run_calls_refresh_repo() -> None:
    """run() should resolve repo root and delegate to refresh_repo."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with patch(
            "devcovenant.refresh.resolve_repo_root",
            return_value=repo_root,
        ):
            with patch(
                "devcovenant.refresh.refresh_repo",
                return_value=0,
            ) as mock:
                result = refresh.run(SimpleNamespace())
    assert result == 0
    mock.assert_called_once_with(repo_root)


def _unit_test_refresh_main_exits_with_run_code() -> None:
    """main() should parse args, call run, and exit with its code."""
    captured: dict[str, object] = {}
    original_run = refresh.run

    def _fake_run(args):
        """Capture parsed args and return a stable exit code."""
        captured["args"] = args
        return 0

    refresh.run = _fake_run
    try:
        try:
            refresh.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from main().")
    finally:
        refresh.run = original_run

    assert code == 0
    assert hasattr(captured["args"], "__dict__")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_refresh_builds_tracked_registry_and_agents(self):
        """Run test_refresh_builds_tracked_registry_and_agents."""
        _unit_test_refresh_builds_tracked_registry_and_agents()

    def test_refresh_updates_managed_block_only(self):
        """Run test_refresh_updates_managed_block_only."""
        _unit_test_refresh_updates_managed_block_only()

    def test_refresh_imports_same_version_header_only_spec_doc(self):
        """Run same-version SPEC import assertions."""
        _unit_test_refresh_imports_same_version_header_only_spec_doc()

    def test_refresh_imports_same_version_header_only_plan_doc(self):
        """Run same-version PLAN import assertions."""
        _unit_test_refresh_imports_same_version_header_only_plan_doc()

    def test_refresh_preserves_existing_non_placeholder_plan_body(self):
        """Run existing PLAN preservation assertions."""
        _unit_test_refresh_preserves_existing_non_placeholder_plan_body()

    def test_refresh_replaces_older_header_only_spec_doc(self):
        """Run older SPEC replacement assertions."""
        _unit_test_refresh_replaces_older_header_only_spec_doc()

    def test_refresh_imports_same_version_managed_block_doc(self):
        """Run same-version managed-block import assertions."""
        _unit_test_refresh_imports_same_version_managed_block_doc()

    def test_refresh_updates_all_managed_blocks(self):
        """Run test_refresh_updates_all_managed_blocks."""
        _unit_test_refresh_updates_all_managed_blocks()

    def test_refresh_writes_ruff_cache_gitignore(self):
        """Run test_refresh_writes_ruff_cache_gitignore."""
        _unit_test_refresh_writes_ruff_cache_gitignore()

    def test_refresh_writes_devcovenant_logs_gitignore_rules(self):
        """Run test_refresh_writes_devcovenant_logs_gitignore_rules."""
        _unit_test_refresh_writes_devcovenant_logs_gitignore_rules()

    def test_refresh_writes_global_artifact_ignore_defaults(self):
        """Run global artifact ignore default assertions."""
        _unit_test_refresh_writes_global_artifact_ignore_defaults()

    def test_refresh_writes_clean_config_section(self):
        """Run clean-config template rendering assertions."""
        _unit_test_refresh_writes_clean_config_section()

    def test_refresh_renders_devcov_managed_doc_intros(self):
        """Run DevCovenant managed-doc intro rendering assertions."""
        _unit_test_refresh_renders_devcov_managed_doc_intros()

    def test_refresh_writes_global_artifact_gitignore_rules(self):
        """Run global artifact gitignore assertions."""
        _unit_test_refresh_writes_global_artifact_gitignore_rules()

    def test_refresh_policy_registry_origin_metadata(self):
        """Run test_refresh_policy_registry_origin_metadata."""
        _unit_test_refresh_policy_registry_origin_metadata()

    def test_refresh_policy_registry_records_metadata_resolution(self):
        """Run metadata-resolution registry persistence assertions."""
        _unit_test_refresh_policy_registry_records_metadata_resolution()

    def test_refresh_records_override_replacement_warning(self):
        """Run destructive-override warning persistence assertions."""
        _unit_test_refresh_records_override_replacement_warning()

    def test_refresh_preserves_existing_gate_status(self):
        """Run open-gate preservation assertions for refresh."""
        _unit_test_refresh_preserves_existing_gate_status()

    def test_refresh_recreates_missing_tracked_registry_only(self):
        """Run tracked-registry recreation assertions for refresh."""
        _unit_test_refresh_recreates_missing_tracked_registry_only()

    def test_refresh_defaults_autofix_disabled_globally(self):
        """Run global autofix default-disabled refresh assertions."""
        _unit_test_refresh_defaults_autofix_disabled_globally()

    def test_refresh_seeds_autofix_for_devcovrepo_when_unset(self):
        """Run devcovrepo autofix seeding refresh assertions."""
        _unit_test_refresh_seeds_autofix_for_devcovrepo_when_unset()

    def test_refresh_rejects_missing_version_for_versioned_repo(self):
        """Run missing-version explicit-failure refresh assertions."""
        _unit_test_refresh_rejects_missing_version_for_versioned_repo()

    def test_refresh_allows_unversioned_repo_without_version_file(self):
        """Run unversioned no-version refresh assertions."""
        _unit_test_refresh_allows_unversioned_repo_without_version_file()

    def test_refresh_renders_canonical_workflow_triggers(self):
        """Run canonical governance-trigger rendering refresh assertions."""
        _unit_test_refresh_renders_canonical_workflow_triggers()

    def test_refresh_rejects_multiline_non_block_doc_descriptor(self):
        """Run refresh rejection for non-block multiline descriptor strings."""
        _unit_test_refresh_rejects_multiline_non_block_doc_descriptor()

    def test_refresh_rejects_invalid_doc_descriptor_schema(self):
        """Run refresh rejection for invalid managed-doc schema."""
        _unit_test_refresh_rejects_invalid_doc_descriptor_schema()

    def test_refresh_run_calls_refresh_repo(self):
        """Run test_refresh_run_calls_refresh_repo."""
        _unit_test_refresh_run_calls_refresh_repo()

    def test_refresh_main_exits_with_run_code(self):
        """Run test_refresh_main_exits_with_run_code."""
        _unit_test_refresh_main_exits_with_run_code()
