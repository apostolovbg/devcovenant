"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

MODULE = "devcovenant.core.flow.gate"
_SESSION_SNAPSHOT_REL = "devcovenant/registry/runtime/session_snapshot.json"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _write_policy_registry(repo_root: Path) -> None:
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
                "        after: mid",
                "        before: end",
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
    _write_runtime_config(repo_root)


def _write_runtime_config(repo_root: Path) -> None:
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


def _write_changelog(repo_root: Path) -> None:
    """Write a minimal changelog for gate start fingerprints."""
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


def _write_agents(repo_root: Path) -> None:
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


def _write_session_snapshot(
    repo_root: Path,
    payload: dict[str, object],
) -> str:
    """Write the gate session companion snapshot payload."""
    snapshot_path = repo_root / _SESSION_SNAPSHOT_REL
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return _SESSION_SNAPSHOT_REL


def _read_session_snapshot(repo_root: Path) -> dict[str, object]:
    """Read the gate session companion snapshot payload."""
    snapshot_path = repo_root / _SESSION_SNAPSHOT_REL
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def _write_workflow_session(
    repo_root: Path,
    payload: dict[str, object],
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
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _unit_test_start_clears_stale_pre_commit_end() -> None:
    """Start gate should clear stale end-stage pre-commit evidence."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        end_epoch = time.time() + 3600
        status_payload = {
            "session_id": "old-session",
            "session_state": "closed",
            "session_end_epoch": end_epoch,
            "session_end_utc": "2026-02-24T18:00:00+00:00",
            "pre_commit_end_epoch": 10.0,
            "pre_commit_end_utc": "2026-02-24T18:00:00+00:00",
            "pre_commit_end_command": "pre-commit run --all-files",
            "pre_commit_end_notes": "stale",
            "pre_commit_end_cache_enabled": True,
        }
        status_path.write_text(
            json.dumps(status_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, return_value=(0, "")),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")
        assert exit_code == 0
        updated = json.loads(status_path.read_text(encoding="utf-8"))
        assert updated.get("session_state") == "open"
        assert "pre_commit_end_epoch" not in updated
        assert "pre_commit_end_utc" not in updated
        assert "pre_commit_end_command" not in updated
        assert "pre_commit_end_notes" not in updated
        assert "pre_commit_end_cache_enabled" not in updated


def _unit_test_start_injects_check_orchestration_env() -> None:
    """Start gate should pass gate-owned check orchestration env to hooks."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        captured_env: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
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
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        assert captured_env["DEVCOV_DEVFLOW_STAGE"] == "start"
        assert captured_env["DEVCOV_CHECK_APPLY_FIXES"] == "0"
        assert captured_env["DEVCOV_CHECK_RUN_REFRESH"] == "1"
        assert captured_env["DEVCOV_CHECK_CLEAN_BYTECODE"] == "1"


def _unit_test_start_respects_autofix_enabled_config() -> None:
    """Start gate should enable autofix when config sets it true."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
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
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
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
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        assert captured_env["DEVCOV_CHECK_APPLY_FIXES"] == "1"


def _unit_test_gate_child_output_streams_in_normal_mode() -> None:
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


def _unit_test_gate_child_output_is_suppressed_in_quiet_mode() -> None:
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
            module,
            "_emit_suppressed_failure_tail",
        ) as emit_tail,
    ):
        exit_code, output = module._run_command_with_output(
            "pre-commit run --all-files"
        )

    assert exit_code == 1
    assert output == "hook output"
    emit_tail.assert_called_once_with("hook output")


def _unit_test_gate_child_output_streams_in_verbose_mode() -> None:
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
            module,
            "_emit_suppressed_failure_tail",
        ) as emit_tail,
    ):
        exit_code, output = module._run_command_with_output(
            "pre-commit run --all-files"
        )

    assert exit_code == 1
    assert output == "hook output"
    emit_tail.assert_not_called()


def _unit_test_start_targets_snapshot_files_for_pre_commit() -> None:
    """Start gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        tracked_path = repo_root / "tracked_file.py"
        tracked_path.write_text("print('tracked')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )

        def _capture_command(command, *, env=None):
            """Capture hook command while preserving start success."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, side_effect=_capture_command),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "tracked_file.py" in rendered
        assert "--all-files" not in rendered


def _unit_test_start_resolves_managed_python_module_pre_commit() -> None:
    """Start gate should resolve `python -m pre_commit` via managed Python."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        tracked_path = repo_root / "module_target.py"
        tracked_path.write_text("print('module')\n", encoding="utf-8")
        managed_python = repo_root / ".venv" / "bin" / "python"
        captured: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
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
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        rendered = captured["command"]
        assert rendered.startswith(f"{managed_python} -m pre_commit run")
        assert "--files" in rendered
        assert "module_target.py" in rendered


def _unit_test_start_avoids_pre_commit_console_script_shims() -> None:
    """Start gate should not depend on a discovered pre-commit shim."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        tracked_path = repo_root / "shim_target.py"
        tracked_path.write_text("print('module')\n", encoding="utf-8")
        managed_python = repo_root / ".venv" / "bin" / "python"
        captured: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )

        def _capture_command(command, *, env=None):
            """Capture the rendered hook command for assertions."""
            del env
            captured["command"] = str(command)
            return (0, "")

        with (
            mock.patch(
                managed_env_target,
                return_value=(
                    {"PATH": "/tmp/fake-bin"},
                    str(managed_python),
                ),
            ),
            mock.patch.object(
                module.shutil,
                "which",
                return_value="/tmp/fake-bin/pre-commit",
            ),
            mock.patch(run_command_target, side_effect=_capture_command),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        rendered = captured["command"]
        assert rendered.startswith(f"{managed_python} -m pre_commit run")
        assert "--files" in rendered
        assert "shim_target.py" in rendered


def _unit_test_start_reports_hook_induced_drift_explicitly() -> None:
    """Start gate should report managed drift explicitly when hooks rewrite."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        lines: list[str] = []
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
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
                            "enforce repository policies (DevCovenant)"
                            "................................Failed",
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
                    {
                        "README.md": "after",
                        "PLAN.md": "after",
                    },
                ],
            ),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 1
        assert any(
            "hook-induced baseline drift" in line for line in lines
        ), lines
        assert any("Hook-changed paths:" in line for line in lines), lines
        assert any("README.md" in line and "PLAN.md" in line for line in lines)
        assert any(
            "DevCovenant hook refreshed managed files" in line
            for line in lines
        ), lines


