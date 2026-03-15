"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from devcovenant.core.contracts.policy import FixResult, PolicyFixer, Violation

MODULE = "devcovenant.core.services.policy_autofix"


def _capture_lines():
    """Return a print sink and collected output buffer."""
    lines: list[str] = []

    def _print(*parts, **_kwargs):
        """Collect printed parts as one line."""
        lines.append(" ".join(str(part) for part in parts))

    return _print, lines


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Autofix helper seam functions should remain callable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "load_fixers")
    assert hasattr(module, "apply_auto_fixes")
    assert callable(module.load_fixers)
    assert callable(module.apply_auto_fixes)


def _unit_test_symbol_assertions_cover_autofix_seam() -> None:
    """Tests should assert the autofix helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.load_fixers
    assert module.apply_auto_fixes


def _unit_test_load_fixers_returns_empty_when_roots_missing() -> None:
    """Fixer loader should return an empty list on clean repos."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        loaded = module.load_fixers(repo_root)
        assert loaded == []


def _unit_test_load_fixers_respects_custom_overrides_and_sets_attrs() -> None:
    """Fixer loader should prefer custom overrides and stamp metadata attrs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        custom_demo = (
            repo_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo_policy"
            / "autofix"
        )
        builtin_demo = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "policies"
            / "demo_policy"
            / "autofix"
        )
        builtin_other = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "policies"
            / "other_policy"
            / "autofix"
        )
        for directory in (custom_demo, builtin_demo, builtin_other):
            directory.mkdir(parents=True, exist_ok=True)
        (custom_demo / "custom_fix.py").write_text("", encoding="utf-8")
        (builtin_demo / "builtin_fix.py").write_text("", encoding="utf-8")
        (builtin_other / "builtin_fix.py").write_text("", encoding="utf-8")
        (builtin_other / "__init__.py").write_text("", encoding="utf-8")
        (builtin_other / "_hidden.py").write_text("", encoding="utf-8")

        class _CustomDemoFixer(PolicyFixer):
            """Fake custom fixer."""

            def can_fix(self, violation: Violation) -> bool:
                """Never match during loader-only tests."""
                del violation
                return False

            def fix(self, violation: Violation) -> FixResult:
                """Return a no-op fix result."""
                del violation
                return FixResult(success=True, message="noop")

        class _OtherBuiltinFixer(PolicyFixer):
            """Fake builtin fixer."""

            def can_fix(self, violation: Violation) -> bool:
                """Never match during loader-only tests."""
                del violation
                return False

            def fix(self, violation: Violation) -> FixResult:
                """Return a no-op fix result."""
                del violation
                return FixResult(success=True, message="noop")

        loaded_module_map = {
            (
                "devcovenant.custom.policies." "demo_policy.autofix.custom_fix"
            ): types.SimpleNamespace(CustomDemoFixer=_CustomDemoFixer),
            (
                "devcovenant.builtin.policies."
                "other_policy.autofix.builtin_fix"
            ): types.SimpleNamespace(OtherBuiltinFixer=_OtherBuiltinFixer),
        }
        import_calls: list[str] = []

        def _import_module(name: str):
            """Return stub modules for expected import paths only."""
            import_calls.append(name)
            if name not in loaded_module_map:
                raise AssertionError(f"Unexpected import: {name}")
            return loaded_module_map[name]

        with mock.patch.object(
            module.importlib,
            "import_module",
            side_effect=_import_module,
        ):
            fixers = module.load_fixers(
                repo_root,
                custom_policy_overrides={"demo-policy"},
            )

        assert len(fixers) == 2
        assert {getattr(fixer, "_origin", None) for fixer in fixers} == {
            "custom",
            "builtin",
        }
        assert all(
            getattr(fixer, "repo_root", None) == repo_root for fixer in fixers
        )
        assert (
            "devcovenant.builtin.policies.demo_policy.autofix.builtin_fix"
            not in import_calls
        )


def _unit_test_apply_auto_fixes_reports_success_and_rerun_notice() -> None:
    """Autofix helper should report modified files and rerun guidance."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    violation = Violation(
        policy_id="demo-policy",
        severity="error",
        message="needs fix",
        can_auto_fix=True,
    )
    touched = Path("README.md")

    class _DemoFixer(PolicyFixer):
        """Simple fixer that modifies one file."""

        def can_fix(self, candidate: Violation) -> bool:
            """Match the demo violation only."""
            return candidate.policy_id == "demo-policy"

        def fix(self, candidate: Violation) -> FixResult:
            """Return a successful file-modifying fix result."""
            del candidate
            return FixResult(
                success=True,
                message="Applied demo fix",
                files_modified=[touched],
            )

    applied = module.apply_auto_fixes(
        [violation],
        [_DemoFixer()],
        print_fn=print_fn,
    )
    joined = "\n".join(lines)
    assert applied is True
    assert "🔧 Running auto-fixers" in joined
    assert "Applied demo fix" in joined
    assert "Re-running policy checks after auto-fix" in joined


