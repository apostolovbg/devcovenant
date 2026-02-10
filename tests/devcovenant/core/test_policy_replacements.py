"""Tests for policy replacement workflow in upgrades."""

import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

from devcovenant.core import manifest as manifest_module
from devcovenant.core import policy_replacements, upgrade


def _with_skip_refresh(args: list[str]) -> list[str]:
    """Append the skip-refresh flag to speed up upgrade tests."""
    return [*args, "--skip-refresh"]


def _write_agents(path: Path, enabled_value: str) -> None:
    """Write a minimal AGENTS.md file with one policy."""
    metadata = (
        "id: old-policy\n"
        "status: active\n"
        "severity: warning\n"
        "auto_fix: false\n"
        "enforcement: active\n"
        f"enabled: {enabled_value}\n"
        "custom: false\n"
    )
    text = (
        "# AGENTS\n\n"
        "## Policy: Old Policy\n\n"
        "```policy-def\n"
        f"{metadata}"
        "```\n\n"
        "Policy description.\n"
    )
    path.write_text(text, encoding="utf-8")


def _write_config_policy_state(target: Path, enabled: bool) -> None:
    """Write a config.yaml policy_state override for old-policy."""
    config_dir = target / "devcovenant"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    payload = {"policy_state": {"old-policy": enabled}}
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


@pytest.fixture
def replacement_map() -> dict[str, policy_replacements.PolicyReplacement]:
    """Return a replacement map for tests."""
    replacement = policy_replacements.PolicyReplacement(
        policy_id="old-policy",
        replaced_by="new-policy",
    )
    return {"old-policy": replacement}


def _unit_test_upgrade_migrates_replaced_policy(
    tmp_path: Path, monkeypatch, replacement_map
) -> None:
    """Enabled replaced policies should move to custom with deprecation."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_agents(agents_path, "true")

    core_scripts = target / "devcovenant" / "core" / "policies" / "old_policy"
    core_scripts.mkdir(parents=True, exist_ok=True)
    script_path = core_scripts / "old_policy.py"
    script_path.write_text("print('legacy')\n", encoding="utf-8")

    core_fixers = core_scripts / "fixers"
    core_fixers.mkdir(parents=True, exist_ok=True)
    fixer_path = core_fixers / "global.py"
    fixer_path.write_text("# fixer\n", encoding="utf-8")

    monkeypatch.setattr(
        policy_replacements,
        "load_policy_replacements",
        lambda _root: replacement_map,
    )

    upgrade.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    updated = agents_path.read_text(encoding="utf-8")
    assert "status: deprecated" in updated
    assert "custom: true" in updated

    custom_script = (
        target
        / "devcovenant"
        / "custom"
        / "policies"
        / "old_policy"
        / "old_policy.py"
    )
    assert custom_script.exists()
    assert "legacy" in custom_script.read_text(encoding="utf-8")

    custom_fixer = (
        target
        / "devcovenant"
        / "custom"
        / "policies"
        / "old_policy"
        / "fixers"
        / "global.py"
    )
    assert custom_fixer.exists()

    manifest = manifest_module.load_manifest(target)
    assert manifest
    notifications = manifest.get("notifications", [])
    assert any("old-policy" in entry["message"] for entry in notifications)


def _unit_test_upgrade_removes_disabled_replaced_policy(
    tmp_path: Path, monkeypatch, replacement_map
) -> None:
    """Disabled replaced policies should be removed entirely."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_agents(agents_path, "false")

    custom_scripts = (
        target / "devcovenant" / "custom" / "policies" / "old_policy"
    )
    custom_scripts.mkdir(parents=True, exist_ok=True)
    custom_script = custom_scripts / "old_policy.py"
    custom_script.write_text("# custom\n", encoding="utf-8")

    monkeypatch.setattr(
        policy_replacements,
        "load_policy_replacements",
        lambda _root: replacement_map,
    )

    upgrade.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    updated = agents_path.read_text(encoding="utf-8")
    assert "old-policy" not in updated
    assert not custom_script.exists()


