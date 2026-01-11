"""Tests for the raw string escape policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.fixers.raw_string_escapes import RawStringEscapesFixer
from devcovenant.core.policy_scripts import raw_string_escapes

RawStringEscapesCheck = raw_string_escapes.RawStringEscapesCheck


def _write_module(tmp_path: Path, source: str) -> Path:
    """Create a Python module with provided source."""
    target = tmp_path / "project_lib" / "helpers" / "escape_example.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_detects_suspicious_backslash(tmp_path: Path):
    """Warn when regex uses bare backslashes."""
    source = 'pattern = "\\s+\\."'
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


def test_allows_raw_strings(tmp_path: Path):
    """Allow raw strings with backslashes."""
    source = 'regex = r"\\s+"'
    target = _write_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
    )

    checker = RawStringEscapesCheck()
    assert checker.check(context) == []


def test_allows_standard_escape_sequences(tmp_path: Path):
    """Permit standard escaped sequences."""
    source = 'line = "\\n"'
    target = _write_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
    )

    checker = RawStringEscapesCheck()
    assert checker.check(context) == []


def test_auto_fix_double_escapes_backslashes(tmp_path: Path):
    """Auto-fix should double unknown escapes."""
    source = 'path = "C:\\project\\data"'
    target = _write_module(tmp_path, source)
    context = CheckContext(repo_root=tmp_path, changed_files=[target])
    checker = RawStringEscapesCheck()
    violations = checker.check(context)
    assert violations
    fixer = RawStringEscapesFixer()
    result = fixer.fix(violations[0])
    assert result.success
    updated = target.read_text()
    assert "\\\\project" in updated
    assert "\\\\data" in updated
