"""Regression tests for the installer manifest helpers."""

import re
import shutil
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
        assert manifest_data["options"]["devcov_core_include"] is False
        assert "core" in manifest_data["installed"]
        assert manifest_data["installed"]["docs"] == []
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


def test_apply_profile_policy_state_does_not_migrate_legacy_keys(
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


def test_install_preserves_readme_content(tmp_path: Path) -> None:
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


def test_install_creates_spec_and_plan(tmp_path: Path) -> None:
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


def test_update_respects_doc_assets_user_docs(tmp_path: Path) -> None:
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    pyproject = target / "pyproject.toml"
    assert pyproject.exists()
    assert f'version = "{version_value}"' in pyproject.read_text(
        encoding="utf-8"
    )


def test_disable_policy_sets_enabled_false(tmp_path: Path) -> None:
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


def test_policy_mode_overwrite_replaces_policy_block(tmp_path: Path) -> None:
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


def test_update_defaults_preserve_policy_blocks(tmp_path: Path) -> None:
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


def test_update_removes_legacy_root_paths(tmp_path: Path) -> None:
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


def test_upgrade_refreshes_core_files(tmp_path: Path) -> None:
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


def test_update_writes_manifest(tmp_path: Path) -> None:
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert not (target / "THIRD_PARTY_LICENSES.md").exists()
    assert not (target / "licenses" / "README.md").exists()


def test_stock_policy_descriptor_assets_are_profile_owned(
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


def test_policy_assets_skip_when_policy_state_disabled(
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


def test_custom_policy_assets_install_via_fallback(tmp_path: Path) -> None:
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


def test_custom_policy_assets_fallback_can_be_disabled(
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    assert (target / "requirements.in").exists()
    assert (target / "requirements.lock").exists()


def test_profile_assets_skip_when_profile_inactive(
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
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))
    config_text = (target / "devcovenant" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "dependency-license-sync" in config_text
    assert "dependency_files:" in config_text
    assert "requirements.in" in config_text
