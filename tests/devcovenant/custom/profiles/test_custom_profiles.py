"""Tests for custom profile manifests."""

import textwrap
from pathlib import Path

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def test_custom_profile_manifest_is_discovered(tmp_path: Path) -> None:
    """Profiles added in the custom tree appear in the catalog."""
    custom_manifest = (
        tmp_path
        / "devcovenant"
        / "custom"
        / "profiles"
        / "customlang"
        / "profile.yaml"
    )
    _write_yaml(
        custom_manifest,
        """
        version: 1
        profile: customlang
        suffixes: [".cl"]
        """,
    )

    catalog = profiles.load_profile_catalog(tmp_path)

    assert "customlang" in catalog
    assert catalog["customlang"]["source"] == "custom"
    assert catalog["customlang"]["suffixes"] == [".cl"]
