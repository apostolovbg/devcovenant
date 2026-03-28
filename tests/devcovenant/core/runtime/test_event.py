"""Tests for explicit run-event adapter behavior."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE = "devcovenant.core.runtime.event"
PACKAGE_MODULES = (
    "devcovenant.core.flow",
    "devcovenant.core.runtime",
    "devcovenant.core.services",
    "devcovenant.core.contracts",
    "devcovenant.core.lib",
)
SUBMODULE_IMPORTS = (
    "devcovenant.core.flow.gate",
    "devcovenant.core.runtime.execution",
    "devcovenant.core.runtime.event",
    "devcovenant.core.contracts.policy",
    "devcovenant.core.lib.selectors",
)


def _timestamp_range() -> tuple[datetime, datetime]:
    """Return deterministic start/finish timestamps for event tests."""
    started = datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc)
    finished = started + timedelta(seconds=3)
    return started, finished


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_event_symbol_contract_is_stable() -> None:
    """Event service classes/functions should keep a stable surface."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "consume_run_event_adapter_warnings")
    assert hasattr(module, "generic_run_event_adapter_factory")
    assert hasattr(module, "load_run_event_adapters")
    assert hasattr(module, "python_run_event_adapter_factory")
    assert hasattr(module, "RunEvent")
    assert hasattr(module, "RunEventAdapter")
    assert hasattr(module, "GenericRunEventAdapter")
    assert hasattr(module, "PythonRunEventAdapter")
    assert hasattr(module, "RunEventManager")

    assert hasattr(module.RunEvent, "to_dict")
    assert hasattr(module.RunEventAdapter, "build_event")
    assert hasattr(module.RunEventAdapter, "handles")
    assert hasattr(module.RunEventManager, "record_command")
    assert not hasattr(module, "consume_test_event_adapter_warnings")
    assert not hasattr(module, "load_test_event_adapters")
    assert not hasattr(module, "TestEvent")


def _unit_test_core_packages_do_not_define_dynamic_getattr() -> None:
    """Core package namespaces should not use lazy dynamic package hooks."""
    for module_name in PACKAGE_MODULES:
        module = importlib.import_module(module_name)
        assert "__getattr__" not in module.__dict__


def _unit_test_direct_submodule_imports_still_work() -> None:
    """Concrete submodule imports should work without package shims."""
    for module_name in SUBMODULE_IMPORTS:
        module = importlib.import_module(module_name)
        assert module is not None


def _unit_test_unmatched_command_is_skipped_without_generic_adapter() -> None:
    """Commands without a configured adapter should be skipped explicitly."""
    module = importlib.import_module(MODULE)
    adapter = module.python_run_event_adapter_factory(
        adapter_id="python",
        profile_name="python",
    )
    manager = module.RunEventManager([adapter])
    started, finished = _timestamp_range()

    recorded = manager.record_command(
        command=["npm", "test"],
        command_str="npm test",
        started=started,
        finished=finished,
        exit_code=0,
    )

    assert recorded is False
    assert manager.events == []


def _unit_test_explicit_generic_adapter_records_unmatched_command() -> None:
    """Profiles may opt in to generic coverage explicitly."""
    module = importlib.import_module(MODULE)
    adapter = module.generic_run_event_adapter_factory(
        adapter_id="generic",
        profile_name="demo",
    )
    manager = module.RunEventManager([adapter])
    started, finished = _timestamp_range()

    recorded = manager.record_command(
        command=["npm", "test"],
        command_str="npm test",
        started=started,
        finished=finished,
        exit_code=0,
    )

    assert recorded is True
    assert len(manager.events) == 1
    assert manager.events[0].adapter_id == "generic"
    assert manager.events[0].command == "npm test"


def _unit_test_profile_loader_accepts_explicit_generic_adapter() -> None:
    """Loader should materialize a profile-declared generic adapter."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "profiles:\n" "  active:\n" "    - python\n",
            encoding="utf-8",
        )

        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            "metadata:\n"
            "  schema_version: 1\n"
            "  registry_layout: single-root\n"
            "policies: {}\n"
            "profiles:\n"
            "  python:\n"
            "    run_events:\n"
            "      - id: generic\n"
            "        entrypoint: "
            "devcovenant.core.runtime.event:"
            "generic_run_event_adapter_factory\n"
            "inventory: {}\n",
            encoding="utf-8",
        )

        adapters = module.load_run_event_adapters(repo_root)

    assert len(adapters) == 1
    assert isinstance(adapters[0], module.GenericRunEventAdapter)
    assert adapters[0].adapter_id == "generic"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for run-event runtime assertions."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_event_symbol_contract_is_stable(self):
        """Run event service symbol contract assertions."""
        _unit_test_event_symbol_contract_is_stable()

    def test_core_packages_do_not_define_dynamic_getattr(self):
        """Run package-namespace no-`__getattr__` assertions."""
        _unit_test_core_packages_do_not_define_dynamic_getattr()

    def test_direct_submodule_imports_still_work(self):
        """Run direct-submodule import assertions."""
        _unit_test_direct_submodule_imports_still_work()

    def test_unmatched_command_is_skipped_without_generic_adapter(self):
        """Run unmatched-command explicit-skip assertions."""
        _unit_test_unmatched_command_is_skipped_without_generic_adapter()

    def test_explicit_generic_adapter_records_unmatched_command(self):
        """Run explicit generic-adapter assertions."""
        _unit_test_explicit_generic_adapter_records_unmatched_command()

    def test_profile_loader_accepts_explicit_generic_adapter(self):
        """Run profile-loader explicit generic-adapter assertions."""
        _unit_test_profile_loader_accepts_explicit_generic_adapter()
