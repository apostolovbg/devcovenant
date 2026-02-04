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
        "updated: false\n"
        "enforcement: active\n"
        "apply: true\n"
        f"custom: {'true' if custom else 'false'}\n"
        "profile_scopes: global\n"
        "```\n\n"
        f"{name} description.\n"
    )


def test_refresh_policies_reorders_and_updates(tmp_path: Path) -> None:
    """Refresh reorganizes the policy block and reports
    the touched policies."""
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
        set_updated=True,
    )

    content = agents_path.read_text(encoding="utf-8")
    assert result.updated
    idx_a = content.index("## Policy: Policy A")
    idx_b = content.index("## Policy: Policy B")
    assert idx_a < idx_b


def test_refresh_policies_normalizes_custom_metadata(tmp_path: Path) -> None:
    """Custom policies are normalized to stock defaults when unmanaged."""
    agents_path = tmp_path / "AGENTS.md"
    custom_block = (
        "## Policy: Custom Policy\n\n"
        "```policy-def\n"
        "id: custom-policy\n"
        "status: active\n"
        "severity: error\n"
        "auto_fix: false\n"
        "updated: false\n"
        "enforcement: active\n"
        "apply: true\n"
        "custom: true\n"
        "notes: preserved\n"
        "```\n\n"
        "Custom text.\n"
    )
    _write_agents(agents_path, custom_block)

    refresh_policies(
        agents_path,
        _schema_path(),
        set_updated=True,
    )

    updated_text = agents_path.read_text(encoding="utf-8")
    assert "severity: warning" in updated_text
    assert "custom: false" in updated_text
    assert "notes: preserved" in updated_text
