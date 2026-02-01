"""Python adapter for docstring/comment coverage."""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path
from typing import List, Set

from devcovenant.core.base import Violation


def _collect_comment_lines(source: str) -> Set[int]:
    """Return the line numbers that contain standalone comments."""
    lines: Set[int] = set()
    reader = io.StringIO(source).readline
    try:
        for token in tokenize.generate_tokens(reader):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
    except tokenize.TokenError:
        pass
    return lines


def _has_comment_before(
    line: int, comment_lines: Set[int], lookback: int = 3
) -> bool:
    """Check whether a comment exists in the preceding lines."""
    for offset in range(lookback + 1):
        target = line - offset
        if target <= 0:
            continue
        if target in comment_lines:
            return True
    return False


def check_file(path: Path, source: str, policy_id: str) -> List[Violation]:
    """Return violations for a single Python file."""
    violations: List[Violation] = []

    comment_lines = _collect_comment_lines(source)

    try:
        module_node = ast.parse(source)
    except SyntaxError:
        return violations

    module_doc = ast.get_docstring(module_node)
    if not module_doc and not _has_comment_before(
        1, comment_lines, lookback=5
    ):
        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                message=(
                    "Module lacks a descriptive top-level docstring "
                    "or preceding comment."
                ),
            )
        )

    for node in ast.walk(module_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbol = node.name
            symbol_type = "function"
        elif isinstance(node, ast.ClassDef):
            symbol = node.name
            symbol_type = "class"
        else:
            continue

        if ast.get_docstring(node):
            continue

        if _has_comment_before(node.lineno, comment_lines):
            continue

        violations.append(
            Violation(
                policy_id=policy_id,
                severity="error",
                file_path=path,
                line_number=node.lineno,
                message=(
                    f"{symbol_type.title()} '{symbol}' is missing "
                    "a docstring or adjacent explanatory comment."
                ),
            )
        )

    return violations
