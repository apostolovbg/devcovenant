"""
Tests for the devcovenant engine.
"""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.policy_runtime import DevCovenantEngine, PolicyParser
from tests.devcovenant.support import MonkeyPatch


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

        # Create AGENTS.md with a disabled policy.
        (repo_root / "AGENTS.md").write_text(
            _agents_policy_doc("disabled-policy", enabled=False),
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


def _agents_policy_doc(policy_id: str, enabled: bool) -> str:
    """Return a minimal AGENTS policy block document."""
    enabled_value = "true" if enabled else "false"
    return (
        "# Development Guide\n\n"
        "<!-- DEVCOV-POLICIES:BEGIN -->\n"
        "## Policy: Sample Policy\n\n"
        "```policy-def\n"
        f"id: {policy_id}\n"
        "severity: error\n"
        "auto_fix: false\n"
        "enforcement: active\n"
        f"enabled: {enabled_value}\n"
        "custom: false\n"
        "```\n\n"
        "Sample policy description.\n"
        "<!-- DEVCOV-POLICIES:END -->\n"
    )


def _unit_test_agents_enabled_state_is_runtime_authority(
    tmp_path: Path, monkeypatch
) -> None:
    """Runtime must use AGENTS enabled state over registry/config entries."""
    repo_root = tmp_path
    (repo_root / "devcovenant").mkdir()
    (repo_root / "AGENTS.md").write_text(
        _agents_policy_doc("sample-policy", enabled=False),
        encoding="utf-8",
    )
    registry_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "policies:\n"
        "  sample-policy:\n"
        "    enabled: true\n"
        "    metadata:\n"
        "      id: sample-policy\n"
        "      enabled: true\n",
        encoding="utf-8",
    )
    (repo_root / "devcovenant" / "config.yaml").write_text(
        "policy_state:\n" "  sample-policy: true\n",
        encoding="utf-8",
    )
    engine = DevCovenantEngine(repo_root=repo_root)

    captured = {}

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


def _unit_test_runtime_policy_source_is_agents(
    tmp_path: Path, monkeypatch
) -> None:
    """Registry-only policies must not participate in runtime checks."""
    repo_root = tmp_path
    (repo_root / "devcovenant").mkdir()
    (repo_root / "AGENTS.md").write_text(
        _agents_policy_doc("agents-policy", enabled=True),
        encoding="utf-8",
    )
    registry_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "policies:\n"
        "  registry-only:\n"
        "    enabled: true\n"
        "    metadata:\n"
        "      id: registry-only\n"
        "      enabled: true\n",
        encoding="utf-8",
    )
    engine = DevCovenantEngine(repo_root=repo_root)

    captured = {}

    def _capture_run(policies, mode, context):
        """Capture policy ids seen by runtime check execution."""
        captured["ids"] = [entry.policy_id for entry in policies]
        return []

    monkeypatch.setattr(engine.registry, "check_policy_sync", lambda _: [])
    monkeypatch.setattr(engine, "run_policy_checks", _capture_run)

    result = engine.check(mode="normal")

    assert result.should_block is False
    assert captured["ids"] == ["agents-policy"]


def _unit_test_parse_policy_definition() -> None:
    """PolicyParser should parse a single policy definition block."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as file_obj:
        file_obj.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Test Policy

```policy-def
id: test-policy
severity: warning
auto_fix: true
enabled: false
```

This is a test policy description.

---
<!-- DEVCOV-POLICIES:END -->
"""
        )
        temp_path = Path(file_obj.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()
        assert len(policies) == 1
        policy = policies[0]
        assert policy.policy_id == "test-policy"
        assert policy.name == "Test Policy"
        assert policy.severity == "warning"
        assert policy.auto_fix is True
        assert policy.enabled is False
        assert "test policy description" in policy.description.lower()
    finally:
        temp_path.unlink()


def _unit_test_parse_multiple_policies() -> None:
    """PolicyParser should parse multiple policy sections in one block."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as file_obj:
        file_obj.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: First Policy

```policy-def
id: first-policy
severity: error
auto_fix: false
```

First policy description.

---

## Policy: Second Policy

```policy-def
id: second-policy
severity: critical
auto_fix: true
```

Second policy description.

---
<!-- DEVCOV-POLICIES:END -->
"""
        )
        temp_path = Path(file_obj.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()
        assert len(policies) == 2
        assert policies[0].policy_id == "first-policy"
        assert policies[0].severity == "error"
        assert policies[0].enabled is True
        assert policies[1].policy_id == "second-policy"
        assert policies[1].severity == "critical"
        assert policies[1].enabled is True
    finally:
        temp_path.unlink()


def _unit_test_parse_multiline_metadata() -> None:
    """PolicyParser should fold metadata continuation lines."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as file_obj:
        file_obj.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Continuation Policy

```policy-def
id: continuation-policy
exclude_prefixes: app,apps
  build,dist
```

Continuation policy description.

---
<!-- DEVCOV-POLICIES:END -->
"""
        )
        temp_path = Path(file_obj.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()
        assert len(policies) == 1
        assert (
            policies[0].raw_metadata["exclude_prefixes"]
            == "app,apps,build,dist"
        )
    finally:
        temp_path.unlink()


def _unit_test_parse_ignores_policies_outside_managed_block() -> None:
    """PolicyParser should parse only the managed policies block."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as file_obj:
        file_obj.write(
            """
## Policy: Outside Policy

```policy-def
id: outside-policy
severity: warning
auto_fix: false
```

Outside block policy description.

---

<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Inside Policy

```policy-def
id: inside-policy
severity: error
auto_fix: true
```

Inside block policy description.

---
<!-- DEVCOV-POLICIES:END -->
"""
        )
        temp_path = Path(file_obj.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()
        assert len(policies) == 1
        assert policies[0].policy_id == "inside-policy"
    finally:
        temp_path.unlink()


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

    def test_agents_enabled_state_is_runtime_authority(self):
        """Run test_agents_enabled_state_is_runtime_authority."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_agents_enabled_state_is_runtime_authority(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_runtime_policy_source_is_agents(self):
        """Run test_runtime_policy_source_is_agents."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_runtime_policy_source_is_agents(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_parse_policy_definition(self):
        """Run test_parse_policy_definition."""
        _unit_test_parse_policy_definition()

    def test_parse_multiple_policies(self):
        """Run test_parse_multiple_policies."""
        _unit_test_parse_multiple_policies()

    def test_parse_multiline_metadata(self):
        """Run test_parse_multiline_metadata."""
        _unit_test_parse_multiline_metadata()

    def test_parse_ignores_policies_outside_managed_block(self):
        """Run test_parse_ignores_policies_outside_managed_block."""
        _unit_test_parse_ignores_policies_outside_managed_block()