def _unit_test_mid_targets_snapshot_files_for_pre_commit() -> None:
    """Mid gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
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
                    "session_id": "open-mid-target",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-mid-target",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        tracked_path = repo_root / "mid_target.py"
        tracked_path.write_text("print('mid')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        auto_fix_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_engine_auto_fix_enabled"
        )
        run_hook_target = "devcovenant.core.flow.gate._run_command_with_output"
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        def _capture_command(command, env=None):
            """Capture hook command while preserving mid success."""
            del env
            captured["command"] = str(command)
            return 0, ""

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(auto_fix_target, return_value=False),
            mock.patch(run_hook_target, side_effect=_capture_command),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "mid")

        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "mid_target.py" in rendered
        assert "--all-files" not in rendered


def _unit_test_end_targets_snapshot_files_for_pre_commit() -> None:
    """End gate should run pre-commit against snapshot file targets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_rel = _write_session_snapshot(
            repo_root,
            {
                "last_run_snapshot": {"sample.py": "same"},
                "workflow_run_snapshots": {"tests": {"sample.py": "same"}},
            },
        )
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "open-end-target",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                    "last_run_epoch": 20.0,
                    "last_run_session_id": "open-end-target",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-end-target",
                "session_state": "open",
                "run_ids": ["tests"],
                "session_snapshot_file": snapshot_rel,
                "anchors": {},
                "runs": {
                    "tests": {
                        "id": "tests",
                        "status": "passed",
                        "last_run_session_id": "open-end-target",
                    }
                },
            },
        )
        tracked_path = repo_root / "end_target.py"
        tracked_path.write_text("print('end')\n", encoding="utf-8")
        captured: dict[str, str] = {}
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        changed_since_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "snapshot_paths_changed_since"
        )
        run_hook_target = "devcovenant.core.flow.gate._run_command_with_output"
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        def _capture_command(command, env=None):
            """Capture hook command while preserving end success."""
            del env
            captured["command"] = str(command)
            return 0, ""

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(changed_since_target, return_value=[]),
            mock.patch(run_hook_target, side_effect=_capture_command),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "end")

        assert exit_code == 0
        rendered = captured["command"]
        assert "--files" in rendered
        assert "end_target.py" in rendered
        assert "--all-files" not in rendered


