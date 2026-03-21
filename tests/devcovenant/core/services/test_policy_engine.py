"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.devcovenant.support import MonkeyPatch

MODULE = "devcovenant.core.services.policy_engine"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_engine_surface_contract_is_stable() -> None:
    """Policy-engine classes and methods should stay discoverable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "DevCovenantEngine")
    assert hasattr(module, "CheckResult")
    assert hasattr(module, "load_policy_check_instance")
    assert hasattr(module, "run_policy_runtime_action")

    engine_cls = module.DevCovenantEngine
    assert hasattr(engine_cls, "check")
    assert hasattr(engine_cls, "run_policy_checks")
    assert hasattr(engine_cls, "apply_auto_fixes")
    assert hasattr(engine_cls, "report_violations")
    assert hasattr(engine_cls, "report_sync_issues")
    assert hasattr(engine_cls, "should_block")


def _unit_test_checkresult_helpers_return_expected_flags() -> None:
    """CheckResult helper methods should reflect list-backed state."""
    module = importlib.import_module(MODULE)
    result_with_items = module.CheckResult(
        violations=[object()],
        should_block=True,
        sync_issues=[object()],
    )
    assert result_with_items.has_violations() is True
    assert result_with_items.has_sync_issues() is True

    empty_result = module.CheckResult(
        violations=[],
        should_block=False,
        sync_issues=[],
    )
    assert empty_result.has_violations() is False
    assert empty_result.has_sync_issues() is False


def _unit_test_run_policy_runtime_action_invokes_policy_action(
    monkeypatch: MonkeyPatch,
) -> None:
    """Runtime action dispatcher should call the loaded policy checker."""
    module = importlib.import_module(MODULE)

    class _FakeChecker:
        """Simple checker stub for runtime action dispatch tests."""

        def __init__(self) -> None:
            """Store received options for assertions."""
            self.options = ({}, {})

        def set_options(self, metadata_options, config_overrides) -> None:
            """Capture options passed by runtime dispatcher."""
            self.options = (
                dict(metadata_options or {}),
                dict(config_overrides or {}),
            )

        def run_runtime_action(
            self, action: str, *, repo_root: Path, payload=None
        ):
            """Return the received runtime-action payload for assertions."""
            return {
                "action": action,
                "repo_root": str(repo_root),
                "payload": payload,
                "metadata": self.options[0],
                "config": self.options[1],
            }

    class _Descriptor:
        """Descriptor stub exposing metadata for option wiring tests."""

        metadata = {"alpha": "beta"}

    monkeypatch.setattr(
        module,
        "load_policy_check_instance",
        lambda repo_root, policy_id: _FakeChecker(),
    )
    monkeypatch.setattr(
        module,
        "load_policy_descriptor",
        lambda repo_root, policy_id: _Descriptor(),
    )
    monkeypatch.setattr(
        module,
        "_runtime_policy_config_overrides",
        lambda repo_root, policy_id: {"gamma": "delta"},
    )
    result = module.run_policy_runtime_action(
        Path("/tmp/devcovenant"),
        policy_id="dependency-license-sync",
        action="refresh-locks-and-licenses",
        payload={"scope": "full"},
    )
    assert result["action"] == "refresh-locks-and-licenses"
    assert result["repo_root"] == str(Path("/tmp/devcovenant").resolve())
    assert result["payload"] == {"scope": "full"}
    assert result["metadata"] == {"alpha": "beta"}
    assert result["config"] == {"gamma": "delta"}


def _unit_test_run_policy_runtime_action_fails_when_policy_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    """Runtime action dispatcher should fail cleanly for missing policies."""
    module = importlib.import_module(MODULE)
    monkeypatch.setattr(
        module,
        "load_policy_check_instance",
        lambda repo_root, policy_id: None,
    )
    try:
        module.run_policy_runtime_action(
            Path("/tmp/devcovenant"),
            policy_id="missing-policy",
            action="refresh-locks-and-licenses",
            payload={},
        )
    except ValueError as error:
        assert "Policy script not found" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for missing runtime-action policy."
        )


def _unit_test_engine_autofix_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine autofix wrappers should delegate to `policy_autofix`."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine._custom_policy_overrides = {"demo-policy"}
    engine.fixers = ["loaded-fixer"]
    calls: dict[str, object] = {}

    def _fake_load_fixers(repo_root, custom_policy_overrides=None):
        """Capture wrapper loader args and return a sentinel payload."""
        calls["load_repo_root"] = repo_root
        calls["load_overrides"] = set(custom_policy_overrides or set())
        return ["delegated-fixer"]

    def _fake_apply_auto_fixes(violations, fixers, *, print_fn):
        """Capture wrapper apply args and return a sentinel bool."""
        calls["apply_violations"] = list(violations)
        calls["apply_fixers"] = list(fixers)
        calls["apply_print_fn"] = print_fn
        return True

    monkeypatch.setattr(
        module.policy_autofix, "load_fixers", _fake_load_fixers
    )
    monkeypatch.setattr(
        module.policy_autofix,
        "apply_auto_fixes",
        _fake_apply_auto_fixes,
    )

    loaded_fixers = module.DevCovenantEngine._load_fixers(engine)
    applied = module.DevCovenantEngine.apply_auto_fixes(
        engine,
        [
            module.Violation(
                policy_id="demo-policy",
                severity="warning",
                message="demo",
                can_auto_fix=True,
            )
        ],
    )

    assert loaded_fixers == ["delegated-fixer"]
    assert calls["load_repo_root"] == engine.repo_root
    assert calls["load_overrides"] == {"demo-policy"}
    assert applied is True
    assert calls["apply_fixers"] == ["loaded-fixer"]
    assert calls["apply_print_fn"] is module.runtime_print


def _unit_test_engine_context_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine context builders should delegate to `policy_check_context`."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.repo_root = Path("/tmp/devcovenant")
    engine.config = {"ignore": {"patterns": []}}
    engine.translator_runtime = object()
    engine._DEFAULT_GATE_STATUS_PATH = Path(
        "devcovenant/registry/runtime/gate_status.json"
    )
    engine._is_ignored_path = lambda path: False
    engine._resolve_file_suffixes = lambda: [".py"]
    engine._collect_all_files = lambda suffixes: [engine.repo_root / "a.py"]
    calls: dict[str, object] = {}

    fake_change_state = module.ChangeState(session_valid=True)
    fake_context = module.CheckContext(repo_root=engine.repo_root)

    def _fake_build_change_state(
        repo_root, *, gate_status_path, is_ignored_path
    ):
        """Capture args and return a sentinel change state."""
        calls["change_repo_root"] = repo_root
        calls["change_gate_status_path"] = gate_status_path
        calls["change_ignore_fn"] = is_ignored_path
        return fake_change_state

    def _fake_build_check_context(
        repo_root,
        *,
        config,
        translator_runtime,
        gate_status_path,
        is_ignored_path,
        resolve_file_suffixes,
        collect_all_files,
    ):
        """Capture args and return a sentinel check context."""
        calls["context_repo_root"] = repo_root
        calls["context_config"] = config
        calls["context_translator_runtime"] = translator_runtime
        calls["context_gate_status_path"] = gate_status_path
        calls["context_ignore_fn"] = is_ignored_path
        calls["context_resolve_fn"] = resolve_file_suffixes
        calls["context_collect_fn"] = collect_all_files
        return fake_context

    monkeypatch.setattr(
        module.policy_check_context,
        "build_change_state",
        _fake_build_change_state,
    )
    monkeypatch.setattr(
        module.policy_check_context,
        "build_check_context",
        _fake_build_check_context,
    )

    change_state = module.DevCovenantEngine._build_change_state(engine)
    context = module.DevCovenantEngine._build_check_context(engine)

    assert change_state is fake_change_state
    assert context is fake_context
    assert calls["change_repo_root"] == engine.repo_root
    assert calls["change_gate_status_path"] == engine._DEFAULT_GATE_STATUS_PATH
    assert calls["context_repo_root"] == engine.repo_root
    assert calls["context_config"] is engine.config
    assert calls["context_translator_runtime"] is engine.translator_runtime
    assert (
        calls["context_gate_status_path"] == engine._DEFAULT_GATE_STATUS_PATH
    )
    assert calls["context_resolve_fn"] is engine._resolve_file_suffixes
    assert calls["context_collect_fn"] is engine._collect_all_files


def _unit_test_engine_policy_runner_wrappers_delegate_to_helper(
    monkeypatch: MonkeyPatch,
) -> None:
    """Engine policy-runner wrappers should delegate to helper functions."""
    module = importlib.import_module(MODULE)
    engine = object.__new__(module.DevCovenantEngine)
    engine.config = {"policy_state": {"critical-demo": False}}
    engine.config_path = Path("/tmp/devcovenant/config.yaml")
    engine._normalized_policy_state = {"critical-demo": False}
    engine._RESERVED_METADATA_KEYS = {"severity", "enabled"}
    engine.passed_count = 10
    engine.failed_count = 20
    calls: dict[str, object] = {}

    policy = module.PolicyDefinition(
        policy_id="critical-demo",
        name="Critical Demo",
        severity="critical",
        auto_fix=False,
        enabled=False,
        custom=False,
        description="demo",
        raw_metadata={"header_scan_lines": "4"},
    )
    fake_context = module.CheckContext(repo_root=Path("/tmp/devcovenant"))
    engine._build_check_context = lambda: fake_context
    engine._load_policy_script = lambda policy_id: None

    def _capture_critical_attempted(*args, **kwargs):
        """Capture args for critical-disable check wrapper."""
        calls["critical_attempted_args"] = args
        calls["critical_attempted_kwargs"] = kwargs
        return True

    def _capture_critical_violation(*args, **kwargs):
        """Capture args for critical-disable violation wrapper."""
        calls["critical_violation_args"] = args
        calls["critical_violation_kwargs"] = kwargs
        return module.Violation(
            policy_id="critical-demo",
            severity="critical",
            message="forced",
        )

    def _capture_extract(*args, **kwargs):
        """Capture args for policy-option extraction wrapper."""
        calls["extract_args"] = args
        calls["extract_kwargs"] = kwargs
        return {"severity": "critical"}

    def _capture_run_policy_checks(*args, **kwargs):
        """Capture args for run-policy-checks wrapper."""
        calls["run_args"] = args
        calls["run_kwargs"] = kwargs
        return module.policy_check_runner.PolicyCheckRunResult(
            violations=[
                module.Violation(
                    policy_id="demo",
                    severity="warning",
                    message="demo",
                )
            ],
            passed_count=2,
            failed_count=3,
        )

    monkeypatch.setattr(
        module.policy_check_runner,
        "critical_disable_attempted",
        _capture_critical_attempted,
    )
    monkeypatch.setattr(
        module.policy_check_runner,
        "critical_disable_attempt_violation",
        _capture_critical_violation,
    )
    monkeypatch.setattr(
        module.policy_check_runner,
        "extract_policy_options",
        _capture_extract,
    )
    monkeypatch.setattr(
        module.policy_check_runner,
        "run_policy_checks",
        _capture_run_policy_checks,
    )

    attempted = module.DevCovenantEngine._critical_disable_attempted(
        engine,
        policy,
    )
    violation = module.DevCovenantEngine._critical_disable_attempt_violation(
        engine,
        policy,
    )
    options = module.DevCovenantEngine._extract_policy_options(engine, policy)
    run_violations = module.DevCovenantEngine.run_policy_checks(
        engine,
        [policy],
        context=None,
    )

    assert attempted is True
    assert violation.policy_id == "critical-demo"
    assert options == {"severity": "critical"}
    assert len(run_violations) == 1
    assert engine.passed_count == 12
    assert engine.failed_count == 23

    assert calls["critical_attempted_args"] == (policy,)
    assert calls["critical_attempted_kwargs"]["normalized_policy_state"] == {
        "critical-demo": False
    }
    assert calls["critical_attempted_kwargs"]["config"] is engine.config
    assert calls["critical_violation_args"] == (policy,)
    assert (
        calls["critical_violation_kwargs"]["config_path"] == engine.config_path
    )
    assert calls["extract_args"] == (policy,)
    assert calls["extract_kwargs"]["reserved_metadata_keys"] == {
        "severity",
        "enabled",
    }
    assert calls["run_args"] == ([policy],)
    assert calls["run_kwargs"]["context"] is fake_context
    assert (
        calls["run_kwargs"]["load_policy_script"] is engine._load_policy_script
    )
    extract_fn = calls["run_kwargs"]["extract_policy_options_fn"]
    assert extract_fn.__self__ is engine
    assert (
        extract_fn.__func__ is module.DevCovenantEngine._extract_policy_options
    )
    attempted_fn = calls["run_kwargs"]["critical_disable_attempted_fn"]
    assert attempted_fn.__self__ is engine
    assert (
        attempted_fn.__func__
        is module.DevCovenantEngine._critical_disable_attempted
    )
    violation_fn = calls["run_kwargs"]["critical_disable_attempt_violation_fn"]
    assert violation_fn.__self__ is engine
    assert (
        violation_fn.__func__
        is module.DevCovenantEngine._critical_disable_attempt_violation
    )


def _unit_test_runtime_policy_metadata_options_decodes_registry_strings() -> (
    None
):
    """Runtime metadata loader should decode registry strings.

    It should expose typed values to policy runtime callers.
    """
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "policies": {
                        "demo-policy": {
                            "metadata": {
                                "enabled": "true",
                                "header_scan_lines": "4",
                                "required_globs": "README.md, AGENTS.md",
                            }
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        options = module._runtime_policy_metadata_options(
            repo_root,
            "demo-policy",
        )
        assert options["enabled"] is True
        assert options["header_scan_lines"] == 4
        assert options["required_globs"] == ["README.md", "AGENTS.md"]


def _write_minimal_config(
    repo_root: Path,
    *,
    include_core: bool,
    core_paths: list[str],
) -> None:
    """Write a minimal config payload for core exclusion tests."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                f"developer_mode: {'true' if include_core else 'false'}",
                "profiles:",
                "  active: []",
                "  generated:",
                "    devcov_core_paths:",
            ]
            + [f"      - {entry}" for entry in core_paths]
        )
        + "\n",
        encoding="utf-8",
    )


