"""
Tests for the policy parser.
"""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.parser import PolicyParser


def _unit_test_parse_policy_definition():
    """Test parsing a single policy definition."""
    # Create a temporary AGENTS.md file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
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
<!-- DEVCOV-POLICIES:END -->
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


def _unit_test_parse_multiple_policies():
    """Test parsing multiple policy definitions."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
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
<!-- DEVCOV-POLICIES:END -->
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


def _unit_test_parse_multiline_metadata():
    """Test that continuation lines merge into the prior key."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Continuation Policy

```policy-def
id: continuation-policy
status: active
exclude_prefixes: app,apps
  build,dist
```

Continuation policy description.

---
<!-- DEVCOV-POLICIES:END -->
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


def _unit_test_parse_ignores_policies_outside_managed_block():
    """Parser should only read policies inside DEVCOV policy markers."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write(
            """
## Policy: Outside Policy

```policy-def
id: outside-policy
status: active
severity: warning
auto_fix: false
```

Outside block policy description.

---

<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Inside Policy

```policy-def
id: inside-policy
status: active
severity: error
auto_fix: true
```

Inside block policy description.

---
<!-- DEVCOV-POLICIES:END -->
"""
        )
        temp_path = Path(f.name)

    try:
        parser = PolicyParser(temp_path)
        policies = parser.parse_agents_md()

        assert len(policies) == 1
        assert policies[0].policy_id == "inside-policy"
    finally:
        temp_path.unlink()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

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