def _unit_test_start_recovery_requires_explicit_manual_tests() -> None:
    """Recovery start should fail and instruct explicit workflow runs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        status_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_rel = _write_session_snapshot(
            repo_root,
            {"session_end_snapshot": {"sample.py": "old"}},
        )
        status_path.write_text(
            json.dumps(
                {
                    "session_id": "closed-1",
                    "session_state": "closed",
                    "session_end_epoch": 100.0,
                    "session_end_utc": "2026-02-25T11:00:00+00:00",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
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
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        changed_since_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "snapshot_paths_changed_since"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(
                changed_since_target,
                return_value={"devcovenant/core/flow/gate.py"},
            ),
            mock.patch(run_command_target, return_value=(0, "")),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 1
        assert status_path.read_bytes() == original_bytes
        assert any(
            "requires fresh workflow runs" in line for line in lines
        ), lines
        assert any(
            "devcovenant run" in line and "devcovenant gate --start" in line
            for line in lines
        ), lines
        assert any(
            "no internal workflow-run runs" in line for line in lines
        ), lines


def _unit_test_start_recovery_allows_fresh_explicit_manual_tests() -> None:
    """Recovery start should proceed when runs are already fresh."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_changelog(repo_root)
        _write_agents(repo_root)
        snapshot_rel = _write_session_snapshot(
            repo_root,
            {
                "session_end_snapshot": {"sample.py": "old"},
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
                    "session_end_epoch": 100.0,
                    "session_end_utc": "2026-02-25T11:00:00+00:00",
                    "session_snapshot_file": snapshot_rel,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
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
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        run_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(run_command_target, return_value=(0, "")),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "start")

        assert exit_code == 0
        updated = json.loads(status_path.read_text(encoding="utf-8"))
        snapshot_payload = _read_session_snapshot(repo_root)
        assert updated.get("session_state") == "open"
        assert float(updated.get("pre_commit_start_epoch") or 0.0) > 0.0
        assert snapshot_payload.get("session_start_snapshot") == {
            "sample.py": "same"
        }


def _unit_test_end_requires_explicit_run_and_rerun_on_hook_changes() -> None:
    """
    End gate should require explicit run/rerun steps after hook changes.
    """
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_workflow_session(
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
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        changed_since_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "snapshot_paths_changed_since"
        )
        load_status_target = "devcovenant.core.flow.gate._load_status"
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
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
                    "session_start_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "before"},
                    {"sample.py": "after"},
                ],
            ),
            mock.patch(hook_command_target, return_value=(0, "")),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "end")

        assert exit_code == 1
        assert any(
            "hook-induced file changes" in line for line in lines
        ), lines
        assert any(
            "devcovenant run" in line and "devcovenant gate --end" in line
            for line in lines
        ), lines
        assert not any("no internal reruns" in line for line in lines), lines


