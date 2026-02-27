"""Unit tests for devcov-raw-string-escapes policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.custom.policies.devcov_raw_string_escapes import (
    devcov_raw_string_escapes as policy_module,
)

DevcovRawStringEscapesCheck = policy_module.DevcovRawStringEscapesCheck


def _unit_test_inherits_raw_escape_detection() -> None:
    """Custom policy should emit warnings for bare backslashes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir).resolve()
        target = repo_root / "sample.py"
        target.write_text(r'value = "C:\q"' + "\n", encoding="utf-8")

        check = DevcovRawStringEscapesCheck()
        violations = check.check(
            CheckContext(repo_root=repo_root, changed_files=[target])
        )

        assert violations
        assert violations[0].policy_id == "devcov-raw-string-escapes"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_inherits_raw_escape_detection(self):
        """Run test_inherits_raw_escape_detection."""
        _unit_test_inherits_raw_escape_detection()