def _unit_test_apply_auto_fixes_reports_no_modifications() -> None:
    """Autofix helper should report when no files are modified."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    violation = Violation(
        policy_id="demo-policy",
        severity="warning",
        message="fixable",
        can_auto_fix=True,
    )

    class _NoopFixer(PolicyFixer):
        """Simple fixer that succeeds without file modifications."""

        def can_fix(self, candidate: Violation) -> bool:
            """Match the demo violation only."""
            return candidate.policy_id == "demo-policy"

        def fix(self, candidate: Violation) -> FixResult:
            """Return a success result with no file modifications."""
            del candidate
            return FixResult(success=True, message="No changes needed")

    applied = module.apply_auto_fixes(
        [violation],
        [_NoopFixer()],
        print_fn=print_fn,
    )
    joined = "\n".join(lines)
    assert applied is False
    assert "No changes needed" in joined
    assert "No auto-fixable violations were modified." in joined


def _unit_test_apply_auto_fixes_reports_failures_without_crashing() -> None:
    """Autofix helper should report failed fixer results cleanly."""
    module = importlib.import_module(MODULE)
    print_fn, lines = _capture_lines()
    violation = Violation(
        policy_id="demo-policy",
        severity="error",
        message="fix failed",
        can_auto_fix=True,
    )

    class _FailingFixer(PolicyFixer):
        """Simple fixer that reports failure."""

        def can_fix(self, candidate: Violation) -> bool:
            """Match the demo violation only."""
            return candidate.policy_id == "demo-policy"

        def fix(self, candidate: Violation) -> FixResult:
            """Return a failed result."""
            del candidate
            return FixResult(success=False, message="could not patch")

    applied = module.apply_auto_fixes(
        [violation],
        [_FailingFixer()],
        print_fn=print_fn,
    )
    joined = "\n".join(lines)
    assert applied is False
    assert "Auto-fix failed for demo-policy: could not patch" in joined
    assert "No auto-fixable violations were modified." in joined


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy-autofix helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run policy-autofix helper symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_autofix_seam(self):
        """Run explicit policy-autofix helper symbol assertions."""
        _unit_test_symbol_assertions_cover_autofix_seam()

    def test_load_fixers_returns_empty_when_roots_missing(self):
        """Run empty-repo fixer-loader assertions."""
        _unit_test_load_fixers_returns_empty_when_roots_missing()

    def test_load_fixers_respects_custom_overrides_and_sets_attrs(self):
        """Run fixer-loader override/metadata assertions."""
        _unit_test_load_fixers_respects_custom_overrides_and_sets_attrs()

    def test_apply_auto_fixes_reports_success_and_rerun_notice(self):
        """Run successful autofix output/rerun assertions."""
        _unit_test_apply_auto_fixes_reports_success_and_rerun_notice()

    def test_apply_auto_fixes_reports_no_modifications(self):
        """Run no-op autofix reporting assertions."""
        _unit_test_apply_auto_fixes_reports_no_modifications()

    def test_apply_auto_fixes_reports_failures_without_crashing(self):
        """Run autofix failure reporting assertions."""
        _unit_test_apply_auto_fixes_reports_failures_without_crashing()
