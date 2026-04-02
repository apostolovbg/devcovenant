"""Unit tests for no-raw-errors policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.no_raw_errors.no_raw_errors import (
    NoRawErrorsCheck,
    _RawErrorVisitor,
)
from devcovenant.core.contracts.policy import CheckContext


def _write_file(repo_root: Path, relative: str, body: str) -> Path:
    """Write one file under repo_root and return its path."""
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.lstrip("\n"), encoding="utf-8")
    return path


def _configured_check() -> NoRawErrorsCheck:
    """Return policy with deterministic selector defaults for tests."""
    check = NoRawErrorsCheck()
    check.set_options(
        {
            "severity": "error",
            "include_suffixes": [".py"],
            "include_globs": ["*.py"],
            "forbid_bare_except": True,
            "forbid_raise_exception": True,
            "forbid_broad_exception_handlers": True,
            "forbid_silent_exception_pass": True,
            "broad_exception_waiver_markers": ["DEVCOV_ALLOW_BROAD_ONCE"],
            "broad_exception_waiver_between": [
                "DEVCOV_BROAD_BEGIN=>DEVCOV_BROAD_END"
            ],
        },
        {},
    )
    return check


def _run_policy(repo_root: Path, path: Path) -> list:
    """Run no-raw-errors policy for one file path."""
    context = CheckContext(repo_root=repo_root, all_files=[path])
    return _configured_check().check(context)


def _unit_test_raise_exception_is_reported() -> None:
    """`raise Exception(...)` should trigger a violation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
def run():
    raise Exception("boom")
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert "raise Exception" in violations[0].message


def _unit_test_bare_except_is_reported() -> None:
    """Bare `except:` should trigger a violation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
def run():
    try:
        return 1 / 0
    except:
        return 0
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert "Bare `except:`" in violations[0].message


def _unit_test_except_exception_pass_is_reported() -> None:
    """Silent broad handlers should trigger a violation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
def run():
    try:
        return 1 / 0
    except Exception:
        pass
    return None
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert "Silent `except Exception: pass`" in violations[0].message
        assert len(violations) == 1


def _unit_test_broad_except_exception_is_reported() -> None:
    """Broad handlers should trigger violations without waivers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
def run(raw):
    try:
        return int(raw)
    except Exception as exc:
        raise ValueError(f"invalid value: {raw}") from exc
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert "Broad `except Exception` handlers" in violations[0].message


def _unit_test_broad_except_with_comment_waiver_passes() -> None:
    """Line waiver marker should allow broad handlers at boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
def run(raw):
    try:
        return int(raw)
    # DEVCOV_ALLOW_BROAD_ONCE boundary normalizer
    except Exception as exc:
        raise RuntimeError(f"invalid value: {raw}") from exc
""",
        )
        violations = _run_policy(root, module)
        assert violations == []


def _unit_test_broad_except_with_region_waiver_passes() -> None:
    """Region waiver markers should allow broad handlers in that span."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
# DEVCOV_BROAD_BEGIN
def run(raw):
    try:
        return int(raw)
    except Exception as exc:
        raise RuntimeError(f"invalid value: {raw}") from exc
# DEVCOV_BROAD_END
""",
        )
        violations = _run_policy(root, module)
        assert violations == []


def _unit_test_specific_explicit_errors_pass() -> None:
    """Explicit error handling should not trigger no-raw-errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_file(
            root,
            "pkg/demo.py",
            """
class DemoError(ValueError):
    pass

def run(raw):
    if not raw:
        raise DemoError("missing value")
    try:
        return int(raw)
    except ValueError as exc:
        raise DemoError(f"invalid integer: {raw}") from exc
""",
        )
        violations = _run_policy(root, module)
        assert violations == []


def _unit_test_policy_symbol_contract_is_stable() -> None:
    """Policy class/method symbols should stay explicit and importable."""
    assert NoRawErrorsCheck.__name__ == "NoRawErrorsCheck"
    assert hasattr(NoRawErrorsCheck, "check")
    assert hasattr(_RawErrorVisitor, "visit_ExceptHandler")
    assert hasattr(_RawErrorVisitor, "visit_Raise")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_raise_exception_is_reported(self):
        """Run raise Exception policy assertions."""
        _unit_test_raise_exception_is_reported()

    def test_bare_except_is_reported(self):
        """Run bare except policy assertions."""
        _unit_test_bare_except_is_reported()

    def test_except_exception_pass_is_reported(self):
        """Run except Exception pass policy assertions."""
        _unit_test_except_exception_pass_is_reported()

    def test_broad_except_exception_is_reported(self):
        """Run broad except policy assertions."""
        _unit_test_broad_except_exception_is_reported()

    def test_broad_except_with_comment_waiver_passes(self):
        """Run broad except comment-waiver assertions."""
        _unit_test_broad_except_with_comment_waiver_passes()

    def test_broad_except_with_region_waiver_passes(self):
        """Run broad except region-waiver assertions."""
        _unit_test_broad_except_with_region_waiver_passes()

    def test_specific_explicit_errors_pass(self):
        """Run explicit error-handling pass assertions."""
        _unit_test_specific_explicit_errors_pass()

    def test_policy_symbol_contract_is_stable(self):
        """Run no-raw-errors symbol contract assertions."""
        _unit_test_policy_symbol_contract_is_stable()
