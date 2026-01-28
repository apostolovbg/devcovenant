"""Tests for policy replacement workflow in updates."""

from pathlib import Path

import pytest

from devcovenant.core import manifest as manifest_module
from devcovenant.core import policy_replacements, update


def _write_agents(path: Path, apply_value: str) -> None:
    """Write a minimal AGENTS.md file with one policy."""
    metadata = (
        "id: old-policy\n"
        "status: active\n"
        "severity: warning\n"
        "auto_fix: false\n"
        "updated: false\n"
        "enforcement: active\n"
        f"apply: {apply_value}\n"
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


@pytest.fixture
def replacement_map() -> dict[str, policy_replacements.PolicyReplacement]:
    """Return a replacement map for tests."""
    replacement = policy_replacements.PolicyReplacement(
        policy_id="old-policy",
        replaced_by="new-policy",
    )
    return {"old-policy": replacement}


def test_update_migrates_replaced_policy(
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

    update.main(["--target", str(target), "--version", "0.2.0"])

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


def test_update_removes_disabled_replaced_policy(
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

    update.main(["--target", str(target), "--version", "0.2.0"])

    updated = agents_path.read_text(encoding="utf-8")
    assert "old-policy" not in updated
    assert not custom_script.exists()
