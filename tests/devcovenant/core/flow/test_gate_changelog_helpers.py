"""Unit tests for internal gate changelog helper functions."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.flow.gate_changelog_helpers"


def _write_policy_registry(
    repo_root: Path,
    metadata_lines: list[str] | None = None,
) -> None:
    """Write one minimal tracked registry payload for changelog metadata."""
    lines = metadata_lines or [
        "      main_changelog: CHANGELOG.md",
        "      header_doc_suffixes:",
        "      - .md",
        "      header_keys:",
        "      - Last Updated",
        "      header_scan_lines: 4",
    ]
    registry_path = repo_root / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  schema_version: 1",
                "  registry_layout: single-root",
                "policies:",
                "  changelog-coverage:",
                "    metadata:",
                *lines,
                "profiles: {}",
                "inventory: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_latest_entry_skips_managed_and_fenced_blocks() -> None:
    """Top-entry extraction should skip managed blocks and fenced examples."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        changelog_path = repo_root / "CHANGELOG.md"
        changelog_path.write_text(
            "\n".join(
                [
                    "# Changelog",
                    "",
                    "## Log changes here",
                    "<!-- DEVCOV:BEGIN -->",
                    "managed block",
                    "<!-- DEVCOV:END -->",
                    "```markdown",
                    "- 2026-01-01",
                    "```",
                    "## Version 0.2.6",
                    "- 2026-02-27",
                    "  - Change: add first change. Files: CHANGELOG.md",
                    "  - Why: add first why. Files: CHANGELOG.md",
                    "  - Impact: add first impact. Files: CHANGELOG.md",
                    "- 2026-02-26",
                    "  - Change: add second change. Files: CHANGELOG.md",
                    "  - Why: add second why. Files: CHANGELOG.md",
                    "  - Impact: add second impact. Files: CHANGELOG.md",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        entry = module._latest_changelog_entry(repo_root)
        assert entry.startswith("- 2026-02-27")
        assert "first change" in entry
        assert "second change" not in entry


def _unit_test_resolve_doc_exemption_options_normalizes_metadata() -> None:
    """Doc exemption metadata should normalize list/string/int payloads."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(
            repo_root,
            metadata_lines=[
                "      main_changelog: CHANGELOG.md",
                "      header_doc_suffixes: .md, .txt",
                "      header_keys:",
                "      - Last Updated",
                "      - Version",
                "      header_scan_lines: -3",
            ],
        )
        suffixes, header_keys, scan_lines = (
            module._resolve_doc_exemption_options(repo_root)
        )
        assert suffixes == [".md", ".txt"]
        assert header_keys == ["Last Updated", "Version"]
        assert scan_lines == 0


def _unit_test_entry_fingerprint_is_stable_for_whitespace_noise() -> None:
    """Fingerprint should ignore trailing whitespace differences."""
    module = importlib.import_module(MODULE)
    left = "- 2026-02-27\n  - Change: add example.  \n"
    right = "- 2026-02-27\n  - Change: add example.\n"
    assert module._entry_fingerprint(left) == module._entry_fingerprint(right)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run importability sanity check."""
        _unit_test_module_importable()

    def test_latest_changelog_entry_skips_managed_and_fenced_blocks(self):
        """Run top-entry extraction filtering assertions."""
        _unit_test_latest_entry_skips_managed_and_fenced_blocks()

    def test_resolve_doc_exemption_options_normalizes_metadata(self):
        """Run metadata-normalization assertions for doc exemptions."""
        _unit_test_resolve_doc_exemption_options_normalizes_metadata()

    def test_entry_fingerprint_is_stable_for_whitespace_noise(self):
        """Run fingerprint stability assertions for trailing whitespace."""
        _unit_test_entry_fingerprint_is_stable_for_whitespace_noise()
