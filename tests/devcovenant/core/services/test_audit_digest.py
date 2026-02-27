"""Sanity checks for devcovenant.core.services.audit_digest."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.services.audit_digest"


def _unit_test_module_importable() -> None:
    """Audit-digest helper module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """Audit-digest module should expose stable public helper symbols."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "build_audit_digest_payload",
        "render_audit_digest_text",
        "refresh_audit_digest_artifacts",
    ]:
        assert hasattr(module, symbol), symbol
        assert callable(getattr(module, symbol)), symbol


def _unit_test_symbol_assertions_cover_public_api() -> None:
    """Audit-digest tests should assert explicit public symbols."""
    module = importlib.import_module(MODULE)
    assert module.build_audit_digest_payload
    assert module.render_audit_digest_text
    assert module.refresh_audit_digest_artifacts


def _write_minimal_agents(path: Path) -> None:
    """Write a minimal AGENTS payload with workflow and policy blocks."""
    path.write_text(
        "\n".join(
            [
                "# Dev Guide",
                "",
                "<!-- DEVCOV-WORKFLOW:BEGIN -->",
                "## Workflow Contract",
                "## Execution Order (Mandatory)",
                "1. Read AGENTS.md.",
                "2. Run devcovenant gate --start.",
                "3. Run devcovenant gate --mid.",
                "4. Run devcovenant test.",
                "5. Run devcovenant gate --end.",
                "<!-- DEVCOV-WORKFLOW:END -->",
                "",
                "<!-- DEVCOV-POLICIES:BEGIN -->",
                "## Policy: Demo",
                "```policy-def",
                "id: demo-policy",
                "severity: warning",
                "```",
                "<!-- DEVCOV-POLICIES:END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_minimal_policy_registry(path: Path) -> None:
    """Write a minimal local policy registry payload."""
    payload = {
        "policies": {
            "demo-policy": {
                "enabled": True,
                "severity": "warning",
                "auto_fix": False,
                "custom": False,
            },
            "critical-policy": {
                "enabled": True,
                "severity": "critical",
                "auto_fix": False,
                "custom": False,
            },
            "disabled-policy": {
                "enabled": False,
                "severity": "error",
                "auto_fix": True,
                "custom": True,
            },
        }
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _unit_test_build_payload_marks_digest_non_canonical() -> None:
    """Payload should explicitly mark AGENTS as canonical source."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        agents_path = repo_root / "AGENTS.md"
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        _write_minimal_agents(agents_path)
        _write_minimal_policy_registry(registry_path)
        payload = module.build_audit_digest_payload(
            repo_root,
            agents_text=agents_path.read_text(encoding="utf-8"),
            policy_registry_payload=yaml.safe_load(
                registry_path.read_text(encoding="utf-8")
            ),
        )

        assert payload["informational_only"] is True
        assert payload["canonical_source"]["path"] == "AGENTS.md"
        assert payload["workflow"]["step_count"] == 5
        assert payload["policies"]["enabled_policies"] == 2
        assert payload["policies"]["enabled_by_severity"]["critical"] == 1
        assert payload["policies"]["enabled_critical_ids"] == [
            "critical-policy"
        ]


def _unit_test_refresh_audit_digest_writes_json_and_text() -> None:
    """Refresh helper should write deterministic digest artifacts."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        agents_path = repo_root / "AGENTS.md"
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        _write_minimal_agents(agents_path)
        _write_minimal_policy_registry(registry_path)

        changed = module.refresh_audit_digest_artifacts(repo_root)
        assert "devcovenant/registry/local/audit_digest.json" in changed
        assert "devcovenant/registry/local/audit_digest.txt" in changed

        json_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "audit_digest.json"
        )
        txt_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "audit_digest.txt"
        )
        assert json_path.exists()
        assert txt_path.exists()
        text = txt_path.read_text(encoding="utf-8")
        assert "Informational, Non-Canonical" in text
        assert "Read AGENTS.md as canonical law." in text

        second_pass = module.refresh_audit_digest_artifacts(repo_root)
        assert second_pass == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for audit-digest helper checks."""

    def test_module_importable(self):
        """Run audit-digest module importability assertions."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run audit-digest symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_public_api(self):
        """Run explicit audit-digest symbol assertions."""
        _unit_test_symbol_assertions_cover_public_api()

    def test_build_payload_marks_digest_non_canonical(self):
        """Run payload canonical-source and severity summary assertions."""
        _unit_test_build_payload_marks_digest_non_canonical()

    def test_refresh_audit_digest_writes_json_and_text(self):
        """Run digest artifact write/idempotence assertions."""
        _unit_test_refresh_audit_digest_writes_json_and_text()
