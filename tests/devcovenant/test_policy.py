"""Tests for the namespaced `devcovenant policy` CLI command."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from devcovenant import policy
from tests.devcovenant.support import MonkeyPatch


def _unit_test_run_dispatches_declared_policy_command(
    monkeypatch: MonkeyPatch,
) -> None:
    """The policy command should parse args and dispatch runtime actions."""
    captured: dict[str, object] = {}

    def _fake_run_policy_runtime_action(
        repo_root: Path,
        *,
        policy_id: str,
        action: str,
        payload: dict[str, object],
    ) -> dict[str, str]:
        """Capture dispatch arguments and return a stable runtime payload."""
        captured.update(
            {
                "repo_root": repo_root,
                "policy_id": policy_id,
                "action": action,
                "payload": dict(payload),
            }
        )
        return {"message": "Refreshed."}

    monkeypatch.setattr(
        policy,
        "resolve_repo_root",
        lambda require_install=True: Path("/tmp/repo"),
    )

    def _fake_find_policy_command(*_args, **_kwargs):
        """Return the declared dependency-management policy command."""
        return policy.policy_commands_service.PolicyCommandDefinition(
            name="refresh-all",
            help_text="Refresh dependency artifacts.",
            runtime_action="refresh-all",
            mutates_repo=True,
        )

    monkeypatch.setattr(
        policy.policy_commands_service,
        "find_policy_command",
        _fake_find_policy_command,
    )
    monkeypatch.setattr(
        policy.policy_commands_service,
        "parse_policy_command_payload",
        lambda *_args, **_kwargs: {"scope": "full"},
    )
    monkeypatch.setattr(
        policy,
        "run_policy_runtime_action",
        _fake_run_policy_runtime_action,
    )
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = policy.run(
            type(
                "Args",
                (),
                {
                    "policy_id": "dependency-management",
                    "policy_command": "refresh-all",
                    "command_args": [],
                },
            )()
        )
    assert code == 0
    assert captured["policy_id"] == "dependency-management"
    assert captured["action"] == "refresh-all"
    assert captured["payload"] == {"scope": "full"}
    assert "Refreshed." in stdout.getvalue()


def _unit_test_module_exports_run_entrypoint() -> None:
    """The policy CLI module should keep its run entrypoint public."""
    assert callable(policy.run)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy CLI tests."""

    def test_run_dispatches_declared_policy_command(self):
        """Run policy CLI dispatch assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_dispatches_declared_policy_command(monkeypatch)
        finally:
            monkeypatch.undo()

    def test_module_exports_run_entrypoint(self):
        """Run policy CLI public-entrypoint assertions."""
        _unit_test_module_exports_run_entrypoint()
