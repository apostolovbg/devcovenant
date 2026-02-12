"""Tests for devcov-integrity-guard policy."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.devcov_integrity_guard import (
    devcov_integrity_guard,
)
from devcovenant.core.registry import PolicyRegistry


def _write(path: Path, content: str) -> Path:
    """Write *content* to *path* and return the created path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_agents(
    path: Path, description: str = "Policy description."
) -> None:
    """Write a minimal AGENTS fixture containing one policy."""
    path.write_text(
        (
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "## Policy: Demo\n\n"
            "```policy-def\n"
            "id: demo-policy\n"
            "status: active\n"
            "severity: error\n"
            "auto_fix: false\n"
            "enforcement: active\n"
            "enabled: true\n"
            "custom: false\n"
            "```\n\n"
            f"{description}\n\n"
            "<!-- DEVCOV-POLICIES:END -->\n"
        ),
        encoding="utf-8",
    )


def _write_descriptor(repo_root: Path, text_value: str) -> None:
    """Write a descriptor for demo-policy."""
    descriptor_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "policies"
        / "demo_policy"
        / "demo_policy.yaml"
    )
    payload = {
        "id": "demo-policy",
        "text": text_value,
        "metadata": {"id": "demo-policy"},
    }
    _write(
        descriptor_path,
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
    )


def _write_policy_script(
    repo_root: Path, body: str = "# demo policy\n"
) -> Path:
    """Write demo policy script and return its path."""
    script_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "policies"
        / "demo_policy"
        / "demo_policy.py"
    )
    return _write(script_path, body)


def _build_checker(extra_options: dict[str, object] | None = None):
    """Create a configured integrity guard checker."""
    checker = devcov_integrity_guard.DevcovIntegrityGuardCheck()
    base_options: dict[str, object] = {"policy_definitions": "AGENTS.md"}
    if extra_options:
        base_options.update(extra_options)
    checker.set_options(base_options, {})
    return checker


def _unit_test_policy_text_presence_violation(tmp_path: Path) -> None:
    """Missing policy prose should raise an error."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path, description="---")
    checker = _build_checker()
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    violations = checker.check(context)
    assert violations
    assert "must include descriptive text" in violations[0].message


def _unit_test_descriptor_drift_emits_warning(tmp_path: Path) -> None:
    """Descriptor/AGENTS text mismatches should emit a warning."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path, description="Runtime text")
    _write_policy_script(tmp_path)
    _write_descriptor(tmp_path, text_value="Descriptor text")

    checker = _build_checker()
    violations = checker.check(
        CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    )
    assert any(
        item.severity == "warning"
        and "Descriptor policy text differs" in item.message
        for item in violations
    )


def _unit_test_registry_mismatch_raises_error(tmp_path: Path) -> None:
    """Registry hash mismatches should raise errors."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path, description="Policy description.")
    script_path = _write_policy_script(tmp_path, body="# stale script\n")
    _write_descriptor(tmp_path, text_value="Policy description.")

    registry_path = (
        tmp_path
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    registry = PolicyRegistry(registry_path, tmp_path)
    registry._data.setdefault("policies", {})["demo-policy"] = {"hash": "bad"}
    registry.save()

    checker = _build_checker(
        {"registry_file": "devcovenant/registry/local/policy_registry.yaml"}
    )
    violations = checker.check(
        CheckContext(
            repo_root=tmp_path, changed_files=[agents_path, script_path]
        )
    )
    assert any("hash mismatch" in item.message for item in violations)


def _unit_test_status_update_required_when_watched_files_change(
    tmp_path: Path,
) -> None:
    """Watched file changes should require a refreshed test status file."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path, description="Policy description.")
    _write_policy_script(tmp_path)
    _write_descriptor(tmp_path, text_value="Policy description.")

    registry_path = (
        tmp_path
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    parser_registry = PolicyRegistry(registry_path, tmp_path)
    script_content = (
        tmp_path
        / "devcovenant"
        / "core"
        / "policies"
        / "demo_policy"
        / "demo_policy.py"
    ).read_text(encoding="utf-8")
    full_hash = parser_registry.calculate_full_hash(
        "Policy description.", script_content
    )
    parser_registry._data.setdefault("policies", {})["demo-policy"] = {
        "hash": full_hash
    }
    parser_registry.save()

    changed_code = _write(
        tmp_path / "src" / "module.py", "def run():\n    return 1\n"
    )
    checker = _build_checker(
        {
            "watch_dirs": ["src"],
            "watch_files": ["pyproject.toml"],
        }
    )
    violations = checker.check(
        CheckContext(repo_root=tmp_path, changed_files=[changed_code])
    )
    assert any(
        "fresh test status update" in item.message for item in violations
    )


def _unit_test_status_payload_validation_passes(tmp_path: Path) -> None:
    """Valid status payload with watched changes should pass."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(agents_path, description="Policy description.")
    _write_policy_script(tmp_path)
    _write_descriptor(tmp_path, text_value="Policy description.")

    registry_path = (
        tmp_path
        / "devcovenant"
        / "registry"
        / "local"
        / "policy_registry.yaml"
    )
    registry = PolicyRegistry(registry_path, tmp_path)
    script_text = (
        tmp_path
        / "devcovenant"
        / "core"
        / "policies"
        / "demo_policy"
        / "demo_policy.py"
    ).read_text(encoding="utf-8")
    registry._data.setdefault("policies", {})["demo-policy"] = {
        "hash": registry.calculate_full_hash(
            "Policy description.", script_text
        )
    }
    registry.save()

    code_path = _write(tmp_path / "src" / "module.py", "x = 1\n")
    status_path = _write(
        tmp_path / "devcovenant" / "registry" / "local" / "test_status.json",
        json.dumps(
            {
                "last_run": "2026-02-07T00:00:00+00:00",
                "command": "pytest && python3 -m unittest discover -v",
                "sha": "a" * 40,
            }
        ),
    )

    checker = _build_checker({"watch_dirs": ["src"]})
    violations = checker.check(
        CheckContext(
            repo_root=tmp_path, changed_files=[code_path, status_path]
        )
    )
    assert violations == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_policy_text_presence_violation(self):
        """Run test_policy_text_presence_violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_text_presence_violation(tmp_path=tmp_path)

    def test_descriptor_drift_emits_warning(self):
        """Run test_descriptor_drift_emits_warning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_descriptor_drift_emits_warning(tmp_path=tmp_path)

    def test_registry_mismatch_raises_error(self):
        """Run test_registry_mismatch_raises_error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_registry_mismatch_raises_error(tmp_path=tmp_path)

    def test_status_update_required_when_watched_files_change(self):
        """Run test_status_update_required_when_watched_files_change."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_status_update_required_when_watched_files_change(
                tmp_path=tmp_path
            )

    def test_status_payload_validation_passes(self):
        """Run test_status_payload_validation_passes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_status_payload_validation_passes(tmp_path=tmp_path)
