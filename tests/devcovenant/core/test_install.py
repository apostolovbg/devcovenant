"""Regression tests for the installer manifest helpers."""

import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core import deploy, install
from devcovenant.core import manifest as manifest_module
from devcovenant.core import update, upgrade


def _with_skip_refresh(args: list[str]) -> list[str]:
    """Append the skip-refresh flag to speed up installer tests."""
    return [*args, "--skip-refresh"]


def _mark_config_ready(target: Path) -> None:
    """Set install.generic_config to false so deploy can run."""
    config_path = target / "devcovenant" / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"generic_config:\s*true",
        "generic_config: false",
        text,
    )
    config_path.write_text(updated, encoding="utf-8")


def _set_custom_policy_asset_fallback(target: Path, enabled: bool) -> None:
    """Set install.allow_custom_policy_asset_fallback in config.yaml."""
    config_path = target / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    install_cfg = payload.get("install", {})
    if not isinstance(install_cfg, dict):
        install_cfg = {}
    install_cfg["allow_custom_policy_asset_fallback"] = enabled
    payload["install"] = install_cfg
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _set_doc_assets(
    target: Path, *, autogen: list[str], user: list[str]
) -> None:
    """Set doc_assets.autogen and doc_assets.user in config.yaml."""
    config_path = target / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    payload["doc_assets"] = {
        "autogen": list(autogen),
        "user": list(user),
    }
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _set_version_override(target: Path, override: str | None) -> None:
    """Set version.override in config.yaml for fallback testing."""
    config_path = target / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    version_block = payload.get("version", {})
    if not isinstance(version_block, dict):
        version_block = {}
    version_block["override"] = override
    payload["version"] = version_block
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _write_custom_policy_with_asset(target: Path) -> None:
    """Create a custom policy descriptor with a fallback asset."""
    policy_dir = (
        target / "devcovenant" / "custom" / "policies" / "custom_asset_policy"
    )
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "custom_asset_policy.py").write_text(
        "from devcovenant.core.base import PolicyCheck\n\n"
        "class CustomAssetPolicyCheck(PolicyCheck):\n"
        "    policy_id = 'custom-asset-policy'\n\n"
        "    def check(self, context):\n"
        "        return []\n",
        encoding="utf-8",
    )
    descriptor = {
        "id": "custom-asset-policy",
        "text": "Custom policy asset fallback test.",
        "assets": [
            {
                "path": "CUSTOM_POLICY_ASSET.md",
                "template": "CUSTOM_POLICY_ASSET.md",
                "mode": "replace",
            }
        ],
        "metadata": {
            "id": "custom-asset-policy",
            "enabled": "true",
            "severity": "warning",
            "auto_fix": "false",
            "custom": "true",
        },
    }
    (policy_dir / "custom_asset_policy.yaml").write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )
    assets_dir = policy_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "CUSTOM_POLICY_ASSET.md").write_text(
        "custom fallback asset\n",
        encoding="utf-8",
    )


def _unit_test_install_records_manifest_with_core_excluded(
    tmp_path: Path,
) -> None:
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
        assert manifest_data["options"]["devcov_core_include"] is False
        assert "core" in manifest_data["installed"]
        assert manifest_data["installed"]["docs"] == []
    finally:
        shutil.rmtree(target, ignore_errors=True)


def _unit_test_install_no_touch_only_copies_package(tmp_path: Path) -> None:
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


def _unit_test_update_core_config_text_toggles_include_flag() -> None:
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


def _unit_test_apply_profile_policy_state_does_not_migrate_legacy_keys(
    tmp_path: Path,
) -> None:
    """Legacy activation keys are removed without changing policy_state."""
    config_dir = tmp_path / "devcovenant"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(
        (
            "policy_state:\n"
            "  managed-environment: false\n"
            "autogen_disable:\n"
            "  - raw-string-escapes\n"
            "manual_force_enable:\n"
            "  - managed-environment\n"
        ),
        encoding="utf-8",
    )

    changed = install._apply_profile_policy_state(tmp_path, {})

    assert changed
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    assert payload.get("policy_state") == {"managed-environment": False}
    assert "autogen_disable" not in payload
    assert "manual_force_enable" not in payload


def _unit_test_install_preserves_readme_content(tmp_path: Path) -> None:
    """Existing README content should remain after update."""
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
                "1.2.3",
            ]
        )
    )
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


