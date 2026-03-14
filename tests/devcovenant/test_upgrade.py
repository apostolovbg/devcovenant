"""Unit tests for upgrade command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from devcovenant import install, upgrade
from devcovenant.core.flow import gate_status_helpers
from tests.devcovenant import repo_seed_cache


def _write_policy_descriptor(script_path: Path) -> None:
    """Create a minimal descriptor for a custom policy script."""
    descriptor_path = script_path.with_suffix(".yaml")
    descriptor_path.write_text(
        "id: demo\n"
        "text: Demo custom policy.\n"
        "metadata:\n"
        "  id: demo\n",
        encoding="utf-8",
    )


def _source_version() -> str:
    """Return packaged source version for assertions."""
    version_path = Path(install.__file__).resolve().parent / "VERSION"
    return version_path.read_text(encoding="utf-8").strip()


def _seed_runtime_local_state(repo_root: Path) -> tuple[str, str]:
    """Seed local registry and logs state that upgrade must preserve."""
    gate_status_path = (
        repo_root / "devcovenant" / "registry" / "local" / "gate_status.json"
    )
    gate_status_path.parent.mkdir(parents=True, exist_ok=True)
    gate_status_payload = {
        "session_id": "preserve-me",
        "session_state": "open",
        "custom_note": "runtime-local-state",
    }
    gate_status_path.write_text(
        json.dumps(gate_status_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    logs_root = repo_root / "devcovenant" / "logs"
    run_dir = logs_root / "20260225T000000000000Z-upgrade-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_payload = {"run_dir": f"devcovenant/logs/{run_dir.name}"}
    (logs_root / "latest.json").write_text(
        json.dumps(latest_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "run.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "summary.txt").write_text(
        "preserved summary\n",
        encoding="utf-8",
    )

    return (
        gate_status_path.read_text(encoding="utf-8"),
        (run_dir / "summary.txt").read_text(encoding="utf-8"),
    )


def _unit_test_upgrade_replaces_when_target_is_older() -> None:
    """upgrade_repo should replace core when target version is older."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        version_path = repo_root / "devcovenant" / "VERSION"
        version_path.write_text("0.0.1\n", encoding="utf-8")

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0
        assert (
            version_path.read_text(encoding="utf-8").strip()
            == _source_version()
        )


def _unit_test_upgrade_preserves_custom_tree() -> None:
    """upgrade_repo should preserve custom policies/profiles content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        custom_file = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_text("# keep\n", encoding="utf-8")
        _write_policy_descriptor(custom_file)

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0
        assert custom_file.exists()
        assert custom_file.read_text(encoding="utf-8") == "# keep\n"


def _unit_test_upgrade_prunes_repo_only_custom_payload() -> None:
    """upgrade_repo should remove leaked repo-only custom payload paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        leaked_policy_dir = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "devcov_raw_string_escapes"
        )
        leaked_policy_dir.mkdir(parents=True, exist_ok=True)
        (leaked_policy_dir / "__init__.py").write_text(
            "__all__ = []\n",
            encoding="utf-8",
        )
        (leaked_policy_dir / "devcov_raw_string_escapes.py").write_text(
            "# leaked repo-only policy script\n",
            encoding="utf-8",
        )

        leaked_profile_dir = (
            repo_root / "devcovenant" / "custom" / "profiles" / "devcovrepo"
        )
        leaked_profile_dir.mkdir(parents=True, exist_ok=True)
        (leaked_profile_dir / "devcovrepo.yaml").write_text(
            "profile: devcovrepo\n",
            encoding="utf-8",
        )

        user_policy = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo"
            / "demo.py"
        )
        user_policy.parent.mkdir(parents=True, exist_ok=True)
        user_policy.write_text("# keep-user-payload\n", encoding="utf-8")
        _write_policy_descriptor(user_policy)

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0

        assert not leaked_policy_dir.exists()
        assert not leaked_profile_dir.exists()
        assert user_policy.exists()
        assert (
            user_policy.read_text(encoding="utf-8") == "# keep-user-payload\n"
        )


def _unit_test_upgrade_runs_full_refresh() -> None:
    """upgrade_repo should end with full refresh and registries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        version_path = repo_root / "devcovenant" / "VERSION"
        version_path.write_text("0.0.1\n", encoding="utf-8")

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        assert policy_registry.exists()


def _unit_test_upgrade_preserves_runtime_local_registry_and_logs() -> None:
    """upgrade_repo should preserve local registry state and logs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        expected_gate_status, expected_summary = _seed_runtime_local_state(
            repo_root
        )
        version_path = repo_root / "devcovenant" / "VERSION"
        version_path.write_text("0.0.1\n", encoding="utf-8")

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0

        gate_status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "gate_status.json"
        )
        assert gate_status_path.exists()
        assert (
            gate_status_path.read_text(encoding="utf-8")
            == expected_gate_status
        )

        logs_root = repo_root / "devcovenant" / "logs"
        run_dir = logs_root / "20260225T000000000000Z-upgrade-test"
        assert (logs_root / "README.md").exists()
        assert (logs_root / "latest.json").exists()
        assert run_dir.exists()
        assert (run_dir / "run.json").exists()
        assert (run_dir / "summary.txt").read_text(
            encoding="utf-8"
        ) == expected_summary


