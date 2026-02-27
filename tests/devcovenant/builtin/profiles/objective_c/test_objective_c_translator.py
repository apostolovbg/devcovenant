"""Unit tests for the Objective-C language translator."""

import importlib.util
import unittest
from pathlib import Path

from devcovenant.core.services.translator_engine import TranslatorDeclaration

_REPO_ROOT = Path(__file__).resolve().parents[5]
_TRANSLATOR_PATH = (
    _REPO_ROOT
    / "devcovenant/builtin/profiles/objective_c/objective_c_translator.py"
)


def _load_translator_module():
    """Load the translator module from the profile directory."""
    spec = importlib.util.spec_from_file_location(
        "objective_c_translator", _TRANSLATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _declaration() -> TranslatorDeclaration:
    """Build a translator declaration for this profile."""
    return TranslatorDeclaration(
        translator_id="objective_c",
        profile_name="objective_c",
        extensions=(".m", ".mm", ".h"),
        can_handle_strategy="module_function",
        can_handle_entrypoint="objective_c_translator.py:can_handle",
        translate_strategy="module_function",
        translate_entrypoint="objective_c_translator.py:translate",
    )


class ObjectiveCTranslatorTests(unittest.TestCase):
    """Verify Objective-C translation behavior."""

    def test_can_handle_suffix(self):
        """Declared suffixes are honored."""
        module = _load_translator_module()
        self.assertTrue(
            module.can_handle(
                path=Path("sample.m"), declaration=_declaration()
            )
        )

    def test_translate_emits_identifier_and_risk_facts(self):
        """Translation includes identifiers and risky patterns."""
        module = _load_translator_module()
        unit = module.translate(
            path=Path("sample.m"),
            source=(
                "// docs\n@interface Runner : NSObject\n"
                "- (void)run;\n@end\n"
                'void launch(void) { system("ls"); }\n'
            ),
            declaration=_declaration(),
        )
        names = {fact.name for fact in unit.identifier_facts}
        self.assertIn("Runner", names)
        self.assertTrue(unit.risk_facts)


if __name__ == "__main__":
    unittest.main()
