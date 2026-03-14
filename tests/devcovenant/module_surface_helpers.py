"""Shared helpers for mirrored module surface tests."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def assert_module_importable(module_name: str):
    """Import one module and return it for follow-up assertions."""
    module = importlib.import_module(module_name)
    assert module is not None
    return module


def assert_module_has_public_symbols(module_name: str) -> None:
    """Assert that an importable module exposes public names."""
    module = assert_module_importable(module_name)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def assert_python_file_parses(relative_path: str) -> None:
    """Assert that a repository Python file parses successfully."""
    source_path = REPO_ROOT / relative_path
    source_text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    assert tree is not None


def assert_source_contains_tokens(
    relative_path: str,
    expected_tokens: list[str],
) -> None:
    """Assert that source text contains expected marker tokens."""
    source_path = REPO_ROOT / relative_path
    source_text = source_path.read_text(encoding="utf-8")
    for token in expected_tokens:
        assert token in source_text, token
