"""Profile catalog helpers for DevCovenant."""

import textwrap
from pathlib import Path

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_load_profile_catalog_merges_core_and_custom(tmp_path: Path) -> None:
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
        / "profile.yaml"
    )
    custom_manifest = (
        tmp_path
        / "devcovenant"
        / "custom"
        / "profiles"
        / "python"
        / "profile.yaml"
    )
    _write_yaml(core_manifest, core_yaml)
    _write_yaml(custom_manifest, custom_yaml)

    custom_profile_dir = (
        tmp_path / "devcovenant" / "custom" / "profiles" / "zig"
    )
    custom_profile_dir.mkdir(parents=True, exist_ok=True)

    catalog = profiles.load_profile_catalog(tmp_path)

    assert catalog["python"]["suffixes"] == [".py", ".pyi"]
    assert catalog["python"]["source"] == "custom"
    assert "zig" in catalog


def test_list_profiles_sorts_catalog() -> None:
    """Profile list is sorted for stable prompts."""
    catalog = {"lua": {}, "python": {}, "zig": {}}
    assert profiles.list_profiles(catalog) == ["lua", "python", "zig"]


def test_resolve_profile_suffixes_ignores_placeholders() -> None:
    """Suffix resolution skips empty and placeholder entries."""
    catalog = {
        "python": {"suffixes": [".py", ".pyi"]},
        "docs": {"suffixes": ["__none__", " "]},
    }
    resolved = profiles.resolve_profile_suffixes(catalog, ["docs", "python"])
    assert resolved == [".py", ".pyi"]
