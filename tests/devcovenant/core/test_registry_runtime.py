"""Consistency checks for registry, descriptors, and manifest defaults."""

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install, upgrade
from devcovenant.core import registry_runtime as registry_runtime_module
from devcovenant.core.registry_runtime import (
    PolicyRegistry,
    load_policy_replacements,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_REGISTRY_PATH = (
    REPO_ROOT / "devcovenant" / "registry" / "local" / "policy_registry.yaml"
)
ASSETS_ROOT = (
    REPO_ROOT / "devcovenant" / "core" / "profiles" / "global" / "assets"
)


def _load_descriptor_policy_ids() -> set[str]:
    """Return policy IDs declared by core and custom descriptors."""
    policy_ids: set[str] = set()
    for root in (
        REPO_ROOT / "devcovenant" / "core" / "policies",
        REPO_ROOT / "devcovenant" / "custom" / "policies",
    ):
        for descriptor_path in sorted(root.glob("*/*.yaml")):
            payload = yaml.safe_load(
                descriptor_path.read_text(encoding="utf-8")
            )
            if not isinstance(payload, dict):
                continue
            policy_id = payload.get("id")
            if isinstance(policy_id, str) and policy_id:
                policy_ids.add(policy_id)
    return policy_ids


def _unit_test_policy_registry_lists_exact_policy_inventory() -> None:
    """Local policy registry should match descriptor inventory."""
    descriptor_ids = _load_descriptor_policy_ids()
    payload = (
        yaml.safe_load(POLICY_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    )
    policies = payload.get("policies")
    assert isinstance(policies, dict)
    registry_ids = set(policies.keys())

    assert registry_ids == descriptor_ids, (
        "policy_registry.yaml policy IDs drifted.\n"
        f"Missing: {sorted(descriptor_ids - registry_ids)}\n"
        f"Unexpected: {sorted(registry_ids - descriptor_ids)}"
    )


def _unit_test_registry_prune_policies_removes_stale_entries() -> None:
    """Registry prune should remove entries outside keep_ids."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "policies": {
                "alpha": {"enabled": True},
                "beta": {"enabled": True},
            },
            "metadata": {"version": "1.0.0"},
        }
        registry_path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
        registry = PolicyRegistry(registry_path, repo_root)
        removed = registry.prune_policies({"beta", "gamma"})
        assert removed == ["alpha"]
        assert registry.policy_ids() == {"beta"}


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
        "custom: false\n"
        "enabled: true\n"
        "```\n\n"
        "Old text.\n"
        "<!-- DEVCOV-POLICIES:END -->\n",
        encoding="utf-8",
    )


def _unit_test_load_policy_replacements_reads_mapping() -> None:
    """Replacement loader should parse registry/global mapping payloads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "devcovenant").mkdir(parents=True, exist_ok=True)
        _write_replacements(repo_root)

        loaded = load_policy_replacements(repo_root)
        assert "old-policy" in loaded
        assert loaded["old-policy"].replaced_by == "new-policy"


def _unit_test_apply_replacements_migrates_policy_state() -> None:
    """Upgrade replacement pass should migrate config policy_state keys."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _write_replacements(repo_root)
        _write_agents(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_payload = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        config_payload["policy_state"] = {"old-policy": False}
        config_path.write_text(
            yaml.safe_dump(config_payload, sort_keys=False),
            encoding="utf-8",
        )

        notices = upgrade._apply_policy_replacements(repo_root)
        assert any("old-policy" in notice for notice in notices)

        updated_config = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        state = updated_config.get("policy_state", {})
        assert state.get("new-policy") is False
        assert "old-policy" not in state


def _unit_test_apply_replacements_skips_custom_overrides() -> None:
    """Replacement migration should not rewrite keys for custom overrides."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _write_replacements(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_payload = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        config_payload["policy_state"] = {"old-policy": True}
        config_path.write_text(
            yaml.safe_dump(config_payload, sort_keys=False),
            encoding="utf-8",
        )
        custom_policy = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "old_policy"
            / "old_policy.py"
        )
        custom_policy.parent.mkdir(parents=True, exist_ok=True)
        custom_policy.write_text("# custom old policy\n", encoding="utf-8")

        notices = upgrade._apply_policy_replacements(repo_root)
        assert any("custom override exists" in notice for notice in notices)

        updated_config = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        state = updated_config.get("policy_state", {})
        assert state.get("old-policy") is True
        assert "new-policy" not in state


def _unit_test_ensure_manifest_returns_none_without_install() -> None:
    """Manifest is not created when DevCovenant is absent."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        assert registry_runtime_module.ensure_manifest(repo_root) is None


def _unit_test_ensure_manifest_creates_when_installed() -> None:
    """Manifest is created when DevCovenant is installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "devcovenant").mkdir()
        manifest = registry_runtime_module.ensure_manifest(repo_root)
        assert manifest is not None
        manifest_path = repo_root / registry_runtime_module.MANIFEST_REL_PATH
        assert manifest_path.exists()
        assert "core" in manifest


