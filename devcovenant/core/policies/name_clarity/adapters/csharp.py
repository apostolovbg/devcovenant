"""C# adapter for name clarity."""

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
    "as",
    "base",
    "bool",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "checked",
    "class",
    "const",
    "continue",
    "decimal",
    "default",
    "delegate",
    "do",
    "double",
    "else",
    "enum",
    "event",
    "explicit",
    "extern",
    "false",
    "finally",
    "fixed",
    "float",
    "for",
    "foreach",
    "goto",
    "if",
    "implicit",
    "in",
    "int",
    "interface",
    "internal",
    "is",
    "lock",
    "long",
    "namespace",
    "new",
    "null",
    "object",
    "operator",
    "out",
    "override",
    "params",
    "private",
    "protected",
    "public",
    "readonly",
    "ref",
    "return",
    "sbyte",
    "sealed",
    "short",
    "sizeof",
    "stackalloc",
    "static",
    "string",
    "struct",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "typeof",
    "uint",
    "ulong",
    "unchecked",
    "unsafe",
    "ushort",
    "using",
    "virtual",
    "void",
    "volatile",
    "while",
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
    """Return violations for a C# file."""
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
