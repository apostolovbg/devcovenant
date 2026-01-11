"""Tests for devcovenant_check wrapper."""

import importlib.util
from pathlib import Path


def test_devcovenant_check_module_imports():
    """Wrapper module should import without executing CLI."""
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "devcovenant_check.py"
    spec = importlib.util.spec_from_file_location(
        "devcovenant_check", wrapper_path
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