def _unit_test_core_exclusions_ignore_builtin_when_disabled() -> None:
    """Core exclusions should ignore builtin paths when disabled."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_minimal_config(
            repo_root,
            include_core=False,
            core_paths=["devcovenant/core", "devcovenant/builtin"],
        )
        monkeypatch = MonkeyPatch()
        try:
            monkeypatch.setattr(module, "load_profile_registry", lambda _: {})
            engine = module.DevCovenantEngine(repo_root=repo_root)
        finally:
            monkeypatch.undo()
        builtin_path = (
            engine.repo_root / "devcovenant" / "builtin" / "policies"
        )
        core_path = engine.repo_root / "devcovenant" / "core" / "flow"
        custom_path = engine.repo_root / "devcovenant" / "custom" / "policies"
        assert engine._is_ignored_path(builtin_path) is True
        assert engine._is_ignored_path(core_path) is True
        assert engine._is_ignored_path(custom_path) is False


def _unit_test_core_exclusions_respected_when_enabled() -> None:
    """Core exclusions should allow builtin paths when enabled."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _write_minimal_config(
            repo_root,
            include_core=True,
            core_paths=["devcovenant/core", "devcovenant/builtin"],
        )
        monkeypatch = MonkeyPatch()
        try:
            monkeypatch.setattr(module, "load_profile_registry", lambda _: {})
            engine = module.DevCovenantEngine(repo_root=repo_root)
        finally:
            monkeypatch.undo()
        builtin_path = (
            engine.repo_root / "devcovenant" / "builtin" / "policies"
        )
        core_path = engine.repo_root / "devcovenant" / "core" / "flow"
        assert engine._is_ignored_path(builtin_path) is False
        assert engine._is_ignored_path(core_path) is False