def _unit_test_upgrade_policy_state_false_overrides_agents_enabled(
    tmp_path: Path, monkeypatch, replacement_map
) -> None:
    """Config policy_state false should remove replaced policy."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_agents(agents_path, "true")
    _write_config_policy_state(target, False)

    custom_scripts = (
        target / "devcovenant" / "custom" / "policies" / "old_policy"
    )
    custom_scripts.mkdir(parents=True, exist_ok=True)
    custom_script = custom_scripts / "old_policy.py"
    custom_script.write_text("# custom\n", encoding="utf-8")

    monkeypatch.setattr(
        policy_replacements,
        "load_policy_replacements",
        lambda _root: replacement_map,
    )

    upgrade.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    updated = agents_path.read_text(encoding="utf-8")
    assert "old-policy" not in updated
    assert not custom_script.exists()


def _unit_test_upgrade_policy_state_true_overrides_agents_disabled(
    tmp_path: Path, monkeypatch, replacement_map
) -> None:
    """Config policy_state true should migrate replaced policy."""
    target = tmp_path / "repo"
    target.mkdir()
    agents_path = target / "AGENTS.md"
    _write_agents(agents_path, "false")
    _write_config_policy_state(target, True)

    core_scripts = target / "devcovenant" / "core" / "policies" / "old_policy"
    core_scripts.mkdir(parents=True, exist_ok=True)
    script_path = core_scripts / "old_policy.py"
    script_path.write_text("print('legacy')\n", encoding="utf-8")

    monkeypatch.setattr(
        policy_replacements,
        "load_policy_replacements",
        lambda _root: replacement_map,
    )

    upgrade.main(
        _with_skip_refresh(["--target", str(target), "--version", "0.2.0"])
    )

    updated = agents_path.read_text(encoding="utf-8")
    assert "status: deprecated" in updated
    assert "custom: true" in updated

    custom_script = (
        target
        / "devcovenant"
        / "custom"
        / "policies"
        / "old_policy"
        / "old_policy.py"
    )
    assert custom_script.exists()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_upgrade_migrates_replaced_policy(self):
        """Run test_upgrade_migrates_replaced_policy."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                replacement_map_value = (
                    replacement_map.__wrapped__()
                    if hasattr(replacement_map, "__wrapped__")
                    else replacement_map()
                )
                _unit_test_upgrade_migrates_replaced_policy(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    replacement_map=replacement_map_value,
                )
        finally:
            monkeypatch.undo()

    def test_upgrade_removes_disabled_replaced_policy(self):
        """Run test_upgrade_removes_disabled_replaced_policy."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                replacement_map_value = (
                    replacement_map.__wrapped__()
                    if hasattr(replacement_map, "__wrapped__")
                    else replacement_map()
                )
                _unit_test_upgrade_removes_disabled_replaced_policy(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    replacement_map=replacement_map_value,
                )
        finally:
            monkeypatch.undo()

    def test_upgrade_policy_state_false_overrides_agents_enabled(self):
        """Run test_upgrade_policy_state_false_overrides_agents_enabled."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                replacement_map_value = (
                    replacement_map.__wrapped__()
                    if hasattr(replacement_map, "__wrapped__")
                    else replacement_map()
                )
                _unit_test_upgrade_policy_state_false_overrides_agents_enabled(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    replacement_map=replacement_map_value,
                )
        finally:
            monkeypatch.undo()

    def test_upgrade_policy_state_true_overrides_agents_disabled(self):
        """Run test_upgrade_policy_state_true_overrides_agents_disabled."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                replacement_map_value = (
                    replacement_map.__wrapped__()
                    if hasattr(replacement_map, "__wrapped__")
                    else replacement_map()
                )
                _unit_test_upgrade_policy_state_true_overrides_agents_disabled(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    replacement_map=replacement_map_value,
                )
        finally:
            monkeypatch.undo()
