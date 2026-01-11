"""Ensure DevCovenant runs inside the bench-managed env listed via
`expected_virtualenvs`."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

from devcovenant.base import CheckContext, PolicyCheck, Violation


class ManagedBenchCheck(PolicyCheck):
    """Verify the active interpreter is the bench-managed virtualenv."""

    policy_id = "managed-bench"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Error when DevCovenant runs outside the configured bench env."""
        repo_root = context.repo_root.resolve()
        entries_option = self.get_option(
            "expected_virtualenvs",
            [".venv"],
        )
        if isinstance(entries_option, str):
            expected_entries = [entries_option]
        else:
            expected_entries = list(entries_option or [".venv"])
        expected_paths = [
            (repo_root / Path(entry)).resolve() for entry in expected_entries
        ]
        if not any(path.exists() for path in expected_paths):
            return []

        if self._in_expected_venv(expected_paths):
            return []

        message = (
            "DevCovenant must run from the bench-managed virtual "
            "environment. Please re-run commands through the bench "
            "environment before editing code."
        )
        return [
            Violation(
                policy_id=self.policy_id,
                severity="error",
                file_path=expected_paths[0],
                line_number=1,
                message=message,
            )
        ]

    def _in_expected_venv(self, expected_paths: List[Path]) -> bool:
        """Return True when the active interpreter lives inside *expected*."""
        env_path = os.environ.get("VIRTUAL_ENV")
        candidates = []
        if env_path:
            candidates.append(Path(env_path))
        candidates.append(Path(sys.executable).parent)

        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            for directory in expected_paths:
                if directory in resolved.parents or resolved == directory:
                    return True
        return False
