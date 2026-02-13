"""Unit tests for the Rust language translator."""

import importlib.util
import unittest
from pathlib import Path

from devcovenant.core.translator_runtime import TranslatorDeclaration

_REPO_ROOT = Path(__file__).resolve().parents[5]
_TRANSLATOR_PATH = _REPO_ROOT / "devcovenant/core/profiles/rust/translator.py"


def _load_translator_module():
    """Load the translator module from the profile directory."""
    spec = importlib.util.spec_from_file_location(
        "rust_translator", _TRANSLATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _declaration() -> TranslatorDeclaration:
    """Build a translator declaration for this profile."""
    return TranslatorDeclaration(
        translator_id="rust",
        profile_name="rust",
        extensions=(".rs",),
        can_handle_strategy="module_function",
        can_handle_entrypoint="translator.py:can_handle",
        translate_strategy="module_function",
        translate_entrypoint="translator.py:translate",
    )


class RustTranslatorTests(unittest.TestCase):
    """Verify Rust translation behavior."""

    def test_can_handle_suffix(self):
        """Declared suffixes are honored."""
        module = _load_translator_module()
        self.assertTrue(
            module.can_handle(
                path=Path("sample.rs"), declaration=_declaration()
            )
        )

    def test_translate_emits_identifier_and_risk_facts(self):
        """Translation includes identifiers and risky patterns."""
        module = _load_translator_module()
        unit = module.translate(
            path=Path("sample.rs"),
            source="// docs\nfn run(){ unsafe { let _x = 1; }}\n",
            declaration=_declaration(),
        )
        names = {fact.name for fact in unit.identifier_facts}
        self.assertIn("run", names)
        self.assertTrue(unit.risk_facts)


if __name__ == "__main__":
    unittest.main()
