"""Regression tests for the installer manifest helpers."""

import json
import shutil
from pathlib import Path

from devcovenant.core import install


def test_install_records_manifest_with_core_excluded(tmp_path: Path) -> None:
    """Installer run on an empty repo records its manifest and options."""
    target = tmp_path / "repo"
    target.mkdir()
    try:
        install.main(["--target", str(target), "--mode", "empty"])
        manifest = target / install.MANIFEST_PATH
        assert manifest.exists()
        manifest_data = json.loads(manifest.read_text())
        assert manifest_data["options"]["devcov_core_include"] is False
        assert "core" in manifest_data["installed"]
        assert "docs" in manifest_data["installed"]
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_update_core_config_text_toggles_include_flag() -> None:
    """Toggling the include flag rewrites the config block."""
    original = "# comment\n"
    updated, changed = install._update_core_config_text(
        original,
        include_core=True,
        core_paths=["devcovenant/core"],
    )
    assert changed
    assert "devcov_core_include: true" in updated
    assert "devcov_core_paths" in updated

    updated_again, changed_again = install._update_core_config_text(
        updated,
        include_core=False,
        core_paths=["devcovenant/core"],
    )
    assert changed_again
    assert "devcov_core_include: false" in updated_again
