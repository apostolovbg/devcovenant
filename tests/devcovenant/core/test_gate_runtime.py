"""Mirrored tests for devcovenant.core.gate_runtime."""

from __future__ import annotations

import importlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

MODULE = "devcovenant.core.gate_runtime"


def _write_changelog_registry(
    repo_root: Path, metadata_lines: list[str] | None = None
) -> None:
    """Write one minimal tracked registry payload for changelog metadata."""
    lines = metadata_lines or [
        "      main_changelog: CHANGELOG.md",
        "      header_doc_suffixes:",
        "      - .md",
        "      header_keys:",
        "      - Last Updated",
        "      header_scan_lines: 4",
    ]
    registry_path = repo_root / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  schema_version: 1",
                "  registry_layout: single-root",
                "policies:",
                "  changelog-coverage:",
                "    metadata:",
                *lines,
                "profiles: {}",
                "inventory: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "project-governance:",
                "  stage: stable",
                "  maintenance_stance: active",
                "  compatibility_policy: breaking-allowed",
                "  versioning_mode: versioned",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _changelog_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _changelog_latest_entry_skips_managed_and_fenced_blocks() -> None:
    """Top-entry extraction should skip managed blocks and fenced examples."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_changelog_registry(repo_root)
        changelog_path = repo_root / "CHANGELOG.md"
        changelog_path.write_text(
            "\n".join(
                [
                    "# Changelog",
                    "",
                    "## Log changes here",
                    "<!-- DEVCOV:BEGIN -->",
                    "managed block",
                    "<!-- DEVCOV:END -->",
                    "```markdown",
                    "- 2026-01-01",
                    "```",
                    "## Version 0.2.6",
                    "- 2026-02-27",
                    "  - Change: add first change. Files: CHANGELOG.md",
                    "  - Why: add first why. Files: CHANGELOG.md",
                    "  - Impact: add first impact. Files: CHANGELOG.md",
                    "- 2026-02-26",
                    "  - Change: add second change. Files: CHANGELOG.md",
                    "  - Why: add second why. Files: CHANGELOG.md",
                    "  - Impact: add second impact. Files: CHANGELOG.md",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        entry = module._latest_changelog_entry(repo_root)
        assert entry.startswith("- 2026-02-27")
        assert "first change" in entry
        assert "second change" not in entry


def _changelog_latest_entry_stops_before_next_version_heading() -> None:
    """Top-entry extraction should stop at the next version heading."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_changelog_registry(repo_root)
        changelog_path = repo_root / "CHANGELOG.md"
        changelog_path.write_text(
            "\n".join(
                [
                    "# Changelog",
                    "",
                    "## Log changes here",
                    "## Version 0.2.7",
                    "- 2026-02-28",
                    "  Change: add first change.",
                    "  Why: add first why.",
                    "  Impact: add first impact.",
                    "",
                    "## Version 0.2.6",
                    "- 2026-02-27",
                    "  Change: add second change.",
                    "  Why: add second why.",
                    "  Impact: add second impact.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        entry = module._latest_changelog_entry(repo_root)
        assert entry.startswith("- 2026-02-28")
        assert "## Version 0.2.6" not in entry
        assert "second change" not in entry


def _changelog_resolve_doc_exemption_options_normalizes_metadata() -> None:
    """Doc exemption metadata should normalize list/string/int payloads."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_changelog_registry(
            repo_root,
            metadata_lines=[
                "      main_changelog: CHANGELOG.md",
                "      header_doc_suffixes: .md, .txt",
                "      header_keys:",
                "      - Last Updated",
                "      - Version",
                "      header_scan_lines: -3",
            ],
        )
        suffixes, header_keys, scan_lines = (
            module._resolve_doc_exemption_options(repo_root)
        )
        assert suffixes == [".md", ".txt"]
        assert header_keys == ["Last Updated", "Version"]
        assert scan_lines == 0


def _changelog_entry_fingerprint_is_stable_for_whitespace_noise() -> None:
    """Fingerprint should ignore trailing whitespace differences."""
    module = importlib.import_module(MODULE)
    left = "- 2026-02-27\n  - Change: add example.  \n"
    right = "- 2026-02-27\n  - Change: add example.\n"
    assert module._entry_fingerprint(left) == module._entry_fingerprint(right)


class GateRuntimeChangelogTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run importability sanity check."""
        _changelog_module_importable()

    def test_latest_changelog_entry_skips_managed_and_fenced_blocks(self):
        """Run top-entry extraction filtering assertions."""
        _changelog_latest_entry_skips_managed_and_fenced_blocks()

    def test_latest_changelog_entry_stops_before_next_version_heading(self):
        """Run top-entry extraction boundary assertions."""
        _changelog_latest_entry_stops_before_next_version_heading()

    def test_resolve_doc_exemption_options_normalizes_metadata(self):
        """Run metadata-normalization assertions for doc exemptions."""
        _changelog_resolve_doc_exemption_options_normalizes_metadata()

    def test_entry_fingerprint_is_stable_for_whitespace_noise(self):
        """Run fingerprint stability assertions for trailing whitespace."""
        _changelog_entry_fingerprint_is_stable_for_whitespace_noise()


MODULE = "devcovenant.core.gate_runtime"
_SESSION_SNAPSHOT_REL = "devcovenant/registry/runtime/session_snapshot.json"
_MANAGED_ENV_TARGET = (
    "devcovenant.core.gate_runtime.execution_runtime_module."
    "resolve_managed_environment_for_stage"
)
_AUTO_FIX_TARGET = (
    "devcovenant.core.gate_runtime.execution_runtime_module."
    "resolve_engine_auto_fix_enabled"
)
_CHANGED_SINCE_TARGET = (
    "devcovenant.core.gate_runtime.execution_runtime_module."
    "snapshot_paths_changed_since"
)
_HOOK_FAILURE_LINE = (
    "enforce repository policies "
    "(DevCovenant)................................Failed"
)
_BLOCKED_OUTPUT = (
    "enforce repository policies (DevCovenant)\n"
    "Summary: 0 critical, 1 errors, 0 warnings, 0 info\n"
    "Status: 🚫 BLOCKED (violations >= error threshold)\n"
)
_SAMPLE_DOC_TEXT = (
    "# Sample\n"
    "**Last Updated:** 2026-02-26\n"
    "**Project Version:** 0.0.1\n"
    "<!-- DEVCOV:BEGIN -->\n"
    "Managed text.\n"
    "<!-- DEVCOV:END -->\n"
    "Visible content.\n"
)
_SAMPLE_AGENTS_TEXT = (
    "# AGENTS\n"
    "before workflow\n"
    "<!-- DEVCOV-WORKFLOW:BEGIN -->\n"
    "workflow body\n"
    "<!-- DEVCOV-WORKFLOW:END -->\n"
    "after workflow\n"
)
_SAMPLE_WORKFLOW_TEXT = (
    "name: sample\n"
    "<!-- DEVCOV:BEGIN -->\n"
    "managed: true\n"
    "<!-- DEVCOV:END -->\n"
    "jobs: {}\n"
)


def _gate_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _gate_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _write_gate_registry(repo_root: Path) -> None:
    """Write a minimal tracked registry for changelog metadata."""
    registry_path = repo_root / "devcovenant" / "registry" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  schema_version: 1",
                "  registry_layout: single-root",
                "policies:",
                "  changelog-coverage:",
                "    metadata:",
                "      main_changelog: CHANGELOG.md",
                "      header_doc_suffixes:",
                "      - .md",
                "      header_keys:",
                "      - Last Updated",
                "      header_scan_lines: 4",
                "profiles:",
                "  global:",
                "    category: system",
                "  python:",
                "    category: language",
                "    workflow_runs:",
                "      - id: tests",
                "        enabled: true",
                "        after: verify",
                "        before: close",
                "        order: 100",
                "        runner:",
                "          kind: command_group",
                "          commands:",
                "            - python3 -m unittest discover -v",
                "        success_contract:",
                "          kind: all_commands_exit_zero",
                "        recording:",
                "          record_in_session: true",
                "          summary_label: Tests",
                "inventory: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_gate_runtime_config(repo_root)


def _write_gate_runtime_config(repo_root: Path) -> None:
    """Write the minimal runtime config required by gate helpers."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "project-governance:",
                "  stage: stable",
                "  maintenance_stance: active",
                "  compatibility_policy: breaking-allowed",
                "  versioning_mode: versioned",
                "profiles:",
                "  active:",
                "    - python",
                "engine:",
                "  auto_fix_enabled: false",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_gate_changelog(repo_root: Path) -> None:
    """Write a minimal changelog for gate open fingerprints."""
    changelog_path = repo_root / "CHANGELOG.md"
    changelog_path.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "## Version 0.2.6",
                "- 2026-02-24",
                "  - Change: add baseline entry. Files: CHANGELOG.md",
                "  - Why: add fingerprint seed. Files: CHANGELOG.md",
                "  - Impact: add gate baseline. Files: CHANGELOG.md",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_gate_agents(repo_root: Path) -> None:
    """Write a minimal AGENTS file for hash capture."""
    agents_path = repo_root / "AGENTS.md"
    agents_path.write_text(
        "\n".join(
            [
                "# Agents",
                "",
                "<!-- DEVCOV-WORKFLOW:BEGIN -->",
                "workflow",
                "<!-- DEVCOV-WORKFLOW:END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_gate_session_snapshot(
    repo_root: Path, payload: dict[str, object]
) -> str:
    """Write the gate session companion snapshot payload."""
    snapshot_path = repo_root / _SESSION_SNAPSHOT_REL
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return _SESSION_SNAPSHOT_REL


def _read_gate_session_snapshot(
    repo_root: Path,
) -> dict[str, object]:
    """Read the gate session companion snapshot payload."""
    snapshot_path = repo_root / _SESSION_SNAPSHOT_REL
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def _write_gate_workflow_session(
    repo_root: Path, payload: dict[str, object]
) -> None:
    """Write the runtime workflow-session payload."""
    path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "runtime"
        / "workflow_session.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _gate_open_clears_stale_pre_commit_close() -> None:
    """Open gate should clear stale close-stage pre-commit evidence."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        close_epoch = time.time() + 3600
        status_payload = {
            "session_id": "old-session",
            "session_state": "closed",
            "session_close_epoch": close_epoch,
            "session_close_utc": "2026-02-24T18:00:00+00:00",
            "pre_commit_close_epoch": 10.0,
            "pre_commit_close_utc": "2026-02-24T18:00:00+00:00",
            "pre_commit_close_command": "pre-commit run --all-files",
            "pre_commit_close_notes": "stale",
            "pre_commit_close_cache_enabled": True,
        }
        status_path.write_text(
            json.dumps(status_payload, indent=2) + "\n", encoding="utf-8"
        )
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, return_value=(0, "")),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        updated = json.loads(status_path.read_text(encoding="utf-8"))
        assert updated.get("session_state") == "open"
        assert "pre_commit_close_epoch" not in updated
        assert "pre_commit_close_utc" not in updated
        assert "pre_commit_close_command" not in updated
        assert "pre_commit_close_notes" not in updated
        assert "pre_commit_close_cache_enabled" not in updated


def _gate_open_injects_check_orchestration_env() -> None:
    """Open gate should pass gate-owned check orchestration env to hooks."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        captured_env: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_env(_command, *, env=None):
            """Capture env passed into the pre-commit command wrapper."""
            assert env is not None
            captured_env.update(env)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, side_effect=_capture_env),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        assert captured_env["DEVCOV_DEVFLOW_STAGE"] == "open"
        assert captured_env["DEVCOV_CHECK_APPLY_FIXES"] == "0"
        assert captured_env["DEVCOV_CHECK_RUN_REFRESH"] == "1"
        assert captured_env["DEVCOV_CHECK_CLEAN_BYTECODE"] == "1"


def _gate_open_respects_autofix_enabled_config() -> None:
    """Open gate should enable autofix when config sets it true."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "project-governance:",
                    "  stage: stable",
                    "  maintenance_stance: active",
                    "  compatibility_policy: breaking-allowed",
                    "  versioning_mode: versioned",
                    "engine:",
                    "  auto_fix_enabled: true",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        captured_env: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_env(_command, *, env=None):
            """Capture env passed into the pre-commit command wrapper."""
            assert env is not None
            captured_env.update(env)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, side_effect=_capture_env),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        assert captured_env["DEVCOV_CHECK_APPLY_FIXES"] == "1"


def _gate_gate_child_output_streams_in_normal_mode() -> None:
    """Normal mode should stream gate child output with heartbeat support."""
    module = importlib.import_module(MODULE)
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        """Capture child-run kwargs while returning a successful result."""
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return (type("R", (), {"returncode": 0})(), "hook output")

    with (
        mock.patch.object(
            module.execution_runtime_module,
            "run_child_command_with_output_policy",
            side_effect=_fake_run,
        ),
        mock.patch.object(
            module.execution_runtime_module,
            "resolve_child_output_plan_for_channel",
            return_value=SimpleNamespace(child_output_suppressed=False),
        ),
    ):
        exit_code, output = module._run_command_with_output(
            "pre-commit run --all-files"
        )
    kwargs = dict(captured["kwargs"])
    assert exit_code == 0
    assert output == "hook output"
    assert kwargs["channel"] == "gate_child"
    assert kwargs["capture_combined_output"] is True


def _gate_gate_child_output_is_suppressed_in_quiet_mode() -> None:
    """Quiet mode should suppress gate child output and heartbeat chatter."""
    module = importlib.import_module(MODULE)
    fake_result = (type("R", (), {"returncode": 1})(), "hook output")
    with (
        mock.patch.object(
            module.execution_runtime_module,
            "run_child_command_with_output_policy",
            return_value=fake_result,
        ),
        mock.patch.object(
            module.execution_runtime_module,
            "resolve_child_output_plan_for_channel",
            return_value=SimpleNamespace(child_output_suppressed=True),
        ),
        mock.patch.object(
            module, "_emit_suppressed_failure_tail"
        ) as emit_tail,
    ):
        exit_code, output = module._run_command_with_output(
            "pre-commit run --all-files"
        )
    assert exit_code == 1
    assert output == "hook output"
    emit_tail.assert_called_once_with("hook output")


def _gate_gate_child_output_streams_in_verbose_mode() -> None:
    """Verbose mode should stream gate child output without heartbeat."""
    module = importlib.import_module(MODULE)
    fake_result = (type("R", (), {"returncode": 1})(), "hook output")
    with (
        mock.patch.object(
            module.execution_runtime_module,
            "run_child_command_with_output_policy",
            return_value=fake_result,
        ),
        mock.patch.object(
            module.execution_runtime_module,
            "resolve_child_output_plan_for_channel",
            return_value=SimpleNamespace(child_output_suppressed=False),
        ),
        mock.patch.object(
            module, "_emit_suppressed_failure_tail"
        ) as emit_tail,
    ):
        exit_code, output = module._run_command_with_output(
            "pre-commit run --all-files"
        )
    assert exit_code == 1
    assert output == "hook output"
    emit_tail.assert_not_called()


def _gate_open_targets_snapshot_files_for_pre_commit() -> None:
    """Open gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        tracked_path = repo_root / "tracked_file.py"
        tracked_path.write_text("print('tracked')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_command(command, *, env=None):
            """Capture hook command while preserving open success."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, side_effect=_capture_command),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "tracked_file.py" in rendered
        assert "--all-files" not in rendered


def _gate_open_resolves_managed_python_module_pre_commit() -> None:
    """Open gate should resolve `python -m pre_commit` via managed Python."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        tracked_path = repo_root / "module_target.py"
        tracked_path.write_text("print('module')\n", encoding="utf-8")
        managed_python = repo_root / ".venv" / "bin" / "python"
        captured: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_command(command, *, env=None):
            """Capture the rendered hook command for assertions."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(
                managed_env_target,
                return_value=({"PATH": ""}, str(managed_python)),
            ),
            mock.patch.object(module.shutil, "which", return_value=None),
            mock.patch(run_command_target, side_effect=_capture_command),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        rendered = captured["command"]
        assert rendered.startswith(f"{managed_python} -m pre_commit run")
        assert "--files" in rendered
        assert "module_target.py" in rendered