def _unit_test_end_requires_explicit_run_and_rerun_on_stale_tests() -> None:
    """End gate should require `run` when the configured tests run is stale."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_workflow_session(
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
        _write_session_snapshot(
            repo_root,
            {"workflow_run_snapshots": {"tests": {"sample.py": "old"}}},
        )
        lines: list[str] = []
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        changed_since_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "snapshot_paths_changed_since"
        )
        load_status_target = "devcovenant.core.flow.gate._load_status"
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(
                changed_since_target,
                return_value=["devcovenant/core/flow/gate.py"],
            ),
            mock.patch(
                load_status_target,
                return_value={
                    "session_id": "open-2",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
            mock.patch(hook_command_target, return_value=(0, "")),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "end")

        assert exit_code == 1
        assert any(
            "fresh workflow runs before closure" in line for line in lines
        ), lines
        assert any(
            "devcovenant run" in line and "devcovenant gate --end" in line
            for line in lines
        ), lines
        assert not any("no internal reruns" in line for line in lines), lines


def _unit_test_end_reports_blocking_devcov_failure_clearly() -> None:
    """End gate should report blocking DevCovenant failures plainly."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
        _write_workflow_session(
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
        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        changed_since_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "snapshot_paths_changed_since"
        )
        load_status_target = "devcovenant.core.flow.gate._load_status"
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )
        hook_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        blocking_output = (
            "enforce repository policies (DevCovenant)\n"
            "Summary: 0 critical, 1 errors, 0 warnings, 0 info\n"
            "Status: 🚫 BLOCKED (violations >= error threshold)\n"
        )

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(changed_since_target, return_value=[]),
            mock.patch(
                load_status_target,
                return_value={
                    "session_id": "open-end-1",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                    "last_run_epoch": 20.0,
                },
            ),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
            mock.patch(
                hook_command_target,
                return_value=(1, blocking_output),
            ),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "end")

        assert exit_code == 1
        assert any(
            "blocking non-autofixed DevCovenant violations" in line
            for line in lines
        ), lines
        assert any(
            "Fix violations and rerun `devcovenant gate --end`." in line
            for line in lines
        ), lines
        assert not any(
            "Failing without test reruns" in line for line in lines
        ), lines


def _unit_test_mid_requires_open_session() -> None:
    """Mid gate should require an active open session."""
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
            module,
            "runtime_print",
            side_effect=_capture_runtime_print,
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "mid")

        assert exit_code == 1
        assert not status_path.exists()
        assert any("active open session" in line for line in lines), lines
        assert any("gate --start" in line for line in lines), lines


