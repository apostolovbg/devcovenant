"""Tests for the policy registry refresh helper."""

from __future__ import annotations

from pathlib import Path

from devcovenant.core.refresh_registry import (
    _split_metadata_values,
    refresh_registry,
)


def test_split_metadata_values_handles_commas_and_newlines() -> None:
    """Value splitter should normalize comma/newline separated entries."""
    values = _split_metadata_values("a, b\nc")
    assert values == ["a", "b", "c"]


def test_refresh_registry_requires_agents_file(tmp_path: Path) -> None:
    """Refreshing a repo without AGENTS.md should fail with code 1."""
    result = refresh_registry(tmp_path)
    assert result == 1
