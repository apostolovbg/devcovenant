"""Sanity checks for devcovenant.core.services.translator_engine."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE = "devcovenant.core.services.translator_engine"


def _unit_test_module_importable() -> None:
    """Module should import without compatibility wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_translator_engine_symbol_contract_is_stable() -> None:
    """Translator engine public symbols and methods should remain available."""
    module = importlib.import_module(MODULE)

    class_contract = [
        "IdentifierFact",
        "LanguageUnit",
        "RiskFact",
        "SymbolDocFact",
        "TranslatorDeclaration",
        "TranslatorResolution",
        "TranslatorRuntime",
    ]
    for symbol in class_contract:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))

    function_contract = [
        "can_handle",
        "can_handle_declared_extensions",
        "translate_language_unit",
    ]
    for symbol in function_contract:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))

    runtime_method_contract = [
        "resolve",
        "translate",
    ]
    for symbol in runtime_method_contract:
        assert hasattr(module.TranslatorRuntime, symbol)
        assert callable(getattr(module.TranslatorRuntime, symbol))


def _unit_test_translator_engine_symbol_assertions_cover_public_api() -> None:
    """Translator engine tests should assert key public symbols explicitly."""
    module = importlib.import_module(MODULE)
    assert module.IdentifierFact
    assert module.LanguageUnit
    assert module.RiskFact
    assert module.SymbolDocFact
    assert module.TranslatorDeclaration
    assert module.TranslatorResolution
    assert module.TranslatorRuntime
    assert module.can_handle
    assert module.can_handle_declared_extensions
    assert module.translate_language_unit
    assert module.TranslatorRuntime.resolve
    assert module.TranslatorRuntime.translate


def _runtime_with_one_python_translator(module, repo_root: Path):
    """Build a minimal translator runtime with one translator."""
    profile_registry = {
        "python": {
            "category": "language",
            "path": "devcovenant/builtin/profiles/python",
            "translators": [
                {
                    "id": "python",
                    "extensions": [".py"],
                    "can_handle": {
                        "strategy": "module_function",
                        "entrypoint": "devcovenant.core.services."
                        "translator_engine.can_handle",
                    },
                    "translate": {
                        "strategy": "module_function",
                        "entrypoint": "devcovenant.core.services."
                        "translator_engine.translate",
                    },
                }
            ],
        }
    }
    return module.TranslatorRuntime(repo_root, profile_registry, ["python"])


def _fake_language_unit(module, *, path: Path, source: str):
    """Create one minimal immutable LanguageUnit for translator tests."""
    return module.LanguageUnit(
        translator_id="python",
        profile_name="python",
        language="python",
        path=str(path),
        suffix=path.suffix.lower(),
        source=source,
        module_documented=False,
        identifier_facts=tuple(),
        symbol_doc_facts=tuple(),
        risk_facts=tuple(),
        test_name_templates=tuple(),
    )


def _unit_test_resolve_reuses_can_handle_cache_across_policies() -> None:
    """Resolve should reuse can_handle results for same file/context."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        path = repo_root / "sample.py"
        path.write_text("print('x')\n", encoding="utf-8")
        runtime = _runtime_with_one_python_translator(module, repo_root)
        context = object()

        with mock.patch.object(
            runtime,
            "_invoke_strategy",
            side_effect=lambda *_a, **_k: True,
        ) as invoke_mock:
            first = runtime.resolve(
                path=path,
                policy_id="policy-one",
                context=context,
            )
            second = runtime.resolve(
                path=path,
                policy_id="policy-two",
                context=context,
            )

        assert first.is_resolved is True
        assert second.is_resolved is True
        assert invoke_mock.call_count == 1


def _unit_test_translate_reuses_cached_language_unit() -> None:
    """Translate should return cached immutable LanguageUnit on repeats."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        path = repo_root / "sample.py"
        path.write_text("print('x')\n", encoding="utf-8")
        runtime = _runtime_with_one_python_translator(module, repo_root)
        declaration = runtime._by_extension[".py"][0]
        resolution = module.TranslatorResolution(declaration, tuple())
        source = "print('x')\n"
        expected = _fake_language_unit(module, path=path, source=source)
        context = object()

        with mock.patch.object(
            runtime,
            "_invoke_strategy",
            return_value=expected,
        ) as invoke_mock:
            first = runtime.translate(
                resolution,
                path=path,
                source=source,
                context=context,
            )
            second = runtime.translate(
                resolution,
                path=path,
                source=source,
                context=context,
            )

        assert first is expected
        assert second is expected
        assert invoke_mock.call_count == 1


def _unit_test_translate_cache_is_bounded() -> None:
    """Translate cache should evict oldest entries when over capacity."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        path = repo_root / "sample.py"
        path.write_text("print('x')\n", encoding="utf-8")
        runtime = _runtime_with_one_python_translator(module, repo_root)
        declaration = runtime._by_extension[".py"][0]
        resolution = module.TranslatorResolution(declaration, tuple())
        context = object()
        call_count = 0

        def _fake_translate(*_args, **kwargs):
            """Return unique LanguageUnit payloads keyed by source text."""
            nonlocal call_count
            call_count += 1
            return _fake_language_unit(
                module,
                path=kwargs["path"],
                source=kwargs["source"],
            )

        with mock.patch.object(
            module,
            "_TRANSLATE_CACHE_MAX_ENTRIES",
            2,
        ):
            with mock.patch.object(
                runtime,
                "_invoke_strategy",
                side_effect=_fake_translate,
            ):
                runtime.translate(
                    resolution,
                    path=path,
                    source="a\n",
                    context=context,
                )
                runtime.translate(
                    resolution,
                    path=path,
                    source="b\n",
                    context=context,
                )
                runtime.translate(
                    resolution,
                    path=path,
                    source="c\n",
                    context=context,
                )
                assert len(runtime._translate_result_cache) == 2
                runtime.translate(
                    resolution,
                    path=path,
                    source="a\n",
                    context=context,
                )

        assert call_count == 4


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_translator_engine_symbol_contract_is_stable(self):
        """Run translator-engine public symbol contract assertions."""
        _unit_test_translator_engine_symbol_contract_is_stable()

    def test_translator_engine_symbol_assertions_cover_public_api(self):
        """Run translator-engine explicit symbol coverage assertions."""
        _unit_test_translator_engine_symbol_assertions_cover_public_api()

    def test_resolve_reuses_can_handle_cache_across_policies(self):
        """Run can-handle cache reuse assertions across policy resolves."""
        _unit_test_resolve_reuses_can_handle_cache_across_policies()

    def test_translate_reuses_cached_language_unit(self):
        """Run translator result-cache reuse assertions."""
        _unit_test_translate_reuses_cached_language_unit()

    def test_translate_cache_is_bounded(self):
        """Run translator result-cache bounded eviction assertions."""
        _unit_test_translate_cache_is_bounded()
