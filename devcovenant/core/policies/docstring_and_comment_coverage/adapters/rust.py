"""Rust adapter for doc/comment coverage."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from devcovenant.core.base import Violation

ALLOW_COMMENT = "doc-coverage: allow"
FN_PATTERN = re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)")
STRUCT_PATTERN = re.compile(r"^\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)")
ENUM_PATTERN = re.compile(r"^\s*enum\s+([A-Za-z_][A-Za-z0-9_]*)")


def _has_doc(lines, idx: int) -> bool:
    """Return True if a doc comment immediately precedes the declaration."""
    i = idx - 1
    while i >= 0 and not lines[i].strip():
        i -= 1
    if i < 0:
        return False
    return lines[i].lstrip().startswith("///")


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return violations for Rust declarations lacking doc comments."""
    lines = source.splitlines()
    violations: List[Violation] = []

    def record(name: str, lineno: int):
        """Add a violation for the given declaration."""
        if ALLOW_COMMENT in lines[lineno - 1]:
            return
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                line_number=lineno,
                message=f"{name} is missing a doc comment (///).",
            )
        )

    for idx, line in enumerate(lines):
        lineno = idx + 1
        if ALLOW_COMMENT in line:
            continue

        for pattern in (FN_PATTERN, STRUCT_PATTERN, ENUM_PATTERN):
            match_result = pattern.match(line)
            if match_result and not _has_doc(lines, idx):
                record(match_result.group(1), lineno)

    return violations
