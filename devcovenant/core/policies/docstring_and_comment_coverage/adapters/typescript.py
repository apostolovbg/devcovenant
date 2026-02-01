"""TypeScript/TSX adapter for doc/comment coverage."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from devcovenant.core.base import Violation

ALLOW_COMMENT = "doc-coverage: allow"
COMMENT_PREFIXES = ("//", "/*", "*", "/**")

FUNCTION_PATTERNS = [
    re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"\bconst\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>"),
    re.compile(r"\bexport\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
]
CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b")


def _has_doc(lines: List[str], idx: int) -> bool:
    """Return True when a doc/comment line exists immediately above idx."""
    i = idx - 1
    while i >= 0 and not lines[i].strip():
        i -= 1
    if i < 0:
        return False
    return lines[i].lstrip().startswith(COMMENT_PREFIXES)


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return violations for TS/TSX when declarations lack docs."""
    lines = source.splitlines()
    violations: List[Violation] = []

    def record(name: str, lineno: int):
        """Add a violation for the given symbol."""
        if ALLOW_COMMENT in lines[lineno - 1]:
            return
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                line_number=lineno,
                message=f"{name} is missing a leading comment/doc block.",
            )
        )

    for idx, line in enumerate(lines):
        lineno = idx + 1
        if ALLOW_COMMENT in line:
            continue

        for pattern in FUNCTION_PATTERNS:
            match_result = pattern.search(line)
            if match_result and not _has_doc(lines, idx):
                record(match_result.group(1), lineno)

        m_class = CLASS_PATTERN.search(line)
        if m_class and not _has_doc(lines, idx):
            record(m_class.group(1), lineno)

    return violations
