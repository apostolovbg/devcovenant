"""Python translator for DevCovenant LanguageUnit generation."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.translator_engine import (
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


def _has_nearby_comment(line_number: int, lines: list[str]) -> bool:
    """Return True when a nearby comment marker is present."""
    start = max(1, line_number - 3)
    for current in range(start, line_number + 1):
        if current > len(lines):
            continue
        if lines[current - 1].strip().startswith("#"):
            return True
    return False


class _PythonFactsVisitor(ast.NodeVisitor):
    """Collect identifier and documentation facts in one tree walk."""

    def __init__(self, *, lines: list[str]) -> None:
        """Store source lines and initialize fact containers."""
        self.lines = lines
        self.identifiers: list[IdentifierFact] = []
        self.symbol_docs: list[SymbolDocFact] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Collect function identifiers and documentation facts."""
        self._visit_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Collect async-function identifiers and documentation facts."""
        self._visit_function(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect class identifiers and documentation facts."""
        self.identifiers.append(
            IdentifierFact(node.name, node.lineno, "class")
        )
        documented = bool(ast.get_docstring(node)) or _has_nearby_comment(
            node.lineno,
            self.lines,
        )
        self.symbol_docs.append(
            SymbolDocFact("class", node.name, node.lineno, documented)
        )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Collect generic identifier facts."""
        self.identifiers.append(
            IdentifierFact(node.id, getattr(node, "lineno", 1), "identifier")
        )

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Collect function facts for sync and async nodes."""
        self.identifiers.append(
            IdentifierFact(node.name, node.lineno, "function")
        )
        documented = bool(ast.get_docstring(node)) or _has_nearby_comment(
            node.lineno,
            self.lines,
        )
        self.symbol_docs.append(
            SymbolDocFact("function", node.name, node.lineno, documented)
        )
        args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        for arg in args:
            self.identifiers.append(
                IdentifierFact(
                    arg.arg,
                    getattr(arg, "lineno", node.lineno),
                    "argument",
                )
            )
        if node.args.vararg:
            self.identifiers.append(
                IdentifierFact(node.args.vararg.arg, node.lineno, "argument")
            )
        if node.args.kwarg:
            self.identifiers.append(
                IdentifierFact(node.args.kwarg.arg, node.lineno, "argument")
            )


def translate(
    *, path: Path, source: str, declaration: TranslatorDeclaration, **_: Any
) -> LanguageUnit:
    """Translate Python source into a policy-agnostic LanguageUnit."""
    lines = source.splitlines()
    risks: list[RiskFact] = []

    if path.exists():
        module = yaml_cache_service.parse_python_ast(path)
    else:
        try:
            module = ast.parse(source, filename=str(path))
        except SyntaxError:
            module = None
    if module is None:
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
        line.strip().startswith("#") for line in lines[:5]
    )
    visitor = _PythonFactsVisitor(lines=lines)
    visitor.visit(module)

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
        identifier_facts=tuple(visitor.identifiers),
        symbol_doc_facts=tuple(visitor.symbol_docs),
        risk_facts=tuple(risks),
        test_name_templates=TEST_TEMPLATES,
    )
