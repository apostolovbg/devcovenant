"""Unit tests for the Rust new-modules adapter."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.modules_need_tests.adapters import rust
from devcovenant.core.selector_helpers import SelectorSet


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for rust adapter checks."""

    def test_changed_rust_module_requires_test(self):
        """Changed Rust modules should require *_test.rs under tests/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "engine.rs"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("fn run() {}\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".rs"])
            violations = rust.check_changes(
                context=context,
                policy_id="modules-need-tests",
                selector=selector,
                tests_dirs=["tests"],
                mirror_roots=[],
                added={module},
                modified=set(),
                deleted=set(),
            )
            self.assertTrue(violations)

    def test_changed_rust_module_passes_with_test(self):
        """Rust modules pass when a related *_test.rs exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            module = repo_root / "src" / "engine.rs"
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_text("fn run() {}\n", encoding="utf-8")
            tests_path = repo_root / "tests" / "rust" / "engine_test.rs"
            tests_path.parent.mkdir(parents=True, exist_ok=True)
            tests_path.write_text("fn test_run() {}\n", encoding="utf-8")
            context = CheckContext(repo_root=repo_root)
            selector = SelectorSet(include_suffixes=[".rs"])
            violations = rust.check_changes(
                context=context,
                policy_id="modules-need-tests",
                selector=selector,
                tests_dirs=["tests"],
                mirror_roots=[],
                added={module},
                modified=set(),
                deleted=set(),
            )
            self.assertEqual(violations, [])
