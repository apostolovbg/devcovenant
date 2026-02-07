"""
Tests for the policy parser.
"""

import tempfile
from pathlib import Path

from devcovenant.core.parser import PolicyParser


def test_parse_policy_definition():
    """Test parsing a single policy definition."""
    # Create a temporary AGENTS.md file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
## Policy: Test Policy

```policy-def
id: test-policy
status: active
severity: warning
auto_fix: true
enabled: false
```

This is a test policy description.

---
"""
        )
        temp_path = Path(f.name)

    try:
        # Parse the file
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()

        # Verify we got one policy
        assert len(policies) == 1

        # Verify the policy fields
        policy = policies[0]
        assert policy.policy_id == "test-policy"
        assert policy.name == "Test Policy"
        assert policy.status == "active"
        assert policy.severity == "warning"
        assert policy.auto_fix is True
        assert policy.enabled is False
        assert "test policy description" in policy.description.lower()

    finally:
        # Clean up
        temp_path.unlink()


def test_parse_multiple_policies():
    """Test parsing multiple policy definitions."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
## Policy: First Policy

```policy-def
id: first-policy
status: active
severity: error
auto_fix: false
```

First policy description.

---

## Policy: Second Policy

```policy-def
id: second-policy
status: new
severity: critical
auto_fix: true
```

Second policy description.

---
"""
        )
        temp_path = Path(f.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()

        assert len(policies) == 2

        # Check first policy
        assert policies[0].policy_id == "first-policy"
        assert policies[0].severity == "error"
        assert policies[0].enabled is True

        # Check second policy
        assert policies[1].policy_id == "second-policy"
        assert policies[1].severity == "critical"
        assert policies[1].enabled is True

    finally:
        temp_path.unlink()


def test_parse_multiline_metadata():
    """Test that continuation lines merge into the prior key."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
## Policy: Continuation Policy

```policy-def
id: continuation-policy
status: active
exclude_prefixes: app,apps
  build,dist
```

Continuation policy description.

---
"""
        )
        temp_path = Path(f.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()

        assert len(policies) == 1
        policy = policies[0]
        assert policy.raw_metadata["exclude_prefixes"] == "app,apps,build,dist"
    finally:
        temp_path.unlink()
