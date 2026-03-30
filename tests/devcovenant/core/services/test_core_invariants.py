"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.services.core_invariants"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_core_invariant_ids_are_stable() -> None:
    """Canonical invariant ids should remain present and ordered."""
    module = importlib.import_module(MODULE)
    assert module.core_invariant_ids() == [
        "devcov-integrity-guard",
        "devcov-structure-guard",
        "devflow-run-gates",
    ]


def _unit_test_load_core_invariant_descriptor_reads_real_descriptor() -> None:
    """Real repo descriptor loading should return the invariant metadata."""
    module = importlib.import_module(MODULE)
    descriptor = module.load_core_invariant_descriptor(
        REPO_ROOT, "devflow-run-gates"
    )
    assert descriptor is not None
    assert descriptor.policy_id == "devflow-run-gates"
    assert isinstance(descriptor.metadata, dict)


def _unit_test_devflow_location_uses_flow_owned_module() -> None:
    """Devflow invariant should resolve to the flow-owned module path."""
    module = importlib.import_module(MODULE)
    location = module.resolve_core_invariant_location(
        REPO_ROOT,
        "devflow-run-gates",
    )
    assert location is not None
    assert location.module == "devcovenant.core.flow.workflow_validation"
    assert location.path == (
        REPO_ROOT / "devcovenant" / "core" / "flow" / "workflow_validation.py"
    )


def _unit_test_integrity_location_uses_validation_module() -> None:
    """Integrity invariant should resolve to the renamed validation module."""
    module = importlib.import_module(MODULE)
    location = module.resolve_core_invariant_location(
        REPO_ROOT,
        "devcov-integrity-guard",
    )
    assert location is not None
    assert location.module == "devcovenant.core.services.integrity_validation"
    assert location.path == (
        REPO_ROOT
        / "devcovenant"
        / "core"
        / "services"
        / "integrity_validation.py"
    )


def _unit_test_structure_location_uses_validation_module() -> None:
    """Structure invariant should resolve to the renamed validation module."""
    module = importlib.import_module(MODULE)
    location = module.resolve_core_invariant_location(
        REPO_ROOT,
        "devcov-structure-guard",
    )
    assert location is not None
    assert location.module == "devcovenant.core.services.structure_validation"
    assert location.path == (
        REPO_ROOT
        / "devcovenant"
        / "core"
        / "services"
        / "structure_validation.py"
    )


def _unit_test_runtime_overrides_use_dedicated_config_sections() -> None:
    """Invariant config overrides should come from dedicated config keys."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            yaml.safe_dump(
                {
                    "paths": {
                        "policy_definitions": "AGENTS.md",
                        "registry_file": "devcovenant/registry/registry.yaml",
                        "gate_status_file": (
                            "devcovenant/registry/runtime/evidence/status.json"
                        ),
                        "workflow_session_file": (
                            "devcovenant/registry/runtime/evidence/"
                            "workflow.json"
                        ),
                    },
                    "workflow": {
                        "pre_commit_command": "pre-commit run --all-files",
                        "skipped_globs": ["devcovenant/registry/runtime/**"],
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        overrides = module.runtime_core_invariant_config_overrides(
            repo_root,
            "devflow-run-gates",
        )
        assert overrides["gate_status_file"].endswith("status.json")
        assert overrides["workflow_session_file"].endswith("workflow.json")
        assert overrides["pre_commit_command"] == "pre-commit run --all-files"
        assert overrides["skipped_globs"] == [
            "devcovenant/registry/runtime/**"
        ]


def _unit_test_resolved_core_invariants_keep_only_invariant_metadata() -> None:
    """Resolved invariants should not carry policy-style metadata fields."""
    module = importlib.import_module(MODULE)
    resolved = module.resolve_core_invariants(REPO_ROOT)
    by_id = {item.definition.invariant_id: item for item in resolved}
    devflow = by_id["devflow-run-gates"]
    for forbidden_key in (
        "severity",
        "auto_fix",
        "enforcement",
        "enabled",
        "custom",
        "id",
    ):
        assert forbidden_key not in devflow.definition.raw_metadata
        assert forbidden_key not in devflow.metadata_resolution
        assert (
            forbidden_key
            not in devflow.runtime_option_views["runtime_metadata_options"]
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_core_invariant_ids_are_stable(self):
        """Run core invariant id contract assertions."""
        _unit_test_core_invariant_ids_are_stable()

    def test_load_core_invariant_descriptor_reads_real_descriptor(self):
        """Run real-descriptor loading assertions."""
        _unit_test_load_core_invariant_descriptor_reads_real_descriptor()

    def test_devflow_location_uses_flow_owned_module(self):
        """Run flow-owned invariant location assertions."""
        _unit_test_devflow_location_uses_flow_owned_module()

    def test_integrity_location_uses_validation_module(self):
        """Run integrity invariant location assertions."""
        _unit_test_integrity_location_uses_validation_module()

    def test_structure_location_uses_validation_module(self):
        """Run structure invariant location assertions."""
        _unit_test_structure_location_uses_validation_module()

    def test_runtime_overrides_use_dedicated_config_sections(self):
        """Run dedicated invariant-config override assertions."""
        _unit_test_runtime_overrides_use_dedicated_config_sections()

    def test_resolved_core_invariants_keep_only_invariant_metadata(self):
        """Run invariant metadata-shape assertions."""
        _unit_test_resolved_core_invariants_keep_only_invariant_metadata()
