"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import os
import unittest

MODULE = "devcovenant.core.contracts.policy"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_contract_symbols_covered() -> None:
    """Core contract classes/methods should remain available."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "ChangeState")
    assert hasattr(module, "CheckContext")
    assert hasattr(module, "FixResult")
    assert hasattr(module, "PolicyCheck")
    assert hasattr(module, "PolicyFixer")
    assert hasattr(module, "Violation")

    assert hasattr(module.CheckContext, "get_policy_config")
    assert hasattr(module.CheckContext, "is_ignored")
    assert hasattr(module.PolicyCheck, "get_metadata")
    assert hasattr(module.PolicyCheck, "get_option")
    assert hasattr(module.PolicyCheck, "run_runtime_action")
    assert hasattr(module.PolicyCheck, "scoped_changed_files")
    assert hasattr(module.PolicyCheck, "set_options")
    assert hasattr(module.PolicyFixer, "can_fix")
    assert hasattr(module.PolicyFixer, "fix")


def _unit_test_scoped_changed_files_allows_read_only_check_bootstrap() -> None:
    """Read-only check tolerates missing gate status before first gate."""
    module = importlib.import_module(MODULE)

    class _DummyPolicy(module.PolicyCheck):
        """Minimal policy stub for read-only scope tests."""

        policy_id = "dummy-policy"

        def check(self, context):
            """Return no violations for this scope-only test stub."""
            return []

    previous = os.environ.get("DEVCOV_TOP_COMMAND")
    os.environ["DEVCOV_TOP_COMMAND"] = "check"
    try:
        context = module.CheckContext(
            repo_root=module.Path("/tmp/repo"),
            change_state=module.ChangeState(
                session_valid=False,
                session_error="Gate status file is missing.",
                session_reason_code="missing_gate_status",
                phase="",
            ),
        )
        scoped = _DummyPolicy().scoped_changed_files(context)
        assert scoped == []
    finally:
        if previous is None:
            os.environ.pop("DEVCOV_TOP_COMMAND", None)
        else:
            os.environ["DEVCOV_TOP_COMMAND"] = previous


def _unit_test_scoped_changed_files_stays_strict_outside_check() -> None:
    """Non-check commands should still fail when session scope is invalid."""
    module = importlib.import_module(MODULE)

    class _DummyPolicy(module.PolicyCheck):
        """Minimal policy stub for strict non-check scope tests."""

        policy_id = "dummy-policy"

        def check(self, context):
            """Return no violations for this scope-only test stub."""
            return []

    previous = os.environ.get("DEVCOV_TOP_COMMAND")
    os.environ["DEVCOV_TOP_COMMAND"] = "test"
    try:
        context = module.CheckContext(
            repo_root=module.Path("/tmp/repo"),
            change_state=module.ChangeState(
                session_valid=False,
                session_error="Gate status file is missing.",
                session_reason_code="missing_gate_status",
                phase="",
            ),
        )
        try:
            _DummyPolicy().scoped_changed_files(context)
        except ValueError as error:
            assert "missing" in str(error).lower()
        else:
            raise AssertionError(
                "Expected ValueError outside read-only check."
            )
    finally:
        if previous is None:
            os.environ.pop("DEVCOV_TOP_COMMAND", None)
        else:
            os.environ["DEVCOV_TOP_COMMAND"] = previous


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_contract_symbols_covered(self):
        """Run core policy contract symbol assertions."""
        _unit_test_contract_symbols_covered()

    def test_scoped_changed_files_allows_read_only_check_bootstrap(self):
        """Run read-only check bootstrap fallback assertions."""
        _unit_test_scoped_changed_files_allows_read_only_check_bootstrap()

    def test_scoped_changed_files_stays_strict_outside_check(self):
        """Run strict scoped-change assertions for non-check commands."""
        _unit_test_scoped_changed_files_stays_strict_outside_check()
