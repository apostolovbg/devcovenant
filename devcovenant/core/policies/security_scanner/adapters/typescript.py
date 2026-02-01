"""TypeScript/TSX adapter for security scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from devcovenant.core.base import Violation

# security-scanner: allow (defining patterns for the scanner itself)
PATTERNS = [
    (re.compile(r"\beval\s*\("), "avoid eval()"),
    (re.compile(r"\bnew\s+Function\s*\("), "avoid Function() constructor"),
    (re.compile(r"child_process\.exec"), "avoid child_process.exec"),
]
ALLOW_COMMENT = "security-scanner: allow"


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return TS security violations."""
    violations: List[Violation] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if ALLOW_COMMENT in line:
            continue
        for regex, msg in PATTERNS:
            if regex.search(line):
                violations.append(
                    Violation(
                        policy_id=policy_id,
                        severity="error",
                        file_path=path,
                        line_number=lineno,
                        message=f"Insecure construct: {msg}",
                    )
                )
    return violations
