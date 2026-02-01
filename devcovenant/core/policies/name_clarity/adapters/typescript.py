"""TypeScript/TSX adapter for name clarity."""

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
    "abstract",
    "any",
    "as",
    "asserts",
    "async",
    "await",
    "boolean",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "constructor",
    "continue",
    "debugger",
    "declare",
    "default",
    "delete",
    "do",
    "else",
    "enum",
    "export",
    "extends",
    "false",
    "finally",
    "for",
    "from",
    "function",
    "get",
    "if",
    "implements",
    "import",
    "in",
    "infer",
    "instanceof",
    "interface",
    "is",
    "keyof",
    "let",
    "module",
    "namespace",
    "new",
    "null",
    "number",
    "object",
    "package",
    "private",
    "protected",
    "public",
    "readonly",
    "return",
    "set",
    "static",
    "string",
    "super",
    "switch",
    "symbol",
    "this",
    "throw",
    "true",
    "try",
    "type",
    "typeof",
    "undefined",
    "unique",
    "unknown",
    "var",
    "void",
    "while",
    "with",
    "yield",
}
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
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
    """Return violations for a TS/TSX file."""
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
