"""Tests for the refresh_policies helper."""

from __future__ import annotations

from pathlib import Path

import yaml

from devcovenant.core.refresh_policies import refresh_policies


def _write_agents(path: Path) -> None:
    """Write a minimal AGENTS file with policy markers."""
    path.write_text(
        (
            "# AGENTS\n\n"
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "<!-- DEVCOV-POLICIES:END -->\n"
        ),
        encoding="utf-8",
    )


def test_refresh_policies_uses_registry_as_source(tmp_path: Path) -> None:
    """Policy block should be regenerated from policy_registry.yaml."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path)
    registry_path = (
        tmp_path
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
                    "alpha-policy": {
                        "description": "Alpha Policy",
                        "policy_text": "Alpha policy text.",
                        "metadata": {
                            "id": "alpha-policy",
                            "status": "active",
                            "enabled": "true",
                        },
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = refresh_policies(agents_path, None, repo_root=tmp_path)

    updated = agents_path.read_text(encoding="utf-8")
    assert result.updated
    assert "## Policy: Alpha Policy" in updated
    assert "id: alpha-policy" in updated
    assert "Alpha policy text." in updated


def test_refresh_policies_no_registry_noop(tmp_path: Path) -> None:
    """Without a policy registry file, refresh should be a no-op."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path)

    before = agents_path.read_text(encoding="utf-8")
    result = refresh_policies(agents_path, None, repo_root=tmp_path)
    after = agents_path.read_text(encoding="utf-8")

    assert not result.updated
    assert before == after
