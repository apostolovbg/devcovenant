"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import ChangeState, CheckContext
from tests.devcovenant.support import MonkeyPatch

MODULE = "devcovenant.core.contracts.invariant"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_core_invariant_check_option_precedence() -> None:
    """Config overrides should win over metadata options when non-empty."""
    module = importlib.import_module(MODULE)

    class _DemoInvariant(module.CoreInvariantCheck):
        """Small invariant fixture for option-precedence checks."""

        invariant_id = "demo-invariant"

        def check(self, context: CheckContext):
            """Return no violations for the test fixture."""
            return []

    checker = _DemoInvariant()
    checker.set_options(
        {"alpha": "metadata", "beta": "metadata"}, {"alpha": "config"}
    )
    assert checker.get_option("alpha") == "config"
    assert checker.get_option("beta") == "metadata"
    assert checker.policy_id == "demo-invariant"


def _unit_test_scoped_changed_files_allows_read_only_check_bootstrap(
    monkeypatch: MonkeyPatch,
) -> None:
    """Read-only pre-session checks should return an empty session scope."""
    module = importlib.import_module(MODULE)

    class _DemoInvariant(module.CoreInvariantCheck):
        """Small invariant fixture for session-scope bootstrap checks."""

        invariant_id = "demo-invariant"

        def check(self, context: CheckContext):
            """Return no violations for the test fixture."""
            return []

    checker = _DemoInvariant()
    monkeypatch.setenv("DEVCOV_TOP_COMMAND", "check")
    context = CheckContext(
        repo_root=Path("/tmp/demo"),
        change_state=ChangeState(
            session_valid=False,
            session_reason_code="missing_gate_status",
        ),
    )
    assert checker.scoped_changed_files(context) == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_core_invariant_check_option_precedence(self):
        """Run core invariant option precedence assertions."""
        _unit_test_core_invariant_check_option_precedence()

    def test_scoped_changed_files_allows_read_only_check_bootstrap(self):
        """Run bootstrap session-scope assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_scoped_changed_files_allows_read_only_check_bootstrap(
                monkeypatch
            )
        finally:
            monkeypatch.undo()
