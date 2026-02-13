"""Tests for centralized translator runtime resolution."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.translator_runtime import LanguageUnit, TranslatorRuntime


def _runtime_with_profiles(
    profile_registry: dict, active: list[str]
) -> TranslatorRuntime:
    """Create runtime with provided profile metadata."""
    return TranslatorRuntime(
        repo_root=Path.cwd(),
        profile_registry=profile_registry,
        active_profiles=active,
    )


def _translator_decl(
    translator_id: str,
    extensions: list[str],
    *,
    can_handle_entrypoint: str = (
        "devcovenant.core.translator_runtime.can_handle_declared_extensions"
    ),
) -> dict:
    """Build one normalized translator declaration dict."""
    return {
        "id": translator_id,
        "extensions": extensions,
        "can_handle": {
            "strategy": "module_function",
            "entrypoint": can_handle_entrypoint,
        },
        "translate": {
            "strategy": "module_function",
            "entrypoint": (
                "devcovenant.core.translator_runtime.translate_language_unit"
            ),
        },
    }


def _unit_test_resolve_no_candidate_violation(tmp_path: Path) -> None:
    """Resolution should error when no extension candidate exists."""
    runtime = _runtime_with_profiles(
        {
            "python": {
                "category": "language",
                "translators": [_translator_decl("python", [".py"])],
            }
        },
        ["python"],
    )
    target = tmp_path / "sample.js"
    target.write_text("const x = 1;\n", encoding="utf-8")
    result = runtime.resolve(path=target, policy_id="name-clarity")
    assert not result.is_resolved
    assert result.declaration is None
    assert len(result.violations) == 1
    assert (
        "No translator matched extension '.js'" in result.violations[0].message
    )


def _unit_test_resolve_ambiguous_violation(tmp_path: Path) -> None:
    """Resolution should error when multiple candidates match."""
    registry = {
        "javascript": {
            "category": "language",
            "translators": [_translator_decl("javascript", [".js"])],
        },
        "typescript": {
            "category": "language",
            "translators": [_translator_decl("typescript", [".js"])],
        },
    }
    runtime = _runtime_with_profiles(registry, ["javascript", "typescript"])
    target = tmp_path / "sample.js"
    target.write_text("const x = 1;\n", encoding="utf-8")
    result = runtime.resolve(path=target, policy_id="name-clarity")
    assert not result.is_resolved
    assert result.declaration is None
    assert len(result.violations) == 1
    assert "ambiguous" in result.violations[0].message.lower()


def _unit_test_resolve_single_candidate_and_translate(tmp_path: Path) -> None:
    """Resolution should return one declaration and translated payload."""
    runtime = _runtime_with_profiles(
        {
            "python": {
                "category": "language",
                "translators": [_translator_decl("python", [".py", ".pyi"])],
            }
        },
        ["python"],
    )
    target = tmp_path / "sample.py"
    target.write_text("value = 1\n", encoding="utf-8")
    result = runtime.resolve(path=target, policy_id="name-clarity")
    assert result.is_resolved
    assert result.declaration is not None
    payload = runtime.translate(
        result,
        path=target,
        source=target.read_text(encoding="utf-8"),
    )
    assert isinstance(payload, LanguageUnit)
    assert payload.translator_id == "python"
    assert payload.suffix == ".py"
    assert payload.source == "value = 1\n"


def _unit_test_can_handle_no_match_violation(tmp_path: Path) -> None:
    """Resolution should report no-match when candidates reject file."""
    runtime = _runtime_with_profiles(
        {
            "python": {
                "category": "language",
                "translators": [
                    _translator_decl(
                        "python",
                        [".py"],
                        can_handle_entrypoint=(
                            "tests.devcovenant.core.test_translator_runtime."
                            "always_false_can_handle"
                        ),
                    )
                ],
            }
        },
        ["python"],
    )
    target = tmp_path / "sample.py"
    target.write_text("value = 1\n", encoding="utf-8")
    result = runtime.resolve(path=target, policy_id="name-clarity")
    assert not result.is_resolved
    assert "no accepted candidate" in result.violations[0].message.lower()


def always_false_can_handle(**_kwargs) -> bool:
    """Helper strategy that always rejects candidates."""
    return False


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_resolve_no_candidate_violation(self):
        """Run test_resolve_no_candidate_violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_resolve_no_candidate_violation(Path(temp_dir))

    def test_resolve_ambiguous_violation(self):
        """Run test_resolve_ambiguous_violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_resolve_ambiguous_violation(Path(temp_dir))

    def test_resolve_single_candidate_and_translate(self):
        """Run test_resolve_single_candidate_and_translate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_resolve_single_candidate_and_translate(Path(temp_dir))

    def test_can_handle_no_match_violation(self):
        """Run test_can_handle_no_match_violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_can_handle_no_match_violation(Path(temp_dir))
