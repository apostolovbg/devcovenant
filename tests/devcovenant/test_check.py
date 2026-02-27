"""Unit tests for check command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import check


def _mock_check_result(*, blocked: bool = False, sync_issues: bool = False):
    """Build a minimal engine result object for check command tests."""
    return SimpleNamespace(
        should_block=blocked,
        has_sync_issues=lambda: sync_issues,
    )


def _unit_test_run_is_read_only_by_default() -> None:
    """run() should skip refresh/fixes/cleanup in default audit mode."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=False)

    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check.refresh_repo") as refresh_mock:
            with patch(
                "devcovenant.check.cleanup_repo_bytecode_artifacts"
            ) as cleanup_mock:
                with patch("devcovenant.check.warn_version_mismatch"):
                    with patch("devcovenant.check.print_banner"):
                        with patch("devcovenant.check.print_step"):
                            with patch(
                                "devcovenant.check.DevCovenantEngine"
                            ) as engine:
                                engine.return_value.check.return_value = (
                                    _mock_check_result()
                                )
                                exit_code = check.run(args)

    assert exit_code == 0
    refresh_mock.assert_not_called()
    cleanup_mock.assert_not_called()
    engine.return_value.check.assert_called_once_with(apply_fixes=False)


def _unit_test_run_uses_gate_env_for_refresh_and_autofix() -> None:
    """Gate env should enable refresh/fixes/cleanup for the check routine."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=False)
    gate_env = {
        check._CHECK_APPLY_FIXES_ENV: "1",
        check._CHECK_RUN_REFRESH_ENV: "1",
        check._CHECK_CLEAN_BYTECODE_ENV: "1",
    }

    with patch.dict("devcovenant.check.os.environ", gate_env, clear=False):
        with patch(
            "devcovenant.check.resolve_repo_root", return_value=repo_root
        ):
            with patch(
                "devcovenant.check.refresh_repo",
                return_value=0,
            ) as refresh_mock:
                with patch(
                    "devcovenant.check.cleanup_repo_bytecode_artifacts"
                ) as cleanup_mock:
                    with patch("devcovenant.check.warn_version_mismatch"):
                        with patch("devcovenant.check.print_banner"):
                            with patch("devcovenant.check.print_step"):
                                with patch(
                                    "devcovenant.check.DevCovenantEngine"
                                ) as engine:
                                    engine.return_value.check.return_value = (
                                        _mock_check_result()
                                    )
                                    exit_code = check.run(args)

    assert exit_code == 0
    refresh_mock.assert_called_once_with(repo_root)
    cleanup_mock.assert_called_once_with(repo_root)
    engine.return_value.check.assert_called_once_with(apply_fixes=True)


def _unit_test_run_stops_when_gate_refresh_fails() -> None:
    """Gate-orchestrated refresh failure should abort before checks."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=False)
    gate_env = {check._CHECK_RUN_REFRESH_ENV: "1"}

    with patch.dict("devcovenant.check.os.environ", gate_env, clear=False):
        with patch(
            "devcovenant.check.resolve_repo_root", return_value=repo_root
        ):
            with patch("devcovenant.check.refresh_repo", return_value=9):
                with patch(
                    "devcovenant.check.cleanup_repo_bytecode_artifacts"
                ) as cleanup_mock:
                    with patch("devcovenant.check.warn_version_mismatch"):
                        with patch("devcovenant.check.print_banner"):
                            with patch("devcovenant.check.print_step"):
                                with patch(
                                    "devcovenant.check.DevCovenantEngine"
                                ) as engine:
                                    exit_code = check.run(args)
    assert exit_code == 9
    cleanup_mock.assert_not_called()
    engine.assert_not_called()


