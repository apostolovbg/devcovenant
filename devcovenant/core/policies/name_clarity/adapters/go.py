"""Go adapter for name clarity."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Tuple

from devcovenant.core.base import Violation

BLACKLIST = {
    "foo",
    "bar",
    "baz",
    "tmp",
    "temp",
    "var",
    "data",
    "val",
    "value",
    "obj",
    "item",
}
ALLOW_SHORT = {"i", "j", "k", "x", "y", "z"}
KEYWORDS = {
    "break",
    "case",
    "chan",
    "const",
    "continue",
    "default",
    "defer",
    "else",
    "fallthrough",
    "for",
    "func",
    "go",
    "goto",
    "if",
    "import",
    "interface",
    "map",
    "package",
    "range",
    "return",
    "select",
    "struct",
    "switch",
    "type",
    "var",
}
IDENT_RE = re.compile(r"\b[_A-Za-z][A-Za-z0-9_]*\b")
ALLOW_COMMENT = "name-clarity: allow"


def _should_flag(identifier: str) -> bool:
    """Return True when an identifier is generic or too short."""
    name = identifier.lstrip("_")
    if not name:
        return False
    lower = name.lower()
    if lower in KEYWORDS:
        return False
    if lower in BLACKLIST:
        return True
    if len(name) < 3 and lower not in ALLOW_SHORT:
        return True
    return False


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return violations for a Go file."""
    violations: Set[Tuple[str, int]] = set()
    for lineno, line in enumerate(source.splitlines(), start=1):
        if ALLOW_COMMENT in line:
            continue
        for ident in IDENT_RE.findall(line):
            if _should_flag(ident):
                violations.add((ident, lineno))

    return [
        Violation(
            policy_id=policy_id,
            severity="warning",
            file_path=path,
            line_number=lineno,
            message=(
                f"Identifier '{ident}' is overly generic or too short; "
                "choose a more descriptive name."
            ),
        )
        for ident, lineno in sorted(violations, key=lambda x: x[1])
    ]