def _unit_test_append_notifications_creates_manifest() -> None:
    """append_notifications creates manifest and records messages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "devcovenant").mkdir()
        registry_runtime_module.append_notifications(
            repo_root, ["hello world"]
        )

        manifest = registry_runtime_module.load_manifest(repo_root)
        assert manifest is not None
        notes = manifest.get("notifications", [])
        assert len(notes) == 1
        assert "hello world" in notes[0]["message"]


def _unit_test_ensure_manifest_normalizes_stale_default_sections() -> None:
    """ensure_manifest should refresh stale default inventories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        (repo_root / "devcovenant").mkdir()
        stale = registry_runtime_module.build_manifest()
        stale["core"]["files"] = [
            *stale["core"]["files"],
            "devcovenant/core/profiles/global/assets/AGENTS.md",
            "devcovenant/core/profiles/global/assets/CONTRIBUTING.md",
        ]
        registry_runtime_module.write_manifest(repo_root, stale)

        manifest = registry_runtime_module.ensure_manifest(repo_root)

        assert manifest is not None
        assert (
            manifest["core"]["files"]
            == registry_runtime_module.DEFAULT_CORE_FILES
        )
        assert (
            "devcovenant/core/profiles/global/assets/AGENTS.md"
            not in manifest["core"]["files"]
        )
        assert (
            "devcovenant/core/profiles/global/assets/CONTRIBUTING.md"
            not in manifest["core"]["files"]
        )


def _unit_test_managed_doc_descriptors_exist() -> None:
    """Managed docs should be backed by YAML descriptors."""
    required = (
        ASSETS_ROOT / "AGENTS.yaml",
        ASSETS_ROOT / "README.yaml",
        ASSETS_ROOT / "SPEC.yaml",
        ASSETS_ROOT / "PLAN.yaml",
        ASSETS_ROOT / "CHANGELOG.yaml",
        ASSETS_ROOT / "CONTRIBUTING.yaml",
        ASSETS_ROOT / "devcovenant" / "README.yaml",
    )
    for descriptor_path in required:
        assert descriptor_path.exists()


def _unit_test_legacy_markdown_templates_are_absent() -> None:
    """Legacy managed-doc markdown templates should not exist."""
    assert not (ASSETS_ROOT / "AGENTS.md").exists()
    assert not (ASSETS_ROOT / "CONTRIBUTING.md").exists()


def _unit_test_legacy_gpl_template_is_absent() -> None:
    """Retired GPL template asset should not exist."""
    assert not (ASSETS_ROOT / "LICENSE_GPL-3.0.txt").exists()


def _unit_test_manifest_excludes_no_devcov_state_path() -> None:
    """MANIFEST.in should not keep retired .devcov-state rules."""
    manifest_path = REPO_ROOT / "MANIFEST.in"
    contents = manifest_path.read_text(encoding="utf-8")
    assert ".devcov-state" not in contents


def _unit_test_manifest_excludes_root_managed_docs() -> None:
    """MANIFEST.in should not include root managed docs."""
    manifest_path = REPO_ROOT / "MANIFEST.in"
    contents = manifest_path.read_text(encoding="utf-8")
    forbidden = (
        "include AGENTS.md",
        "include CONTRIBUTING.md",
        "include SPEC.md",
        "include PLAN.md",
        "include CHANGELOG.md",
    )
    for entry in forbidden:
        assert entry not in contents


def _unit_test_manifest_core_files_skip_legacy_markdown_templates() -> None:
    """Manifest defaults should not list removed markdown templates."""
    assert (
        "devcovenant/core/profiles/global/assets/AGENTS.md"
        not in registry_runtime_module.DEFAULT_CORE_FILES
    )
    assert (
        "devcovenant/core/profiles/global/assets/CONTRIBUTING.md"
        not in registry_runtime_module.DEFAULT_CORE_FILES
    )
    assert (
        "devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt"
        not in registry_runtime_module.DEFAULT_CORE_FILES
    )


def _unit_test_loads_changelog_descriptor() -> None:
    """Descriptor loader should return changelog-coverage metadata."""
    descriptor = registry_runtime_module.load_policy_descriptor(
        REPO_ROOT,
        "changelog-coverage",
    )

    assert descriptor is not None
    assert descriptor.policy_id == "changelog-coverage"
    assert descriptor.metadata.get("severity") == "error"
    assert descriptor.metadata.get("main_changelog") == ["CHANGELOG.md"]


