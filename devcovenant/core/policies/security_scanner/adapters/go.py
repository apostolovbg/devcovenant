"""Go adapter for security scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from devcovenant.core.base import Violation

PATTERNS = [
    (re.compile(r"os/exec"), "importing os/exec"),
    (re.compile(r"\bexec\.Command\s*\("), "exec.Command usage"),
]


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return Go security violations."""
    violations: List[Violation] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        for regex, msg in PATTERNS:
            if regex.search(line):
                violations.append(
                    Violation(
                        policy_id=policy_id,
                        severity="warning",
                        file_path=path,
                        line_number=lineno,
                        message=f"Potentially risky construct: {msg}",
                    )
                )
    return violations
