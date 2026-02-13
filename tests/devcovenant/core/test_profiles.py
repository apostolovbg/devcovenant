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
    exempt = {"global", "devcovuser"}
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


def _unit_test_language_profile_translator_declarations_normalize() -> None:
    """Language profiles should normalize translator declaration fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        manifest_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "python"
            / "python.yaml"
        )
        _write_yaml(
            manifest_path,
            """
            version: 1
            profile: python
            category: language
            translators:
              - id: Python
                extensions: [py, ".PYI", ".Pyw", ".py"]
                can_handle:
                  strategy: MODULE_FUNCTION
                  entrypoint: devcovenant.core.translators.python.can_handle
                translate:
                  strategy: MODULE_FUNCTION
                  entrypoint: devcovenant.core.translators.python.translate
            """,
        )
        registry = profiles.discover_profiles(repo_root)
        translators = registry["python"]["translators"]
        assert len(translators) == 1
        declaration = translators[0]
        assert declaration["id"] == "python"
        assert declaration["extensions"] == [".py", ".pyi", ".pyw"]
        assert declaration["can_handle"]["strategy"] == "module_function"
        assert declaration["translate"]["strategy"] == "module_function"


def _unit_test_non_language_profile_translators_raise() -> None:
    """Only language profiles can carry translator declarations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        manifest_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "react"
            / "react.yaml"
        )
        _write_yaml(
            manifest_path,
            """
            version: 1
            profile: react
            category: framework
            translators:
              - id: javascript
                extensions: [".js"]
                can_handle:
                  strategy: module_function
                  entrypoint: translator.javascript.can_handle
                translate:
                  strategy: module_function
                  entrypoint: translator.javascript.translate
            """,
        )
        with unittest.TestCase().assertRaises(ValueError):
            profiles.discover_profiles(repo_root)


def _unit_test_translator_declaration_shape_is_validated() -> None:
    """Translator declarations must provide required fields."""
    invalid_manifests = [
        """
        version: 1
        profile: python
        category: language
        translators:
          - id: python
            extensions: [".py"]
            translate:
              strategy: module_function
              entrypoint: devcovenant.core.translators.python.translate
        """,
        """
        version: 1
        profile: python
        category: language
        translators:
          - id: python
            extensions: [".py"]
            can_handle:
              strategy: module_function
              entrypoint: devcovenant.core.translators.python.can_handle
            translate:
              strategy: module_function
        """,
        """
        version: 1
        profile: python
        category: language
        translators:
          - id: ""
            extensions: [".py"]
            can_handle:
              strategy: module_function
              entrypoint: devcovenant.core.translators.python.can_handle
            translate:
              strategy: module_function
              entrypoint: devcovenant.core.translators.python.translate
        """,
    ]
    for content in invalid_manifests:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            manifest_path = (
                repo_root
                / "devcovenant"
                / "core"
                / "profiles"
                / "python"
                / "python.yaml"
            )
            _write_yaml(manifest_path, content)
            with unittest.TestCase().assertRaises(ValueError):
                profiles.discover_profiles(repo_root)


def _unit_test_profile_registry_load_validates_translator_schema() -> None:
    """Loading registry metadata should validate translator declarations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "profile_registry.yaml"
        )
        _write_yaml(
            registry_path,
            """
            generated_at: "2026-02-13T00:00:00+00:00"
            profiles:
              react:
                category: framework
                translators:
                  - id: javascript
                    extensions: [".js"]
                    can_handle:
                      strategy: module_function
                      entrypoint: translator.javascript.can_handle
                    translate:
                      strategy: module_function
                      entrypoint: translator.javascript.translate
            """,
        )
        with unittest.TestCase().assertRaises(ValueError):
            profiles.load_profile_registry(repo_root)


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

    def test_language_profile_translator_declarations_normalize(self):
        """Run test_language_profile_translator_declarations_normalize."""
        _unit_test_language_profile_translator_declarations_normalize()

    def test_non_language_profile_translators_raise(self):
        """Run test_non_language_profile_translators_raise."""
        _unit_test_non_language_profile_translators_raise()

    def test_translator_declaration_shape_is_validated(self):
        """Run test_translator_declaration_shape_is_validated."""
        _unit_test_translator_declaration_shape_is_validated()

    def test_profile_registry_load_validates_translator_schema(self):
        """Run test_profile_registry_load_validates_translator_schema."""
        _unit_test_profile_registry_load_validates_translator_schema()

    def test_devcovuser_new_modules_overlay_uses_custom_mirror(self):
        """Run test_devcovuser_new_modules_overlay_uses_custom_mirror."""
        _unit_test_devcovuser_new_modules_overlay_uses_custom_mirror()

    def test_devcovrepo_new_modules_overlay_uses_full_mirror(self):
        """Run test_devcovrepo_new_modules_overlay_uses_full_mirror."""
        _unit_test_devcovrepo_new_modules_overlay_uses_full_mirror()
