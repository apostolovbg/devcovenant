"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.runtime.policy_runtime_actions"


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Runtime-action helper seam functions should stay callable."""
    module = importlib.import_module(MODULE)
    assert hasattr(module, "build_runtime_policy_option_views")
    assert hasattr(module, "load_policy_check_instance")
    assert hasattr(module, "runtime_policy_config_overrides")
    assert hasattr(module, "runtime_policy_metadata_options")
    assert hasattr(module, "run_policy_runtime_action")
    assert callable(module.build_runtime_policy_option_views)
    assert callable(module.load_policy_check_instance)
    assert callable(module.runtime_policy_config_overrides)
    assert callable(module.runtime_policy_metadata_options)
    assert callable(module.run_policy_runtime_action)


def _unit_test_symbol_assertions_cover_runtime_action_seam() -> None:
    """Tests should assert the runtime-action helper seam directly."""
    module = importlib.import_module(MODULE)
    assert module.build_runtime_policy_option_views
    assert module.load_policy_check_instance
    assert module.runtime_policy_config_overrides
    assert module.runtime_policy_metadata_options
    assert module.run_policy_runtime_action


def _unit_test_load_policy_check_instance_returns_none_when_missing() -> None:
    """Missing policy scripts should return None from the loader helper."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        loaded = module.load_policy_check_instance(repo_root, "missing-policy")
        assert loaded is None