def _unit_test_upgrade_preserves_open_gate_status_visibility() -> None:
    """upgrade_repo should keep open gate state visible to status helpers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        repo_seed_cache.copy_installed_repo(repo_root)

        gate_status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "gate_status.json"
        )
        gate_status_path.parent.mkdir(parents=True, exist_ok=True)
        gate_status_path.write_text(
            json.dumps(
                {
                    "session_id": "upgrade-open-session",
                    "session_state": "open",
                    "pre_commit_start_utc": "2026-03-01T10:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with redirect_stderr(StringIO()):
            result = upgrade.upgrade_repo(repo_root)
        assert result == 0

        summary_lines = gate_status_helpers._gate_status_summary_lines(
            repo_root
        )
        assert "Gate Status: open" in summary_lines
        assert "Session ID: upgrade-open-session" in summary_lines


def _unit_test_parse_version_for_compare_normalizes_partial_and_v_prefix() -> (
    None
):
    """Upgrade parser should normalize partial tokens and `v` prefix."""
    parsed = upgrade._parse_version_for_compare("v1.2")
    assert str(parsed) == "1.2.0"
    parsed_plain = upgrade._parse_version_for_compare("1")
    assert str(parsed_plain) == "1.0.0"


def _unit_test_parse_version_for_compare_supports_prerelease_ordering() -> (
    None
):
    """Upgrade version parser should preserve SemVer prerelease ordering."""
    release = upgrade._parse_version_for_compare("1.0.0")
    prerelease = upgrade._parse_version_for_compare("1.0.0-rc.1")
    next_prerelease = upgrade._parse_version_for_compare("1.0.0-rc.2")
    assert release > prerelease
    assert next_prerelease > prerelease


def _unit_test_parse_version_for_compare_rejects_invalid_tokens() -> None:
    """Upgrade version parser should reject invalid non-semver strings."""
    try:
        upgrade._parse_version_for_compare("1.2.x")
    except ValueError as error:
        message = str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for invalid version.")
    assert "Invalid semantic version string" in message


def _unit_test_main_invokes_run_and_exits_with_code() -> None:
    """upgrade.main should parse args, call run, and exit with run code."""
    captured: dict[str, object] = {}
    original_run = upgrade.run

    def _fake_run(args):
        """Capture parsed args and return a sentinel exit code."""
        captured["args"] = args
        return 7

    upgrade.run = _fake_run
    try:
        try:
            upgrade.main([])
        except SystemExit as exc:
            exit_code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from main().")
    finally:
        upgrade.run = original_run

    assert exit_code == 7
    assert "args" in captured


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_upgrade_replaces_when_target_is_older(self):
        """Run test_upgrade_replaces_when_target_is_older."""
        _unit_test_upgrade_replaces_when_target_is_older()

    def test_upgrade_preserves_custom_tree(self):
        """Run test_upgrade_preserves_custom_tree."""
        _unit_test_upgrade_preserves_custom_tree()

    def test_upgrade_prunes_repo_only_custom_payload(self):
        """Run repo-only custom payload prune assertions for upgrade."""
        _unit_test_upgrade_prunes_repo_only_custom_payload()

    def test_upgrade_runs_full_refresh(self):
        """Run test_upgrade_runs_full_refresh."""
        _unit_test_upgrade_runs_full_refresh()

    def test_upgrade_preserves_runtime_local_registry_and_logs(self):
        """Run test_upgrade_preserves_runtime_local_registry_and_logs."""
        _unit_test_upgrade_preserves_runtime_local_registry_and_logs()

    def test_upgrade_preserves_open_gate_status_visibility(self):
        """Run open-gate visibility assertions for upgrade."""
        _unit_test_upgrade_preserves_open_gate_status_visibility()

    def test_parse_version_for_compare_normalizes_partial_and_v_prefix(self):
        """Run version normalization assertions for upgrade comparisons."""
        _unit_test_parse_version_for_compare_normalizes_partial_and_v_prefix()

    def test_parse_version_for_compare_supports_prerelease_ordering(self):
        """Run prerelease ordering assertions for upgrade comparisons."""
        _unit_test_parse_version_for_compare_supports_prerelease_ordering()

    def test_parse_version_for_compare_rejects_invalid_tokens(self):
        """Run invalid-version rejection assertions for upgrade parser."""
        _unit_test_parse_version_for_compare_rejects_invalid_tokens()

    def test_main_invokes_run_and_exits_with_code(self):
        """Run main-entrypoint run/exit-code assertions."""
        _unit_test_main_invokes_run_and_exits_with_code()
