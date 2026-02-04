"""Regression tests for the installer manifest helpers."""

import re
import shutil
from pathlib import Path

from devcovenant.core import install
from devcovenant.core import manifest as manifest_module
from devcovenant.core import update


def _with_skip_refresh(args: list[str]) -> list[str]:
    """Append the skip-refresh flag to speed up installer tests."""
    return [*args, "--skip-refresh"]


def test_install_records_manifest_with_core_excluded(tmp_path: Path) -> None:
    """Installer run on an empty repo records its manifest and options."""
    target = tmp_path / "repo"
    target.mkdir()
    try:
        install.main(
            _with_skip_refresh(
                [
                    "--target",
                    str(target),
                    "--mode",
                    "empty",
                    "--version",
                    "0.1.0",
                ]
            )
        )
        manifest = manifest_module.manifest_path(target)
        assert manifest.exists()
        manifest_data = manifest_module.load_manifest(target)
        assert "profiles" in manifest_data
        assert "policy_assets" in manifest_data
        assert manifest_data["options"]["devcov_core_include"] is False
        assert "core" in manifest_data["installed"]
        assert "docs" in manifest_data["installed"]
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_install_no_touch_only_copies_package(tmp_path: Path) -> None:
    """`--no-touch` installs only the DevCovenant package and manifest."""
    target = tmp_path / "repo"
    target.mkdir()
    try:
        install.main(
            _with_skip_refresh(
                [
                    "--target",
                    str(target),
                    "--mode",
                    "empty",
                    "--version",
                    "0.1.1",
                    "--no-touch",
                ]
            )
        )
        assert (target / "devcovenant").exists()
        assert not (target / "AGENTS.md").exists()
        manifest_path = manifest_module.manifest_path(target)
        assert manifest_path.exists()
        manifest_data = manifest_module.load_manifest(target)
        assert manifest_data["installed"]["docs"] == []
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
    """Existing README content should remain after update."""
    target = tmp_path / "repo"
    target.mkdir()
    readme = target / "README.md"
    readme.write_text("# Example\nCustom content.\n", encoding="utf-8")
    update.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version",
                "1.2.3",
            ]
        )
    )
    updated = readme.read_text(encoding="utf-8")
    assert "Custom content." in updated
    assert "**Last Updated:**" in updated
    assert install.BLOCK_BEGIN in updated


def test_install_creates_spec_and_plan(tmp_path: Path) -> None:
    """SPEC and PLAN are generated for every install by default."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.6.0",
            ]
        )
    )
    assert (target / "SPEC.md").exists()
    assert (target / "PLAN.md").exists()


def test_profile_assets_use_target_version(tmp_path: Path) -> None:
    """Profile assets sow the target version into templated files."""
    target = tmp_path / "repo"
    target.mkdir()
    version_value = "2.4.5"
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                version_value,
            ]
        )
    )
    pyproject = target / "pyproject.toml"
    assert pyproject.exists()
    assert f'version = "{version_value}"' in pyproject.read_text(
        encoding="utf-8"
    )


def test_disable_policy_sets_apply_false(tmp_path: Path) -> None:
    """Disable-policy should set apply: false for listed policies."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.6.1",
                "--disable-policy",
                "changelog-coverage",
            ]
        )
    )
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "id: changelog-coverage" in agents_text
    assert re.search(
        r"id:\s*changelog-coverage[\s\S]*?apply:\s*false",
        agents_text,
    )


def _write_custom_agents(path: Path) -> None:
    """Write a minimal AGENTS.md with custom policy content."""
    content = """# AGENTS
**Last Updated:** 2026-01-01
**Version:** 0.1.0

<!-- DEVCOV:BEGIN -->
Managed block A.
<!-- DEVCOV:END -->

# EDITABLE SECTION

Custom notes.

<!-- DEVCOV:BEGIN -->
Managed block B.
<!-- DEVCOV:END -->

## Policy: Custom

```policy-def
id: custom-policy
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: true
```

Custom policy description.
"""
    path.write_text(content, encoding="utf-8")


