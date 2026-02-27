"""Unit tests for the `devcovenant update_lock` CLI wrapper."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from devcovenant import update_lock
from tests.devcovenant.support import MonkeyPatch


def _unit_test_run_reports_when_no_targets(monkeypatch: MonkeyPatch) -> None:
    """run should print a clear message when no lock targets are configured."""

    temp_root = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        update_lock,
        "resolve_repo_root",
        lambda require_install=True: temp_root,
    )
    monkeypatch.setattr(
        update_lock,
        "refresh_locks_and_licenses",
        lambda repo_root: ([], []),
    )
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = update_lock.run(args=object())
    assert code == 0
    assert "No metadata-selected lockfiles are configured" in stdout.getvalue()


def _unit_test_run_resolves_repo_root_from_subdirectory(
    monkeypatch: MonkeyPatch,
) -> None:
    """run should resolve and use the git root from a subdirectory."""

    temp_root = Path(tempfile.mkdtemp())
    (temp_root / ".git").mkdir(parents=True, exist_ok=True)
    (temp_root / "devcovenant").mkdir(parents=True, exist_ok=True)
    nested = temp_root / "src" / "nested"
    nested.mkdir(parents=True, exist_ok=True)

    captured: dict[str, Path] = {}

    def _fake_refresh(
        repo_root: Path,
    ) -> tuple[list[update_lock.LockHandlerResult], list[Path]]:
        """Capture resolved root used by run()."""

        captured["repo_root"] = repo_root
        return [], []

    monkeypatch.setattr(
        update_lock,
        "refresh_locks_and_licenses",
        _fake_refresh,
    )

    previous_cwd = Path.cwd()
    try:
        os.chdir(nested)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = update_lock.run(args=object())
    finally:
        os.chdir(previous_cwd)

    assert code == 0
    assert captured["repo_root"].resolve() == temp_root.resolve()


def _unit_test_run_prints_refresh_summary(monkeypatch: MonkeyPatch) -> None:
    """run should print changed lockfile and license refresh summary lines."""

    temp_root = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        update_lock,
        "resolve_repo_root",
        lambda require_install=True: temp_root,
    )
    monkeypatch.setattr(
        update_lock,
        "refresh_locks_and_licenses",
        lambda repo_root: (
            [
                update_lock.LockHandlerResult(
                    "requirements.lock",
                    changed=True,
                    attempted=True,
                    message="Updated requirements.lock.",
                ),
                update_lock.LockHandlerResult(
                    "package-lock.json",
                    changed=False,
                    attempted=True,
                    message="No change.",
                ),
            ],
            [repo_root / "THIRD_PARTY_LICENSES.md"],
        ),
    )

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = update_lock.run(args=object())

    output = stdout.getvalue()
    assert code == 0
    assert "Lock refresh results:" in output
    assert "Updated lockfiles: requirements.lock" in output
    assert "Refreshed license artifacts:" in output


def _unit_test_update_lock_symbol_contract_is_stable() -> None:
    """update_lock module should expose stable runtime contract symbols."""
    assert hasattr(update_lock, "LockFilePieces")
    assert hasattr(update_lock, "LockHandlerResult")
    assert hasattr(update_lock, "main")
    assert hasattr(update_lock, "refresh_locks_and_licenses")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for update_lock CLI tests."""

    def test_run_reports_when_no_targets(self):
        """Run test_run_reports_when_no_targets."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_reports_when_no_targets(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_run_resolves_repo_root_from_subdirectory(self):
        """Run test_run_resolves_repo_root_from_subdirectory."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_resolves_repo_root_from_subdirectory(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_prints_refresh_summary(self):
        """Run test_run_prints_refresh_summary."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_prints_refresh_summary(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_update_lock_symbol_contract_is_stable(self):
        """Run update_lock symbol contract assertions."""
        _unit_test_update_lock_symbol_contract_is_stable()
