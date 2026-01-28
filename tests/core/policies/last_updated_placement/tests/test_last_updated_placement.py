"""Tests for last-updated-placement policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.last_updated_placement import (
    last_updated_placement,
)


def test_required_file_missing_marker(tmp_path: Path) -> None:
    """Required docs must include a Last Updated marker."""
    doc_path = tmp_path / "README.md"
    doc_path.write_text("# Title\nContent\n", encoding="utf-8")

    checker = last_updated_placement.LastUpdatedPlacementCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[doc_path])
    violations = checker.check(context)
    assert violations


def test_last_updated_allowed_and_top_lines(tmp_path: Path) -> None:
    """Allow Last Updated markers in allowlisted docs near the top."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "# Title\n**Last Updated:** 2026-01-07\n",
        encoding="utf-8",
    )

    checker = last_updated_placement.LastUpdatedPlacementCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[md_path])
    assert checker.check(context) == []


def test_marker_in_non_allowlisted_file(tmp_path: Path) -> None:
    """Last Updated markers in non-allowlisted files are flagged."""
    script_path = tmp_path / "script.py"
    script_path.write_text(
        "**Last Updated:** 2026-01-07\n",
        encoding="utf-8",
    )

    checker = last_updated_placement.LastUpdatedPlacementCheck()
    checker.set_options(
        {"allowed_globs": "**/README.md"},
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[script_path])
    violations = checker.check(context)
    assert violations


def test_marker_after_third_line(tmp_path: Path) -> None:
    """Markers after line three should be flagged."""
    md_path = tmp_path / "README.md"
    md_path.write_text(
        "# Title\nLine 2\nLine 3\nLast Updated: 2026-01-07\n",
        encoding="utf-8",
    )

    checker = last_updated_placement.LastUpdatedPlacementCheck()
    checker.set_options(
        {
            "required_globs": "**/README.md",
            "allowed_globs": "**/README.md",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, all_files=[md_path])
    violations = checker.check(context)
    assert violations
