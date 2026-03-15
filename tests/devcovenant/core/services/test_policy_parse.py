"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import unittest

from devcovenant.core.services.policy_parse import PolicyParser

MODULE = "devcovenant.core.services.policy_parse"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_symbol_contract_is_stable() -> None:
    """Policy parser module should expose stable parser/model symbols."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "PolicyDefinition")
    assert hasattr(module, "PolicyParser")
    assert hasattr(module.PolicyParser, "parse_agents_md")


def _unit_test_parse_metadata_preserves_colon_continuations() -> None:
    """Metadata parser should keep indented values containing colons."""
    block = """
id: demo-policy
severity: warning
auto_fix: false
enabled: true
custom: false
url_prefixes: http://
  https://
  ftp://
allow_long_lines: true
long_lines_contain: marker://
  token:with:colon
long_lines_between: START=>END
  before:=>after:
"""
    metadata = PolicyParser._parse_metadata_block(block.strip())
    assert metadata["url_prefixes"] == "http://,https://,ftp://"
    assert metadata["allow_long_lines"] == "true"
    assert metadata["long_lines_contain"] == "marker://,token:with:colon"
    assert metadata["long_lines_between"] == "START=>END,before:=>after:"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_symbol_contract_is_stable(self):
        """Run stable policy-parse symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_parse_metadata_preserves_colon_continuations(self):
        """Run metadata-continuation parsing assertions."""
        _unit_test_parse_metadata_preserves_colon_continuations()
