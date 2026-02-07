"""Profile registry helpers for DevCovenant."""

import textwrap
from pathlib import Path

import yaml

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_load_profile_registry_merges_core_and_custom(tmp_path: Path) -> None:
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


def test_list_profiles_sorts_registry() -> None:
    """Profile list is sorted for stable prompts."""
    registry = {"lua": {}, "python": {}, "zig": {}}
    assert profiles.list_profiles(registry) == ["lua", "python", "zig"]


def test_resolve_profile_suffixes_ignores_placeholders() -> None:
    """Suffix resolution skips empty and placeholder entries."""
    registry = {
        "python": {"suffixes": [".py", ".pyi"]},
        "docs": {"suffixes": ["__none__", " "]},
    }
    resolved = profiles.resolve_profile_suffixes(registry, ["docs", "python"])
    assert resolved == [".py", ".pyi"]


def test_version_sync_listed_in_scoped_profiles() -> None:
    """Profiles that scope version-sync must list it explicitly."""
    repo_root = Path(__file__).resolve().parents[3]
    vsync_meta = yaml.safe_load(
        (
            repo_root
            / "devcovenant"
            / "core"
            / "policies"
            / "version_sync"
            / "version_sync.yaml"
        ).read_text(encoding="utf-8")
    )
    scoped = set(vsync_meta["metadata"].get("profile_scopes", []))
    registry = profiles.build_profile_registry(repo_root)
    entries = registry["profiles"] if "profiles" in registry else registry

    for name, meta in entries.items():
        if name not in scoped:
            continue
        manifest_path = repo_root / meta["path"] / f"{name}.yaml"
        manifest = profiles.load_profile(manifest_path)
        policies = set(manifest.get("policies", []))
        assert (
            "version-sync" in policies
        ), f"profile {name} (scoped for version-sync) must list version-sync"


def test_profiles_have_assets_unless_exempt() -> None:
    """Most profiles should ship assets; allow a few explicit exceptions."""
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