def _unit_test_install_creates_spec_and_plan(tmp_path: Path) -> None:
    """SPEC and PLAN are generated when deploying managed docs."""
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert (target / "SPEC.md").exists()
    assert (target / "PLAN.md").exists()


def _unit_test_update_respects_doc_assets_user_docs(tmp_path: Path) -> None:
    """Update should skip docs listed under doc_assets.user."""
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
    _set_doc_assets(
        target,
        autogen=["README.md", "SPEC.md", "PLAN.md"],
        user=["README.md"],
    )
    readme_path = target / "README.md"
    custom_readme = "# User README\n\nKeep this exactly.\n"
    readme_path.write_text(custom_readme, encoding="utf-8")

    update.main(_with_skip_refresh(["--target", str(target)]))

    updated_readme = readme_path.read_text(encoding="utf-8")
    assert updated_readme == custom_readme
    assert install.BLOCK_BEGIN not in updated_readme


def _unit_test_profile_assets_use_target_version(tmp_path: Path) -> None:
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    pyproject = target / "pyproject.toml"
    assert pyproject.exists()
    assert f'version = "{version_value}"' in pyproject.read_text(
        encoding="utf-8"
    )


def _unit_test_update_force_config_preserves_version_and_license_by_default(
    tmp_path: Path,
) -> None:
    """Force-config should preserve VERSION/LICENSE on inherit defaults."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    version_path = target / "devcovenant" / "VERSION"
    license_path = target / "LICENSE"
    version_path.write_text("9.9.9\n", encoding="utf-8")
    license_path.write_text("custom license\n", encoding="utf-8")

    update.main(
        _with_skip_refresh(["--target", str(target), "--force-config"])
    )

    assert version_path.read_text(encoding="utf-8") == "9.9.9\n"
    assert license_path.read_text(encoding="utf-8") == "custom license\n"


def _unit_test_update_preserve_creates_missing_version_and_license(
    tmp_path: Path,
) -> None:
    """Preserve mode should still bootstrap missing VERSION/LICENSE files."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _set_version_override(target, "2.3.4")
    version_path = target / "devcovenant" / "VERSION"
    if version_path.exists():
        version_path.unlink()
    license_path = target / "LICENSE"
    if license_path.exists():
        license_path.unlink()

    update.main(_with_skip_refresh(["--target", str(target)]))

    assert version_path.read_text(encoding="utf-8") == "2.3.4\n"
    assert license_path.exists()
    assert license_path.read_text(encoding="utf-8").startswith(
        "Project Version: 2.3.4\n"
    )


def _unit_test_update_overwrite_uses_pyproject_when_existing_version_invalid(
    tmp_path: Path,
) -> None:
    """Invalid existing versions should fall back to pyproject metadata."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _set_version_override(target, None)
    version_path = target / "devcovenant" / "VERSION"
    version_path.write_text("not-a-version\n", encoding="utf-8")
    (target / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "3.4.5"\n',
        encoding="utf-8",
    )

    update.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version-mode",
                "overwrite",
            ]
        )
    )

    assert version_path.read_text(encoding="utf-8") == "3.4.5\n"


def _unit_test_update_cli_version_overrides_other_version_sources(
    tmp_path: Path,
) -> None:
    """CLI --version must win over config override and pyproject fallback."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _set_version_override(target, "2.0.0")
    (target / "devcovenant" / "VERSION").write_text(
        "1.0.0\n",
        encoding="utf-8",
    )
    (target / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "3.0.0"\n',
        encoding="utf-8",
    )

    update.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version-mode",
                "overwrite",
                "--version",
                "4.5.6",
            ]
        )
    )

    assert (target / "devcovenant" / "VERSION").read_text(
        encoding="utf-8"
    ) == "4.5.6\n"


