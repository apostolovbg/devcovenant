"""Tests for devcov-parity-guard policy."""

from pathlib import Path

import yaml

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.devcov_parity_guard import (
    devcov_parity_guard,
)


def _write_agents(path: Path, text: str) -> None:
    """Write the sample policy definition to AGENTS.md."""
    path.write_text(text, encoding="utf-8")


def _write_descriptor(path: Path, policy_id: str, text: str) -> None:
    """Persist a descriptor YAML for the policy."""
    payload = {
        "id": policy_id,
        "text": text,
        "metadata": {"id": policy_id, "profile_scopes": ["global"]},
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _write_policy_script(path: Path) -> None:
    """Create a placeholder policy script."""
    path.write_text("# policy script\n", encoding="utf-8")


def test_descriptor_text_matches_agents(tmp_path: Path) -> None:
    """Matching descriptor text should pass."""
    agents_path = tmp_path / "AGENTS.md"
    policy_dir = (
        tmp_path
        / "devcovenant"
        / "core"
        / "policies"
        / "example_policy"
    )
    policy_dir.mkdir(parents=True)
    _write_policy_script(policy_dir / "example_policy.py")
    _write_descriptor(
        policy_dir / "example_policy.yaml", "example-policy", "Text"
    )
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Text

---
""".strip()
        + "\n",
    )

    checker = devcov_parity_guard.DevcovParityGuardCheck()
    checker.set_options({"policy_definitions": "AGENTS.md"}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])

    assert checker.check(context) == []


def test_descriptor_text_differs(tmp_path: Path) -> None:
    """Mismatched descriptor text should raise a warning."""
    agents_path = tmp_path / "AGENTS.md"
    policy_dir = (
        tmp_path
        / "devcovenant"
        / "core"
        / "policies"
        / "example_policy"
    )
    policy_dir.mkdir(parents=True)
    _write_policy_script(policy_dir / "example_policy.py")
    _write_descriptor(
        policy_dir / "example_policy.yaml", "example-policy", "Canonical"
    )
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Custom text

---
""".strip()
        + "\n",
    )

    checker = devcov_parity_guard.DevcovParityGuardCheck()
    checker.set_options({"policy_definitions": "AGENTS.md"}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    violations = checker.check(context)

    assert violations
    assert "Descriptor policy text differs" in violations[0].message


def test_missing_descriptor_is_skipped(tmp_path: Path) -> None:
    """Missing descriptors should not emit violations."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Text

---
""".strip()
        + "\n",
    )

    checker = devcov_parity_guard.DevcovParityGuardCheck()
    checker.set_options({"policy_definitions": "AGENTS.md"}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])

    assert checker.check(context) == []