def _unit_test_run_blocks_when_sync_issues_exist() -> None:
    """run() should return non-zero when sync issues are reported."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=False, norefresh=True)

    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check.refresh_repo") as refresh_mock:
            with patch(
                "devcovenant.check.cleanup_repo_bytecode_artifacts"
            ) as cleanup_mock:
                with patch("devcovenant.check.warn_version_mismatch"):
                    with patch("devcovenant.check.print_banner"):
                        with patch("devcovenant.check.print_step"):
                            with patch(
                                "devcovenant.check.DevCovenantEngine"
                            ) as engine:
                                engine.return_value.check.return_value = (
                                    _mock_check_result(sync_issues=True)
                                )
                                exit_code = check.run(args)

    assert exit_code == 1
    refresh_mock.assert_not_called()
    cleanup_mock.assert_not_called()
    engine.return_value.check.assert_called_once_with(apply_fixes=False)


def _unit_test_legacy_flags_do_not_change_default_audit_behavior() -> None:
    """Legacy compatibility flags should not enable mutating behavior."""
    repo_root = Path("/repo")
    args = SimpleNamespace(nofix=True, norefresh=True)

    with patch("devcovenant.check.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.check.refresh_repo") as refresh_mock:
            with patch(
                "devcovenant.check.cleanup_repo_bytecode_artifacts"
            ) as cleanup_mock:
                with patch("devcovenant.check.warn_version_mismatch"):
                    with patch("devcovenant.check.print_banner"):
                        with patch("devcovenant.check.print_step"):
                            with patch(
                                "devcovenant.check.DevCovenantEngine"
                            ) as engine:
                                engine.return_value.check.return_value = (
                                    _mock_check_result()
                                )
                                exit_code = check.run(args)

    assert exit_code == 0
    refresh_mock.assert_not_called()
    cleanup_mock.assert_not_called()
    engine.return_value.check.assert_called_once_with(apply_fixes=False)


def _unit_test_run_does_not_mutate_gate_status_file() -> None:
    """run() should not mutate gate status in read-only audit mode."""
    args = SimpleNamespace(nofix=False, norefresh=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_bytes = (
            json.dumps(
                {
                    "session_id": "s1",
                    "session_state": "open",
                    "pre_commit_start_epoch": 1.0,
                },
                indent=2,
            ).encode("utf-8")
            + b"\n"
        )
        status_path.write_bytes(status_bytes)

        with patch(
            "devcovenant.check.resolve_repo_root", return_value=repo_root
        ):
            with patch("devcovenant.check.refresh_repo") as refresh_mock:
                with patch(
                    "devcovenant.check.cleanup_repo_bytecode_artifacts"
                ) as cleanup_mock:
                    with patch("devcovenant.check.warn_version_mismatch"):
                        with patch("devcovenant.check.print_banner"):
                            with patch("devcovenant.check.print_step"):
                                with patch(
                                    "devcovenant.check.DevCovenantEngine"
                                ) as engine:
                                    engine.return_value.check.return_value = (
                                        _mock_check_result()
                                    )
                                    exit_code = check.run(args)

        assert exit_code == 0
        refresh_mock.assert_not_called()
        cleanup_mock.assert_not_called()
        assert status_path.read_bytes() == status_bytes


def _unit_test_main_parses_args_and_exits_with_run_result() -> None:
    """main() should parse args and raise SystemExit with run() result."""
    with patch("devcovenant.check.run", return_value=7) as run_mock:
        try:
            check.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from check.main().")

    assert code == 7
    run_mock.assert_called_once()


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_run_is_read_only_by_default(self):
        """Run test_run_is_read_only_by_default."""
        _unit_test_run_is_read_only_by_default()

    def test_run_uses_gate_env_for_refresh_and_autofix(self):
        """Run test_run_uses_gate_env_for_refresh_and_autofix."""
        _unit_test_run_uses_gate_env_for_refresh_and_autofix()

    def test_run_stops_when_gate_refresh_fails(self):
        """Run test_run_stops_when_gate_refresh_fails."""
        _unit_test_run_stops_when_gate_refresh_fails()

    def test_run_blocks_when_sync_issues_exist(self):
        """Run test_run_blocks_when_sync_issues_exist."""
        _unit_test_run_blocks_when_sync_issues_exist()

    def test_legacy_flags_do_not_change_default_audit_behavior(self):
        """Run test_legacy_flags_do_not_change_default_audit_behavior."""
        _unit_test_legacy_flags_do_not_change_default_audit_behavior()

    def test_run_does_not_mutate_gate_status_file(self):
        """Run test_run_does_not_mutate_gate_status_file."""
        _unit_test_run_does_not_mutate_gate_status_file()

    def test_main_parses_args_and_exits_with_run_result(self):
        """Run check.main() CLI entrypoint delegation assertions."""
        _unit_test_main_parses_args_and_exits_with_run_result()
