"""Tests for custom profile manifests."""

import tempfile
import textwrap
import unittest
from pathlib import Path

from devcovenant.core import profiles


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML content to a path, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def _unit_test_custom_profile_manifest_is_discovered(tmp_path: Path) -> None:
    """Profiles added in the custom tree appear in the registry."""
    custom_manifest = (
        tmp_path
        / "devcovenant"
        / "custom"
        / "profiles"
        / "customlang"
        / "customlang.yaml"
    )
    _write_yaml(
        custom_manifest,
        """
        version: 1
        profile: customlang
        suffixes: [".cl"]
        """,
    )

    registry = profiles.load_profile_registry(tmp_path)

    assert "customlang" in registry
    assert registry["customlang"]["source"] == "custom"
    assert registry["customlang"]["suffixes"] == [".cl"]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_custom_profile_manifest_is_discovered(self):
        """Run test_custom_profile_manifest_is_discovered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_custom_profile_manifest_is_discovered(tmp_path=tmp_path)