def _unit_test_summary_status_respects_warning_fail_threshold() -> None:
    """Summary status text should match blocking threshold semantics."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"engine": {"fail_threshold": "warning"}}
    printed: list[str] = []
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "runtime_print",
            lambda *parts, **_kwargs: printed.append(
                " ".join(str(part) for part in parts)
            ),
        )
        engine._report_summary({"warning": [object(), object()]})
    finally:
        monkeypatch.undo()

    joined = "\n".join(printed)
    assert "Status: 🚫 BLOCKED (violations >= warning threshold)" in joined
    assert "Status: ✅ PASSED" not in joined


def _unit_test_quiet_mode_reports_violations_to_stderr(
    monkeypatch: MonkeyPatch,
) -> None:
    """Quiet-mode violation reporting should route output to stderr."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"engine": {"fail_threshold": "warning"}}
    engine.passed_count = 0
    engine.failed_count = 1
    printed: list[dict[str, object]] = []

    def _fake_runtime_print(message="", **kwargs):
        """Capture runtime_print invocations for quiet-mode assertions."""
        printed.append({"message": str(message), **kwargs})

    monkeypatch.setattr(module, "runtime_print", _fake_runtime_print)
    monkeypatch.setattr(module, "get_output_mode", lambda: "quiet")
    engine.report_violations(
        [
            module.Violation(
                policy_id="demo-policy",
                severity="warning",
                message="demo warning",
            )
        ]
    )
    assert printed
    assert all(entry.get("file") is sys.stderr for entry in printed)


