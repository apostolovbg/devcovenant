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
        install.main(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.1.0",
                "--citation-mode",
                "skip",
            ]
        )
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


def test_install_preserves_readme_content(tmp_path: Path) -> None:
    """Existing README content should remain after install."""
    target = tmp_path / "repo"
    target.mkdir()
    readme = target / "README.md"
    readme.write_text("# Example\nCustom content.\n", encoding="utf-8")
    install.main(
        [
            "--target",
            str(target),
            "--mode",
            "existing",
            "--version",
            "1.2.3",
            "--citation-mode",
            "skip",
        ]
    )
    updated = readme.read_text(encoding="utf-8")
    assert "Custom content." in updated
    assert "**Last Updated:**" in updated
    assert install.BLOCK_BEGIN in updated


def test_install_disables_citation_when_skipped(tmp_path: Path) -> None:
    """CITATION enforcement should be disabled when skipped."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        [
            "--target",
            str(target),
            "--mode",
            "empty",
            "--version",
            "0.3.0",
            "--citation-mode",
            "skip",
        ]
    )
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "citation_file: __none__" in agents_text
