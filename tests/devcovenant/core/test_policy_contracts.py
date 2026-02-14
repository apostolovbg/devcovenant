"""Tests for core base helpers."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import unittest
from pathlib import Path

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    PolicyFixer,
)


class DummyPolicy(PolicyCheck):
    """Minimal policy used for get_option tests."""

    def check(self, context):
        """Return no violations for the dummy policy."""
        return []


def _iter_policy_script_paths() -> list[Path]:
    """Return policy implementation module paths."""
    roots = [
        Path("devcovenant/core/policies"),
        Path("devcovenant/custom/policies"),
    ]
    scripts: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for policy_dir in sorted(root.iterdir()):
            if not policy_dir.is_dir() or policy_dir.name.startswith("_"):
                continue
            script = policy_dir / f"{policy_dir.name}.py"
            if script.exists():
                scripts.append(script)
    return scripts


def _iter_fixer_module_paths() -> list[Path]:
    """Return policy fixer module paths."""
    roots = [
        Path("devcovenant/core/policies"),
        Path("devcovenant/custom/policies"),
    ]
    modules: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for policy_dir in sorted(root.iterdir()):
            if not policy_dir.is_dir() or policy_dir.name.startswith("_"):
                continue
            fixer_dir = policy_dir / "fixers"
            if not fixer_dir.exists():
                continue
            for module_path in sorted(fixer_dir.glob("*.py")):
                if (
                    module_path.name.startswith("_")
                    or module_path.name == "__init__.py"
                ):
                    continue
                modules.append(module_path)
    return modules


def _load_module_from_path(module_path: Path, module_name: str):
    """Load one module from path using deterministic module naming."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _assert_contract_method_signature(signature: inspect.Signature) -> None:
    """Validate required self + context/violation contract shape."""
    parameters = list(signature.parameters.values())
    assert len(parameters) >= 2
    assert parameters[0].name == "self"
    assert parameters[1].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )


def _unit_test_get_option_empty_metadata_falls_back() -> None:
    """Empty metadata values should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": []}, None)
    assert policy.get_option("alpha", "default") == "default"


def _unit_test_get_option_empty_string_falls_back() -> None:
    """Empty strings should not override defaults."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ""}, None)
    assert policy.get_option("alpha", "default") == "default"


def _unit_test_get_option_non_empty_preserves_value() -> None:
    """Non-empty values should be returned as-is."""
    policy = DummyPolicy()
    policy.set_options({"alpha": ["one", "two"]}, None)
    assert policy.get_option("alpha", "default") == ["one", "two"]


def _unit_test_get_policy_config_merges_autogen_and_user_overrides() -> None:
    """User overrides should win over autogen values."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "autogen_metadata_overrides": {
                "line-length-limit": {"max_length": 79, "severity": "warning"}
            },
            "user_metadata_overrides": {
                "line-length-limit": {"severity": "error"}
            },
        },
    )
    assert context.get_policy_config("line-length-limit") == {
        "max_length": 79,
        "severity": "error",
    }


def _unit_test_get_policy_config_ignores_legacy_policies_block() -> None:
    """Legacy config.policies entries should not be used for overrides."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "policies": {"line-length-limit": {"max_length": 999}},
        },
    )
    assert context.get_policy_config("line-length-limit") == {}


def _unit_test_get_policy_config_normalizes_scalar_path_overrides() -> None:
    """Path-valued scalar keys should flatten singleton override lists."""
    context = CheckContext(
        repo_root=Path("."),
        config={
            "autogen_metadata_overrides": {
                "version-sync": {
                    "version_file": ["devcovenant/VERSION"],
                    "readme_files": ["README.md", "AGENTS.md"],
                }
            },
            "user_metadata_overrides": {
                "version-sync": {
                    "changelog_file": ["CHANGELOG.md"],
                }
            },
        },
    )
    assert context.get_policy_config("version-sync") == {
        "version_file": "devcovenant/VERSION",
        "readme_files": ["README.md", "AGENTS.md"],
        "changelog_file": "CHANGELOG.md",
    }


def _unit_test_policy_modules_expose_policy_check_contract() -> None:
    """Policy modules should expose PolicyCheck subclasses."""
    scripts = _iter_policy_script_paths()
    assert scripts
    for module_path in scripts:
        module_token = module_path.with_suffix("").as_posix().replace("/", ".")
        module_name = "tests.devcovenant.core.contract_policy." + module_token
        module = _load_module_from_path(module_path, module_name)
        policy_classes = []
        for _, value in inspect.getmembers(module, inspect.isclass):
            if issubclass(value, PolicyCheck) and value is not PolicyCheck:
                policy_classes.append(value)
        assert policy_classes, f"missing PolicyCheck subclass in {module_path}"
        for policy_class in policy_classes:
            instance = policy_class()
            assert isinstance(instance, PolicyCheck)
            assert str(instance.policy_id or "").strip()
            _assert_contract_method_signature(
                inspect.signature(policy_class.check)
            )


def _unit_test_fixer_modules_expose_policy_fixer_contract() -> None:
    """Fixer modules should expose PolicyFixer subclasses."""
    modules = _iter_fixer_module_paths()
    assert modules
    for module_path in modules:
        module_token = module_path.with_suffix("").as_posix().replace("/", ".")
        module_name = "tests.devcovenant.core.contract_fixer." + module_token
        module = _load_module_from_path(module_path, module_name)
        fixer_classes = []
        for _, value in inspect.getmembers(module, inspect.isclass):
            if issubclass(value, PolicyFixer) and value is not PolicyFixer:
                fixer_classes.append(value)
        assert fixer_classes, f"missing PolicyFixer subclass in {module_path}"
        for fixer_class in fixer_classes:
            instance = fixer_class()
            assert isinstance(instance, PolicyFixer)
            assert str(instance.policy_id or "").strip()
            _assert_contract_method_signature(
                inspect.signature(fixer_class.can_fix)
            )
            _assert_contract_method_signature(
                inspect.signature(fixer_class.fix)
            )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_get_option_empty_metadata_falls_back(self):
        """Run test_get_option_empty_metadata_falls_back."""
        _unit_test_get_option_empty_metadata_falls_back()

    def test_get_option_empty_string_falls_back(self):
        """Run test_get_option_empty_string_falls_back."""
        _unit_test_get_option_empty_string_falls_back()

    def test_get_option_non_empty_preserves_value(self):
        """Run test_get_option_non_empty_preserves_value."""
        _unit_test_get_option_non_empty_preserves_value()

    def test_get_policy_config_merges_autogen_and_user_overrides(self):
        """Run test_get_policy_config_merges_autogen_and_user_overrides."""
        _unit_test_get_policy_config_merges_autogen_and_user_overrides()

    def test_get_policy_config_ignores_legacy_policies_block(self):
        """Run test_get_policy_config_ignores_legacy_policies_block."""
        _unit_test_get_policy_config_ignores_legacy_policies_block()

    def test_get_policy_config_normalizes_scalar_path_overrides(self):
        """Run test_get_policy_config_normalizes_scalar_path_overrides."""
        _unit_test_get_policy_config_normalizes_scalar_path_overrides()

    def test_policy_modules_expose_policy_check_contract(self):
        """Run test_policy_modules_expose_policy_check_contract."""
        _unit_test_policy_modules_expose_policy_check_contract()

    def test_fixer_modules_expose_policy_fixer_contract(self):
        """Run test_fixer_modules_expose_policy_fixer_contract."""
        _unit_test_fixer_modules_expose_policy_fixer_contract()
