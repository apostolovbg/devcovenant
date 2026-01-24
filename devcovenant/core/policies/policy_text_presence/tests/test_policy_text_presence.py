"""Tests for policy-text-presence policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.policy_text_presence import policy_text_presence


def _write_agents(path: Path, text: str) -> None:
    """Write the given policy fixture to AGENTS.md."""
    path.write_text(text, encoding="utf-8")


def test_missing_policy_text_raises_violation(tmp_path: Path) -> None:
    """Policies without text should raise a violation."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: error
auto_fix: false
updated: false
```

---
""".strip()
        + "\n",
    )

    checker = policy_text_presence.PolicyTextPresenceCheck()
    checker.set_options({"policy_definitions": "AGENTS.md"}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    violations = checker.check(context)

    assert violations
    assert "example-policy" in violations[0].message


def test_policy_text_present_passes(tmp_path: Path) -> None:
    """Policies with text should pass."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: error
auto_fix: false
updated: false
```

Policy text goes here.

---
""".strip()
        + "\n",
    )

    checker = policy_text_presence.PolicyTextPresenceCheck()
    checker.set_options({"policy_definitions": "AGENTS.md"}, {})
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])

    assert checker.check(context) == []
