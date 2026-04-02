"""Contract tests for the run-scoped YAML cache helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.services import yaml_cache as yaml_cache_service


class GeneratedUnittestCases(unittest.TestCase):
    """unittest coverage for cached YAML/text loading."""

    def tearDown(self) -> None:
        """Clear cache state after each test."""
        yaml_cache_service.clear_yaml_cache()

    def test_load_yaml_reuses_cached_parse_for_unchanged_file(self):
        """Repeated loads should reuse cached YAML for one file signature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "demo.yaml"
            path.write_text("value: 1\n", encoding="utf-8")

            calls = {"count": 0}
            original = yaml_cache_service.yaml.load

            def counting_safe_load(text, *, Loader):
                """Count parser calls so the test can prove cache reuse."""
                calls["count"] += 1
                return original(text, Loader=Loader)

            yaml_cache_service.yaml.load = counting_safe_load
            try:
                first = yaml_cache_service.load_yaml(path)
                second = yaml_cache_service.load_yaml(path)
            finally:
                yaml_cache_service.yaml.load = original

            self.assertEqual({"value": 1}, first)
            self.assertEqual({"value": 1}, second)
            self.assertEqual(1, calls["count"])

    def test_load_yaml_reloads_after_file_signature_changes(self):
        """File updates should invalidate the cached YAML content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "demo.yaml"
            path.write_text("value: 1\n", encoding="utf-8")

            first = yaml_cache_service.load_yaml(path)
            path.write_text("value: 22\nextra: true\n", encoding="utf-8")
            second = yaml_cache_service.load_yaml(path)

            self.assertEqual({"value": 1}, first)
            self.assertEqual({"value": 22, "extra": True}, second)

    def test_read_text_reuses_cached_text_for_unchanged_file(self):
        """Repeated text reads should reuse cached content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "demo.txt"
            path.write_text("alpha\n", encoding="utf-8")

            first = yaml_cache_service.read_text(path)
            second = yaml_cache_service.read_text(path)

            self.assertEqual("alpha\n", first)
            self.assertEqual("alpha\n", second)