def _unit_test_mid_runs_without_status_mutation() -> None:
    """Mid gate should run hooks but avoid lifecycle writes to gate status."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
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
                    "session_id": "open-mid-1",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                    "session_start_utc": "2026-02-26T18:00:00+00:00",
                    "pre_commit_start_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-mid-1",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        original_bytes = status_path.read_bytes()
        captured: dict[str, object] = {}
        lines: list[str] = []

        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        auto_fix_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_engine_auto_fix_enabled"
        )
        hook_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        def _capture_stage(repo_root_arg, stage_arg):
            """Capture managed-env stage token and return no env override."""
            del repo_root_arg
            captured["managed_stage"] = stage_arg
            return None, None

        def _capture_hook(_command, env=None):
            """Capture hook env for assertions and report success."""
            assert env is not None
            captured["hook_env"] = dict(env)
            return 0, ""

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
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "mid")

        assert exit_code == 0
        assert captured["managed_stage"] == "command"
        hook_env = captured["hook_env"]
        assert hook_env["DEVCOV_DEVFLOW_STAGE"] == ""
        assert hook_env["DEVCOV_CHECK_APPLY_FIXES"] == "0"
        assert hook_env["DEVCOV_CHECK_RUN_REFRESH"] == "1"
        assert hook_env["DEVCOV_CHECK_CLEAN_BYTECODE"] == "1"
        assert status_path.read_bytes() == original_bytes
        assert any(
            "without changing gate session lifecycle state" in line
            for line in lines
        ), lines


def _unit_test_mid_reports_blocking_devcov_failure() -> None:
    """Mid gate should classify blocking DevCovenant hook failures clearly."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_policy_registry(repo_root)
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
                    "session_id": "open-mid-2",
                    "session_state": "open",
                    "session_start_epoch": 10.0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_workflow_session(
            repo_root,
            {
                "schema_version": 1,
                "workflow_contract_schema_version": 1,
                "session_id": "open-mid-2",
                "session_state": "open",
                "run_ids": ["tests"],
                "anchors": {},
                "runs": {},
            },
        )
        original_bytes = status_path.read_bytes()
        lines: list[str] = []

        managed_env_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_managed_environment_for_stage"
        )
        auto_fix_target = (
            "devcovenant.core.flow.gate.execution_runtime_module."
            "resolve_engine_auto_fix_enabled"
        )
        hook_command_target = (
            "devcovenant.core.flow.gate._run_command_with_output"
        )
        snapshot_target = (
            "devcovenant.core.flow.gate._current_numstat_snapshot"
        )

        def _capture_runtime_print(message, *args, **kwargs):
            """Capture runtime messages while ignoring output kwargs."""
            del args, kwargs
            lines.append(str(message))

        blocking_output = (
            "enforce repository policies (DevCovenant)\n"
            "Summary: 0 critical, 1 errors, 0 warnings, 0 info\n"
            "Status: 🚫 BLOCKED (violations >= error threshold)\n"
        )

        with (
            mock.patch(managed_env_target, return_value=(None, None)),
            mock.patch(auto_fix_target, return_value=True),
            mock.patch(
                hook_command_target,
                return_value=(1, blocking_output),
            ),
            mock.patch(
                snapshot_target,
                side_effect=[
                    {"sample.py": "same"},
                    {"sample.py": "same"},
                ],
            ),
            mock.patch.object(
                module,
                "runtime_print",
                side_effect=_capture_runtime_print,
            ),
        ):
            exit_code = module.run_pre_commit_gate(repo_root, "mid")

        assert exit_code == 1
        assert status_path.read_bytes() == original_bytes
        assert any(
            "blocking non-autofixed DevCovenant violations" in line
            for line in lines
        ), lines
        assert any("gate --mid" in line for line in lines), lines


def _unit_test_show_gate_status_reports_open_session_read_only() -> None:
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
            "pre_commit_start_epoch": 10.0,
            "pre_commit_start_utc": "2026-02-25T11:00:00+00:00",
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
                            "devcovenant/logs/" f"{run_dir.name}/summary.txt"
                        ),
                        "summary_json": (
                            "devcovenant/logs/" f"{run_dir.name}/summary.json"
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
            module,
            "runtime_print",
            side_effect=lines.append,
        ):
            exit_code = module.show_gate_status(repo_root)

        assert exit_code == 0
        assert status_path.read_bytes() == status_bytes
        assert "Gate Status: open" in lines
        assert "Session ID: abc123" in lines
        assert "Last Stage: run" in lines
        assert "Session Start: 2026-02-25T11:00:00+00:00" in lines
        assert "Last Workflow Run: 2026-02-25T11:05:00+00:00" in lines
        assert any(
            "Latest Relevant Logs: devcovenant/logs/" in line for line in lines
        )


