"""Unit tests for metadata-driven `devcovenant update_lock`."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from devcovenant import update_lock
from tests.devcovenant.support import MonkeyPatch


def _unit_test_refresh_uses_metadata_targets_and_syncs_licenses(
    monkeypatch: MonkeyPatch,
) -> None:
    """refresh_locks_and_licenses should use metadata-selected handlers."""

    temp_root = Path(tempfile.mkdtemp())
    monkeypatch.setattr(update_lock, "ROOT", temp_root)
    monkeypatch.setattr(
        update_lock,
        "_resolve_dependency_metadata",
        lambda repo_root: {
            "dependency_files": ["requirements.lock", "package-lock.json"],
            "third_party_file": "THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        },
    )

    def _requirements_handler(
        repo_root: Path,
    ) -> update_lock.LockHandlerResult:
        """Simulate a changed Python lockfile."""

        assert repo_root == temp_root
        return update_lock.LockHandlerResult(
            "requirements.lock",
            changed=True,
            attempted=True,
            message="Updated requirements.lock.",
        )

    def _npm_handler(repo_root: Path) -> update_lock.LockHandlerResult:
        """Simulate unchanged npm lockfile."""

        assert repo_root == temp_root
        return update_lock.LockHandlerResult(
            "package-lock.json",
            changed=False,
            attempted=True,
            message="No change.",
        )

    monkeypatch.setattr(
        update_lock,
        "LOCKFILE_HANDLERS",
        {
            "requirements.lock": _requirements_handler,
            "package-lock.json": _npm_handler,
        },
    )

    refresh_calls: dict[str, object] = {}

    def _fake_refresh(repo_root: Path, **kwargs):
        """Capture license refresh invocation."""

        refresh_calls["repo_root"] = repo_root
        refresh_calls["kwargs"] = kwargs
        return [repo_root / "THIRD_PARTY_LICENSES.md"]

    monkeypatch.setattr(
        update_lock.dependency_license_sync,
        "refresh_license_artifacts",
        _fake_refresh,
    )

    results, license_files = update_lock.refresh_locks_and_licenses(temp_root)
    assert [entry.lock_file for entry in results] == [
        "requirements.lock",
        "package-lock.json",
    ]
    assert [entry.changed for entry in results] == [True, False]
    assert license_files == [temp_root / "THIRD_PARTY_LICENSES.md"]
    assert refresh_calls["repo_root"] == temp_root
    assert refresh_calls["kwargs"]["changed_dependency_files"] == [
        "requirements.lock"
    ]


def _unit_test_refresh_skips_license_sync_without_changed_locks(
    monkeypatch: MonkeyPatch,
) -> None:
    """No changed lockfiles should skip license artifact refresh."""

    temp_root = Path(tempfile.mkdtemp())
    monkeypatch.setattr(update_lock, "ROOT", temp_root)
    monkeypatch.setattr(
        update_lock,
        "_resolve_dependency_metadata",
        lambda repo_root: {
            "dependency_files": ["requirements.lock"],
            "third_party_file": "THIRD_PARTY_LICENSES.md",
            "licenses_dir": "licenses",
            "report_heading": "## License Report",
        },
    )

    def _handler(repo_root: Path) -> update_lock.LockHandlerResult:
        """Simulate no lockfile change."""

        assert repo_root == temp_root
        return update_lock.LockHandlerResult(
            "requirements.lock",
            changed=False,
            attempted=True,
            message="No change.",
        )

    monkeypatch.setattr(
        update_lock,
        "LOCKFILE_HANDLERS",
        {"requirements.lock": _handler},
    )

    called = {"refresh": False}

    def _fake_refresh(repo_root: Path, **kwargs):
        """Track unexpected refresh calls."""

        del repo_root, kwargs
        called["refresh"] = True
        return []

    monkeypatch.setattr(
        update_lock.dependency_license_sync,
        "refresh_license_artifacts",
        _fake_refresh,
    )

    results, license_files = update_lock.refresh_locks_and_licenses(temp_root)
    assert len(results) == 1
    assert results[0].changed is False
    assert license_files == []
    assert called["refresh"] is False


def _unit_test_run_reports_when_no_targets(monkeypatch: MonkeyPatch) -> None:
    """run should print a clear message when no lock targets are configured."""

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


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for metadata-driven update_lock tests."""

    def test_refresh_uses_metadata_targets_and_syncs_licenses(self):
        """Run test_refresh_uses_metadata_targets_and_syncs_licenses."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_refresh_uses_metadata_targets_and_syncs_licenses(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_refresh_skips_license_sync_without_changed_locks(self):
        """Run test_refresh_skips_license_sync_without_changed_locks."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_refresh_skips_license_sync_without_changed_locks(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_reports_when_no_targets(self):
        """Run test_run_reports_when_no_targets."""

        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_reports_when_no_targets(monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()
