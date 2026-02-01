"""Python adapter for security scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Sequence

from devcovenant.core.base import Violation

PATTERNS = [
    (
        re.compile(r"\beval\s*\("),
        "Avoid `eval`; prefer safer alternatives.",
    ),
    (
        re.compile(r"\bexec\s*\("),
        "Avoid `exec`; prefer explicit parsing.",
    ),
    (
        re.compile(r"\bpickle\.loads\s*\("),
        "Avoid untrusted `pickle.loads`.",
    ),
    (
        re.compile(r"\bsubprocess\.run\s*\([^)]*shell\s*=\s*True"),
        "Avoid `shell=True` in subprocess calls.",
    ),
]

ALLOW_COMMENT = "security-scanner: allow"


def _has_allow_comment(lines: Sequence[str], line_index: int) -> bool:
    """Return True when this or a nearby line carries the allow flag."""
    for offset in (0, -1, -2):
        idx = line_index + offset
        if not (0 <= idx < len(lines)):
            continue
        if ALLOW_COMMENT in lines[idx]:
            return True
    return False


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return security violations for a Python file."""
    violations: List[Violation] = []
    lines = source.splitlines()
    for pattern, reason in PATTERNS:
        for match in pattern.finditer(source):
            line_index = source.count("\n", 0, match.start())
            if _has_allow_comment(lines, line_index):
                continue
            violations.append(
                Violation(
                    policy_id=policy_id,
                    severity="error",
                    file_path=path,
                    line_number=line_index + 1,
                    message=(
                        "Insecure construct detected: "
                        f"{reason} (pattern `{pattern.pattern}`). "
                        "Review the compliance rationale before committing."
                    ),
                )
            )
    return violations