def _unit_test_show_gate_status_handles_missing_and_malformed_status() -> None:
    """`show_gate_status` should be non-destructive for bad/missing files."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        missing_lines: list[str] = []
        with mock.patch.object(
            module,
            "runtime_print",
            side_effect=missing_lines.append,
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
            module,
            "runtime_print",
            side_effect=malformed_lines.append,
        ):
            malformed_exit = module.show_gate_status(repo_root)
        assert malformed_exit == 0
        assert status_path.read_bytes() == malformed_bytes
        assert "Gate Status: malformed" in malformed_lines
        assert any(line.startswith("Error: ") for line in malformed_lines)


def _unit_test_show_gate_status_reports_mid_stage() -> None:
    """`show_gate_status` should report the public `mid` lifecycle stage."""

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
                    "session_id": "mid-1",
                    "session_state": "open",
                    "pre_commit_start_epoch": 10.0,
                    "pre_commit_start_utc": "2026-02-25T11:00:00+00:00",
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
                    "session_id": "mid-1",
                    "session_state": "open",
                    "anchors": {
                        "mid": {
                            "id": "mid",
                            "status": "passed",
                            "last_run_utc": "2026-02-25T11:02:00+00:00",
                            "last_run_epoch": 12.0,
                            "commands": ["devcovenant gate --mid"],
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
            module,
            "runtime_print",
            side_effect=lines.append,
        ):
            exit_code = module.show_gate_status(repo_root)

        assert exit_code == 0
        assert "Gate Status: open" in lines
        assert "Session ID: mid-1" in lines
        assert "Last Stage: mid" in lines


def _unit_test_status_pointer_skips_current_gate_status_run() -> None:
    """Status pointer should prefer the prior non-status run over itself."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        run_logging = (
            module.execution_runtime_module.run_logging_runtime_module
        )
        run_logging.create_run_log_context(
            repo_root,
            "run",
            ["devcovenant", "run"],
        )
        current = run_logging.create_run_log_context(
            repo_root,
            "gate",
            ["devcovenant", "gate", "--status"],
        )
        module.execution_runtime_module.set_active_run_log_context(current)
        try:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
        finally:
            module.execution_runtime_module.clear_active_run_log_context()
        assert pointer is None


def _unit_test_latest_pointer_wrapper_delegates_to_status_helper() -> None:
    """Gate latest-pointer helper should delegate to the status helper seam."""
    module = importlib.import_module(MODULE)
    sentinel = {"run_id": "delegated-run"}
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with mock.patch.object(
            module,
            "_resolve_latest_pointer_impl",
            return_value=sentinel,
        ) as patched:
            pointer = module._resolve_latest_relevant_run_pointer(repo_root)
    patched.assert_called_once_with(repo_root)
    assert pointer is sentinel


