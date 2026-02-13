"""Centralized translator runtime and policy-agnostic LanguageUnit model."""

from __future__ import annotations

import ast
import importlib
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import Violation

MODULE_FUNCTION = "module_function"
ALLOW_NAME_CLARITY = "name-clarity: allow"
ALLOW_SECURITY = "security-scanner: allow"

_PLACEHOLDER_NAMES = {
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
_SHORT_NAME_ALLOW = {"i", "j", "k", "x", "y", "z"}

_LANGUAGE_ALIASES = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "go": "go",
    "rust": "rust",
    "java": "java",
    "csharp": "csharp",
}

_SYMBOL_PATTERNS = {
    "javascript": [
        ("function", re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)")),
        (
            "class",
            re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
        (
            "variable",
            re.compile(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
    ],
    "typescript": [
        ("function", re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)")),
        (
            "class",
            re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
        (
            "variable",
            re.compile(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
    ],
    "go": [
        ("function", re.compile(r"\bfunc\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("type", re.compile(r"\btype\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("variable", re.compile(r"\bvar\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ],
    "rust": [
        ("function", re.compile(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("type", re.compile(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)")),
        (
            "variable",
            re.compile(r"\blet\s+(?:mut\s+)?([A-Za-z_][A-Za-z0-9_]*)"),
        ),
    ],
    "java": [
        (
            "class",
            re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
        (
            "function",
            re.compile(
                r"\b(?:public|private|protected)?\s*"
                r"(?:static\s+)?[A-Za-z_][A-Za-z0-9_<>,\[\]]*\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\("
            ),
        ),
        (
            "variable",
            re.compile(
                r"\b(?:final\s+)?[A-Za-z_][A-Za-z0-9_<>,\[\]]*\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*="
            ),
        ),
    ],
    "csharp": [
        (
            "class",
            re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)"),
        ),
        (
            "function",
            re.compile(
                r"\b(?:public|private|protected|internal)?\s*"
                r"(?:static\s+)?[A-Za-z_][A-Za-z0-9_<>,\[\]?]*\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\("
            ),
        ),
        (
            "variable",
            re.compile(
                r"\b(?:var|[A-Za-z_][A-Za-z0-9_<>,\[\]?]*)\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*="
            ),
        ),
    ],
}

_RISK_PATTERNS = {
    "python": [
        (
            "error",
            re.compile(r"\beval\s*\("),  # security-scanner: allow
            "Avoid eval().",
        ),
        (
            "error",
            re.compile(r"\bexec\s*\("),  # security-scanner: allow
            "Avoid exec().",
        ),
        (
            "error",
            re.compile(r"\bpickle\.loads\s*\("),  # security-scanner: allow
            "Avoid untrusted pickle.loads().",
        ),
        (
            "error",
            re.compile(r"\bsubprocess\.run\s*\([^)]*shell\s*=\s*True"),
            "Avoid shell=True in subprocess.run().",
        ),
    ],
    "javascript": [
        (
            "error",
            re.compile(r"\beval\s*\("),  # security-scanner: allow
            "Avoid eval().",
        ),
        (
            "error",
            re.compile(r"\bnew\s+Function\s*\("),
            "Avoid Function constructor.",
        ),
        (
            "error",
            re.compile(r"child_process\.exec"),
            "Avoid child_process.exec.",
        ),
    ],
    "typescript": [
        (
            "error",
            re.compile(r"\beval\s*\("),  # security-scanner: allow
            "Avoid eval().",
        ),
        (
            "error",
            re.compile(r"\bnew\s+Function\s*\("),
            "Avoid Function constructor.",
        ),
        (
            "error",
            re.compile(r"child_process\.exec"),
            "Avoid child_process.exec.",
        ),
    ],
    "go": [
        (
            "warning",
            re.compile(r"os/exec"),
            "Avoid os/exec imports.",
        ),
        (
            "warning",
            re.compile(r"\bexec\.Command\s*\("),
            "Review exec.Command usage.",
        ),
    ],
    "rust": [
        (
            "warning",
            re.compile(r"\bunsafe\s*\{"),
            "Review unsafe blocks.",
        )
    ],
    "java": [
        (
            "warning",
            re.compile(r"Runtime\.getRuntime\(\)\.exec"),
            "Review Runtime.exec usage.",
        ),
        (
            "warning",
            re.compile(r"ProcessBuilder\s*\("),
            "Review ProcessBuilder usage.",
        ),
    ],
    "csharp": [
        (
            "warning",
            re.compile(r"\bProcess\.Start\s*\("),
            "Review Process.Start usage.",
        )
    ],
}

_TEST_NAMING = {
    "python": ["test_{stem}.py", "{stem}_test.py"],
    "javascript": [
        "{stem}.test.js",
        "{stem}.spec.js",
        "test_{stem}.js",
        "{stem}.test.jsx",
        "{stem}.spec.jsx",
    ],
    "typescript": [
        "{stem}.test.ts",
        "{stem}.spec.ts",
        "test_{stem}.ts",
        "{stem}.test.tsx",
        "{stem}.spec.tsx",
    ],
    "go": ["{stem}_test.go"],
    "rust": ["{stem}_test.rs"],
    "java": ["{stem}Test.java", "{stem}Tests.java"],
    "csharp": ["{stem}Test.cs", "{stem}Tests.cs"],
}


@dataclass(frozen=True)
class IdentifierFact:
    """Identifier discovered by a translator."""

    name: str
    line_number: int
    kind: str


@dataclass(frozen=True)
class SymbolDocFact:
    """Symbol documentation status emitted by a translator."""

    kind: str
    name: str
    line_number: int
    documented: bool


@dataclass(frozen=True)
class RiskFact:
    """Potentially risky construct discovered by a translator."""

    severity: str
    line_number: int
    message: str


@dataclass(frozen=True)
class LanguageUnit:
    """Policy-agnostic translated representation for one source file."""

    translator_id: str
    profile_name: str
    language: str
    path: str
    suffix: str
    source: str
    module_documented: bool
    identifier_facts: tuple[IdentifierFact, ...]
    symbol_doc_facts: tuple[SymbolDocFact, ...]
    risk_facts: tuple[RiskFact, ...]
    test_name_templates: tuple[str, ...]


@dataclass(frozen=True)
class TranslatorDeclaration:
    """Normalized translator declaration owned by one language profile."""

    translator_id: str
    profile_name: str
    extensions: tuple[str, ...]
    can_handle_strategy: str
    can_handle_entrypoint: str
    translate_strategy: str
    translate_entrypoint: str


@dataclass(frozen=True)
class TranslatorResolution:
    """Result of resolving a translator for one file."""

    declaration: TranslatorDeclaration | None
    violations: tuple[Violation, ...]

    @property
    def is_resolved(self) -> bool:
        """Return True when exactly one translator matched."""
        return self.declaration is not None and not self.violations


@dataclass(frozen=True)
class _LanguageFacts:
    """Internal normalized facts before LanguageUnit assembly."""

    module_documented: bool
    identifiers: tuple[IdentifierFact, ...]
    symbol_docs: tuple[SymbolDocFact, ...]
    risks: tuple[RiskFact, ...]


def can_handle_declared_extensions(
    *, path: Path, declaration: TranslatorDeclaration, **_: Any
) -> bool:
    """Default can_handle strategy using declaration extensions."""
    return path.suffix.lower() in declaration.extensions


def translate_language_unit(
    *, path: Path, source: str, declaration: TranslatorDeclaration, **_: Any
) -> LanguageUnit:
    """Default translate strategy returning normalized LanguageUnit."""
    language = _normalize_language_key(declaration.translator_id)
    facts = _extract_language_facts(language, source)
    return LanguageUnit(
        translator_id=declaration.translator_id,
        profile_name=declaration.profile_name,
        language=language,
        path=str(path),
        suffix=path.suffix.lower(),
        source=source,
        module_documented=facts.module_documented,
        identifier_facts=facts.identifiers,
        symbol_doc_facts=facts.symbol_docs,
        risk_facts=facts.risks,
        test_name_templates=tuple(_TEST_NAMING.get(language, [])),
    )


def can_handle(**kwargs: Any) -> bool:
    """Short alias for profile entrypoints."""
    return can_handle_declared_extensions(**kwargs)


def translate(**kwargs: Any) -> LanguageUnit:
    """Short alias for profile entrypoints."""
    return translate_language_unit(**kwargs)


def _normalize_language_key(raw: str) -> str:
    """Normalize translator ids to the runtime language key."""
    normalized = str(raw or "").strip().lower()
    return _LANGUAGE_ALIASES.get(normalized, normalized)


def _collect_python_comment_lines(source: str) -> set[int]:
    """Collect line numbers that contain Python comments."""
    lines: set[int] = set()
    reader = io.StringIO(source).readline
    try:
        for token in tokenize.generate_tokens(reader):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
    except tokenize.TokenError:
        return lines
    return lines


def _has_nearby_comment(
    line_number: int,
    lines: list[str],
    *,
    lookback: int = 3,
    prefixes: tuple[str, ...] = ("#", "//", "///", "/**", "/*", "*"),
) -> bool:
    """Return True when a nearby comment marker is present."""
    start = max(1, line_number - lookback)
    for current in range(start, line_number + 1):
        if current > len(lines):
            continue
        text = lines[current - 1].strip()
        if any(text.startswith(prefix) for prefix in prefixes):
            return True
    return False


def _extract_python_facts(source: str) -> _LanguageFacts:
    """Extract identifiers, documentation and risks from Python source."""
    lines = source.splitlines()
    comments = _collect_python_comment_lines(source)
    identifiers: list[IdentifierFact] = []
    symbol_docs: list[SymbolDocFact] = []
    risks: list[RiskFact] = []

    try:
        module = ast.parse(source)
    except SyntaxError:
        return _LanguageFacts(False, tuple(), tuple(), tuple())

    module_documented = bool(ast.get_docstring(module))
    if not module_documented:
        module_documented = any(line <= 5 for line in comments)

    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            identifiers.append(
                IdentifierFact(node.name, node.lineno, "function")
            )
            documented = bool(ast.get_docstring(node))
            if not documented:
                documented = _has_nearby_comment(node.lineno, lines)
            symbol_docs.append(
                SymbolDocFact("function", node.name, node.lineno, documented)
            )
            arguments = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
            for arg in arguments:
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
            documented = bool(ast.get_docstring(node))
            if not documented:
                documented = _has_nearby_comment(node.lineno, lines)
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

    for severity, pattern, message in _RISK_PATTERNS.get("python", []):
        for match in pattern.finditer(source):
            line_number = source.count("\n", 0, match.start()) + 1
            window = lines[max(0, line_number - 3) : line_number]
            if any(ALLOW_SECURITY in text for text in window):
                continue
            risks.append(RiskFact(severity, line_number, message))

    return _LanguageFacts(
        module_documented,
        tuple(identifiers),
        tuple(symbol_docs),
        tuple(risks),
    )


def _extract_generic_facts(language: str, source: str) -> _LanguageFacts:
    """Extract facts from non-Python source using regex heuristics."""
    lines = source.splitlines()
    module_documented = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        module_documented = stripped.startswith(
            ("//", "///", "/*", "/**", "*")
        )
        break

    identifiers: list[IdentifierFact] = []
    symbol_docs: list[SymbolDocFact] = []
    patterns = _SYMBOL_PATTERNS.get(language, [])
    for line_number, line in enumerate(lines, start=1):
        for kind, pattern in patterns:
            for match in pattern.finditer(line):
                name = match.group(1)
                identifiers.append(IdentifierFact(name, line_number, kind))
                if kind in {"function", "class", "type"}:
                    documented = _has_nearby_comment(line_number, lines)
                    symbol_docs.append(
                        SymbolDocFact(kind, name, line_number, documented)
                    )

    risks: list[RiskFact] = []
    for severity, pattern, message in _RISK_PATTERNS.get(language, []):
        for line_number, line in enumerate(lines, start=1):
            if ALLOW_SECURITY in line:
                continue
            if pattern.search(line):
                risks.append(RiskFact(severity, line_number, message))

    return _LanguageFacts(
        module_documented,
        tuple(identifiers),
        tuple(symbol_docs),
        tuple(risks),
    )


def _extract_language_facts(language: str, source: str) -> _LanguageFacts:
    """Dispatch language fact extraction."""
    if language == "python":
        return _extract_python_facts(source)
    return _extract_generic_facts(language, source)


def flag_name_clarity_identifiers(
    unit: LanguageUnit,
) -> tuple[IdentifierFact, ...]:
    """Return identifier facts that violate name-clarity heuristics."""
    lines = unit.source.splitlines()
    violations: list[IdentifierFact] = []
    seen: set[tuple[str, int]] = set()
    for fact in unit.identifier_facts:
        cleaned = fact.name.lstrip("_")
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in _SHORT_NAME_ALLOW:
            continue
        if len(cleaned) >= 3 and lowered not in _PLACEHOLDER_NAMES:
            continue
        if 1 <= fact.line_number <= len(lines):
            if ALLOW_NAME_CLARITY in lines[fact.line_number - 1]:
                continue
        key = (fact.name, fact.line_number)
        if key in seen:
            continue
        seen.add(key)
        violations.append(fact)
    return tuple(violations)


class TranslatorRuntime:
    """Resolve and invoke translators declared by active language profiles."""

    def __init__(
        self,
        repo_root: Path,
        profile_registry: dict[str, dict[str, Any]],
        active_profiles: list[str],
    ) -> None:
        """Store runtime state and precompute declarations by extension."""
        self.repo_root = Path(repo_root).resolve()
        self.profile_registry = profile_registry
        self.active_profiles = sorted(set(active_profiles))
        self._by_extension = self._build_extension_map()

    def resolve(
        self,
        *,
        path: Path,
        policy_id: str,
        context: Any | None = None,
    ) -> TranslatorResolution:
        """Resolve one translator declaration for a file path."""
        extension = path.suffix.lower()
        candidates = list(self._by_extension.get(extension, []))
        if not candidates:
            violation = Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                message=(
                    f"No translator matched extension '{extension}' for "
                    f"policy '{policy_id}'."
                ),
                suggestion=(
                    "Declare a language-profile translator with matching "
                    "extensions in active profile metadata."
                ),
            )
            return TranslatorResolution(None, (violation,))

        matched: list[TranslatorDeclaration] = []
        for declaration in candidates:
            if self._can_handle(declaration, path=path, context=context):
                matched.append(declaration)

        if not matched:
            candidate_ids = ", ".join(
                sorted(d.translator_id for d in candidates)
            )
            violation = Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                message=(
                    "Translator arbitration found no accepted candidate for "
                    f"extension '{extension}'. Candidates: {candidate_ids}."
                ),
                suggestion=(
                    "Review can_handle strategy/entrypoint declarations in "
                    "active language profiles."
                ),
            )
            return TranslatorResolution(None, (violation,))

        if len(matched) > 1:
            ids = ", ".join(sorted(d.translator_id for d in matched))
            violation = Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                message=(
                    f"Translator arbitration is ambiguous for extension "
                    f"'{extension}'. Matched translators: {ids}."
                ),
                suggestion=(
                    "Adjust translator extensions or can_handle logic so "
                    "exactly one translator matches."
                ),
            )
            return TranslatorResolution(None, (violation,))

        return TranslatorResolution(matched[0], ())

    def translate(
        self,
        resolution: TranslatorResolution,
        *,
        path: Path,
        source: str,
        context: Any | None = None,
    ) -> LanguageUnit | None:
        """Invoke the translate strategy for a resolved declaration."""
        declaration = resolution.declaration
        if declaration is None:
            return None
        translated = self._invoke_strategy(
            declaration.translate_strategy,
            declaration.translate_entrypoint,
            path=path,
            source=source,
            context=context,
            declaration=declaration,
        )
        if isinstance(translated, LanguageUnit):
            return translated
        return None

    def _build_extension_map(self) -> dict[str, list[TranslatorDeclaration]]:
        """Build extension->declarations map from active language profiles."""
        mapping: dict[str, list[TranslatorDeclaration]] = {}
        for profile_name in self.active_profiles:
            metadata = self.profile_registry.get(profile_name, {})
            if metadata.get("category") != "language":
                continue
            translators = metadata.get("translators") or []
            for raw in translators:
                declaration = TranslatorDeclaration(
                    translator_id=str(raw["id"]),
                    profile_name=profile_name,
                    extensions=tuple(raw["extensions"]),
                    can_handle_strategy=str(raw["can_handle"]["strategy"]),
                    can_handle_entrypoint=str(raw["can_handle"]["entrypoint"]),
                    translate_strategy=str(raw["translate"]["strategy"]),
                    translate_entrypoint=str(raw["translate"]["entrypoint"]),
                )
                for extension in declaration.extensions:
                    mapping.setdefault(extension, []).append(declaration)
        return mapping

    def _can_handle(
        self,
        declaration: TranslatorDeclaration,
        *,
        path: Path,
        context: Any | None,
    ) -> bool:
        """Run the can_handle strategy and coerce to bool."""
        raw_result = self._invoke_strategy(
            declaration.can_handle_strategy,
            declaration.can_handle_entrypoint,
            path=path,
            context=context,
            declaration=declaration,
        )
        return bool(raw_result)

    def _invoke_strategy(
        self,
        strategy: str,
        entrypoint: str,
        **kwargs: Any,
    ) -> Any:
        """Invoke one strategy with deterministic supported modes."""
        if strategy != MODULE_FUNCTION:
            raise ValueError(
                f"Unsupported translator strategy '{strategy}'. "
                f"Expected '{MODULE_FUNCTION}'."
            )
        module_name, _, function_name = entrypoint.rpartition(".")
        if not module_name or not function_name:
            raise ValueError(
                f"Translator entrypoint '{entrypoint}' must be "
                "module.function."
            )
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        return function(**kwargs)