def _gate_open_avoids_pre_commit_console_script_shims() -> None:
    """Open gate should not depend on a discovered pre-commit shim."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        tracked_path = repo_root / "shim_target.py"
        tracked_path.write_text("print('module')\n", encoding="utf-8")
        managed_python = repo_root / ".venv" / "bin" / "python"
        captured: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_command(command, *, env=None):
            """Capture the rendered hook command for assertions."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(
                managed_env_target,
                return_value=({"PATH": "/tmp/fake-bin"}, str(managed_python)),
            ),
            mock.patch.object(
                module.shutil, "which", return_value="/tmp/fake-bin/pre-commit"
            ),
            mock.patch(run_command_target, side_effect=_capture_command),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        rendered = captured["command"]
        assert rendered.startswith(f"{managed_python} -m pre_commit run")
        assert "--files" in rendered
        assert "shim_target.py" in rendered


def _gate_open_reports_hook_induced_drift_explicitly() -> None:
    """Open gate should report managed drift explicitly when hooks rewrite."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(
                run_command_target,
                return_value=(
                    1,
                    "\n".join(
                        [
                            _HOOK_FAILURE_LINE,
                            "- hook id: devcovenant",
                            "- files were modified by this hook",
                        ]
                    ),
                ),
            ),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"README.md": "before"},
                    {"README.md": "after", "PLAN.md": "after"},
                ],
            ),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 1
        assert any(
            ("hook-induced baseline drift" in line for line in lines)
        ), lines
        assert any(("Hook-changed paths:" in line for line in lines)), lines
        assert any(
            ("README.md" in line and "PLAN.md" in line for line in lines)
        )
        assert any(
            (
                "DevCovenant hook refreshed managed files" in line
                for line in lines
            )
        ), lines


def _gate_verify_targets_snapshot_files_for_pre_commit() -> None:
    """Verify gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "open-verify-target",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-verify-target",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        tracked_path = repo_root / "verify_target.py"
        tracked_path.write_text("print('verify')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        auto_fix_target = _AUTO_FIX_TARGET
        run_hook_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_command(command, env=None):
            """Capture hook command while preserving verify success."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(auto_fix_target, return_value=False),
            mock.patch(run_hook_target, side_effect=_capture_command),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "verify")
        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "verify_target.py" in rendered
        assert "--all-files" not in rendered


def _gate_close_targets_snapshot_files_for_pre_commit() -> None:
    """Close gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_rel = _write_gate_session_snapshot(
            repo_root,
            {
                "last_run_snapshot": {"sample.py": "same"},
                "workflow_run_snapshots": {"tests": {"sample.py": "same"}},
            },
        )
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "open-close-target",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                    "last_run_epoch": 20.0,
                    "last_run_session_id": "open-close-target",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-close-target",
                "session_state": "open",
                "run_ids": ["tests"],
                "session_snapshot_file": snapshot_rel,
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "open-close-target",
                    }
                },
            },
        )
        tracked_path = repo_root / "close_target.py"
        tracked_path.write_text("print('close')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = _MANAGED_ENV_TARGET
        changed_since_target = _CHANGED_SINCE_TARGET
        run_hook_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_command(command, env=None):
            """Capture hook command while preserving close success."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(changed_since_target, return_value=[]),
            mock.patch(run_hook_target, side_effect=_capture_command),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "close")
        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "close_target.py" in rendered
        assert "--all-files" not in rendered


def _gate_open_recovery_requires_explicit_manual_tests() -> None:
    """Recovery open should fail and instruct explicit workflow runs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_rel = _write_gate_session_snapshot(
            repo_root, {"session_close_snapshot": {"sample.py": "old"}}
        )
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "closed-1",
                    "session_state": "closed",
                    "session_close_epoch": 100.0,
                    "session_close_utc": "2026-02-25T11:00:00+00:00",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "closed-1",
                "session_state": "closed",
                "run_ids": ["tests"],
                "session_snapshot_file": snapshot_rel,
                "anchors": {},
                "runs": {},
            },
        )
        original_bytes = status_path.read_bytes()
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        changed_since_target = _CHANGED_SINCE_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(
                changed_since_target,
                return_value={"devcovenant/core/gate_runtime.py"},
            ),
            mock.patch(run_command_target, return_value=(0, "")),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 1
        assert status_path.read_bytes() == original_bytes
        assert any(
            ("requires fresh workflow runs" in line for line in lines)
        ), lines
        assert any(
            (
                "devcovenant run" in line and "devcovenant gate --open" in line
                for line in lines
            )
        ), lines
        assert any(
            ("no internal workflow-run runs" in line for line in lines)
        ), lines


