"""Tests for the refresh_policies helper."""

from pathlib import Path

from devcovenant.core.refresh_policies import refresh_policies


def _schema_path() -> Path:
    """Return the canonical schema used for tests."""
    return (
        Path(__file__).resolve().parents[4]
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "AGENTS.md"
    )


def _base_agents_header() -> str:
    """Return the minimal header for test AGENTS files."""
    return (
        "# Sample AGENTS\n\n"
        "Prelude text.\n\n"
        "<!-- DEVCOV-POLICIES:BEGIN -->\n"
    )


def _final_agents_footer() -> str:
    """Return the trailing footer for test AGENTS files."""
    return "<!-- DEVCOV-POLICIES:END -->\n"


def _write_agents(path: Path, body: str) -> Path:
    """Write the test AGENTS file with the provided policy body."""
    path.write_text(
        f"{_base_agents_header()}{body}{_final_agents_footer()}",
        encoding="utf-8",
    )
    return path


def _policy_block(policy_id: str, name: str, custom: bool = False) -> str:
    """Build a simplistic policy block for the given identifier."""
    return (
        f"## Policy: {name}\n\n"
        "```policy-def\n"
        f"id: {policy_id}\n"
        "status: active\n"
        "severity: warning\n"
        "auto_fix: false\n"
        "enforcement: active\n"
        "enabled: true\n"
        f"custom: {'true' if custom else 'false'}\n"
        "profile_scopes: global\n"
        "```\n\n"
        f"{name} description.\n"
    )


def test_refresh_policies_skips_unknown_policies(tmp_path: Path) -> None:
    """Refresh skips policy blocks that have no source descriptors."""
    agents_path = tmp_path / "AGENTS.md"
    body = (
        _policy_block("policy-b", "Policy B")
        + "\n---\n\n"
        + _policy_block("policy-a", "Policy A")
    )
    _write_agents(agents_path, body)

    result = refresh_policies(
        agents_path,
        _schema_path(),
    )

    content = agents_path.read_text(encoding="utf-8")
    assert not result.updated
    assert set(result.skipped_policies) == {"policy-a", "policy-b"}
    assert "## Policy: Policy A" in content
    assert "## Policy: Policy B" in content


def test_refresh_policies_keeps_unknown_custom_policy_block(
    tmp_path: Path,
) -> None:
    """Refresh preserves unknown custom blocks and reports them as skipped."""
    agents_path = tmp_path / "AGENTS.md"
    custom_block = (
        "## Policy: Custom Policy\n\n"
        "```policy-def\n"
        "id: custom-policy\n"
        "status: active\n"
        "severity: error\n"
        "auto_fix: false\n"
        "enforcement: active\n"
        "enabled: true\n"
        "custom: true\n"
        "notes: preserved\n"
        "```\n\n"
        "Custom text.\n"
    )
    _write_agents(agents_path, custom_block)

    result = refresh_policies(
        agents_path,
        _schema_path(),
    )

    updated_text = agents_path.read_text(encoding="utf-8")
    assert not result.updated
    assert result.skipped_policies == ("custom-policy",)
    assert "severity: error" in updated_text
    assert "custom: true" in updated_text
    assert "notes: preserved" in updated_text
