"""Tests for devcovenant.core.document_exemptions."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.document_exemptions"


def _doc_exemption_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _doc_exemption_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _doc_exemption_document_exemptions_symbol_contract_is_stable() -> None:
    """Shared exemption helpers should keep a stable public surface."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "document_exemption_fingerprint_for_path")
    assert hasattr(module, "managed_marker_signature")
    assert hasattr(module, "non_exempt_content_hash")
    assert hasattr(module, "normalize_document_exemption_entry")


def _doc_exemption_doc_header_and_managed_changes_keep_non_exempt_hash() -> (
    None
):
    """Header-only and managed-only doc edits should preserve visible hash."""
    module = importlib.import_module(MODULE)
    old_doc = (
        "# Notes\n"
        "**Last Updated:** 2026-02-16\n"
        "**Project Version:** 0.2.6\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old managed text.\n"
        "<!-- DEVCOV:END -->\n"
        "Visible body text.\n"
    )
    exempt_only_doc = old_doc.replace(
        "**Last Updated:** 2026-02-16", "**Last Updated:** 2026-02-17"
    ).replace("Old managed text.", "New managed text.")
    visible_change_doc = exempt_only_doc.replace(
        "Visible body text.", "Visible body text changed."
    )
    kwargs = {
        "header_doc_suffixes": {".md", ".rst", ".txt"},
        "header_keys": {
            "last updated",
            "project version",
            "devcovenant version",
        },
        "header_scan_lines": 4,
    }
    assert module.managed_marker_signature(
        old_doc
    ) == module.managed_marker_signature(exempt_only_doc)
    assert module.non_exempt_content_hash(
        old_doc, "notes.md", **kwargs
    ) == module.non_exempt_content_hash(exempt_only_doc, "notes.md", **kwargs)
    assert module.non_exempt_content_hash(
        old_doc, "notes.md", **kwargs
    ) != module.non_exempt_content_hash(
        visible_change_doc, "notes.md", **kwargs
    )


def _doc_exemption_fingerprint_for_path_supports_yml_and_yaml_assets() -> None:
    """Managed workflow assets in `.yml` and `.yaml` should fingerprint."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        yml_rel = ".github/workflows/sample.yml"
        yaml_rel = ".github/workflows/sample.yaml"
        workflow_text = (
            "name: Sample\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "managed: true\n"
            "<!-- DEVCOV:END -->\n"
            "jobs: {}\n"
        )
        yml_path = repo_root / yml_rel
        yml_path.parent.mkdir(parents=True, exist_ok=True)
        yml_path.write_text(workflow_text, encoding="utf-8")
        (repo_root / yaml_rel).write_text(workflow_text, encoding="utf-8")
        kwargs = {
            "header_doc_suffixes": {".md", ".rst", ".txt"},
            "header_keys": {
                "last updated",
                "project version",
                "devcovenant version",
            },
            "header_scan_lines": 4,
        }
        yml_fingerprint = module.document_exemption_fingerprint_for_path(
            repo_root, yml_rel, **kwargs
        )
        yaml_fingerprint = module.document_exemption_fingerprint_for_path(
            repo_root, yaml_rel, **kwargs
        )
        missing = module.document_exemption_fingerprint_for_path(
            repo_root, ".github/workflows/missing.yml", **kwargs
        )
        assert yml_fingerprint is not None
        assert yaml_fingerprint is not None
        assert yml_fingerprint["managed_marker_signature"]
        assert yaml_fingerprint["managed_marker_signature"]
        assert yml_fingerprint["non_exempt_content_sha256"]
        assert yaml_fingerprint["non_exempt_content_sha256"]
        assert missing is None


def _doc_exemption_normalize_document_exemption_entry_validates_shape() -> (
    None
):
    """
    Normalization should validate required gate-status fingerprint fields.
    """
    module = importlib.import_module(MODULE)
    normalized = module.normalize_document_exemption_entry(
        {
            "non_exempt_content_sha256": "abc123",
            "managed_marker_signature": "def456",
        },
        relative_path="README.md",
    )
    assert normalized == {
        "non_exempt_content_sha256": "abc123",
        "managed_marker_signature": "def456",
    }
    try:
        module.normalize_document_exemption_entry(
            {"non_exempt_content_sha256": "abc123"}, relative_path="README.md"
        )
    except ValueError as exc:
        assert "README.md" in str(exc)
    else:
        raise AssertionError(
            "Expected normalize_document_exemption_entry() to fail"
        )


class DocumentExemptionsTests(unittest.TestCase):
    """unittest wrappers for shared exemption helper regressions."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _doc_exemption_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _doc_exemption_module_has_public_symbols()

    def test_document_exemptions_symbol_contract_is_stable(self):
        """Run shared exemption helper symbol contract assertions."""
        _doc_exemption_document_exemptions_symbol_contract_is_stable()

    def test_doc_header_and_managed_changes_keep_non_exempt_hash(self):
        """Run doc header/managed exemption hash parity assertions."""
        _doc_exemption_doc_header_and_managed_changes_keep_non_exempt_hash()

    def test_fingerprint_for_path_supports_yml_and_yaml_assets(self):
        """Run `.yml`/`.yaml` fingerprint support assertions."""
        _doc_exemption_fingerprint_for_path_supports_yml_and_yaml_assets()

    def test_normalize_document_exemption_entry_validates_shape(self):
        """Run exemption entry normalization validation assertions."""
        _doc_exemption_normalize_document_exemption_entry_validates_shape()
