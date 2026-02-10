"""Tests for command dispatch in the top-level CLI."""

from __future__ import annotations

import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

import pytest

from devcovenant import cli

REPO_ROOT = Path(__file__).resolve().parents[3]


class _CheckResult:
    """Minimal check result used by CLI dispatch tests."""

    should_block = False

    @staticmethod
    def has_sync_issues() -> bool:
        """Return False so CLI exits successfully."""
        return False


def _make_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo layout accepted by the CLI."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "devcovenant").mkdir()
    return repo


def _unit_test_check_defaults_to_autofix(tmp_path: Path, monkeypatch) -> None:
    """`check` should apply fixes unless --nofix is passed."""
    repo = _make_repo(tmp_path)
    captured: dict[str, object] = {}

    class FakeEngine:
        """Capture check parameters from CLI."""

        def __init__(self, repo_root: Path) -> None:
            """Store the repo root passed by CLI construction."""
            captured["repo_root"] = repo_root

        def check(self, mode: str, apply_fixes: bool):
            """Record check inputs and return a pass result."""
            captured["mode"] = mode
            captured["apply_fixes"] = apply_fixes
            return _CheckResult()

    monkeypatch.setattr(cli, "DevCovenantEngine", FakeEngine)
    monkeypatch.setattr(cli, "_warn_version_mismatch", lambda _repo: None)
    monkeypatch.setattr(
        "devcovenant.core.refresh_registry.refresh_registry",
        lambda _repo, skip_freeze=True: 0,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check", "--repo", str(repo)],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert captured["repo_root"] == repo
    assert captured["mode"] == "normal"
    assert captured["apply_fixes"] is True


def _unit_test_check_nofix_disables_autofix(
    tmp_path: Path, monkeypatch
) -> None:
    """`check --nofix` should disable fixer execution."""
    repo = _make_repo(tmp_path)
    captured: dict[str, object] = {}

    class FakeEngine:
        """Capture check parameters from CLI."""

        def __init__(self, repo_root: Path) -> None:
            """Store the repo root passed by CLI construction."""
            captured["repo_root"] = repo_root

        def check(self, mode: str, apply_fixes: bool):
            """Record check inputs and return a pass result."""
            captured["mode"] = mode
            captured["apply_fixes"] = apply_fixes
            return _CheckResult()

    monkeypatch.setattr(cli, "DevCovenantEngine", FakeEngine)
    monkeypatch.setattr(cli, "_warn_version_mismatch", lambda _repo: None)
    monkeypatch.setattr(
        "devcovenant.core.refresh_registry.refresh_registry",
        lambda _repo, skip_freeze=True: 0,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check", "--nofix", "--repo", str(repo)],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert captured["repo_root"] == repo
    assert captured["mode"] == "normal"
    assert captured["apply_fixes"] is False


@pytest.mark.parametrize(
    "flag,phase",
    [
        ("--start", "start"),
        ("--end", "end"),
    ],
)
def _unit_test_check_gate_flags_run_pre_commit_phase(
    tmp_path: Path,
    monkeypatch,
    flag: str,
    phase: str,
) -> None:
    """`check --start/--end` should delegate to the gate runner."""
    repo = _make_repo(tmp_path)
    captured: dict[str, object] = {}

    def _fake_gate(repo_root: Path, gate_phase: str) -> int:
        """Capture gate phase and simulate a successful run."""
        captured["repo_root"] = repo_root
        captured["phase"] = gate_phase
        return 0

    monkeypatch.setattr(cli, "_run_pre_commit_gate", _fake_gate)
    monkeypatch.setattr(
        cli,
        "DevCovenantEngine",
        lambda _repo_root: (_ for _ in ()).throw(
            AssertionError("Engine should not initialize for gate flags")
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check", flag, "--repo", str(repo)],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert captured["repo_root"] == repo
    assert captured["phase"] == phase


def _unit_test_check_gate_flags_are_mutually_exclusive(monkeypatch) -> None:
    """CLI should reject --start and --end together."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "check", "--start", "--end"],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def _unit_test_refresh_skips_bootstrap_registry_refresh(
    tmp_path: Path, monkeypatch
) -> None:
    """`refresh` should not run the bootstrap registry refresh first."""
    repo = _make_repo(tmp_path)

    monkeypatch.setattr(
        "devcovenant.core.refresh_registry.refresh_registry",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("bootstrap refresh should be skipped")
        ),
    )
    monkeypatch.setattr(cli, "_warn_version_mismatch", lambda _repo: None)
    monkeypatch.setattr(
        cli,
        "DevCovenantEngine",
        lambda _repo_root: (_ for _ in ()).throw(
            AssertionError("Engine should not initialize for refresh")
        ),
    )
    monkeypatch.setattr(
        "devcovenant.core.refresh_all.refresh_all",
        lambda *_args, **_kwargs: 0,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["devcovenant", "refresh", "--target", str(repo)],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0


def _unit_test_test_help_is_command_scoped() -> None:
    """`test --help` should not include install/deploy-only options."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "test", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo" in result.stdout
    assert "--install-mode" not in result.stdout
    assert "--docs-mode" not in result.stdout


def _unit_test_install_help_shows_lifecycle_options() -> None:
    """`install --help` should expose lifecycle install options."""
    result = subprocess.run(
        [sys.executable, "-m", "devcovenant", "install", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--install-mode" in result.stdout
    assert "--target" in result.stdout
    assert "--nofix" not in result.stdout


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_check_defaults_to_autofix(self):
        """Run test_check_defaults_to_autofix."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_check_defaults_to_autofix(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_check_nofix_disables_autofix(self):
        """Run test_check_nofix_disables_autofix."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_check_nofix_disables_autofix(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_check_gate_flags_run_pre_commit_phase__case_000(self):
        """Run test_check_gate_flags_run_pre_commit_phase__case_000."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                flag = "--start"
                phase = "start"
                _unit_test_check_gate_flags_run_pre_commit_phase(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    flag=flag,
                    phase=phase,
                )
        finally:
            monkeypatch.undo()

    def test_check_gate_flags_run_pre_commit_phase__case_001(self):
        """Run test_check_gate_flags_run_pre_commit_phase__case_001."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                flag = "--end"
                phase = "end"
                _unit_test_check_gate_flags_run_pre_commit_phase(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    flag=flag,
                    phase=phase,
                )
        finally:
            monkeypatch.undo()

    def test_check_gate_flags_are_mutually_exclusive(self):
        """Run test_check_gate_flags_are_mutually_exclusive."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            _unit_test_check_gate_flags_are_mutually_exclusive(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_refresh_skips_bootstrap_registry_refresh(self):
        """Run test_refresh_skips_bootstrap_registry_refresh."""
        monkeypatch = pytest.MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_refresh_skips_bootstrap_registry_refresh(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_test_help_is_command_scoped(self):
        """Run test_test_help_is_command_scoped."""
        _unit_test_test_help_is_command_scoped()

    def test_install_help_shows_lifecycle_options(self):
        """Run test_install_help_shows_lifecycle_options."""
        _unit_test_install_help_shows_lifecycle_options()
