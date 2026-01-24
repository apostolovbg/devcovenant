"""Profile catalog helpers for DevCovenant."""

import textwrap
from pathlib import Path

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_load_profile_catalog_merges_core_and_custom(tmp_path: Path) -> None:
    """Custom profile entries override core catalog data."""
    core_yaml = """
    profiles:
      python:
        suffixes: [".py"]
      docs:
        suffixes: ["__none__"]
    """
    custom_yaml = """
    profiles:
      python:
        suffixes: [".py", ".pyi"]
      lua:
        suffixes: [".lua"]
    """
    core_catalog = tmp_path / "devcovenant" / "core" / "profile_catalog.yaml"
    custom_catalog = (
        tmp_path / "devcovenant" / "custom" / "profile_catalog.yaml"
    )
    _write_yaml(core_catalog, core_yaml)
    _write_yaml(custom_catalog, custom_yaml)

    custom_templates = (
        tmp_path / "devcovenant" / "custom" / "templates" / "profiles" / "zig"
    )
    custom_templates.mkdir(parents=True, exist_ok=True)

    catalog = profiles.load_profile_catalog(tmp_path)

    assert catalog["python"]["suffixes"] == [".py", ".pyi"]
    assert "lua" in catalog
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