def _unit_test_deploy_defaults_preserve_version_and_license(
    tmp_path: Path,
) -> None:
    """Deploy defaults should preserve existing VERSION and LICENSE."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _mark_config_ready(target)
    _set_version_override(target, "2.3.4")
    version_path = target / "devcovenant" / "VERSION"
    license_path = target / "LICENSE"
    version_path.write_text("9.9.9\n", encoding="utf-8")
    license_path.write_text("custom license\n", encoding="utf-8")

    deploy.main(_with_skip_refresh(["--target", str(target)]))

    assert version_path.read_text(encoding="utf-8") == "9.9.9\n"
    assert license_path.read_text(encoding="utf-8") == "custom license\n"


def _unit_test_deploy_preserve_bootstraps_missing_version_and_license(
    tmp_path: Path,
) -> None:
    """Deploy preserve mode should bootstrap missing VERSION and LICENSE."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _mark_config_ready(target)
    _set_version_override(target, "2.3.4")
    version_path = target / "devcovenant" / "VERSION"
    license_path = target / "LICENSE"
    if version_path.exists():
        version_path.unlink()
    if license_path.exists():
        license_path.unlink()

    deploy.main(_with_skip_refresh(["--target", str(target)]))

    assert version_path.read_text(encoding="utf-8") == "2.3.4\n"
    assert license_path.exists()
    assert license_path.read_text(encoding="utf-8").startswith(
        "Project Version: 2.3.4\n"
    )


def _unit_test_deploy_overwrite_uses_pyproject_for_invalid_version(
    tmp_path: Path,
) -> None:
    """Deploy overwrite mode should use pyproject when VERSION is invalid."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _mark_config_ready(target)
    _set_version_override(target, None)
    version_path = target / "devcovenant" / "VERSION"
    version_path.write_text("not-a-version\n", encoding="utf-8")
    (target / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "3.4.5"\n',
        encoding="utf-8",
    )

    deploy.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version-mode",
                "overwrite",
            ]
        )
    )

    assert version_path.read_text(encoding="utf-8") == "3.4.5\n"


def _unit_test_upgrade_defaults_preserve_version_and_license(
    tmp_path: Path,
) -> None:
    """Upgrade defaults should preserve existing VERSION and LICENSE."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    version_path = target / "devcovenant" / "VERSION"
    license_path = target / "LICENSE"
    version_path.write_text("0.0.2\n", encoding="utf-8")
    license_path.write_text("custom license\n", encoding="utf-8")

    upgrade.main(_with_skip_refresh(["--target", str(target)]))

    assert version_path.read_text(encoding="utf-8") == "0.0.2\n"
    assert license_path.read_text(encoding="utf-8") == "custom license\n"


def _unit_test_upgrade_overwrite_honors_cli_version(
    tmp_path: Path,
) -> None:
    """Upgrade overwrite mode should honor explicit CLI version."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    _set_version_override(target, "2.0.0")
    (target / "devcovenant" / "VERSION").write_text(
        "0.0.1\n",
        encoding="utf-8",
    )
    (target / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "3.0.0"\n',
        encoding="utf-8",
    )

    upgrade.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version-mode",
                "overwrite",
                "--version",
                "4.5.6",
            ]
        )
    )

    assert (target / "devcovenant" / "VERSION").read_text(
        encoding="utf-8"
    ) == "4.5.6\n"


def _unit_test_upgrade_skip_keeps_existing_version(tmp_path: Path) -> None:
    """Upgrade with --version-mode skip should keep VERSION unchanged."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            ["--target", str(target), "--mode", "empty", "--version", "0.5.0"]
        )
    )
    version_path = target / "devcovenant" / "VERSION"
    version_path.write_text("0.0.3\n", encoding="utf-8")

    upgrade.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--version-mode",
                "skip",
            ]
        )
    )

    assert version_path.read_text(encoding="utf-8") == "0.0.3\n"