def _unit_test_show_gate_status_reports_closed_session() -> None:
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
                    "pre_commit_start_epoch": 10.0,
                    "pre_commit_start_utc": "2026-02-25T11:00:00+00:00",
                    "last_run_epoch": 20.0,
                    "last_run_utc": "2026-02-25T11:10:00+00:00",
                    "pre_commit_end_epoch": 30.0,
                    "pre_commit_end_utc": "2026-02-25T11:20:00+00:00",
                    "session_end_utc": "2026-02-25T11:20:01+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lines: list[str] = []
        with mock.patch.object(
            module,
            "runtime_print",
            side_effect=lines.append,
        ):
            exit_code = module.show_gate_status(repo_root)
        assert exit_code == 0
        assert "Gate Status: closed" in lines
        assert "Session ID: closed-1" in lines
        assert "Last Stage: end" in lines
        assert "Session End: 2026-02-25T11:20:01+00:00" in lines


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_start_clears_stale_pre_commit_end(self):
        """Run start-gate stale end evidence cleanup check."""
        _unit_test_start_clears_stale_pre_commit_end()

    def test_start_injects_check_orchestration_env(self):
        """Run start-gate env injection assertions for local check hooks."""
        _unit_test_start_injects_check_orchestration_env()

    def test_start_respects_autofix_enabled_config(self):
        """Run start-gate autofix toggle assertions from config."""
        _unit_test_start_respects_autofix_enabled_config()

    def test_gate_child_output_streams_in_normal_mode(self):
        """Run gate-child normal-mode streaming policy assertions."""
        _unit_test_gate_child_output_streams_in_normal_mode()

    def test_gate_child_output_is_suppressed_in_quiet_mode(self):
        """Run gate-child quiet-mode suppression policy assertions."""
        _unit_test_gate_child_output_is_suppressed_in_quiet_mode()

    def test_gate_child_output_streams_in_verbose_mode(self):
        """Run gate-child verbose-mode streaming policy assertions."""
        _unit_test_gate_child_output_streams_in_verbose_mode()

    def test_start_targets_snapshot_files_for_pre_commit(self):
        """Run start-gate snapshot target coverage assertions."""
        _unit_test_start_targets_snapshot_files_for_pre_commit()

    def test_start_resolves_managed_python_module_pre_commit(self):
        """Run start-gate managed-python module-resolution assertions."""
        _unit_test_start_resolves_managed_python_module_pre_commit()

    def test_start_avoids_pre_commit_console_script_shims(self):
        """Run start-gate console-script-independence assertions."""
        _unit_test_start_avoids_pre_commit_console_script_shims()

    def test_start_reports_hook_induced_drift_explicitly(self):
        """Run start-gate explicit drift-reporting assertions."""
        _unit_test_start_reports_hook_induced_drift_explicitly()

    def test_mid_targets_snapshot_files_for_pre_commit(self):
        """Run mid-gate snapshot target coverage assertions."""
        _unit_test_mid_targets_snapshot_files_for_pre_commit()

    def test_end_targets_snapshot_files_for_pre_commit(self):
        """Run end-gate snapshot target coverage assertions."""
        _unit_test_end_targets_snapshot_files_for_pre_commit()

    def test_start_recovery_requires_explicit_manual_tests(self):
        """Run start-recovery explicit-test instruction assertions."""
        _unit_test_start_recovery_requires_explicit_manual_tests()

    def test_start_recovery_allows_fresh_explicit_manual_tests(self):
        """Run start-recovery success assertions when tests are fresh."""
        _unit_test_start_recovery_allows_fresh_explicit_manual_tests()

    def test_end_requires_explicit_run_and_rerun_on_hook_changes(self):
        """Run end-gate explicit run/rerun assertions for hook changes."""
        _unit_test_end_requires_explicit_run_and_rerun_on_hook_changes()

    def test_end_requires_explicit_run_and_rerun_on_stale_tests(self):
        """Run end-gate stale-stage explicit run/rerun assertions."""
        _unit_test_end_requires_explicit_run_and_rerun_on_stale_tests()

    def test_end_reports_blocking_devcov_failure_clearly(self):
        """Run end-gate blocking-DevCovenant message clarity assertions."""
        _unit_test_end_reports_blocking_devcov_failure_clearly()

    def test_mid_requires_open_session(self):
        """Run mid-gate open-session requirement assertions."""
        _unit_test_mid_requires_open_session()

    def test_mid_runs_without_status_mutation(self):
        """Run mid-gate non-lifecycle hook sweep assertions."""
        _unit_test_mid_runs_without_status_mutation()

    def test_mid_reports_blocking_devcov_failure(self):
        """Run mid-gate blocking-DevCovenant failure messaging assertions."""
        _unit_test_mid_reports_blocking_devcov_failure()

    def test_show_gate_status_reports_open_session_read_only(self):
        """Run gate-status open-session read-only reporting assertions."""
        _unit_test_show_gate_status_reports_open_session_read_only()

    def test_show_gate_status_handles_missing_and_malformed_status(self):
        """Run gate-status missing/malformed read-only handling assertions."""
        _unit_test_show_gate_status_handles_missing_and_malformed_status()

    def test_show_gate_status_reports_mid_stage(self):
        """Run gate-status `mid` reporting assertions."""

        _unit_test_show_gate_status_reports_mid_stage()

    def test_status_pointer_skips_current_gate_status_run(self):
        """Run strict-pointer assertions for current `gate --status` runs."""
        _unit_test_status_pointer_skips_current_gate_status_run()

    def test_latest_pointer_wrapper_delegates_to_status_helper(self):
        """Run gate-wrapper delegation assertions for status helper seam."""
        _unit_test_latest_pointer_wrapper_delegates_to_status_helper()

    def test_show_gate_status_reports_closed_session(self):
        """Run gate-status closed-session reporting assertions."""
        _unit_test_show_gate_status_reports_closed_session()
