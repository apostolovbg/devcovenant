"""Unit tests for refresh command behavior."""

from __future__ import annotations

import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import yaml

from devcovenant import refresh
from tests.devcovenant import repo_seed_cache


def _unit_test_refresh_builds_local_registries_and_agents() -> None:
    """refresh_repo should build local registries and render AGENTS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        profile_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "profile_registry.yaml"
        )
        agents_path = repo_root / "AGENTS.md"

        assert policy_registry.exists()
        assert profile_registry.exists()
        assert agents_path.exists()


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


def _unit_test_refresh_policy_registry_origin_metadata() -> None:
    """refresh_repo should record builtin/custom policy origins."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        result = refresh.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        payload = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policies = payload.get("policies", {})
        assert policies["changelog-coverage"]["origin"] == "builtin"
        assert "readme-sync" not in policies
        assert "core" not in policies["changelog-coverage"]


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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_refresh_builds_local_registries_and_agents(self):
        """Run test_refresh_builds_local_registries_and_agents."""
        _unit_test_refresh_builds_local_registries_and_agents()

    def test_refresh_updates_managed_block_only(self):
        """Run test_refresh_updates_managed_block_only."""
        _unit_test_refresh_updates_managed_block_only()

    def test_refresh_updates_all_managed_blocks(self):
        """Run test_refresh_updates_all_managed_blocks."""
        _unit_test_refresh_updates_all_managed_blocks()

    def test_refresh_writes_ruff_cache_gitignore(self):
        """Run test_refresh_writes_ruff_cache_gitignore."""
        _unit_test_refresh_writes_ruff_cache_gitignore()

    def test_refresh_writes_devcovenant_logs_gitignore_rules(self):
        """Run test_refresh_writes_devcovenant_logs_gitignore_rules."""
        _unit_test_refresh_writes_devcovenant_logs_gitignore_rules()

    def test_refresh_policy_registry_origin_metadata(self):
        """Run test_refresh_policy_registry_origin_metadata."""
        _unit_test_refresh_policy_registry_origin_metadata()

    def test_refresh_defaults_autofix_disabled_globally(self):
        """Run global autofix default-disabled refresh assertions."""
        _unit_test_refresh_defaults_autofix_disabled_globally()

    def test_refresh_seeds_autofix_for_devcovrepo_when_unset(self):
        """Run devcovrepo autofix seeding refresh assertions."""
        _unit_test_refresh_seeds_autofix_for_devcovrepo_when_unset()

    def test_refresh_renders_canonical_workflow_triggers(self):
        """Run canonical governance-trigger rendering refresh assertions."""
        _unit_test_refresh_renders_canonical_workflow_triggers()

    def test_refresh_rejects_multiline_non_block_doc_descriptor(self):
        """Run refresh rejection for non-block multiline descriptor strings."""
        _unit_test_refresh_rejects_multiline_non_block_doc_descriptor()

    def test_refresh_rejects_invalid_doc_descriptor_schema(self):
        """Run refresh rejection for invalid managed-doc schema."""
        _unit_test_refresh_rejects_invalid_doc_descriptor_schema()
