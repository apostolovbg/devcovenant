"""Rust adapter for security scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from devcovenant.core.base import Violation

PATTERNS = [
    (re.compile(r"\bunsafe\s*\{"), "unsafe block"),
]


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return Rust security violations."""
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
                        message=f"Potentially unsafe construct: {msg}",
                    )
                )
    return violations