def _unit_test_disable_policy_sets_enabled_false(tmp_path: Path) -> None:
    """Disable-policy should set enabled: false for listed policies."""
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "id: changelog-coverage" in agents_text
    assert re.search(
        r"id:\s*changelog-coverage[\s\S]*?enabled:\s*false",
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
enforcement: active
enabled: true
custom: true
```

Custom policy description.
"""
    path.write_text(content, encoding="utf-8")


def _unit_test_policy_mode_preserve_keeps_policy_text(tmp_path: Path) -> None:
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
                "empty",
                "--version",
                "0.2.0",
            ]
        )
    )
    _mark_config_ready(target)
    deploy.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--policy-mode",
                "preserve",
            ]
        )
    )
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." in updated
    assert "id: version-sync" not in updated


def _unit_test_policy_mode_overwrite_replaces_policy_block(
    tmp_path: Path,
) -> None:
    """Overwrite mode should regenerate policy sections from registry data."""
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
                "empty",
                "--version",
                "0.2.0",
            ]
        )
    )
    _mark_config_ready(target)
    deploy.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--policy-mode",
                "overwrite",
            ]
        )
    )
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." not in updated
    assert "id: version-sync" in updated


def _unit_test_update_defaults_preserve_policy_blocks(tmp_path: Path) -> None:
    """Update should preserve policy blocks by default."""
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
                "0.1.0",
            ]
        )
    )
    agents_path = target / "AGENTS.md"
    _write_custom_agents(agents_path)
    update.main(_with_skip_refresh(["--target", str(target)]))
    updated = agents_path.read_text(encoding="utf-8")
    assert "Custom policy description." in updated
    assert "id: version-sync" not in updated


def _unit_test_update_removes_legacy_root_paths(tmp_path: Path) -> None:
    """Update should remove legacy root-level files."""
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
                "0.2.0",
            ]
        )
    )
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


def _unit_test_upgrade_refreshes_core_files(tmp_path: Path) -> None:
    """Upgrade should refresh core files from the package."""
    target = tmp_path / "repo"
    target.mkdir()
    core_dir = target / "devcovenant"
    core_dir.mkdir()
    cli_path = core_dir / "cli.py"
    cli_path.write_text("# legacy\n", encoding="utf-8")

    upgrade.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    source_root = Path(install.__file__).resolve().parents[2]
    source_cli = source_root / "devcovenant" / "cli.py"
    assert cli_path.read_text(encoding="utf-8") == source_cli.read_text(
        "utf-8"
    )


def _unit_test_update_writes_manifest(tmp_path: Path) -> None:
    """Update should refresh the install manifest for existing installs."""
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
                "0.2.0",
            ]
        )
    )
    update.main(_with_skip_refresh(["--target", str(target)]))

    manifest_path = manifest_module.manifest_path(target)
    assert manifest_path.exists()
    manifest = manifest_module.load_manifest(target)
    assert manifest
    assert manifest.get("mode") == "update"


def _unit_test_policy_assets_skip_when_disabled(tmp_path: Path) -> None:
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "THIRD_PARTY_LICENSES.md").exists()
    assert not (target / "licenses" / "README.md").exists()


def _unit_test_stock_policy_descriptor_assets_are_profile_owned(
    tmp_path: Path,
) -> None:
    """Core policy descriptor assets are not installed directly."""
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
            ]
        )
    )
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "THIRD_PARTY_LICENSES.md").exists()
    assert not (target / "licenses" / "README.md").exists()


def _unit_test_policy_assets_skip_when_policy_state_disabled(
    tmp_path: Path,
) -> None:
    """Config policy_state must disable policy assets before refresh."""
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
            ]
        )
    )
    config_path = target / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    state = payload.get("policy_state", {})
    if not isinstance(state, dict):
        state = {}
    state["dependency-license-sync"] = False
    payload["policy_state"] = state
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "THIRD_PARTY_LICENSES.md").exists()
    assert not (target / "licenses" / "README.md").exists()


def _unit_test_custom_policy_assets_install_via_fallback(
    tmp_path: Path,
) -> None:
    """Custom policy descriptor assets install without profile wiring."""
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
            ]
        )
    )
    _write_custom_policy_with_asset(target)
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    asset_path = target / "CUSTOM_POLICY_ASSET.md"
    assert asset_path.exists()
    assert "custom fallback asset" in asset_path.read_text(encoding="utf-8")


def _unit_test_custom_policy_assets_fallback_can_be_disabled(
    tmp_path: Path,
) -> None:
    """install.allow_custom_policy_asset_fallback disables fallback assets."""
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
            ]
        )
    )
    _write_custom_policy_with_asset(target)
    _set_custom_policy_asset_fallback(target, False)
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "CUSTOM_POLICY_ASSET.md").exists()


def _unit_test_profile_assets_installed_for_active_profiles(
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert (target / "requirements.in").exists()
    assert (target / "requirements.lock").exists()


def _unit_test_profile_assets_skip_when_profile_inactive(
    tmp_path: Path,
) -> None:
    """Inactive profiles should not install their assets."""
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
                "0.7.2",
            ]
        )
    )
    config_dir = target / "devcovenant"
    config = config_dir / "config.yaml"
    config.write_text(
        "profiles:\n  active:\n    - docs\n",
        encoding="utf-8",
    )
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "requirements.in").exists()
    assert not (target / "requirements.lock").exists()


def _unit_test_profile_overlays_update_policy_config(
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    config_text = (target / "devcovenant" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "dependency-license-sync" in config_text
    assert "dependency_files:" in config_text
    assert "requirements.in" in config_text


def _unit_test_tests_mirror_prunes_empty_stale_policy_dirs(
    tmp_path: Path,
) -> None:
    """Mirror sync should drop empty stale policy dirs only."""
    target = tmp_path / "repo"
    (target / "devcovenant" / "core" / "policies" / "line_length_limit").mkdir(
        parents=True
    )
    (target / "devcovenant" / "core" / "profiles" / "python").mkdir(
        parents=True
    )
    (target / "devcovenant" / "custom" / "policies" / "readme_sync").mkdir(
        parents=True
    )
    (target / "devcovenant" / "custom" / "profiles" / "devcovrepo").mkdir(
        parents=True
    )

    stale_empty = (
        target
        / "tests"
        / "devcovenant"
        / "core"
        / "policies"
        / "removed_policy"
    )
    stale_empty.mkdir(parents=True)
    stale_nonempty = (
        target
        / "tests"
        / "devcovenant"
        / "core"
        / "policies"
        / "manual_policy"
    )
    stale_nonempty.mkdir(parents=True)
    (stale_nonempty / ".keep").write_text("keep\n", encoding="utf-8")

    install._ensure_tests_mirror(target, include_core=True)

    assert not stale_empty.exists()
    assert stale_nonempty.exists()
    assert (
        target
        / "tests"
        / "devcovenant"
        / "core"
        / "policies"
        / "line_length_limit"
    ).exists()
    assert (
        target
        / "tests"
        / "devcovenant"
        / "custom"
        / "policies"
        / "readme_sync"
    ).exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_install_records_manifest_with_core_excluded(self):
        """Run test_install_records_manifest_with_core_excluded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_install_records_manifest_with_core_excluded(
                tmp_path=tmp_path
            )

    def test_install_no_touch_only_copies_package(self):
        """Run test_install_no_touch_only_copies_package."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_install_no_touch_only_copies_package(tmp_path=tmp_path)

    def test_update_core_config_text_toggles_include_flag(self):
        """Run test_update_core_config_text_toggles_include_flag."""
        _unit_test_update_core_config_text_toggles_include_flag()

    def test_apply_profile_policy_state_does_not_migrate_legacy_keys(self):
        """Run test_apply_profile_policy_state_does_not_migrate_legacy_keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_apply_profile_policy_state_does_not_migrate_legacy_keys(
                tmp_path=tmp_path
            )

    def test_install_preserves_readme_content(self):
        """Run test_install_preserves_readme_content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_install_preserves_readme_content(tmp_path=tmp_path)

    def test_install_creates_spec_and_plan(self):
        """Run test_install_creates_spec_and_plan."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_install_creates_spec_and_plan(tmp_path=tmp_path)

    def test_update_respects_doc_assets_user_docs(self):
        """Run test_update_respects_doc_assets_user_docs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_respects_doc_assets_user_docs(tmp_path=tmp_path)

    def test_profile_assets_use_target_version(self):
        """Run test_profile_assets_use_target_version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_profile_assets_use_target_version(tmp_path=tmp_path)

    def test_update_force_config_preserves_version_and_license_by_default(
        self,
    ):
        """Run wrapper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            test_case = globals()[
                "_unit_test_update_force_config_"
                "preserves_version_and_license_by_default"
            ]
            test_case(tmp_path=tmp_path)

    def test_update_preserve_creates_missing_version_and_license(self):
        """Run test_update_preserve_creates_missing_version_and_license."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_preserve_creates_missing_version_and_license(
                tmp_path=tmp_path
            )

    def test_update_overwrite_uses_pyproject_when_existing_version_invalid(
        self,
    ):
        """Run wrapper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            test_case = globals()[
                "_unit_test_update_overwrite_uses_pyproject_"
                "when_existing_version_invalid"
            ]
            test_case(tmp_path=tmp_path)

    def test_update_cli_version_overrides_other_version_sources(self):
        """Run test_update_cli_version_overrides_other_version_sources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_cli_version_overrides_other_version_sources(
                tmp_path=tmp_path
            )

    def test_deploy_defaults_preserve_version_and_license(self):
        """Run test_deploy_defaults_preserve_version_and_license."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_deploy_defaults_preserve_version_and_license(
                tmp_path=tmp_path
            )

    def test_deploy_preserve_bootstraps_missing_version_and_license(self):
        """Run test_deploy_preserve_bootstraps_missing_version_and_license."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_deploy_preserve_bootstraps_missing_version_and_license(
                tmp_path=tmp_path
            )

    def test_deploy_overwrite_uses_pyproject_for_invalid_version(self):
        """Run test_deploy_overwrite_uses_pyproject_for_invalid_version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_deploy_overwrite_uses_pyproject_for_invalid_version(
                tmp_path=tmp_path
            )

    def test_upgrade_defaults_preserve_version_and_license(self):
        """Run test_upgrade_defaults_preserve_version_and_license."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_upgrade_defaults_preserve_version_and_license(
                tmp_path=tmp_path
            )

    def test_upgrade_overwrite_honors_cli_version(self):
        """Run test_upgrade_overwrite_honors_cli_version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_upgrade_overwrite_honors_cli_version(tmp_path=tmp_path)

    def test_upgrade_skip_keeps_existing_version(self):
        """Run test_upgrade_skip_keeps_existing_version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_upgrade_skip_keeps_existing_version(tmp_path=tmp_path)

    def test_disable_policy_sets_enabled_false(self):
        """Run test_disable_policy_sets_enabled_false."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_disable_policy_sets_enabled_false(tmp_path=tmp_path)

    def test_policy_mode_preserve_keeps_policy_text(self):
        """Run test_policy_mode_preserve_keeps_policy_text."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_mode_preserve_keeps_policy_text(
                tmp_path=tmp_path
            )

    def test_policy_mode_overwrite_replaces_policy_block(self):
        """Run test_policy_mode_overwrite_replaces_policy_block."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_mode_overwrite_replaces_policy_block(
                tmp_path=tmp_path
            )

    def test_update_defaults_preserve_policy_blocks(self):
        """Run test_update_defaults_preserve_policy_blocks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_defaults_preserve_policy_blocks(
                tmp_path=tmp_path
            )

    def test_update_removes_legacy_root_paths(self):
        """Run test_update_removes_legacy_root_paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_removes_legacy_root_paths(tmp_path=tmp_path)

    def test_upgrade_refreshes_core_files(self):
        """Run test_upgrade_refreshes_core_files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_upgrade_refreshes_core_files(tmp_path=tmp_path)

    def test_update_writes_manifest(self):
        """Run test_update_writes_manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_update_writes_manifest(tmp_path=tmp_path)

    def test_policy_assets_skip_when_disabled(self):
        """Run test_policy_assets_skip_when_disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_assets_skip_when_disabled(tmp_path=tmp_path)

    def test_stock_policy_descriptor_assets_are_profile_owned(self):
        """Run test_stock_policy_descriptor_assets_are_profile_owned."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_stock_policy_descriptor_assets_are_profile_owned(
                tmp_path=tmp_path
            )

    def test_policy_assets_skip_when_policy_state_disabled(self):
        """Run test_policy_assets_skip_when_policy_state_disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_assets_skip_when_policy_state_disabled(
                tmp_path=tmp_path
            )

    def test_custom_policy_assets_install_via_fallback(self):
        """Run test_custom_policy_assets_install_via_fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_custom_policy_assets_install_via_fallback(
                tmp_path=tmp_path
            )

    def test_custom_policy_assets_fallback_can_be_disabled(self):
        """Run test_custom_policy_assets_fallback_can_be_disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_custom_policy_assets_fallback_can_be_disabled(
                tmp_path=tmp_path
            )

    def test_profile_assets_installed_for_active_profiles(self):
        """Run test_profile_assets_installed_for_active_profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_profile_assets_installed_for_active_profiles(
                tmp_path=tmp_path
            )

    def test_profile_assets_skip_when_profile_inactive(self):
        """Run test_profile_assets_skip_when_profile_inactive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_profile_assets_skip_when_profile_inactive(
                tmp_path=tmp_path
            )

    def test_profile_overlays_update_policy_config(self):
        """Run test_profile_overlays_update_policy_config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_profile_overlays_update_policy_config(tmp_path=tmp_path)

    def test_tests_mirror_prunes_empty_stale_policy_dirs(self):
        """Run test_tests_mirror_prunes_empty_stale_policy_dirs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_tests_mirror_prunes_empty_stale_policy_dirs(
                tmp_path=tmp_path
            )