def _gate_open_recovery_allows_fresh_explicit_manual_tests() -> None:
    """Recovery open should proceed when runs are already fresh."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_changelog(repo_root)
        _write_gate_agents(repo_root)
        snapshot_rel = _write_gate_session_snapshot(
            repo_root,
            {
                "session_close_snapshot": {"sample.py": "old"},
                "workflow_run_snapshots": {"tests": {"sample.py": "same"}},
            },
        )
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "closed-1",
                    "session_state": "closed",
                    "session_close_epoch": 100.0,
                    "session_close_utc": "2026-02-25T11:00:00+00:00",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "closed-1",
                "session_state": "closed",
                "run_ids": ["tests"],
                "session_snapshot_file": snapshot_rel,
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "closed-1",
                    }
                },
            },
        )
        managed_env_target = _MANAGED_ENV_TARGET
        run_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )
        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, return_value=(0, "")),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "open")
        assert exit_code == 0
        updated = json.loads(status_path.read_text(encoding="utf-8"))
        snapshot_payload = _read_gate_session_snapshot(repo_root)
        assert updated.get("session_state") == "open"
        assert float(updated.get("pre_commit_open_epoch") or 0.0) > 0.0
        assert snapshot_payload.get("session_open_snapshot") == {
            "sample.py": "same"
        }


def _gate_close_requires_explicit_run_and_rerun_on_hook_changes() -> None:
    """
    Close gate should require explicit run/rerun steps after hook changes.
    """
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-1",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "open-1",
                    }
                },
            },
        )
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        changed_since_target = _CHANGED_SINCE_TARGET
        load_status_target = "devcovenant.core.gate_runtime._load_status"
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(changed_since_target, return_value=[]),
            mock.patch(
                load_status_target,
                return_value={
                    "session_id": "open-1",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "before"}, {"sample.py": "after"}],
            ),
            mock.patch(hook_command_target, return_value=(0, "")),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "close")
        assert exit_code == 1
        assert any(
            ("hook-induced file changes" in line for line in lines)
        ), lines
        assert any(
            (
                "devcovenant run" in line
                and "devcovenant gate --close" in line
                for line in lines
            )
        ), lines
        assert not any(("no internal reruns" in line for line in lines)), lines


def _gate_close_requires_explicit_run_and_rerun_on_stale_tests() -> None:
    """Close gate should require `run` when tests are stale."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-2",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "open-2",
                    }
                },
            },
        )
        _write_gate_session_snapshot(
            repo_root,
            {"workflow_run_snapshots": {"tests": {"sample.py": "old"}}},
        )
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        changed_since_target = _CHANGED_SINCE_TARGET
        load_status_target = "devcovenant.core.gate_runtime._load_status"
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(
                changed_since_target,
                return_value=["devcovenant/core/gate_runtime.py"],
            ),
            mock.patch(
                load_status_target,
                return_value={
                    "session_id": "open-2",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
            mock.patch(hook_command_target, return_value=(0, "")),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "close")
        assert exit_code == 1
        assert any(
            ("fresh workflow runs before closure" in line for line in lines)
        ), lines
        assert any(
            (
                "devcovenant run" in line
                and "devcovenant gate --close" in line
                for line in lines
            )
        ), lines
        assert not any(("no internal reruns" in line for line in lines)), lines


def _gate_close_reports_blocking_devcov_failure_clearly() -> None:
    """Close gate should report blocking DevCovenant failures plainly."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-2",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "open-2",
                    }
                },
            },
        )
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        changed_since_target = _CHANGED_SINCE_TARGET
        load_status_target = "devcovenant.core.gate_runtime._load_status"
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        blocking_output = _BLOCKED_OUTPUT
        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(changed_since_target, return_value=[]),
            mock.patch(
                load_status_target,
                return_value={
                    "session_id": "open-close-1",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
            mock.patch(hook_command_target, return_value=(1, blocking_output)),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "close")
        assert exit_code == 1
        assert any(
            (
                "blocking non-autofixed DevCovenant violations" in line
                for line in lines
            )
        ), lines
        assert any(
            (
                "Fix violations and rerun `devcovenant gate --close`." in line
                for line in lines
            )
        ), lines
        assert not any(
            ("Failing without test reruns" in line for line in lines)
        ), lines


def _gate_verify_requires_open_session() -> None:
    """Verify gate should require an active open session."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        lines: list[str] = []

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with mock.patch.object(
            module, "runtime_print", side_effect=_capture_runtime_print
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "verify")
        assert exit_code == 1
        assert not status_path.exists()
        assert any(("active open session" in line for line in lines)), lines
        assert any(("gate --open" in line for line in lines)), lines


def _gate_verify_runs_without_status_mutation() -> None:
    """Verify gate should avoid lifecycle writes."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "open-verify-1",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                    "session_open_utc": "2026-02-26T18:00:00+00:00",
                    "pre_commit_open_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-verify-1",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        original_bytes = status_path.read_bytes()
        captured: dict[str, object] = {}
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        auto_fix_target = _AUTO_FIX_TARGET
        hook_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_stage(repo_root_arg, stage_arg):
            """Capture managed-env stage token and return no env override."""
            del repo_root_arg
            captured["managed_stage"] = stage_arg
            return (None, None)

        def _capture_hook(_command, env=None):
            """Capture hook env for assertions and report success."""
            assert env is not None
            captured["hook_env"] = dict(env)
            return (0, "")

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, side_effect=_capture_stage),
            mock.patch(auto_fix_target, return_value=False),
            mock.patch(hook_command_target, side_effect=_capture_hook),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "verify")
        assert exit_code == 0
        assert captured["managed_stage"] == "managed"
        hook_env = captured["hook_env"]
        assert hook_env["DEVCOV_DEVFLOW_STAGE"] == ""
        assert hook_env["DEVCOV_CHECK_APPLY_FIXES"] == "0"
        assert hook_env["DEVCOV_CHECK_RUN_REFRESH"] == "1"
        assert hook_env["DEVCOV_CHECK_CLEAN_BYTECODE"] == "1"
        assert status_path.read_bytes() == original_bytes
        assert any(
            (
                "without changing gate session lifecycle state" in line
                for line in lines
            )
        ), lines


def _gate_verify_reports_blocking_devcov_failure() -> None:
    """Verify gate should classify blocking DevCovenant failures."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_gate_registry(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "open-verify-2",
                    "session_state": "open",
                    "session_open_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gate_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-verify-2",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        original_bytes = status_path.read_bytes()
        lines: list[str] = []
        managed_env_target = _MANAGED_ENV_TARGET
        auto_fix_target = _AUTO_FIX_TARGET
        hook_command_target = (
            "devcovenant.core.gate_runtime._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.gate_runtime._current_numstat_snapshot"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        blocking_output = _BLOCKED_OUTPUT
        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(auto_fix_target, return_value=True),
            mock.patch(hook_command_target, return_value=(1, blocking_output)),
            mock.patch(
                snapshot_target,
                side_effect=[{"sample.py": "same"}, {"sample.py": "same"}],
            ),
            mock.patch.object(
                module, "runtime_print", side_effect=_capture_runtime_print
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "verify")
        assert exit_code == 1
        assert status_path.read_bytes() == original_bytes
        assert any(
            (
                "blocking non-autofixed DevCovenant violations" in line
                for line in lines
            )
        ), lines
        assert any(("gate --verify" in line for line in lines)), lines


def _gate_show_gate_status_reports_open_session_read_only() -> None:
    """`show_gate_status` should report session state without mutating file."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_payload = {
            "session_id": "abc123",
            "session_state": "open",
            "pre_commit_open_epoch": 10.0,
            "pre_commit_open_utc": "2026-02-25T11:00:00+00:00",
            "last_run_epoch": 20.0,
            "last_run_utc": "2026-02-25T11:05:00+00:00",
        }
        status_bytes = (
            json.dumps(status_payload, indent=2).encode("utf-8") + b"\n"
        )
        status_path.write_bytes(status_bytes)
        logs_root = repo_root / "devcovenant" / "logs"
        run_dir = logs_root / "20260225T110500000000Z-run"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "run",
                    "status": "success",
                    "artifacts": {
                        "summary_txt": (
                            f"devcovenant/logs/{run_dir.name}/summary.txt"
                        ),
                        "summary_json": (
                            f"devcovenant/logs/{run_dir.name}/summary.json"
                        ),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        runtime_latest = (
            repo_root / "devcovenant" / "registry" / "runtime" / "latest.json"
        )
        runtime_latest.parent.mkdir(parents=True, exist_ok=True)
        runtime_latest.write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "run",
                    "status": "success",
                    "run_dir": f"devcovenant/logs/{run_dir.name}",
                    "summary_txt": (
                        f"devcovenant/logs/{run_dir.name}/summary.txt"
                    ),
                    "summary_json": (
                        f"devcovenant/logs/{run_dir.name}/summary.json"
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines: list[str] = []
        with mock.patch.object(
            module, "runtime_print", side_effect=lines.append
        ):
            exit_code = module.show_gate_status(repo_root)
        assert exit_code == 0
        assert status_path.read_bytes() == status_bytes
        assert "Gate Status: open" in lines
        assert "Session ID: abc123" in lines
        assert "Last Stage: run" in lines
        assert "Session Open: 2026-02-25T11:00:00+00:00" in lines
        assert "Last Workflow Run: 2026-02-25T11:05:00+00:00" in lines
        assert any(
            (
                "Latest Relevant Logs: devcovenant/logs/" in line
                for line in lines
            )
        )


def _gate_show_gate_status_handles_missing_and_malformed_status() -> None:
    """`show_gate_status` should be non-destructive for bad/missing files."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        missing_lines: list[str] = []
        with mock.patch.object(
            module, "runtime_print", side_effect=missing_lines.append
        ):
            missing_exit = module.show_gate_status(repo_root)
        assert missing_exit == 0
        assert "Gate Status: missing" in missing_lines
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        malformed_bytes = b"{not-json\n"
        status_path.write_bytes(malformed_bytes)
        malformed_lines: list[str] = []
        with mock.patch.object(
            module, "runtime_print", side_effect=malformed_lines.append
        ):
            malformed_exit = module.show_gate_status(repo_root)
        assert malformed_exit == 0
        assert status_path.read_bytes() == malformed_bytes
        assert "Gate Status: malformed" in malformed_lines
        assert any((line.startswith("Error: ") for line in malformed_lines))


def _gate_show_gate_status_reports_verify_stage() -> None:
    """`show_gate_status` should report the public `verify` lifecycle stage."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "verify-1",
                    "session_state": "open",
                    "pre_commit_open_epoch": 10.0,
                    "pre_commit_open_utc": "2026-02-25T11:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        workflow_session_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "workflow_session.json"
        )
        workflow_session_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "session_id": "verify-1",
                    "session_state": "open",
                    "anchors": {
                        "verify": {
                            "id": "verify",
                            "status": "passed",
                            "last_run_utc": "2026-02-25T11:02:00+00:00",
                            "last_run_epoch": 12.0,
                            "commands": ["devcovenant gate --verify"],
                        }
                    },
                    "runs": {},
                    "run_ids": ["tests"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines: list[str] = []
        with mock.patch.object(
            module, "runtime_print", side_effect=lines.append
        ):
            exit_code = module.show_gate_status(repo_root)
        assert exit_code == 0
        assert "Gate Status: open" in lines
        assert "Session ID: verify-1" in lines
        assert "Last Stage: verify" in lines


def _gate_status_pointer_skips_current_gate_status_run() -> None:
    """Status pointer should prefer the prior non-status run over itself."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        run_logging = (
            module.execution_runtime_module.run_logging_runtime_module
        )
        run_logging.create_run_log_context(
            repo_root, "run", ["devcovenant", "run"]
        )
        current = run_logging.create_run_log_context(
            repo_root, "gate", ["devcovenant", "gate", "--status"]
        )
        module.execution_runtime_module.set_active_run_log_context(current)
        try:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
        finally:
            module.execution_runtime_module.clear_active_run_log_context()
        assert pointer is None


def _gate_latest_pointer_wrapper_delegates_to_status_helper() -> None:
    """Gate latest-pointer helper should delegate to the status helper seam."""
    module = importlib.import_module(MODULE)
    sentinel = {"run_id": "delegated-run"}
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with mock.patch.object(
            module, "_resolve_latest_pointer_impl", return_value=sentinel
        ) as patched:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
    patched.assert_called_once_with(repo_root)
    assert pointer is sentinel


def _gate_show_gate_status_reports_closed_session() -> None:
    """`show_gate_status` should report closed-session status fields."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "closed-1",
                    "session_state": "closed",
                    "pre_commit_open_epoch": 10.0,
                    "pre_commit_open_utc": "2026-02-25T11:00:00+00:00",
                    "last_run_epoch": 20.0,
                    "last_run_utc": "2026-02-25T11:10:00+00:00",
                    "pre_commit_close_epoch": 30.0,
                    "pre_commit_close_utc": "2026-02-25T11:20:00+00:00",
                    "session_close_utc": "2026-02-25T11:20:01+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines: list[str] = []
        with mock.patch.object(
            module, "runtime_print", side_effect=lines.append
        ):
            exit_code = module.show_gate_status(repo_root)
        assert exit_code == 0
        assert "Gate Status: closed" in lines
        assert "Session ID: closed-1" in lines
        assert "Last Stage: close" in lines
        assert "Session Close: 2026-02-25T11:20:01+00:00" in lines


class GateRuntimeGateTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _gate_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _gate_module_has_public_symbols()

    def test_open_clears_stale_pre_commit_close(self):
        """Run open-gate stale close evidence cleanup check."""
        _gate_open_clears_stale_pre_commit_close()

    def test_open_injects_check_orchestration_env(self):
        """Run open-gate env injection assertions for local check hooks."""
        _gate_open_injects_check_orchestration_env()

    def test_open_respects_autofix_enabled_config(self):
        """Run open-gate autofix toggle assertions from config."""
        _gate_open_respects_autofix_enabled_config()

    def test_gate_child_output_streams_in_normal_mode(self):
        """Run gate-child normal-mode streaming policy assertions."""
        _gate_gate_child_output_streams_in_normal_mode()

    def test_gate_child_output_is_suppressed_in_quiet_mode(self):
        """Run gate-child quiet-mode suppression policy assertions."""
        _gate_gate_child_output_is_suppressed_in_quiet_mode()

    def test_gate_child_output_streams_in_verbose_mode(self):
        """Run gate-child verbose-mode streaming policy assertions."""
        _gate_gate_child_output_streams_in_verbose_mode()

    def test_open_targets_snapshot_files_for_pre_commit(self):
        """Run open-gate snapshot target coverage assertions."""
        _gate_open_targets_snapshot_files_for_pre_commit()

    def test_open_resolves_managed_python_module_pre_commit(self):
        """Run open-gate managed-python module-resolution assertions."""
        _gate_open_resolves_managed_python_module_pre_commit()

    def test_open_avoids_pre_commit_console_script_shims(self):
        """Run open-gate console-script-independence assertions."""
        _gate_open_avoids_pre_commit_console_script_shims()

    def test_open_reports_hook_induced_drift_explicitly(self):
        """Run open-gate explicit drift-reporting assertions."""
        _gate_open_reports_hook_induced_drift_explicitly()

    def test_verify_targets_snapshot_files_for_pre_commit(self):
        """Run verify-gate snapshot target coverage assertions."""
        _gate_verify_targets_snapshot_files_for_pre_commit()

    def test_close_targets_snapshot_files_for_pre_commit(self):
        """Run close-gate snapshot target coverage assertions."""
        _gate_close_targets_snapshot_files_for_pre_commit()

    def test_open_recovery_requires_explicit_manual_tests(self):
        """Run open-recovery explicit-test instruction assertions."""
        _gate_open_recovery_requires_explicit_manual_tests()

    def test_open_recovery_allows_fresh_explicit_manual_tests(self):
        """Run open-recovery success assertions when tests are fresh."""
        _gate_open_recovery_allows_fresh_explicit_manual_tests()

    def test_close_requires_explicit_run_and_rerun_on_hook_changes(self):
        """Run close-gate explicit run/rerun assertions for hook changes."""
        _gate_close_requires_explicit_run_and_rerun_on_hook_changes()

    def test_close_requires_explicit_run_and_rerun_on_stale_tests(self):
        """Run close-gate stale-stage explicit run/rerun assertions."""
        _gate_close_requires_explicit_run_and_rerun_on_stale_tests()

    def test_close_reports_blocking_devcov_failure_clearly(self):
        """Run close-gate blocking-DevCovenant message clarity assertions."""
        _gate_close_reports_blocking_devcov_failure_clearly()

    def test_verify_requires_open_session(self):
        """Run verify-gate open-session requirement assertions."""
        _gate_verify_requires_open_session()

    def test_verify_runs_without_status_mutation(self):
        """Run verify-gate non-lifecycle hook sweep assertions."""
        _gate_verify_runs_without_status_mutation()

    def test_verify_reports_blocking_devcov_failure(self):
        """Run verify-gate blocking failure assertions."""
        _gate_verify_reports_blocking_devcov_failure()

    def test_show_gate_status_reports_open_session_read_only(self):
        """Run gate-status open-session read-only reporting assertions."""
        _gate_show_gate_status_reports_open_session_read_only()

    def test_show_gate_status_handles_missing_and_malformed_status(self):
        """Run gate-status missing/malformed read-only handling assertions."""
        _gate_show_gate_status_handles_missing_and_malformed_status()

    def test_show_gate_status_reports_verify_stage(self):
        """Run gate-status `verify` reporting assertions."""
        _gate_show_gate_status_reports_verify_stage()

    def test_status_pointer_skips_current_gate_status_run(self):
        """Run strict-pointer assertions for current `gate --status` runs."""
        _gate_status_pointer_skips_current_gate_status_run()

    def test_latest_pointer_wrapper_delegates_to_status_helper(self):
        """Run gate-wrapper delegation assertions for status helper seam."""
        _gate_latest_pointer_wrapper_delegates_to_status_helper()

    def test_show_gate_status_reports_closed_session(self):
        """Run gate-status closed-session reporting assertions."""
        _gate_show_gate_status_reports_closed_session()


MODULE = "devcovenant.core.gate_runtime"


def _session_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _session_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


class GateRuntimeSessionTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _session_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _session_module_has_public_symbols()


MODULE = "devcovenant.core.gate_runtime"


def _snapshot_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _snapshot_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _snapshot_snapshot_paths_changed_since_ignores_equal_epoch_boundary():
    """Equal-microsecond mtimes should not be treated as post-epoch changes."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        sample = repo_root / "sample.txt"
        sample.write_text("x\n", encoding="utf-8")
        epoch = 1000.123456
        equal_ns = 1000123456000
        later_ns = equal_ns + 2000
        os.utime(sample, ns=(equal_ns, equal_ns))
        assert module.snapshot_paths_changed_since(repo_root, epoch) == set()
        os.utime(sample, ns=(later_ns, later_ns))
        assert module.snapshot_paths_changed_since(repo_root, epoch) == {
            "sample.txt"
        }


def _snapshot_public_session_snapshot_helpers_are_deterministic() -> None:
    """Public helper APIs should produce deterministic, scoped outputs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "README.md").write_text(
            _SAMPLE_DOC_TEXT,
            encoding="utf-8",
        )
        (repo_root / "AGENTS.md").write_text(
            _SAMPLE_AGENTS_TEXT,
            encoding="utf-8",
        )
        workflow_path = repo_root / ".github" / "workflows" / "sample.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(
            _SAMPLE_WORKFLOW_TEXT,
            encoding="utf-8",
        )
        yaml_workflow_path = (
            repo_root / ".github" / "workflows" / "sample.yaml"
        )
        yaml_workflow_path.write_text(
            _SAMPLE_WORKFLOW_TEXT,
            encoding="utf-8",
        )
        (repo_root / "sample.py").write_text("value = 1\n", encoding="utf-8")
        pycache_dir = repo_root / ".gha-pycache" / "tmp"
        pycache_dir.mkdir(parents=True, exist_ok=True)
        (pycache_dir / "sample.cpython-311.pyc").write_bytes(b"x")
        (repo_root / "scratch.pyc").write_bytes(b"x")
        current_paths = module.capture_current_snapshot_paths(repo_root)
        assert "AGENTS.md" in current_paths
        assert "README.md" in current_paths
        assert "sample.py" in current_paths
        assert ".gha-pycache/tmp/sample.cpython-311.pyc" not in current_paths
        assert "scratch.pyc" not in current_paths
        current_snapshot = module.capture_current_numstat_snapshot(repo_root)
        assert "sample.py" in current_snapshot
        assert current_snapshot["sample.py"].endswith("\tsample.py")
        assert (
            ".gha-pycache/tmp/sample.cpython-311.pyc" not in current_snapshot
        )
        assert "scratch.pyc" not in current_snapshot
        assert module.snapshot_row_style(current_snapshot) == "filesystem_hash"
        assert (
            module.snapshot_row_style({"a.py": "1\t1\ta.py"})
            == "unsupported_legacy"
        )
        assert module.snapshot_row_style({}) == "empty"
        changed = module.changed_numstat_paths(
            {"a.py": "old\ta.py"}, {"a.py": "new\ta.py", "b.py": "hash\tb.py"}
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
            {"a.py": " hash\ta.py "}, field_name="session_open_snapshot"
        )
        assert normalized == {"a.py": "hash\ta.py"}
        try:
            module.normalize_snapshot_rows(
                [], field_name="session_open_snapshot"
            )
        except ValueError as exc:
            assert "session_open_snapshot" in str(exc)
        else:
            raise AssertionError("Expected normalize_snapshot_rows to fail")
        session_delta = module.session_delta_paths(
            repo_root,
            {"a.py": "old\ta.py"},
            {"a.py": "new\ta.py", "b.py": "hash\tb.py"},
        )
        assert session_delta == {"a.py", "b.py"}
        try:
            module.session_delta_paths(
                repo_root,
                {"legacy.py": "1\t1\tlegacy.py"},
                current_snapshot,
                session_open_epoch=1.0,
            )
        except ValueError as exc:
            assert "legacy snapshot rows" in str(exc)
            assert "gate --open" in str(exc)
        else:
            raise AssertionError(
                "Expected legacy snapshot rows to be rejected."
            )
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


def _snapshot_active_profile_ignore_dirs_are_honored() -> None:
    """Profile ignore dirs should affect gate-open snapshot collection."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "profiles:",
                    "  active:",
                    "  - userproject",
                    "engine:",
                    "  ignore_dirs: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        profile_path = (
            repo_root
            / "devcovenant"
            / "custom"
            / "profiles"
            / "userproject"
            / "userproject.yaml"
        )
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            "\n".join(
                [
                    "version: 1",
                    "profile: userproject",
                    "category: custom",
                    "ignore_dirs:",
                    "  - data",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (repo_root / "README.md").write_text(
            "snapshot root\n", encoding="utf-8"
        )
        ignored_file = repo_root / "data" / "research" / "paper.txt"
        ignored_file.parent.mkdir(parents=True, exist_ok=True)
        ignored_file.write_text("paper\n", encoding="utf-8")
        current_paths = module.capture_current_snapshot_paths(repo_root)
        current_snapshot = module.capture_current_numstat_snapshot(repo_root)
        assert "README.md" in current_paths
        assert "data/research/paper.txt" not in current_paths
        assert "data/research/paper.txt" not in current_snapshot


class GateRuntimeSnapshotTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _snapshot_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _snapshot_module_has_public_symbols()

    def test_snapshot_paths_changed_since_ignores_equal_epoch_boundary(self):
        """Run epoch-boundary false-positive regression assertions."""
        _snapshot_snapshot_paths_changed_since_ignores_equal_epoch_boundary()

    def test_public_session_snapshot_helpers_are_deterministic(self):
        """Run symbol-level assertions for public helper coverage."""
        _snapshot_public_session_snapshot_helpers_are_deterministic()

    def test_active_profile_ignore_dirs_are_honored(self):
        """Run active-profile ignore-dir regression assertions."""
        _snapshot_active_profile_ignore_dirs_are_honored()


MODULE = "devcovenant.core.gate_runtime"


def _write_status_payload(repo_root: Path, payload: dict[str, object]) -> Path:
    """Write one gate status payload under the runtime registry path."""
    status_path = (
        repo_root / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return status_path


def _write_status_workflow_session(
    repo_root: Path, payload: dict[str, object]
) -> Path:
    """Write one workflow-session payload under the runtime registry path."""
    session_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "runtime"
        / "workflow_session.json"
    )
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return session_path


def _status_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _status_load_status_rejects_non_mapping_payload() -> None:
    """Status loader should reject non-object JSON payloads."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "gate_status.json"
        path.write_text("[1, 2, 3]\n", encoding="utf-8")
        with unittest.TestCase().assertRaises(ValueError):
            module._load_status(path)


def _status_latest_pointer_skips_active_status_run() -> None:
    """Pointer resolver should skip the active `gate --status` run."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        run_logging = (
            module.execution_runtime_module.run_logging_runtime_module
        )
        run_logging.create_run_log_context(
            repo_root, "run", ["devcovenant", "run"]
        )
        current = run_logging.create_run_log_context(
            repo_root, "gate", ["devcovenant", "gate", "--status"]
        )
        module.execution_runtime_module.set_active_run_log_context(current)
        try:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
        finally:
            module.execution_runtime_module.clear_active_run_log_context()
        assert pointer is None


def _status_gate_status_summary_lines_report_open_session() -> None:
    """Summary lines should include open-session fields and latest pointer."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_status_payload(
            repo_root,
            {
                "session_id": "open-1",
                "session_state": "open",
                "pre_commit_open_epoch": 10.0,
                "pre_commit_open_utc": "2026-02-27T06:00:00+00:00",
                "last_run_epoch": 20.0,
                "last_run_utc": "2026-02-27T06:05:00+00:00",
            },
        )
        logs_root = repo_root / "devcovenant" / "logs"
        run_dir = logs_root / "20260227T060500000000Z-run"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "run",
                    "status": "success",
                    "artifacts": {
                        "summary_txt": (
                            f"devcovenant/logs/{run_dir.name}/summary.txt"
                        ),
                        "summary_json": (
                            f"devcovenant/logs/{run_dir.name}/summary.json"
                        ),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        runtime_latest = (
            repo_root / "devcovenant" / "registry" / "runtime" / "latest.json"
        )
        runtime_latest.parent.mkdir(parents=True, exist_ok=True)
        runtime_latest.write_text(
            json.dumps(
                {
                    "run_id": run_dir.name,
                    "command_name": "run",
                    "status": "success",
                    "run_dir": f"devcovenant/logs/{run_dir.name}",
                    "summary_txt": (
                        f"devcovenant/logs/{run_dir.name}/summary.txt"
                    ),
                    "summary_json": (
                        f"devcovenant/logs/{run_dir.name}/summary.json"
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = module._gate_status_summary_lines(repo_root)
        assert "Gate Status: open" in lines
        assert "Session ID: open-1" in lines
        assert "Last Stage: run" in lines
        assert "Session Open: 2026-02-27T06:00:00+00:00" in lines
        assert "Last Workflow Run: 2026-02-27T06:05:00+00:00" in lines
        assert any(
            (
                "Latest Relevant Logs: devcovenant/logs/" in line
                for line in lines
            )
        )


def _status_gate_status_summary_lines_report_verify_stage() -> None:
    """Summary lines should report `verify` from workflow-session anchors."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_status_payload(
            repo_root,
            {
                "session_id": "open-verify-1",
                "session_state": "open",
                "pre_commit_open_epoch": 10.0,
                "pre_commit_open_utc": "2026-02-27T06:00:00+00:00",
            },
        )
        _write_status_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "session_id": "open-verify-1",
                "session_state": "open",
                "anchors": {
                    "verify": {
                        "id": "verify",
                        "status": "passed",
                        "last_run_utc": "2026-02-27T06:02:00+00:00",
                        "last_run_epoch": 12.0,
                        "commands": ["devcovenant gate --verify"],
                    }
                },
                "runs": {},
                "run_ids": ["tests"],
            },
        )
        lines = module._gate_status_summary_lines(repo_root)
        assert "Gate Status: open" in lines
        assert "Session ID: open-verify-1" in lines
        assert "Last Stage: verify" in lines


class GateRuntimeStatusTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run importability sanity check."""
        _status_module_importable()

    def test_load_status_rejects_non_mapping_payload(self):
        """Run status-loader payload-shape validation assertions."""
        _status_load_status_rejects_non_mapping_payload()

    def test_latest_pointer_skips_active_status_run(self):
        """Run latest-pointer strict-pointer assertions for active runs."""
        _status_latest_pointer_skips_active_status_run()

    def test_gate_status_summary_lines_report_open_session(self):
        """Run gate-status summary line assertions for open sessions."""
        _status_gate_status_summary_lines_report_open_session()

    def test_gate_status_summary_lines_report_verify_stage(self):
        """Run gate-status summary line assertions for `verify` sessions."""
        _status_gate_status_summary_lines_report_verify_stage()


MODULE = "devcovenant.core.gate_runtime"


def _write_status_validation_payload(path: Path, payload: object) -> None:
    """Write one gate-status payload fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _status_validation_valid_payload_passes() -> None:
    """Valid gate-status payloads should pass flow-owned validation."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status_validation_payload(
            status_path,
            {
                "last_run_utc": "2026-03-26T12:00:00+00:00",
                "commands": ["devcovenant run"],
            },
        )
        payload = module.validate_gate_status_payload(status_path)
        assert payload["commands"] == ["devcovenant run"]


def _status_validation_missing_timestamp_fails() -> None:
    """Missing `last_run_utc` should raise an explicit validation error."""
    module = importlib.import_module(MODULE)
    case = unittest.TestCase()
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status_validation_payload(
            status_path, {"commands": ["devcovenant run"]}
        )
        with case.assertRaisesRegex(ValueError, "last_run_utc"):
            module.validate_gate_status_payload(status_path)


def _status_validation_empty_commands_fail() -> None:
    """Empty command lists should be rejected by validation."""
    module = importlib.import_module(MODULE)
    case = unittest.TestCase()
    with tempfile.TemporaryDirectory() as temp_dir:
        status_path = Path(temp_dir) / "gate_status.json"
        _write_status_validation_payload(
            status_path,
            {
                "last_run_utc": "2026-03-26T12:00:00+00:00",
                "commands": ["", "  "],
            },
        )
        with case.assertRaisesRegex(
            ValueError, "at least one executed workflow command"
        ):
            module.validate_gate_status_payload(status_path)


class GateRuntimeStatusValidationTests(unittest.TestCase):
    """unittest wrappers for flow-owned gate-status validation tests."""

    def test_valid_payload_passes(self):
        """Run valid gate-status payload assertions."""
        _status_validation_valid_payload_passes()

    def test_missing_timestamp_fails(self):
        """Run timestamp validation assertions."""
        _status_validation_missing_timestamp_fails()

    def test_empty_commands_fail(self):
        """Run commands validation assertions."""
        _status_validation_empty_commands_fail()


MODULE = "devcovenant.core.gate_runtime"


def _workflow_session_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _workflow_session_workflow_session_round_trip_uses_runtime_registry() -> (
    None
):
    """Workflow-session payloads should round-trip through runtime storage."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
            "anchors": {"open": {"status": "passed"}},
            "runs": {"tests": {"status": "passed"}},
            "run_ids": ["tests"],
        }
        written = module.write_workflow_session(repo_root, payload)
        loaded = module.load_workflow_session(repo_root)
        assert written == module.workflow_session_path(repo_root)
        assert written.exists()
        assert loaded["session_id"] == "demo-session"
        assert loaded["anchors"] == {"open": {"status": "passed"}}
        assert loaded["runs"] == {"tests": {"status": "passed"}}
        assert loaded["run_ids"] == ["tests"]


