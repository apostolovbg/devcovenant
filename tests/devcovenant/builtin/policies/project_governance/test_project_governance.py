"""Unit tests for the project-governance policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.builtin.policies.project_governance import (
    project_governance as project_governance_module,
)
from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.flow.refresh import refresh_repo

ProjectGovernanceCheck = project_governance_module.ProjectGovernanceCheck
ProjectGovernanceState = project_governance_module.ProjectGovernanceState
resolve_release_headings = project_governance_module.resolve_release_headings
resolve_runtime_state = project_governance_module.resolve_runtime_state


def _write_unversioned_config(repo_root: Path) -> None:
    """Configure one repo for active unversioned project-governance."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    payload.setdefault("policy_state", {})
    payload["policy_state"]["project-governance"] = True
    payload.setdefault("user_metadata_overlays", {})
    payload["user_metadata_overlays"]["project-governance"] = {
        "stage": "beta",
        "development_stance": "active-development",
        "versioning_mode": "unversioned",
        "unversioned_label": "Unversioned",
        "unreleased_heading": "## Unreleased",
    }
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _policy_messages(repo_root: Path) -> list[str]:
    """Run the policy and return violation messages."""
    check = ProjectGovernanceCheck()
    state = resolve_runtime_state(repo_root)
    options = {
        "enabled": state.enabled,
        "stage": state.stage,
        "development_stance": state.development_stance,
        "versioning_mode": state.versioning_mode,
        "codename": state.codename,
        "build_identity": state.build_identity,
        "unversioned_label": state.unversioned_label,
        "unreleased_heading": state.unreleased_heading,
    }
    check.set_options(options, {})
    context = CheckContext(repo_root=repo_root, config={})
    return [violation.message for violation in check.check(context)]


def _unit_test_runtime_state_defaults_to_unversioned_governance() -> None:
    """Fresh installs should default to explicit unversioned governance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        state = resolve_runtime_state(repo_root)
        assert state.enabled is True
        assert state.is_unversioned is True
        assert state.displayed_project_version("1.2.3") == "Unversioned"
        assert "**Project Stage:** prototype" in state.agents_header_lines()


def _unit_test_unversioned_policy_requires_unreleased_heading() -> None:
    """Unversioned repos should require the configured unreleased heading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _write_unversioned_config(repo_root)
        changelog = repo_root / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## Log changes here\n\n## Version 1.0.0\n",
            encoding="utf-8",
        )
        result = refresh_repo(repo_root)
        assert result == 0
        messages = _policy_messages(repo_root)
        assert any("top changelog heading" in message for message in messages)


def _unit_test_unversioned_runtime_state_renders_unversioned_label() -> None:
    """Unversioned runtime state should expose its explicit doc label."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        _write_unversioned_config(repo_root)
        assert refresh_repo(repo_root) == 0
        state = resolve_runtime_state(repo_root)
        assert state.enabled is True
        assert state.is_unversioned is True
        assert state.displayed_project_version("9.9.9") == "Unversioned"
        assert "**Project Stage:** beta" in state.governance_header_lines()


def _unit_test_versioned_runtime_state_requires_declared_version() -> None:
    """Versioned repos should reject fake fallback versions."""
    state = ProjectGovernanceState(enabled=True, versioning_mode="versioned")
    try:
        state.displayed_project_version("")
    except ValueError as exc:
        assert "missing a declared project version" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError(
            "Expected versioned project governance to reject empty version."
        )


def _unit_test_release_heading_resolution_is_scheme_aware() -> None:
    """Release headings should follow project-governance mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        assert resolve_release_headings(repo_root) == ["## Unreleased"]
        _write_unversioned_config(repo_root)
        assert refresh_repo(repo_root) == 0
        assert resolve_release_headings(repo_root) == ["## Unreleased"]


def _unit_test_symbol_contracts_are_stable() -> None:
    """Core project-governance symbols should remain directly usable."""
    checker = project_governance_module.ProjectGovernanceCheck()
    assert isinstance(
        checker,
        project_governance_module.ProjectGovernanceCheck,
    )
    checker.set_options({"enabled": False}, {})
    state = checker.runtime_state(Path("."))
    assert isinstance(state, ProjectGovernanceState)
    assert state.enabled is False
    assert state.governance_header_lines() == []
    assert checker.policy_id == "project-governance"
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        result = checker.check(CheckContext(repo_root=repo_root, config={}))
        assert result == []


def _unit_test_spec_descriptor_opts_into_governance_headers() -> None:
    """SPEC descriptor should opt into project-governance headers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        spec_descriptor = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "SPEC.yaml"
        )
        content = spec_descriptor.read_text(encoding="utf-8")
        assert "project_governance_headers: true" in content


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_runtime_state_defaults_to_unversioned_governance(self):
        """Run fresh-install unversioned-governance assertions."""
        _unit_test_runtime_state_defaults_to_unversioned_governance()

    def test_unversioned_policy_requires_unreleased_heading(self):
        """Run unversioned changelog-heading assertions."""
        _unit_test_unversioned_policy_requires_unreleased_heading()

    def test_unversioned_runtime_state_renders_unversioned_label(self):
        """Run unversioned runtime label assertions."""
        _unit_test_unversioned_runtime_state_renders_unversioned_label()

    def test_versioned_runtime_state_requires_declared_version(self):
        """Run versioned runtime no-fake-version assertions."""
        _unit_test_versioned_runtime_state_requires_declared_version()

    def test_release_heading_resolution_is_scheme_aware(self):
        """Run release-heading resolution assertions."""
        _unit_test_release_heading_resolution_is_scheme_aware()

    def test_symbol_contracts_are_stable(self):
        """Run symbol-level project-governance assertions."""
        _unit_test_symbol_contracts_are_stable()

    def test_spec_descriptor_opts_into_governance_headers(self):
        """Run SPEC governance-header opt-in assertions."""
        _unit_test_spec_descriptor_opts_into_governance_headers()