def _unit_test_descriptors_do_not_define_activation_scope_keys() -> None:
    """Descriptors should not expose retired scope metadata keys."""
    forbidden = {"profile_scopes", "policy_scopes"}

    for policy_root in (
        REPO_ROOT / "devcovenant" / "core" / "policies",
        REPO_ROOT / "devcovenant" / "custom" / "policies",
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
            assert not present, (
                f"{descriptor_path} contains retired scope keys: "
                f"{sorted(present)}"
            )


def _unit_test_parse_metadata_block_reads_order_and_multiline_values() -> None:
    """Metadata parsing should preserve key order and folded entries."""
    block = (
        "id: sample\n"
        "severity: error\n"
        "required_files:\n"
        "  README.md\n"
        "  PLAN.md\n"
    )
    order, values = registry_runtime_module.parse_metadata_block(block)
    assert order == ["id", "severity", "required_files"]
    assert values["required_files"] == ["README.md", "PLAN.md"]


def _unit_test_resolve_script_location_prefers_custom_policy() -> None:
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

        resolved = registry_runtime_module.resolve_script_location(
            repo_root,
            "sample-policy",
        )

        assert resolved is not None
        assert resolved.kind == "custom"
        assert resolved.path == custom_script


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_policy_registry_lists_exact_policy_inventory(self):
        """Run test_policy_registry_lists_exact_policy_inventory."""
        _unit_test_policy_registry_lists_exact_policy_inventory()

    def test_registry_prune_policies_removes_stale_entries(self):
        """Run test_registry_prune_policies_removes_stale_entries."""
        _unit_test_registry_prune_policies_removes_stale_entries()

    def test_load_policy_replacements_reads_mapping(self):
        """Run test_load_policy_replacements_reads_mapping."""
        _unit_test_load_policy_replacements_reads_mapping()

    def test_apply_replacements_migrates_policy_state(self):
        """Run test_apply_replacements_migrates_policy_state."""
        _unit_test_apply_replacements_migrates_policy_state()

    def test_apply_replacements_skips_custom_overrides(self):
        """Run test_apply_replacements_skips_custom_overrides."""
        _unit_test_apply_replacements_skips_custom_overrides()

    def test_ensure_manifest_returns_none_without_install(self):
        """Run test_ensure_manifest_returns_none_without_install."""
        _unit_test_ensure_manifest_returns_none_without_install()

    def test_ensure_manifest_creates_when_installed(self):
        """Run test_ensure_manifest_creates_when_installed."""
        _unit_test_ensure_manifest_creates_when_installed()

    def test_append_notifications_creates_manifest(self):
        """Run test_append_notifications_creates_manifest."""
        _unit_test_append_notifications_creates_manifest()

    def test_ensure_manifest_normalizes_stale_default_sections(self):
        """Run test_ensure_manifest_normalizes_stale_default_sections."""
        _unit_test_ensure_manifest_normalizes_stale_default_sections()

    def test_managed_doc_descriptors_exist(self):
        """Run test_managed_doc_descriptors_exist."""
        _unit_test_managed_doc_descriptors_exist()

    def test_legacy_markdown_templates_are_absent(self):
        """Run test_legacy_markdown_templates_are_absent."""
        _unit_test_legacy_markdown_templates_are_absent()

    def test_legacy_gpl_template_is_absent(self):
        """Run test_legacy_gpl_template_is_absent."""
        _unit_test_legacy_gpl_template_is_absent()

    def test_manifest_excludes_no_devcov_state_path(self):
        """Run test_manifest_excludes_no_devcov_state_path."""
        _unit_test_manifest_excludes_no_devcov_state_path()

    def test_manifest_excludes_root_managed_docs(self):
        """Run test_manifest_excludes_root_managed_docs."""
        _unit_test_manifest_excludes_root_managed_docs()

    def test_manifest_core_files_skip_legacy_markdown_templates(self):
        """Run test_manifest_core_files_skip_legacy_markdown_templates."""
        _unit_test_manifest_core_files_skip_legacy_markdown_templates()

    def test_loads_changelog_descriptor(self):
        """Run test_loads_changelog_descriptor."""
        _unit_test_loads_changelog_descriptor()

    def test_descriptors_do_not_define_activation_scope_keys(self):
        """Run test_descriptors_do_not_define_activation_scope_keys."""
        _unit_test_descriptors_do_not_define_activation_scope_keys()

    def test_parse_metadata_block_reads_order_and_multiline_values(self):
        """Run parse metadata block order/value test."""
        _unit_test_parse_metadata_block_reads_order_and_multiline_values()

    def test_resolve_script_location_prefers_custom_policy(self):
        """Run resolve script location custom-priority test."""
        _unit_test_resolve_script_location_prefers_custom_policy()
