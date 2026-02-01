"""C# adapter for doc/comment coverage."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from devcovenant.core.base import Violation

ALLOW_COMMENT = "doc-coverage: allow"
CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)")
METHOD_PATTERN = re.compile(
    r"\b(public|protected|internal|private)\s+[\w<>\[\]]+\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*\("
)


def _has_doc(lines, idx: int) -> bool:
    """Return True if a comment immediately precedes the declaration."""
    i = idx - 1
    while i >= 0 and not lines[i].strip():
        i -= 1
    if i < 0:
        return False
    stripped = lines[i].lstrip()
    return (
        stripped.startswith("///")
        or stripped.startswith("//")
        or stripped.startswith("/*")
    )


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return violations for C# classes/methods missing doc comments."""
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
                message=f"{name} is missing an XML doc comment.",
            )
        )

    for idx, line in enumerate(lines):
        lineno = idx + 1
        if ALLOW_COMMENT in line:
            continue

        m_class = CLASS_PATTERN.search(line)
        if m_class and not _has_doc(lines, idx):
            record(m_class.group(1), lineno)

        m_method = METHOD_PATTERN.search(line)
        if m_method and not _has_doc(lines, idx):
            record(m_method.group(2), lineno)

    return violations
