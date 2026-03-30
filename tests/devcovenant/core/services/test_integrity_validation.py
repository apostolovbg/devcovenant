"""Tests for repository integrity validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.services import integrity_validation
from devcovenant.core.services.policy_registry import PolicyRegistry


def _write(path: Path, content: str) -> Path:
    """Write content to path and return the created path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_agents(
    path: Path,
    description: str = "Policy description.",
) -> None:
    """Write a minimal AGENTS fixture containing one policy."""
    path.write_text(
        (
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "## Policy: Demo\n\n"
            "```policy-def\n"
            "id: demo-policy\n"
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
        / "builtin"
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
    repo_root: Path,
    body: str = "# demo policy\n",
) -> Path:
    """Write demo policy script and return its path."""
    script_path = (
        repo_root
        / "devcovenant"
        / "builtin"
        / "policies"
        / "demo_policy"
        / "demo_policy.py"
    )
    return _write(script_path, body)


def _make_context(
    repo_root: Path,
    *,
    changed_files: list[Path] | None = None,
    config: dict | None = None,
) -> CheckContext:
    """Create one integrity-validation context."""
    return CheckContext(
        repo_root=repo_root,
        changed_files=list(changed_files or []),
        config=config or {},
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_policy_text_presence_violation(self):
        """Missing policy prose should raise an error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "AGENTS.md"
            _write_agents(agents_path, description="---")
            violations = integrity_validation.check_integrity(
                _make_context(repo_root, changed_files=[agents_path])
            )
            self.assertTrue(violations)
            self.assertIn(
                "must include descriptive text", violations[0].message
            )

    def test_descriptor_drift_emits_warning(self):
        """Descriptor and AGENTS text mismatches should emit a warning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "AGENTS.md"
            _write_agents(agents_path, description="Runtime text")
            _write_policy_script(repo_root)
            _write_descriptor(repo_root, text_value="Descriptor text")

            violations = integrity_validation.check_integrity(
                _make_context(repo_root, changed_files=[agents_path])
            )
            self.assertTrue(
                any(
                    item.severity == "warning"
                    and "Descriptor policy text differs" in item.message
                    for item in violations
                )
            )

    def test_registry_mismatch_raises_error(self):
        """Registry hash mismatches should raise errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "AGENTS.md"
            _write_agents(agents_path, description="Policy description.")
            script_path = _write_policy_script(
                repo_root, body="# stale script\n"
            )
            _write_descriptor(repo_root, text_value="Policy description.")

            registry_path = (
                repo_root / "devcovenant" / "registry" / "registry.yaml"
            )
            registry = PolicyRegistry(registry_path, repo_root)
            registry._data.setdefault("policies", {})["demo-policy"] = {
                "hash": "bad"
            }
            registry.save()

            violations = integrity_validation.check_integrity(
                _make_context(
                    repo_root, changed_files=[agents_path, script_path]
                )
            )
            self.assertTrue(
                any("hash mismatch" in item.message for item in violations)
            )

    def test_status_update_required_when_watched_files_change(self):
        """Watched file changes should require a refreshed gate status file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "AGENTS.md"
            _write_agents(agents_path, description="Policy description.")
            _write_policy_script(repo_root)
            _write_descriptor(repo_root, text_value="Policy description.")

            registry_path = (
                repo_root / "devcovenant" / "registry" / "registry.yaml"
            )
            parser_registry = PolicyRegistry(registry_path, repo_root)
            script_content = (
                repo_root
                / "devcovenant"
                / "builtin"
                / "policies"
                / "demo_policy"
                / "demo_policy.py"
            ).read_text(encoding="utf-8")
            full_hash = parser_registry.calculate_full_hash(
                "Policy description.",
                script_content,
            )
            parser_registry._data.setdefault("policies", {})["demo-policy"] = {
                "hash": full_hash
            }
            parser_registry.save()

            changed_code = _write(
                repo_root / "src" / "module.py",
                "def run():\n    return 1\n",
            )
            violations = integrity_validation.check_integrity(
                _make_context(
                    repo_root,
                    changed_files=[changed_code],
                    config={"integrity": {"watch_dirs": ["src"]}},
                )
            )
            self.assertTrue(
                any(
                    "fresh gate status update" in item.message
                    for item in violations
                )
            )

    def test_status_payload_validation_passes(self):
        """Valid status payload with watched changes should pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "AGENTS.md"
            _write_agents(agents_path, description="Policy description.")
            _write_policy_script(repo_root)
            _write_descriptor(repo_root, text_value="Policy description.")

            registry_path = (
                repo_root / "devcovenant" / "registry" / "registry.yaml"
            )
            registry = PolicyRegistry(registry_path, repo_root)
            script_text = (
                repo_root
                / "devcovenant"
                / "builtin"
                / "policies"
                / "demo_policy"
                / "demo_policy.py"
            ).read_text(encoding="utf-8")
            registry._data.setdefault("policies", {})["demo-policy"] = {
                "hash": registry.calculate_full_hash(
                    "Policy description.",
                    script_text,
                )
            }
            registry.save()

            code_path = _write(repo_root / "src" / "module.py", "x = 1\n")
            status_path = _write(
                repo_root
                / "devcovenant"
                / "registry"
                / "runtime"
                / "gate_status.json",
                json.dumps(
                    {
                        "last_run_utc": "2026-02-07T00:00:00+00:00",
                        "commands": [
                            "pytest",
                            "python3 -m unittest discover -v",
                        ],
                        "sha": "a" * 40,
                    }
                ),
            )

            violations = integrity_validation.check_integrity(
                _make_context(
                    repo_root,
                    changed_files=[code_path, status_path],
                    config={"integrity": {"watch_dirs": ["src"]}},
                )
            )
            self.assertEqual(violations, [])

    def test_path_options_are_read_from_paths_config(self):
        """Path overrides should come from the normal paths config section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            agents_path = repo_root / "policy-source.md"
            _write_agents(agents_path, description="Policy description.")
            _write_policy_script(repo_root)
            _write_descriptor(repo_root, text_value="Policy description.")
            registry_path = repo_root / "custom-registry.yaml"
            registry = PolicyRegistry(registry_path, repo_root)
            script_text = (
                repo_root
                / "devcovenant"
                / "builtin"
                / "policies"
                / "demo_policy"
                / "demo_policy.py"
            ).read_text(encoding="utf-8")
            registry._data.setdefault("policies", {})["demo-policy"] = {
                "hash": registry.calculate_full_hash(
                    "Policy description.",
                    script_text,
                )
            }
            registry.save()

            violations = integrity_validation.check_integrity(
                _make_context(
                    repo_root,
                    changed_files=[agents_path],
                    config={
                        "paths": {
                            "policy_definitions": "policy-source.md",
                            "registry_file": "custom-registry.yaml",
                            "gate_status_file": (
                                "devcovenant/registry/runtime/gate_status.json"
                            ),
                        }
                    },
                )
            )
            self.assertEqual(violations, [])
