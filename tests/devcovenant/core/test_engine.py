"""
Tests for the devcovenant engine.
"""

import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

from devcovenant.core.engine import DevCovenantEngine
from devcovenant.core.parser import PolicyDefinition


def _unit_test_engine_initialization():
    """Test that the engine initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir).resolve()

        # Create minimal structure
        (repo_root / "devcovenant").mkdir()
        (repo_root / "AGENTS.md").write_text("# Test")

        engine = DevCovenantEngine(repo_root=repo_root)

        assert engine.repo_root == repo_root
        assert engine.agents_md_path.exists()


def _unit_test_engine_check_no_violations():
    """Test engine check with no violations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create structure
        devcov_dir = repo_root / "devcovenant"
        devcov_dir.mkdir()
        (devcov_dir / "core" / "policies" / "test_policy").mkdir(parents=True)
        config_text = "engine:\n  fail_threshold: error"
        (devcov_dir / "config.yaml").write_text(config_text)

        # Create AGENTS.md with no policies
        agents_text = "# Development Guide\n\nNo policies yet."
        (repo_root / "AGENTS.md").write_text(agents_text)
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "policies": {
                        "disabled-policy": {
                            "status": "active",
                            "enabled": False,
                            "custom": False,
                            "description": "Disabled Policy",
                            "policy_text": "Disabled policy text.",
                            "metadata": {
                                "id": "disabled-policy",
                                "status": "active",
                                "enabled": "false",
                                "custom": "false",
                                "severity": "error",
                                "auto_fix": "false",
                            },
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        engine = DevCovenantEngine(repo_root=repo_root)
        result = engine.check(mode="normal")

        # Should have no violations and not block
        assert result.should_block is False


def _unit_test_engine_respects_profile_ignore_dirs(tmp_path: Path) -> None:
    """Profile ignore_dirs should exclude matching paths."""
    repo_root = tmp_path
    devcov_dir = repo_root / "devcovenant"
    profile_dir = devcov_dir / "custom" / "profiles" / "demo"
    profile_dir.mkdir(parents=True)
    profile_manifest = (
        "version: 1\n"
        "profile: demo\n"
        "category: custom\n"
        "suffixes: []\n"
        "ignore_dirs:\n"
        "  - vendor\n"
        "policies: []\n"
    )
    (profile_dir / "demo.yaml").write_text(profile_manifest, encoding="utf-8")
    (devcov_dir / "config.yaml").write_text(
        "profiles:\n  active:\n    - demo\n",
        encoding="utf-8",
    )
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")

    engine = DevCovenantEngine(repo_root=repo_root)
    assert engine._is_ignored_path(repo_root / "vendor" / "file.py")
    assert not engine._is_ignored_path(repo_root / "src" / "file.py")


def _unit_test_custom_override_skips_core_fixers(tmp_path: Path) -> None:
    """Core fixers should be skipped when a custom override exists."""
    repo_root = tmp_path
    (
        repo_root / "devcovenant" / "custom" / "policies" / "no_future_dates"
    ).mkdir(parents=True)
    (
        repo_root
        / "devcovenant"
        / "custom"
        / "policies"
        / "no_future_dates"
        / "no_future_dates.py"
    ).write_text("# custom override\n", encoding="utf-8")
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")

    engine = DevCovenantEngine(repo_root=repo_root)
    core_fixers = [
        fixer
        for fixer in engine.fixers
        if fixer.policy_id == "no-future-dates"
        and getattr(fixer, "_origin", "") == "core"
    ]
    assert not core_fixers


def _policy_definition(policy_id: str, enabled: bool) -> PolicyDefinition:
    """Create a minimal policy definition for engine tests."""
    return PolicyDefinition(
        policy_id=policy_id,
        name="Test Policy",
        status="active",
        severity="error",
        auto_fix=False,
        enabled=enabled,
        custom=False,
        description="Test policy description.",
        raw_metadata={"enabled": "true" if enabled else "false"},
    )


def _unit_test_policy_state_disable_override(
    tmp_path: Path, monkeypatch
) -> None:
    """Config policy_state must disable a policy at runtime."""
    repo_root = tmp_path
    (repo_root / "devcovenant").mkdir()
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
    (repo_root / "devcovenant" / "config.yaml").write_text(
        "policy_state:\n" "  sample-policy: false\n",
        encoding="utf-8",
    )
    engine = DevCovenantEngine(repo_root=repo_root)

    policy = _policy_definition("sample-policy", enabled=True)
    captured = {}
    monkeypatch.setattr(
        engine, "_load_policies_from_registry", lambda: [policy]
    )

    def _capture_sync(policies):
        """Capture enabled state seen by sync checks."""
        captured["sync"] = [entry.enabled for entry in policies]
        return []

    def _capture_run(policies, mode, context):
        """Capture enabled state seen by runtime check execution."""
        captured["run"] = [entry.enabled for entry in policies]
        return []

    monkeypatch.setattr(engine.registry, "check_policy_sync", _capture_sync)
    monkeypatch.setattr(engine, "run_policy_checks", _capture_run)

    result = engine.check(mode="normal")

    assert result.should_block is False
    assert captured["sync"] == [False]
    assert captured["run"] == [False]
    assert policy.raw_metadata["enabled"] == "false"


def _unit_test_policy_state_enable_override(
    tmp_path: Path, monkeypatch
) -> None:
    """Config policy_state must enable a policy at runtime."""
    repo_root = tmp_path
    (repo_root / "devcovenant").mkdir()
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
    (repo_root / "devcovenant" / "config.yaml").write_text(
        "policy_state:\n" "  sample-policy: true\n",
        encoding="utf-8",
    )
    engine = DevCovenantEngine(repo_root=repo_root)

    policy = _policy_definition("sample-policy", enabled=False)
    captured = {}
    monkeypatch.setattr(
        engine, "_load_policies_from_registry", lambda: [policy]
    )

    def _capture_sync(policies):
        """Capture enabled state seen by sync checks."""
        captured["sync"] = [entry.enabled for entry in policies]
        return []

    def _capture_run(policies, mode, context):
        """Capture enabled state seen by runtime check execution."""
        captured["run"] = [entry.enabled for entry in policies]
        return []

    monkeypatch.setattr(engine.registry, "check_policy_sync", _capture_sync)
    monkeypatch.setattr(engine, "run_policy_checks", _capture_run)

    result = engine.check(mode="normal")

    assert result.should_block is False
    assert captured["sync"] == [True]
    assert captured["run"] == [True]
    assert policy.raw_metadata["enabled"] == "true"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_engine_initialization(self):
        """Run test_engine_initialization."""
        _unit_test_engine_initialization()

    def test_engine_check_no_violations(self):
        """Run test_engine_check_no_violations."""
        _unit_test_engine_check_no_violations()

    def test_engine_respects_profile_ignore_dirs(self):
        """Run test_engine_respects_profile_ignore_dirs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_engine_respects_profile_ignore_dirs(tmp_path=tmp_path)

    def test_custom_override_skips_core_fixers(self):
        """Run test_custom_override_skips_core_fixers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_custom_override_skips_core_fixers(tmp_path=tmp_path)

    def test_policy_state_disables_policy_even_if_registry_enables(self):
        """Run test_policy_state_disables_policy_even_if_registry_enables."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                disable_case = _unit_test_policy_state_disable_override
                disable_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_policy_state_enables_policy_even_if_registry_disables(self):
        """Run test_policy_state_enables_policy_even_if_registry_disables."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                enable_case = _unit_test_policy_state_enable_override
                enable_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()
