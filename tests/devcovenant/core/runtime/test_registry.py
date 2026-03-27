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
        "workflow_session_path",
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
