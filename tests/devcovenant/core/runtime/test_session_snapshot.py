"""Sanity checks for devcovenant.core.runtime.session_snapshot."""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.runtime.session_snapshot"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_snapshot_paths_changed_since_ignores_equal_epoch_boundary():
    """Equal-microsecond mtimes should not be treated as post-epoch changes."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        sample = repo_root / "sample.txt"
        sample.write_text("x\n", encoding="utf-8")

        epoch = 1000.123456
        equal_ns = 1_000_123_456_000
        later_ns = equal_ns + 2_000  # +2 microseconds

        os.utime(sample, ns=(equal_ns, equal_ns))
        assert module.snapshot_paths_changed_since(repo_root, epoch) == set()

        os.utime(sample, ns=(later_ns, later_ns))
        assert module.snapshot_paths_changed_since(repo_root, epoch) == {
            "sample.txt"
        }


def _unit_test_public_session_snapshot_helpers_are_deterministic() -> None:
    """Public helper APIs should produce deterministic, scoped outputs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "README.md").write_text(
            (
                "# Sample\n"
                "**Last Updated:** 2026-02-26\n"
                "**Project Version:** 0.0.1\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "Managed text.\n"
                "<!-- DEVCOV:END -->\n"
                "Visible content.\n"
            ),
            encoding="utf-8",
        )
        (repo_root / "AGENTS.md").write_text(
            (
                "# AGENTS\n"
                "before workflow\n"
                "<!-- DEVCOV-WORKFLOW:BEGIN -->\n"
                "workflow body\n"
                "<!-- DEVCOV-WORKFLOW:END -->\n"
                "after workflow\n"
            ),
            encoding="utf-8",
        )
        workflow_path = repo_root / ".github" / "workflows" / "sample.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(
            (
                "name: sample\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "managed: true\n"
                "<!-- DEVCOV:END -->\n"
                "jobs: {}\n"
            ),
            encoding="utf-8",
        )
        yaml_workflow_path = (
            repo_root / ".github" / "workflows" / "sample.yaml"
        )
        yaml_workflow_path.write_text(
            (
                "name: sample\n"
                "<!-- DEVCOV:BEGIN -->\n"
                "managed: true\n"
                "<!-- DEVCOV:END -->\n"
                "jobs: {}\n"
            ),
            encoding="utf-8",
        )
        (repo_root / "sample.py").write_text("value = 1\n", encoding="utf-8")

        current_paths = module.capture_current_snapshot_paths(repo_root)
        assert "AGENTS.md" in current_paths
        assert "README.md" in current_paths
        assert "sample.py" in current_paths

        current_snapshot = module.capture_current_numstat_snapshot(repo_root)
        assert "sample.py" in current_snapshot
        assert current_snapshot["sample.py"].endswith("\tsample.py")
        assert module.snapshot_row_style(current_snapshot) == "filesystem_hash"
        assert module.snapshot_row_style({"a.py": "1\t1\ta.py"}) == (
            "legacy_numstat"
        )
        assert module.snapshot_row_style({}) == "empty"

        changed = module.changed_numstat_paths(
            {"a.py": "old\ta.py"},
            {"a.py": "new\ta.py", "b.py": "hash\tb.py"},
        )
        assert changed == {"a.py", "b.py"}
        symmetric_changed = module.diff_snapshot_paths(
            {"a.py": "old\ta.py", "c.py": "old\tc.py"},
            {"a.py": "new\ta.py", "b.py": "hash\tb.py"},
        )
        assert symmetric_changed == {"a.py", "b.py", "c.py"}

        signature_before = module.snapshot_signature({"a.py": "x\ta.py"})
        signature_after = module.snapshot_signature({"a.py": "y\ta.py"})
        assert signature_before != signature_after
        assert signature_before == module.snapshot_signature(
            {"a.py": "x\ta.py"}
        )

        normalized = module.normalize_snapshot_rows(
            {"a.py": " hash\ta.py "},
            field_name="session_start_snapshot",
        )
        assert normalized == {"a.py": "hash\ta.py"}
        try:
            module.normalize_snapshot_rows(
                [], field_name="session_start_snapshot"
            )
        except ValueError as exc:
            assert "session_start_snapshot" in str(exc)
        else:
            raise AssertionError("Expected normalize_snapshot_rows to fail")

        session_delta = module.session_delta_paths(
            repo_root,
            {"a.py": "old\ta.py"},
            {"a.py": "new\ta.py", "b.py": "hash\tb.py"},
        )
        assert session_delta == {"a.py", "b.py"}

        original_helper = module.snapshot_paths_changed_since
        try:
            module.snapshot_paths_changed_since = lambda _root, _epoch: {
                "sample.py"
            }
            legacy_delta = module.session_delta_paths(
                repo_root,
                {"legacy.py": "1\t1\tlegacy.py"},
                current_snapshot,
                session_start_epoch=1.0,
            )
        finally:
            module.snapshot_paths_changed_since = original_helper
        assert legacy_delta == {"sample.py"}

        agents_hashes = module.capture_agents_section_hashes(repo_root)
        assert agents_hashes["agents_file"] == "AGENTS.md"
        assert agents_hashes["agents_full_sha256"]
        assert agents_hashes["agents_workflow_sha256"]
        assert agents_hashes["agents_non_workflow_sha256"]

        fingerprint = module.document_exemption_fingerprint_for_path(
            repo_root,
            "README.md",
            header_doc_suffixes={".md"},
            header_keys={
                "last updated",
                "project version",
                "devcovenant version",
            },
            header_scan_lines=4,
        )
        assert fingerprint is not None
        assert fingerprint["non_exempt_content_sha256"]
        assert fingerprint["managed_marker_signature"]

        baseline = module.capture_document_exemption_baseline(
            repo_root,
            header_doc_suffixes=[".md"],
            header_keys=[
                "Last Updated",
                "Project Version",
                "DevCovenant Version",
            ],
            header_scan_lines=4,
        )
        assert "README.md" in baseline
        assert ".github/workflows/sample.yml" in baseline
        assert ".github/workflows/sample.yaml" in baseline
        assert baseline["README.md"]["non_exempt_content_sha256"]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_snapshot_paths_changed_since_ignores_equal_epoch_boundary(self):
        """Run epoch-boundary false-positive regression assertions."""
        _unit_test_snapshot_paths_changed_since_ignores_equal_epoch_boundary()

    def test_public_session_snapshot_helpers_are_deterministic(self):
        """Run symbol-level assertions for public helper coverage."""
        _unit_test_public_session_snapshot_helpers_are_deterministic()
