"""Unit tests for the managed doc assets policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.managed_doc_assets.managed_doc_assets import (
    ManagedDocAssetsCheck,
)
from tests.devcovenant import repo_seed_cache


def _load_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _dump_yaml(path: Path, payload: dict[str, object]) -> None:
    """Write YAML mapping payload to disk."""
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _policy_violations(repo_root: Path) -> list[str]:
    """Run managed doc policy and return violation messages."""
    check = ManagedDocAssetsCheck()
    context = CheckContext(repo_root=repo_root)
    return [violation.message for violation in check.check(context)]


def _unit_test_generated_descriptor_and_docs_pass() -> None:
    """Policy should pass for refreshed generated docs/descriptors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        messages = _policy_violations(repo_root)
        assert not any("Managed block for " in message for message in messages)
        assert not any(
            "missing required header" in message for message in messages
        )


def _unit_test_descriptor_generated_label_duplication_is_rejected() -> None:
    """Policy should reject managed_block text that duplicates key labels."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "CONTRIBUTING.yaml"
        )
        raw_yaml = descriptor_path.read_text(encoding="utf-8")
        needle = "managed_block: |-\n"
        assert needle in raw_yaml
        descriptor_path.write_text(
            raw_yaml.replace(
                needle,
                needle + "  **Doc ID:** CONTRIBUTING\n",
                1,
            ),
            encoding="utf-8",
        )

        messages = _policy_violations(repo_root)
        assert any(
            "must not duplicate generated header labels" in message
            for message in messages
        )


def _unit_test_user_preserve_blocks_inside_managed_block_are_ignored() -> None:
    """Policy should ignore user-preserve blocks inside managed blocks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        readme_path = repo_root / "README.md"
        content = readme_path.read_text(encoding="utf-8")
        insert = "\n".join(
            [
                "<!-- DEVCOV-USER-PRESERVE:BEGIN -->",
                "![Banner](https://example.com/banner.png)",
                "<!-- DEVCOV-USER-PRESERVE:END -->",
            ]
        )
        content = content.replace(
            "<!-- DEVCOV:END -->", f"{insert}\n<!-- DEVCOV:END -->"
        )
        readme_path.write_text(content, encoding="utf-8")

        messages = _policy_violations(repo_root)
        assert not any(
            "Managed block for README.md" in message for message in messages
        )


def _unit_test_disabled_builtin_docs_are_not_required() -> None:
    """Policy should ignore authoritative docs disabled in doc_assets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = _load_yaml(config_path)
        doc_assets = payload.setdefault("doc_assets", {})
        assert isinstance(doc_assets, dict)
        doc_assets["autogen"] = ["AGENTS.md"]
        doc_assets["user"] = []
        _dump_yaml(config_path, payload)

        (repo_root / "README.md").unlink(missing_ok=True)

        messages = _policy_violations(repo_root)
        assert not any(
            "Managed document README.md is missing." in message
            for message in messages
        )


def _unit_test_managed_doc_assets_symbol_contract_is_stable() -> None:
    """Managed doc assets class contract should remain callable."""
    assert callable(ManagedDocAssetsCheck)
    assert hasattr(ManagedDocAssetsCheck, "check")
    assert callable(getattr(ManagedDocAssetsCheck, "check"))


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_generated_descriptor_and_docs_pass(self):
        """Run test_generated_descriptor_and_docs_pass."""
        _unit_test_generated_descriptor_and_docs_pass()

    def test_descriptor_generated_label_duplication_is_rejected(self):
        """Run duplication rejection test."""
        _unit_test_descriptor_generated_label_duplication_is_rejected()

    def test_user_preserve_blocks_inside_managed_block_are_ignored(self):
        """Run preserve-block ignore test."""
        _unit_test_user_preserve_blocks_inside_managed_block_are_ignored()

    def test_disabled_builtin_docs_are_not_required(self):
        """Run disabled builtin doc coverage test."""
        _unit_test_disabled_builtin_docs_are_not_required()

    def test_managed_doc_assets_symbol_contract_is_stable(self):
        """Run managed-doc-assets symbol contract assertions."""
        _unit_test_managed_doc_assets_symbol_contract_is_stable()