def _workflow_session_run_snapshots_share_the_session_snapshot_file() -> None:
    """Run snapshots should merge into and resolve from session snapshots."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
        }
        snapshot = {"sample.py": "hash\tsample.py"}
        snapshot_rel_path, merged_payload = module.merge_run_snapshot(
            repo_root, payload, "tests", snapshot
        )
        resolved = module.resolve_run_snapshot(
            repo_root, merged_payload, "tests"
        )
        assert snapshot_rel_path.endswith("session_snapshot.json")
        assert resolved == snapshot


def _workflow_session_workflow_session_write_drops_removed_fields() -> None:
    """Workflow-session writes should keep only the current session shape."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        payload = {
            "schema_version": module.SCHEMA_VERSION,
            "session_id": "demo-session",
            "session_state": "open",
            "anchors": {
                "open": {
                    "status": "passed",
                    "last_run_utc": "2026-03-26T12:00:00+00:00",
                    "commands": ["devcovenant gate --open"],
                    "last_run": "2026-03-26T12:00:00+00:00",
                    "command": "devcovenant gate --open",
                }
            },
            "runs": {
                "tests": {
                    "status": "passed",
                    "last_run_utc": "2026-03-26T12:05:00+00:00",
                    "commands": ["python3 -m unittest discover -v"],
                    "last_run": "2026-03-26T12:05:00+00:00",
                    "command": "pytest && python3 -m unittest discover -v",
                }
            },
            "run_ids": ["tests"],
            "required_run_ids": ["tests", "legacy"],
        }
        written = module.write_workflow_session(repo_root, payload)
        loaded = module.load_workflow_session(repo_root)
        written_payload = written.read_text(encoding="utf-8")
        assert (
            loaded["anchors"]["open"]["last_run_utc"]
            == "2026-03-26T12:00:00+00:00"
        )
        assert loaded["anchors"]["open"]["commands"] == [
            "devcovenant gate --open"
        ]
        assert "last_run" not in loaded["anchors"]["open"]
        assert "command" not in loaded["anchors"]["open"]
        assert (
            loaded["runs"]["tests"]["last_run_utc"]
            == "2026-03-26T12:05:00+00:00"
        )
        assert loaded["runs"]["tests"]["commands"] == [
            "python3 -m unittest discover -v"
        ]
        assert "last_run" not in loaded["runs"]["tests"]
        assert "command" not in loaded["runs"]["tests"]
        assert loaded["run_ids"] == ["tests"]
        assert "required_run_ids" not in written_payload


class GateRuntimeWorkflowSessionTests(unittest.TestCase):
    """unittest wrappers for workflow-session runtime checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _workflow_session_module_importable()

    def test_workflow_session_round_trip_uses_runtime_registry(self):
        """Run workflow-session persistence regression assertions."""
        _workflow_session_workflow_session_round_trip_uses_runtime_registry()

    def test_run_snapshots_share_the_session_snapshot_file(self):
        """Run workflow-session snapshot regression assertions."""
        _workflow_session_run_snapshots_share_the_session_snapshot_file()

    def test_workflow_session_write_drops_removed_fields(self):
        """Run workflow-session field-filtering regression assertions."""
        _workflow_session_workflow_session_write_drops_removed_fields()


MODULE = "devcovenant.core.gate_runtime"


class GateRuntimeTests(unittest.TestCase):
    """unittest wrappers for mirrored collector tests."""

    def test_module_importable(self) -> None:
        """Collector module should still point at the mirrored source."""
        assert importlib.import_module(MODULE) is not None
