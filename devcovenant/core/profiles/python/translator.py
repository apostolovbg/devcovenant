"""Python translator for DevCovenant LanguageUnit generation."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Any

from devcovenant.core.translator_runtime import (
    IdentifierFact,
    LanguageUnit,
    RiskFact,
    SymbolDocFact,
    TranslatorDeclaration,
    can_handle_declared_extensions,
)

ALLOW_SECURITY = "security-scanner: allow"
TEST_TEMPLATES = ("test_{stem}.py", "{stem}_test.py")
RISK_PATTERNS = (
    # security-scanner: allow (pattern literals for policy translation)
    (re.compile(r"\beval\s*\("), "Avoid eval()."),
    (re.compile(r"\bexec\s*\("), "Avoid exec()."),
    (
        re.compile(r"\bpickle\.loads\s*\("),  # security-scanner: allow
        "Avoid untrusted pickle.loads().",
    ),
    (
        re.compile(r"\bsubprocess\.run\s*\([^)]*shell\s*=\s*True"),
        "Avoid shell=True in subprocess.run().",
    ),
)


def can_handle(
    *, path: Path, declaration: TranslatorDeclaration, **kwargs: Any
) -> bool:
    """Return True when declared extensions include the file suffix."""
    return can_handle_declared_extensions(
        path=path, declaration=declaration, **kwargs
    )


def _comment_lines(source: str) -> set[int]:
    """Return source line numbers containing comments."""
    lines: set[int] = set()
    reader = io.StringIO(source).readline
    try:
        for token in tokenize.generate_tokens(reader):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
    except tokenize.TokenError:
        return lines
    return lines


def _has_nearby_comment(line_number: int, lines: list[str]) -> bool:
    """Return True when a nearby comment marker is present."""
    start = max(1, line_number - 3)
    for current in range(start, line_number + 1):
        if current > len(lines):
            continue
        if lines[current - 1].strip().startswith("#"):
            return True
    return False


def translate(
    *, path: Path, source: str, declaration: TranslatorDeclaration, **_: Any
) -> LanguageUnit:
    """Translate Python source into a policy-agnostic LanguageUnit."""
    lines = source.splitlines()
    comments = _comment_lines(source)
    identifiers: list[IdentifierFact] = []
    symbol_docs: list[SymbolDocFact] = []
    risks: list[RiskFact] = []

    try:
        module = ast.parse(source)
    except SyntaxError:
        return LanguageUnit(
            translator_id=declaration.translator_id,
            profile_name=declaration.profile_name,
            language="python",
            path=str(path),
            suffix=path.suffix.lower(),
            source=source,
            module_documented=False,
            identifier_facts=tuple(),
            symbol_doc_facts=tuple(),
            risk_facts=tuple(),
            test_name_templates=TEST_TEMPLATES,
        )

    module_documented = bool(ast.get_docstring(module)) or any(
        line <= 5 for line in comments
    )
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            identifiers.append(
                IdentifierFact(node.name, node.lineno, "function")
            )
            documented = bool(ast.get_docstring(node)) or _has_nearby_comment(
                node.lineno, lines
            )
            symbol_docs.append(
                SymbolDocFact("function", node.name, node.lineno, documented)
            )
            args = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
            for arg in args:
                identifiers.append(
                    IdentifierFact(
                        arg.arg,
                        getattr(arg, "lineno", node.lineno),
                        "argument",
                    )
                )
            if node.args.vararg:
                identifiers.append(
                    IdentifierFact(
                        node.args.vararg.arg, node.lineno, "argument"
                    )
                )
            if node.args.kwarg:
                identifiers.append(
                    IdentifierFact(
                        node.args.kwarg.arg, node.lineno, "argument"
                    )
                )
            continue
        if isinstance(node, ast.ClassDef):
            identifiers.append(IdentifierFact(node.name, node.lineno, "class"))
            documented = bool(ast.get_docstring(node)) or _has_nearby_comment(
                node.lineno, lines
            )
            symbol_docs.append(
                SymbolDocFact("class", node.name, node.lineno, documented)
            )
            continue
        if isinstance(node, ast.Name):
            identifiers.append(
                IdentifierFact(
                    node.id, getattr(node, "lineno", 1), "identifier"
                )
            )

    for pattern, message in RISK_PATTERNS:
        for match in pattern.finditer(source):
            line_number = source.count("\n", 0, match.start()) + 1
            window = lines[max(0, line_number - 3) : line_number]
            if any(ALLOW_SECURITY in text for text in window):
                continue
            risks.append(RiskFact("error", line_number, message))

    return LanguageUnit(
        translator_id=declaration.translator_id,
        profile_name=declaration.profile_name,
        language="python",
        path=str(path),
        suffix=path.suffix.lower(),
        source=source,
        module_documented=module_documented,
        identifier_facts=tuple(identifiers),
        symbol_doc_facts=tuple(symbol_docs),
        risk_facts=tuple(risks),
        test_name_templates=TEST_TEMPLATES,
    )