def _unit_test_quiet_mode_skips_success_banners(
    monkeypatch: MonkeyPatch,
) -> None:
    """Quiet mode should suppress success-only policy output."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"engine": {"fail_threshold": "warning"}}
    engine.passed_count = 1
    engine.failed_count = 0
    printed: list[dict[str, object]] = []

    def _fake_runtime_print(message="", **kwargs):
        """Capture runtime_print invocations for quiet-mode assertions."""
        printed.append({"message": str(message), **kwargs})

    monkeypatch.setattr(module, "runtime_print", _fake_runtime_print)
    monkeypatch.setattr(module, "get_output_mode", lambda: "quiet")
    engine.report_violations([])
    assert printed == []


def _unit_test_critical_policy_disable_attempt_is_reported_and_enforced(
    monkeypatch: MonkeyPatch,
    *,
    custom_policy: bool,
) -> None:
    """Critical disable attempts should emit diagnostics and still execute."""
    module = importlib.import_module(MODULE)
    engine = module.DevCovenantEngine.__new__(module.DevCovenantEngine)
    engine.config = {"policy_state": {"critical-demo": False}}
    engine.config_path = Path("/tmp/devcovenant/config.yaml")
    engine.passed_count = 0
    engine.failed_count = 0
    engine._normalized_policy_state = {"critical-demo": False}

    calls: list[str] = []

    class _FakeChecker:
        """Minimal checker stub that records execution."""

        def set_options(self, metadata_options, config_overrides):
            """Accept runtime options without modifying test state."""
            del metadata_options, config_overrides

        def check(self, context):
            """Record execution and return no policy-script violations."""
            del context
            calls.append("ran")
            return []

    class _FakeContext:
        """Minimal context stub for `run_policy_checks` unit tests."""

        @staticmethod
        def get_policy_config(_policy_id):
            """Return no config overrides for the fake checker."""
            return {}

    monkeypatch.setattr(
        engine,
        "_load_policy_script",
        lambda _policy_id: _FakeChecker(),
    )
    monkeypatch.setattr(
        engine,
        "_extract_policy_options",
        lambda _policy: {},
    )

    policy = module.PolicyDefinition(
        policy_id="critical-demo",
        name="Critical Demo",
        severity="critical",
        auto_fix=False,
        enabled=False,
        custom=custom_policy,
        description="test",
    )
    violations = engine.run_policy_checks([policy], context=_FakeContext())

    assert calls == ["ran"]
    assert engine.passed_count == 0
    assert engine.failed_count == 1
    assert len(violations) == 1
    violation = violations[0]
    assert violation.severity == "critical"
    assert "policy_state" in violation.message
    assert "remain enforced" in violation.message
    if custom_policy:
        assert "custom policy metadata" in str(violation.suggestion)
    else:
        assert "copy the builtin policy" in str(violation.suggestion)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_engine_surface_contract_is_stable(self):
        """Run engine surface contract assertions."""
        _unit_test_engine_surface_contract_is_stable()

    def test_checkresult_helpers_return_expected_flags(self):
        """Run CheckResult helper behavior assertions."""
        _unit_test_checkresult_helpers_return_expected_flags()

    def test_run_policy_runtime_action_invokes_policy_action(self):
        """Run runtime-action dispatch happy-path assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_policy_runtime_action_invokes_policy_action(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_run_policy_runtime_action_fails_when_policy_missing(self):
        """Run runtime-action dispatch missing-policy assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_run_policy_runtime_action_fails_when_policy_missing(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_runtime_policy_metadata_options_decodes_registry_strings(self):
        """Run runtime metadata typed-decoding assertions."""
        _unit_test_runtime_policy_metadata_options_decodes_registry_strings()

    def test_engine_autofix_wrappers_delegate_to_helper(self):
        """Run autofix-wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_engine_autofix_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_engine_context_wrappers_delegate_to_helper(self):
        """Run context-wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_engine_context_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_engine_policy_runner_wrappers_delegate_to_helper(self):
        """Run policy-runner wrapper delegation assertions."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_engine_policy_runner_wrappers_delegate_to_helper(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_core_exclusions_ignore_builtin_when_disabled(self):
        """Run core-exclusion ignore check for builtin paths."""
        _unit_test_core_exclusions_ignore_builtin_when_disabled()

    def test_core_exclusions_respected_when_enabled(self):
        """Run core-exclusion allow check for enabled mode."""
        _unit_test_core_exclusions_respected_when_enabled()

    def test_summary_status_respects_warning_fail_threshold(self):
        """Run fail-threshold-aware summary status assertions."""
        _unit_test_summary_status_respects_warning_fail_threshold()

    def test_quiet_mode_reports_violations_to_stderr(self):
        """Run quiet-mode stderr routing assertions for violations."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_quiet_mode_reports_violations_to_stderr(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_quiet_mode_skips_success_banners(self):
        """Run quiet-mode suppression assertions for success output."""
        monkeypatch = MonkeyPatch()
        try:
            _unit_test_quiet_mode_skips_success_banners(
                monkeypatch=monkeypatch
            )
        finally:
            monkeypatch.undo()

    def test_critical_builtin_disable_attempt_is_reported_and_enforced(self):
        """Run builtin critical-disable immunity assertions."""
        monkeypatch = MonkeyPatch()
        try:
            test_case = globals()[
                "_unit_test_critical_policy_disable_attempt_is_reported_"
                "and_enforced"
            ]
            test_case(
                monkeypatch=monkeypatch,
                custom_policy=False,
            )
        finally:
            monkeypatch.undo()

    def test_critical_custom_disable_attempt_is_reported_and_enforced(self):
        """Run custom critical-disable immunity assertions."""
        monkeypatch = MonkeyPatch()
        try:
            test_case = globals()[
                "_unit_test_critical_policy_disable_attempt_is_reported_"
                "and_enforced"
            ]
            test_case(
                monkeypatch=monkeypatch,
                custom_policy=True,
            )
        finally:
            monkeypatch.undo()
