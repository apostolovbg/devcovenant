"""Verify the policy schema helper captures every metadata key."""

from pathlib import Path

from devcovenant.core import policy_schema


def test_build_schema_includes_known_policy_keys():
    """Document that devflow-run-gates enumerates the helper handles."""
    template = Path("devcovenant/core/profiles/global/assets/AGENTS.md")
    schema = policy_schema.build_schema(template)
    assert "devflow-run-gates" in schema
    devflow_keys = schema["devflow-run-gates"].keys
    assert "test_status_file" in devflow_keys
    assert "required_commands" in devflow_keys


def test_build_schema_respects_defaults():
    """Ensure changelog-coverage defaults reference the main changelog."""
    template = Path("devcovenant/core/profiles/global/assets/AGENTS.md")
    schema = policy_schema.build_schema(template)
    changelog_defaults = schema["changelog-coverage"].defaults
    assert changelog_defaults["main_changelog"] == ["CHANGELOG.md"]