def test_policy_mode_preserve_keeps_policy_text(tmp_path: Path) -> None:
    """Preserve mode should keep policy blocks intact."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_custom_agents(agents_path)
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "existing",
                "--allow-existing",
                "--version",
                "0.2.0",
                "--policy-mode",
                "preserve",
            ]
        )
    )
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." in updated
    assert "## Policy: Version Synchronization" not in updated


def test_policy_mode_append_missing_adds_policies(tmp_path: Path) -> None:
    """Append mode should add missing policy sections from the template."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_custom_agents(agents_path)
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "existing",
                "--allow-existing",
                "--version",
                "0.2.0",
                "--policy-mode",
                "append-missing",
            ]
        )
    )
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." in updated
    assert "## Policy: Version Synchronization" in updated


def test_update_defaults_append_missing(tmp_path: Path) -> None:
    """Update should append missing policies by default."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_custom_agents(agents_path)
    version_dir = target / "devcovenant"
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    update.main(_with_skip_refresh(["--target", str(target)]))
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." in updated
    assert "## Policy: Version Synchronization" in updated


def test_update_removes_legacy_root_paths(tmp_path: Path) -> None:
    """Update should remove legacy root-level files."""
    target = tmp_path / "repo"
    target.mkdir()
    legacy = target / "devcov_check.py"
    legacy.write_text("legacy", encoding="utf-8")
    legacy_dir = target / "devcovenant" / "custom" / "fixers"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "__init__.py").write_text("legacy", encoding="utf-8")

    update.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    assert not legacy.exists()
    assert not legacy_dir.exists()


def test_update_refreshes_core_files(tmp_path: Path) -> None:
    """Update should refresh core files from the package."""
    target = tmp_path / "repo"
    target.mkdir()
    core_dir = target / "devcovenant"
    core_dir.mkdir()
    cli_path = core_dir / "cli.py"
    cli_path.write_text("# legacy\n", encoding="utf-8")

    update.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    source_root = Path(install.__file__).resolve().parents[2]
    source_cli = source_root / "devcovenant" / "cli.py"
    assert cli_path.read_text(encoding="utf-8") == source_cli.read_text(
        "utf-8"
    )


def test_update_writes_manifest(tmp_path: Path) -> None:
    """Update should refresh or create the install manifest."""
    target = tmp_path / "repo"
    target.mkdir()

    update.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    manifest_path = manifest_module.manifest_path(target)
    assert manifest_path.exists()
    manifest = manifest_module.load_manifest(target)
    assert manifest
    assert manifest.get("mode") == "update"


def test_policy_assets_skip_when_disabled(tmp_path: Path) -> None:
    """Disabled policies should not install their assets."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.7.0",
                "--disable-policy",
                "dependency-license-sync",
            ]
        )
    )
    assert not (target / "THIRD_PARTY_LICENSES.md").exists()
    assert not (target / "licenses" / "README.md").exists()


def test_profile_assets_installed_for_active_profiles(
    tmp_path: Path,
) -> None:
    """Active profile assets should be installed by default."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.7.1",
            ]
        )
    )
    assert (target / "requirements.in").exists()
    assert (target / "requirements.lock").exists()


def test_profile_assets_skip_when_profile_inactive(
    tmp_path: Path,
) -> None:
    """Inactive profiles should not install their assets."""
    target = tmp_path / "repo"
    target.mkdir()
    config_dir = target / "devcovenant"
    config_dir.mkdir(parents=True, exist_ok=True)
    config = config_dir / "config.yaml"
    config.write_text(
        "profiles:\n  active:\n    - docs\n",
        encoding="utf-8",
    )
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "existing",
                "--allow-existing",
                "--version",
                "0.7.2",
            ]
        )
    )
    assert not (target / "requirements.in").exists()
    assert not (target / "requirements.lock").exists()


def test_profile_overlays_update_policy_config(
    tmp_path: Path,
) -> None:
    """Profile overlays should populate policy config defaults."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.8.0",
            ]
        )
    )
    config_text = (target / "devcovenant" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "dependency-license-sync" in config_text
    assert "dependency_files:" in config_text
    assert "requirements.in" in config_text