def _unit_test_runtime_policy_config_overrides_reads_config() -> None:
    """Config override helper should merge normalized policy config values."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            yaml.safe_dump(
                {
                    "autogen_metadata_overrides": {
                        "demo": {"alpha": ["one", "two"]}
                    },
                    "user_metadata_overrides": {
                        "demo": {
                            "alpha": ["three"],
                            "status_file": ["devcovenant/status.json"],
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        overrides = module.runtime_policy_config_overrides(repo_root, "demo")
        assert overrides["alpha"] == ["three"]
        assert overrides["status_file"] == "devcovenant/status.json"


def _unit_test_build_runtime_policy_option_views_prefers_overrides() -> None:
    """Runtime option views should expose all three typed option views."""
    module = importlib.import_module(MODULE)
    views = module.build_runtime_policy_option_views(
        {"alpha": ["one"], "beta": "meta", "gamma": "meta"},
        {"alpha": ["two"], "beta": "", "delta": 4},
    )

    assert views["runtime_metadata_options"]["alpha"] == ["one"]
    assert views["runtime_config_overrides"]["alpha"] == ["two"]
    assert views["runtime_effective_options"]["alpha"] == ["two"]
    assert views["runtime_effective_options"]["beta"] == "meta"
    assert views["runtime_effective_options"]["gamma"] == "meta"
    assert views["runtime_effective_options"]["delta"] == 4


def _unit_test_runtime_policy_metadata_options_decodes_registry_strings() -> (
    None
):
    """Registry metadata helper should decode stored string values."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "policies": {
                        "demo-policy": {
                            "metadata": {
                                "enabled": "true",
                                "header_scan_lines": "4",
                                "required_globs": "README.md, AGENTS.md",
                            }
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        options = module.runtime_policy_metadata_options(
            repo_root,
            "demo-policy",
        )
        assert options["enabled"] is True
        assert options["header_scan_lines"] == 4
        assert options["required_globs"] == ["README.md", "AGENTS.md"]


def _unit_test_runtime_policy_metadata_prefers_typed_registry() -> None:
    """Typed registry metadata should win over raw string metadata."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        registry_path = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "policies": {
                        "demo-policy": {
                            "runtime_metadata_options": {
                                "enabled": True,
                                "header_scan_lines": 7,
                                "required_globs": ["PLAN.md"],
                            },
                            "metadata": {
                                "enabled": "true",
                                "header_scan_lines": "4",
                                "required_globs": "README.md, AGENTS.md",
                            },
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        options = module.runtime_policy_metadata_options(
            repo_root,
            "demo-policy",
        )
        assert options["enabled"] is True
        assert options["header_scan_lines"] == 7
        assert options["required_globs"] == ["PLAN.md"]


def _unit_test_runtime_action_dispatches_with_injected_loaders() -> None:
    """Runtime-action helper should dispatch with injected dependencies."""
    module = importlib.import_module(MODULE)
    calls: list[tuple[str, object]] = []

    class _FakeChecker:
        """Simple checker stub for runtime-action dispatch tests."""

        def __init__(self) -> None:
            """Store metadata/config options for assertions."""
            self.metadata_options = {}
            self.config_overrides = {}

        def set_options(self, metadata_options, config_overrides) -> None:
            """Capture injected options."""
            self.metadata_options = dict(metadata_options or {})
            self.config_overrides = dict(config_overrides or {})

        def run_runtime_action(self, action, *, repo_root, payload=None):
            """Return received payload for assertions."""
            calls.append(("action", action))
            return {
                "action": action,
                "repo_root": str(repo_root),
                "payload": payload,
                "metadata": dict(self.metadata_options),
                "config": dict(self.config_overrides),
            }

    result = module.run_policy_runtime_action(
        Path("/tmp/devcovenant"),
        policy_id="demo-policy",
        action="demo-action",
        payload={"scope": "full"},
        checker_loader=lambda repo_root, policy_id: _FakeChecker(),
        metadata_loader=lambda repo_root, policy_id: {"alpha": 1},
        config_loader=lambda repo_root, policy_id: {"beta": 2},
        action_validator=lambda repo_root, *, policy_id, action: None,
    )
    assert calls == [("action", "demo-action")]
    assert result["repo_root"] == str(Path("/tmp/devcovenant").resolve())
    assert result["payload"] == {"scope": "full"}
    assert result["metadata"] == {"alpha": 1}
    assert result["config"] == {"beta": 2}


def _unit_test_run_policy_runtime_action_fails_when_policy_missing() -> None:
    """Runtime-action helper should fail cleanly for missing policies."""
    module = importlib.import_module(MODULE)
    try:
        module.run_policy_runtime_action(
            Path("/tmp/devcovenant"),
            policy_id="missing-policy",
            action="demo-action",
            payload={},
            checker_loader=lambda repo_root, policy_id: None,
            action_validator=lambda repo_root, *, policy_id, action: None,
        )
    except ValueError as error:
        assert "Policy script not found" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for missing runtime-action policy."
        )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for extracted runtime-action helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run runtime-action helper symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_runtime_action_seam(self):
        """Run explicit symbol assertions for test fidelity."""
        _unit_test_symbol_assertions_cover_runtime_action_seam()

    def test_load_policy_check_instance_returns_none_when_missing(self):
        """Run missing-policy loader assertions."""
        _unit_test_load_policy_check_instance_returns_none_when_missing()

    def test_runtime_policy_config_overrides_reads_config(self):
        """Run config-override helper assertions."""
        _unit_test_runtime_policy_config_overrides_reads_config()

    def test_build_runtime_policy_option_views_prefers_overrides(self):
        """Run runtime-option view merge assertions."""
        _unit_test_build_runtime_policy_option_views_prefers_overrides()

    def test_runtime_policy_metadata_options_decodes_registry_strings(self):
        """Run registry metadata typed-decoding assertions."""
        _unit_test_runtime_policy_metadata_options_decodes_registry_strings()

    def test_runtime_policy_metadata_options_prefers_typed_registry_view(
        self,
    ):
        """Run typed-registry metadata option assertions."""
        _unit_test_runtime_policy_metadata_prefers_typed_registry()

    def test_run_policy_runtime_action_dispatches_with_injected_loaders(self):
        """Run runtime-action dispatch assertions with injected loaders."""
        _unit_test_runtime_action_dispatches_with_injected_loaders()

    def test_run_policy_runtime_action_fails_when_policy_missing(self):
        """Run runtime-action missing-policy assertions."""
        _unit_test_run_policy_runtime_action_fails_when_policy_missing()
