"""Tests for metadata-driven no-print-outside-output-runtime policy."""

from __future__ import annotations

import ast
import importlib
import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.no_print_outside_output_runtime import (
    NoPrintOutsideOutputRuntimeCheck,
)
from devcovenant.core.contracts.policy import CheckContext


class _FakeDeclaration:
    """Resolved declaration containing only translator identity."""

    def __init__(self, translator_id: str) -> None:
        """Store translator identity for the fake resolution."""
        self.translator_id = translator_id


class _FakeResolution:
    """Translator resolution compatible with policy runtime expectations."""

    def __init__(self, translator_id: str) -> None:
        """Mark this fake resolution as resolved."""
        self.declaration = _FakeDeclaration(translator_id)
        self.violations = ()
        self.is_resolved = True


class _FakeTranslatorRuntime:
    """Minimal translator runtime used for policy unit tests."""

    def __init__(self, by_suffix: dict[str, str]) -> None:
        """Store suffix-to-language mappings."""
        self.by_suffix = by_suffix

    def resolve(self, *, path, policy_id, context):  # noqa: ANN001, ANN201
        """Resolve fake language based on file suffix."""
        language = self.by_suffix.get(path.suffix.lower(), "")
        return _FakeResolution(language)


def _write_module(repo_root: Path, relative: str, body: str) -> Path:
    """Write body to relative file under repo_root."""
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.lstrip("\n"), encoding="utf-8")
    return path


def _configured_check() -> NoPrintOutsideOutputRuntimeCheck:
    """Return the policy check with metadata-style options."""
    check = NoPrintOutsideOutputRuntimeCheck()
    check.set_options(
        {
            "severity": "error",
            "include_suffixes": [".py", ".js", ".rs"],
            "sink_call_targets": [
                "python=>print",
                "python=>builtins.print",
            ],
            "sink_attr_targets": ["javascript=>console.log"],
            "sink_macro_targets": ["rust=>println"],
            "allowed_file_globs": ["devcovenant/core/runtime/execution.py"],
        },
        {},
    )
    return check


def _policy_module():
    """Return the concrete no-print policy module for symbol-contract tests."""
    return importlib.import_module(
        "devcovenant.builtin.policies.no_print_outside_output_runtime."
        "no_print_outside_output_runtime"
    )


def _run_policy(repo_root: Path, path: Path) -> list:
    """Run policy check against one file path."""
    check = _configured_check()
    context = CheckContext(
        repo_root=repo_root,
        all_files=[path],
        translator_runtime=_FakeTranslatorRuntime(
            {
                ".py": "python",
                ".js": "javascript",
                ".rs": "rust",
            }
        ),
    )
    return check.check(context)


def _unit_test_python_sink_violation_detected() -> None:
    """Python print sink outside allowed boundary should fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_module(
            root,
            "devcovenant/core/flow/gate.py",
            """
def emit():
    print("bad")
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert violations[0].line_number == 2


def _unit_test_allowed_file_glob_is_respected() -> None:
    """Configured output boundary file is allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_module(
            root,
            "devcovenant/core/runtime/execution.py",
            """
def emit():
    print("ok")
""",
        )
        violations = _run_policy(root, module)
        assert not violations


def _unit_test_javascript_attr_sink_detected() -> None:
    """JavaScript console sink should be detected from metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_module(
            root,
            "devcovenant/web/ui.js",
            """
function render() {
  console.log("nope");
}
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert violations[0].line_number == 2


def _unit_test_rust_macro_sink_detected() -> None:
    """Rust macro sink should be detected from metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = _write_module(
            root,
            "devcovenant/core/log.rs",
            """
fn report() {
    println!("nope");
}
""",
        )
        violations = _run_policy(root, module)
        assert violations
        assert violations[0].line_number == 2


def _unit_test_python_sink_visitor_tracks_named_symbols() -> None:
    """The Python sink visitor should keep explicit symbol-tracking hooks."""
    module = _policy_module()
    visitor = module._PythonSinkVisitor(
        call_targets={"print"},
        attr_targets={"console.log"},
    )
    tree = ast.parse(
        "def emit():\n"
        "    print('sync')\n"
        "\n"
        "async def emit_async():\n"
        "    print('async')\n"
    )
    visitor.visit(tree)
    assert hasattr(NoPrintOutsideOutputRuntimeCheck, "check")
    assert hasattr(module._PythonSinkVisitor, "visit_FunctionDef")
    assert hasattr(module._PythonSinkVisitor, "visit_AsyncFunctionDef")
    assert hasattr(module._PythonSinkVisitor, "visit_Call")
    assert isinstance(visitor.hits[0], module.SinkHit)
    assert {hit.symbol for hit in visitor.hits} == {"emit", "emit_async"}


class GeneratedUnittestCases(unittest.TestCase):
    """Unittest wrappers for module-level verification helpers."""

    def test_python_sink_violation_detected(self):
        """Run _unit_test_python_sink_violation_detected."""
        _unit_test_python_sink_violation_detected()

    def test_allowed_file_glob_is_respected(self):
        """Run _unit_test_allowed_file_glob_is_respected."""
        _unit_test_allowed_file_glob_is_respected()

    def test_javascript_attr_sink_detected(self):
        """Run _unit_test_javascript_attr_sink_detected."""
        _unit_test_javascript_attr_sink_detected()

    def test_rust_macro_sink_detected(self):
        """Run _unit_test_rust_macro_sink_detected."""
        _unit_test_rust_macro_sink_detected()

    def test_python_sink_visitor_tracks_named_symbols(self):
        """Run Python sink-visitor contract assertions."""
        _unit_test_python_sink_visitor_tracks_named_symbols()
