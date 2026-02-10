"""Tests for the raw string escape policy."""

import importlib
import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.raw_string_escapes import raw_string_escapes

FIXER_MODULE = "devcovenant.core.policies.raw_string_escapes.fixers.global"
fixer_module = importlib.import_module(FIXER_MODULE)
RawStringEscapesFixer = fixer_module.RawStringEscapesFixer

RawStringEscapesCheck = raw_string_escapes.RawStringEscapesCheck


def _write_module(tmp_path: Path, source: str) -> Path:
    """Create a Python module with provided source."""
    target = tmp_path / "project_lib" / "helpers" / "escape_example.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def _unit_test_detects_suspicious_backslash(tmp_path: Path):
    """Warn when regex uses bare backslashes."""
    source = r'pattern = "\\s+\\."'
    target = _write_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
    )

    checker = RawStringEscapesCheck()
    violations = checker.check(context)

    assert violations
    assert any("backslash" in v.message.lower() for v in violations)
    assert all(v.severity == "warning" for v in violations)


def _unit_test_allows_raw_strings(tmp_path: Path):
    """Allow raw strings with backslashes."""
    source = r'regex = r"\s+"'
    target = _write_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
    )

    checker = RawStringEscapesCheck()
    assert checker.check(context) == []


def _unit_test_allows_standard_escape_sequences(tmp_path: Path):
    """Permit standard escaped sequences."""
    source = r'line = "\n"'
    target = _write_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
    )

    checker = RawStringEscapesCheck()
    assert checker.check(context) == []


def _unit_test_auto_fix_double_escapes_backslashes(tmp_path: Path):
    """Auto-fix should double unknown escapes."""
    source = r'path = "C:\project\data"'
    target = _write_module(tmp_path, source)
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    checker = RawStringEscapesCheck()
    violations = checker.check(context)
    assert violations
    fixer = RawStringEscapesFixer()
    result = fixer.fix(violations[0])
    assert result.success
    updated = target.read_text()
    assert r"\\project" in updated
    assert r"\\data" in updated


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_detects_suspicious_backslash(self):
        """Run test_detects_suspicious_backslash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_detects_suspicious_backslash(tmp_path=tmp_path)

    def test_allows_raw_strings(self):
        """Run test_allows_raw_strings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_allows_raw_strings(tmp_path=tmp_path)

    def test_allows_standard_escape_sequences(self):
        """Run test_allows_standard_escape_sequences."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_allows_standard_escape_sequences(tmp_path=tmp_path)

    def test_auto_fix_double_escapes_backslashes(self):
        """Run test_auto_fix_double_escapes_backslashes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_auto_fix_double_escapes_backslashes(tmp_path=tmp_path)
