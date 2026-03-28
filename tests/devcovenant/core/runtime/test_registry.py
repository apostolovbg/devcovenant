"""Tests for runtime-registry path helpers."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.runtime.registry"


def _unit_test_module_importable() -> None:
    """Runtime registry module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_public_symbol_contract_is_stable() -> None:
    """Runtime registry should expose the runtime path-helper surface."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "RUNTIME_REGISTRY_DIR",
        "GATE_STATUS_FILENAME",
        "WORKFLOW_SESSION_FILENAME",
        "LATEST_RUNTIME_FILENAME",
        "SESSION_SNAPSHOT_FILENAME",
        "runtime_registry_root",
        "latest_runtime_path",
        "session_snapshot_path",
        "gate_status_path",
        "gate_status_path_from_option",
        "workflow_session_path",
        "workflow_session_path_from_option",
    ]:
        assert hasattr(module, symbol)


def _unit_test_path_helpers_resolve_runtime_locations() -> None:
    """Runtime registry helpers should resolve runtime evidence paths."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        runtime_root = repo_root / "devcovenant" / "registry" / "runtime"
        assert module.runtime_registry_root(repo_root) == runtime_root
        assert module.latest_runtime_path(repo_root) == (
            runtime_root / "latest.json"
        )
        assert module.session_snapshot_path(repo_root) == (
            runtime_root / "session_snapshot.json"
        )
        assert module.gate_status_path(repo_root) == (
            runtime_root / "gate_status.json"
        )
        assert module.workflow_session_path(repo_root) == (
            runtime_root / "workflow_session.json"
        )


def _unit_test_path_helpers_honor_runtime_evidence_overrides() -> None:
    """Runtime evidence helpers should honor configured invariant paths."""

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "core_invariants:",
                    "  devflow-run-gates:",
                    "    gate_status_file: "
                    "devcovenant/registry/runtime/evidence/status.json",
                    "    workflow_session_file: "
                    "devcovenant/registry/runtime/evidence/workflow.json",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        assert module.gate_status_path(repo_root) == (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "evidence"
            / "status.json"
        )
        assert module.workflow_session_path(repo_root) == (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "evidence"
            / "workflow.json"
        )


def _unit_test_runtime_evidence_paths_must_stay_under_runtime_root() -> None:
    """
    Configured evidence paths should reject escapes from the runtime root.
    """

    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        try:
            module.gate_status_path_from_option(repo_root, "alt/status.json")
        except ValueError as exc:
            assert "devcovenant/registry/runtime/" in str(exc)
        else:  # pragma: no cover - defensive
            raise AssertionError(
                "Expected ValueError for escaped status path."
            )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_module_importable(self):
        """Run runtime-registry importability assertions."""
        _unit_test_module_importable()

    def test_public_symbol_contract_is_stable(self):
        """Run runtime-registry public symbol assertions."""
        _unit_test_public_symbol_contract_is_stable()

    def test_path_helpers_resolve_runtime_locations(self):
        """Run runtime-registry path resolution assertions."""
        _unit_test_path_helpers_resolve_runtime_locations()

    def test_path_helpers_honor_runtime_evidence_overrides(self):
        """Run runtime-evidence override assertions."""

        _unit_test_path_helpers_honor_runtime_evidence_overrides()

    def test_runtime_evidence_paths_must_stay_under_runtime_root(self):
        """Run runtime-evidence containment assertions."""

        _unit_test_runtime_evidence_paths_must_stay_under_runtime_root()
