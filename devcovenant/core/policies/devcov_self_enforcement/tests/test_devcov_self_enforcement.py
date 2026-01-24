"""
Tests for devcov-self-enforcement policy.
"""

import tempfile
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.parser import PolicyParser
from devcovenant.core.policies.devcov_self_enforcement import (
    devcov_self_enforcement,
)
from devcovenant.core.registry import PolicyRegistry


def _write_agents(repo_root: Path) -> Path:
    """Write a minimal AGENTS.md with one policy."""
    agents = repo_root / "AGENTS.md"
    agents.write_text(
        """
## Policy: Demo Policy

```policy-def
id: demo-policy
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
enforcement: active
apply: true
custom: false
```

Demo policy text.
""".lstrip(),
        encoding="utf-8",
    )
    return agents


def _write_policy_script(repo_root: Path) -> Path:
    """Create a demo policy script on disk."""
    policy_dir = (
        repo_root / "devcovenant" / "core" / "policies" / "demo_policy"
    )
    policy_dir.mkdir(parents=True, exist_ok=True)
    script_path = policy_dir / "demo_policy.py"
    script_path.write_text("# demo policy\n", encoding="utf-8")
    return script_path


def _write_registry(repo_root: Path, agents_path: Path) -> None:
    """Write a registry with matching hashes for the demo policy."""
    registry_path = repo_root / "devcovenant" / "registry" / "registry.json"
    parser = PolicyParser(agents_path)
    policies = parser.parse_agents_md()
    registry = PolicyRegistry(registry_path, repo_root)
    for policy in policies:
        script_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "policies"
            / "demo_policy"
            / "demo_policy.py"
        )
        script_content = script_path.read_text(encoding="utf-8")
        full_hash = registry.calculate_full_hash(
            policy.description, script_content
        )
        registry._data.setdefault("policies", {})[policy.policy_id] = {
            "hash": full_hash
        }
    registry.save()


def test_registry_in_sync_passes():
    """Registry sync passes when hashes match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        agents_path = _write_agents(repo_root)
        _write_policy_script(repo_root)
        _write_registry(repo_root, agents_path)

        checker = devcov_self_enforcement.DevCovenantSelfEnforcementCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations == []


def test_registry_missing_entry_fails():
    """Missing registry entries trigger a violation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_agents(repo_root)
        _write_policy_script(repo_root)

        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.json"
        )
        registry = PolicyRegistry(registry_path, repo_root)
        registry._data.setdefault("policies", {})["demo-policy"] = {
            "hash": "mismatch"
        }
        registry.save()

        checker = devcov_self_enforcement.DevCovenantSelfEnforcementCheck()
        context = CheckContext(repo_root=repo_root)
        violations = checker.check(context)

        assert violations
        assert "Policy registry hash mismatch" in violations[0].message
