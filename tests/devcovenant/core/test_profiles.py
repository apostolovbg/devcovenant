"""Profile registry helpers for DevCovenant."""

import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _unit_test_load_profile_registry_merges_core_and_custom(
    tmp_path: Path,
) -> None:
    """Custom profile manifests override core profile data."""
    core_yaml = """
    version: 1
    profile: python
    suffixes: [".py"]
    """
    custom_yaml = """
    version: 1
    profile: python
    suffixes: [".py", ".pyi"]
    """
    core_manifest = (
        tmp_path
        / "devcovenant"
        / "core"
        / "profiles"
        / "python"
        / "python.yaml"
    )
    custom_manifest = (
        tmp_path
        / "devcovenant"
        / "custom"
        / "profiles"
        / "python"
        / "python.yaml"
    )
    _write_yaml(core_manifest, core_yaml)
    _write_yaml(custom_manifest, custom_yaml)

    custom_profile_dir = (
        tmp_path / "devcovenant" / "custom" / "profiles" / "zig"
    )
    custom_profile_dir.mkdir(parents=True, exist_ok=True)

    registry = profiles.load_profile_registry(tmp_path)

    assert registry["python"]["suffixes"] == [".py", ".pyi"]
    assert registry["python"]["source"] == "custom"
    assert "zig" in registry


def _unit_test_list_profiles_sorts_registry() -> None:
    """Profile list is sorted for stable prompts."""
    registry = {"lua": {}, "python": {}, "zig": {}}
    assert profiles.list_profiles(registry) == ["lua", "python", "zig"]


def _unit_test_resolve_profile_suffixes_ignores_placeholders() -> None:
    """Suffix resolution skips empty and placeholder entries."""
    registry = {
        "python": {"suffixes": [".py", ".pyi"]},
        "docs": {"suffixes": ["__none__", " "]},
    }
    resolved = profiles.resolve_profile_suffixes(registry, ["docs", "python"])
    assert resolved == [".py", ".pyi"]


def _unit_test_profile_overlays_reference_known_policies() -> None:
    """Profiles should only overlay policies that exist in the policy tree."""
    repo_root = Path(__file__).resolve().parents[3]
    known_policies = set()
    for root in (
        repo_root / "devcovenant" / "core" / "policies",
        repo_root / "devcovenant" / "custom" / "policies",
    ):
        for policy_dir in root.iterdir():
            if not policy_dir.is_dir():
                continue
            known_policies.add(policy_dir.name.replace("_", "-"))

    registry = profiles.build_profile_registry(repo_root)
    entries = registry["profiles"] if "profiles" in registry else registry

    for name, meta in entries.items():
        manifest_path = repo_root / meta["path"] / f"{name}.yaml"
        manifest = profiles.load_profile(manifest_path)
        overlays = manifest.get("policy_overlays", {})
        if not isinstance(overlays, dict):
            continue
        for policy_id in overlays:
            assert (
                policy_id in known_policies
            ), f"profile {name} overlays unknown policy {policy_id}"


def _unit_test_profiles_have_assets_unless_exempt() -> None:
    """Most profiles should ship assets; allow explicit exceptions."""
    exempt = {"devcovuser", "suffixes"}
    repo_root = Path(__file__).resolve().parents[3]
    registry = profiles.build_profile_registry(repo_root)
    for name, meta in (
        registry["profiles"].items()
        if "profiles" in registry
        else registry.items()
    ):
        if name in exempt:
            continue
        assets = meta.get("assets_available", [])
        assert assets, f"profile {name} should include assets_available"


def _unit_test_profiles_do_not_define_activation_scope_keys() -> None:
    """Profile manifests must not carry activation keys."""
    repo_root = Path(__file__).resolve().parents[3]
    forbidden = {"profile_scopes", "policy_scopes", "policies"}
    for profile_root in (
        repo_root / "devcovenant" / "core" / "profiles",
        repo_root / "devcovenant" / "custom" / "profiles",
    ):
        for profile_dir in profile_root.iterdir():
            if not profile_dir.is_dir() or profile_dir.name.startswith("_"):
                continue
            manifest_path = profile_dir / f"{profile_dir.name}.yaml"
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            present = forbidden.intersection(payload.keys())
            assert not present, (
                f"{manifest_path} contains retired scope keys: "
                f"{sorted(present)}"
            )


def _unit_test_devcovuser_new_modules_overlay_uses_custom_mirror() -> None:
    """devcovuser should mirror only devcovenant/custom under tests."""
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "devcovuser"
        / "devcovuser.yaml"
    )
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    overlays = payload.get("policy_overlays", {})
    policy_overlay = overlays.get("modules-need-tests", {})
    mirror_roots = policy_overlay.get("mirror_roots", [])
    assert mirror_roots == ["devcovenant/custom=>tests/devcovenant/custom"]
    force_include = policy_overlay.get("force_include_globs", [])
    assert "devcovenant/custom/**" in force_include


def _unit_test_devcovrepo_new_modules_overlay_uses_full_mirror() -> None:
    """devcovrepo should mirror full devcovenant tree into tests."""
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = (
        repo_root
        / "devcovenant"
        / "custom"
        / "profiles"
        / "devcovrepo"
        / "devcovrepo.yaml"
    )
    payload = profiles.load_profile(manifest_path)
    overlays = payload.get("policy_overlays", {})
    policy_overlay = overlays.get("modules-need-tests", {})
    mirror_roots = policy_overlay.get("mirror_roots", [])
    assert mirror_roots == ["devcovenant=>tests/devcovenant"]
    assert policy_overlay.get("watch_dirs", []) == ["tests"]
    assert policy_overlay.get("tests_watch_dirs", []) == ["tests"]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_load_profile_registry_merges_core_and_custom(self):
        """Run test_load_profile_registry_merges_core_and_custom."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_load_profile_registry_merges_core_and_custom(
                tmp_path=tmp_path
            )

    def test_list_profiles_sorts_registry(self):
        """Run test_list_profiles_sorts_registry."""
        _unit_test_list_profiles_sorts_registry()

    def test_resolve_profile_suffixes_ignores_placeholders(self):
        """Run test_resolve_profile_suffixes_ignores_placeholders."""
        _unit_test_resolve_profile_suffixes_ignores_placeholders()

    def test_profile_overlays_reference_known_policies(self):
        """Run test_profile_overlays_reference_known_policies."""
        _unit_test_profile_overlays_reference_known_policies()

    def test_profiles_have_assets_unless_exempt(self):
        """Run test_profiles_have_assets_unless_exempt."""
        _unit_test_profiles_have_assets_unless_exempt()

    def test_profiles_do_not_define_activation_scope_keys(self):
        """Run test_profiles_do_not_define_activation_scope_keys."""
        _unit_test_profiles_do_not_define_activation_scope_keys()

    def test_devcovuser_new_modules_overlay_uses_custom_mirror(self):
        """Run test_devcovuser_new_modules_overlay_uses_custom_mirror."""
        _unit_test_devcovuser_new_modules_overlay_uses_custom_mirror()

    def test_devcovrepo_new_modules_overlay_uses_full_mirror(self):
        """Run test_devcovrepo_new_modules_overlay_uses_full_mirror."""
        _unit_test_devcovrepo_new_modules_overlay_uses_full_mirror()
