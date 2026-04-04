"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

MODULE = "devcovenant.core.refresh_runtime"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_refresh_symbol_contract_is_stable() -> None:
    """Refresh flow module should expose key orchestration symbols."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "refresh_policy_registry")
    assert hasattr(module, "refresh_repo")


def _unit_test_refresh_symbol_assertions_cover_public_api() -> None:
    """Refresh flow tests should assert explicit public helper symbols."""
    module = importlib.import_module(MODULE)
    assert module.refresh_policy_registry
    assert module.refresh_repo
    assert module.refresh_agents_policy_block


def _unit_test_same_id_custom_override_marks_policy_custom() -> None:
    """Active same-id custom overrides should resolve as custom policies."""

    module = importlib.import_module(MODULE)

    class _FakeBundle:
        """Minimal metadata bundle stand-in for refresh tests."""

        order = ["id", "severity", "enabled", "custom", "auto_fix"]
        warnings = []
        resolution_trace = {}

        def __init__(self, *, custom_policy: bool):
            """Store resolved metadata for one synthetic policy."""

            self.raw_map = {
                "id": "demo-policy",
                "severity": "warning",
                "enabled": "true",
                "custom": "true" if custom_policy else "false",
                "auto_fix": "false",
            }

        def decode_options(self):
            """Return one empty decoded-options payload."""

            return {}

        def warning_messages(self):
            """Return no warning messages for the fake bundle."""

            return []

    class _FakeRegistry:
        """Capture policy writes without touching a real registry file."""

        def __init__(self, _registry_path, _repo_root):
            """Initialize one empty capturing registry."""

            self.input_hash = None
            self.updated_policies = []

        def get_registry_metadata_value(self, _key):
            """Return no cached input fingerprint."""

            return None

        def update_policy_entry(
            self,
            policy,
            _location,
            _descriptor,
            **_kwargs,
        ):
            """Record the refreshed policy definition."""

            self.updated_policies.append(policy)

        def prune_policies(self, _seen_policy_ids, *, save=False):
            """Return no stale policy ids."""

            del save
            return []

        def update_registry_metadata_value(self, _key, value, *, save=False):
            """Record the latest input fingerprint."""

            del save
            self.input_hash = value

        def save(self):
            """No-op save for the fake registry."""

            return None

        def update_project_governance(self, _payload):
            """No-op project-governance write for the fake registry."""

            return None

        def update_managed_docs(self, _payload):
            """No-op managed-docs write for the fake registry."""

            return None

        def update_workflow_contract(self, _payload):
            """No-op workflow-contract write for the fake registry."""

            return None

    captured_custom_flags = []
    captured_registries = []
    managed_docs_service = module.managed_docs_service
    profile_registry_service = module.profile_registry_service
    refresh_policy_registry = module.refresh_policy_registry
    workflow_contract = {"workflow_contract": {}}

    def _fake_resolve_policy_metadata_bundle(
        _policy_id,
        _current_order,
        _current_values,
        _descriptor,
        _context,
        *,
        custom_policy=False,
    ):
        """Capture whether refresh marked the active policy as custom."""

        captured_custom_flags.append(custom_policy)
        return _FakeBundle(custom_policy=custom_policy)

    def _fake_registry(_registry_path, _repo_root):
        """Return one capturing registry instance."""

        registry = _FakeRegistry(_registry_path, _repo_root)
        captured_registries.append(registry)
        return registry

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
        (repo_root / "devcovenant").mkdir(parents=True, exist_ok=True)
        fake_project_governance_state = type(
            "ProjectGovernanceState",
            (),
            {
                "is_unversioned": False,
                "registry_payload": staticmethod(lambda _version: {}),
            },
        )()
        fake_location = type(
            "ResolvedPolicyLocation",
            (),
            {
                "kind": "custom",
                "path": repo_root
                / "devcovenant"
                / "custom"
                / "policies"
                / "demo_policy"
                / "demo_policy.py",
            },
        )()
        fake_descriptor = type(
            "PolicyDescriptor",
            (),
            {
                "text": "Demo policy text.",
                "metadata": {
                    "severity": "warning",
                    "enabled": "true",
                    "custom": "false",
                    "auto_fix": "false",
                },
            },
        )()

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    module,
                    "_discover_policy_sources",
                    return_value={"demo-policy"},
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_policy_registry_input_fingerprint",
                    return_value="demo-hash",
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_resolve_policy_sources",
                    return_value=(fake_location, True, True),
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "load_policy_descriptor",
                    return_value=fake_descriptor,
                )
            )
            stack.enter_context(
                patch.object(
                    module.metadata_runtime,
                    "build_metadata_context_from_payload",
                    return_value=object(),
                )
            )
            stack.enter_context(
                patch.object(
                    module.metadata_runtime,
                    "resolve_policy_metadata_bundle",
                    side_effect=_fake_resolve_policy_metadata_bundle,
                )
            )
            stack.enter_context(
                patch.object(
                    module.runtime_actions_module,
                    "build_runtime_policy_option_views",
                    return_value={},
                )
            )
            stack.enter_context(
                patch.object(
                    module.project_governance_service,
                    "resolve_runtime_state",
                    return_value=fake_project_governance_state,
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_read_project_version",
                    return_value="1.0.0",
                )
            )
            stack.enter_context(
                patch.object(
                    managed_docs_service,
                    "managed_docs_registry_payload",
                    return_value={},
                )
            )
            stack.enter_context(
                patch.object(
                    profile_registry_service,
                    "build_profile_registry",
                    return_value=workflow_contract,
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "PolicyRegistry",
                    side_effect=_fake_registry,
                )
            )
            result = refresh_policy_registry(
                repo_root=repo_root,
                config_payload={},
            )

    assert result == 0
    assert captured_custom_flags == [True]
    assert len(captured_registries) == 1
    assert captured_registries[0].updated_policies[0].custom is True


class RefreshRuntimeTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_refresh_symbol_contract_is_stable(self):
        """Run refresh module symbol contract assertions."""
        _unit_test_refresh_symbol_contract_is_stable()

    def test_refresh_symbol_assertions_cover_public_api(self):
        """Run refresh module explicit symbol assertions."""
        _unit_test_refresh_symbol_assertions_cover_public_api()

    def test_same_id_custom_override_marks_policy_custom(self):
        """Run same-id custom-override metadata assertions."""
        _unit_test_same_id_custom_override_marks_policy_custom()
