"""Unit tests for the OpenCL language translator."""

import importlib.util
import unittest
from pathlib import Path

from devcovenant.core.translator import TranslatorDeclaration

_REPO_ROOT = Path(__file__).resolve().parents[5]
_TRANSLATOR_PATH = (
    _REPO_ROOT / "devcovenant/builtin/profiles/opencl/opencl_translator.py"
)


def _load_translator_module():
    """Load the translator module from the profile directory."""
    spec = importlib.util.spec_from_file_location(
        "opencl_translator", _TRANSLATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _declaration() -> TranslatorDeclaration:
    """Build a translator declaration for this profile."""
    return TranslatorDeclaration(
        translator_id="opencl",
        profile_name="opencl",
        extensions=(".cl", ".ocl", ".opencl"),
        can_handle_strategy="module_function",
        can_handle_entrypoint="opencl_translator.py:can_handle",
        translate_strategy="module_function",
        translate_entrypoint="opencl_translator.py:translate",
    )


class OpenClTranslatorTests(unittest.TestCase):
    """Verify OpenCL translation behavior."""

    def test_can_handle_suffix(self):
        """Declared suffixes are honored."""
        module = _load_translator_module()
        self.assertTrue(
            module.can_handle(
                path=Path("kernel.cl"), declaration=_declaration()
            )
        )

    def test_translate_emits_identifier_and_risk_facts(self):
        """Translation includes identifiers and risky patterns."""
        module = _load_translator_module()
        self.assertTrue(callable(module.translate))
        unit = module.translate(
            path=Path("kernel.cl"),
            source=(
                "// docs\n"
                "__kernel void saxpy(__global float* x) {\n"
                '  printf("debug");\n'
                "}\n"
            ),
            declaration=_declaration(),
        )
        names = {fact.name for fact in unit.identifier_facts}
        self.assertIn("saxpy", names)
        self.assertTrue(unit.risk_facts)


if __name__ == "__main__":
    unittest.main()
