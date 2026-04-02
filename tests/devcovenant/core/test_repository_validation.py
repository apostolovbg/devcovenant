"""Tests for devcovenant.core.repository_validation."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

import devcovenant.core.repository_validation as integrity_validation
import devcovenant.core.repository_validation as manifest_module
import devcovenant.core.repository_validation as structure_validation
from devcovenant import install
from devcovenant.core.policy_contract import CheckContext
from devcovenant.core.policy_registry import PolicyRegistry

MODULE = "devcovenant.core.repository_validation"


def _manifest_module_importable() -> None:
    """Manifest inventory module should import successfully."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _manifest_public_symbol_contract_is_stable() -> None:
    """Manifest inventory should expose the expected helper surface."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "DEFAULT_CORE_DIRS",
        "DEFAULT_CORE_FILES",
        "DEFAULT_AVAILABLE_DOCS",
        "DEFAULT_ENABLED_DOCS",
        "DEFAULT_CUSTOM_DIRS",
        "DEFAULT_CUSTOM_FILES",
        "DEFAULT_GENERATED_DIRS",
        "DEFAULT_GENERATED_FILES",
        "manifest_path",
        "build_manifest",
        "load_manifest",
        "write_manifest",
        "ensure_manifest",
    ]:
        assert hasattr(module, symbol)


def _manifest_generated_manifest_includes_runtime_registry_artifacts() -> None:
    """Generated manifests should include runtime registry artifacts."""
    module = importlib.import_module(MODULE)
    manifest = module.build_manifest()
    generated = manifest.get("generated", {})
    files = generated.get("files", [])
    assert (
        f"{module.RUNTIME_REGISTRY_DIR}/{module.GATE_STATUS_FILENAME}" in files
    )
    assert (
        f"{module.RUNTIME_REGISTRY_DIR}/{module.LATEST_RUNTIME_FILENAME}"
        in files
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        assert (
            module.manifest_path(repo_root)
            == repo_root / "devcovenant" / "registry" / "registry.yaml"
        )


def _manifest_ensure_manifest_persists_inventory() -> None:
    """ensure_manifest should create inventory when devcovenant exists."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "devcovenant").mkdir()
        manifest = module.ensure_manifest(repo_root)
        assert isinstance(manifest, dict)
        assert module.manifest_path(repo_root).exists()


def _manifest_manifest_tracks_available_and_enabled_docs() -> None:
    """Manifest inventory should separate available from enabled docs."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        install.install_repo(repo_root)
        manifest = module.ensure_manifest(repo_root)
        assert manifest is not None
        docs = manifest["docs"]
        assert "SECURITY.md" in docs["available"]
        assert "PRIVACY.md" in docs["available"]
        assert "SUPPORT.md" in docs["available"]
        assert "AGENTS.md" in docs["enabled"]
        assert "SECURITY.md" not in docs["enabled"]
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["doc_assets"] = {
            "autogen": ["AGENTS.md", "SECURITY.md"],
            "user": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
        )
        refreshed = module.ensure_manifest(repo_root)
        assert refreshed is not None
        assert refreshed["docs"]["enabled"] == ["AGENTS.md", "SECURITY.md"]


class RepositoryValidationManifestTests(unittest.TestCase):
    """unittest wrappers for manifest-inventory service tests."""

    def test_module_importable(self):
        """Run manifest-inventory importability assertions."""
        _manifest_module_importable()

    def test_public_symbol_contract_is_stable(self):
        """Run manifest-inventory public symbol assertions."""
        _manifest_public_symbol_contract_is_stable()

    def test_generated_manifest_includes_runtime_registry_artifacts(self):
        """Run generated-manifest artifact assertions."""
        _manifest_generated_manifest_includes_runtime_registry_artifacts()

    def test_ensure_manifest_persists_inventory(self):
        """Run manifest persistence assertions."""
        _manifest_ensure_manifest_persists_inventory()

    def test_manifest_tracks_available_and_enabled_docs(self):
        """Run available-vs-enabled doc inventory assertions."""
        _manifest_manifest_tracks_available_and_enabled_docs()


def _write_path(path: Path, content: str) -> Path:
    """Write content to path and return the created path."""
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
    _write_path(
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
        / "builtin"
        / "policies"
        / "demo_policy"
        / "demo_policy.py"
    )
    return _write_path(script_path, body)


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


class RepositoryValidationIntegrityTests(unittest.TestCase):
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
                    (
                        item.severity == "warning"
                        and "Descriptor policy text differs" in item.message
                        for item in violations
                    )
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
                any(("hash mismatch" in item.message for item in violations))
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
                "Policy description.", script_content
            )
            parser_registry._data.setdefault("policies", {})["demo-policy"] = {
                "hash": full_hash
            }
            parser_registry.save()
            changed_code = _write_path(
                repo_root / "src" / "module.py", "def run():\n    return 1\n"
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
                    (
                        "fresh gate status update" in item.message
                        for item in violations
                    )
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
                    "Policy description.", script_text
                )
            }
            registry.save()
            code_path = _write_path(repo_root / "src" / "module.py", "x = 1\n")
            status_path = _write_path(
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
                    "Policy description.", script_text
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
                                "devcovenant/registry/runtime/"
                                "gate_status.json"
                            ),
                        }
                    },
                )
            )
            self.assertEqual(violations, [])


def _repository_validation_structure_seed_required_structure(
    repo_root: Path,
) -> None:
    """Create required core/docs paths for structure checks."""
    for rel_path in manifest_module.DEFAULT_CORE_DIRS:
        (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
    for rel_path in manifest_module.DEFAULT_CORE_FILES:
        if rel_path == manifest_module.REGISTRY_REL_PATH:
            continue
        path = repo_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("#\n", encoding="utf-8")
    for rel_path in manifest_module.DEFAULT_ENABLED_DOCS:
        path = repo_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#\n", encoding="utf-8")


def _repository_validation_structure_write_active_profiles(
    repo_root: Path, profiles: list[str]
) -> None:
    """Write a minimal config with specified active profiles."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "profiles:\n  active:\n"
    for profile in profiles:
        payload += f"  - {profile}\n"
    config_path.write_text(payload, encoding="utf-8")


def _structure_structure_check_passes_with_required_paths() -> None:
    """Structure check should pass when required paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _repository_validation_structure_seed_required_structure(repo_root)
        context = CheckContext(repo_root=repo_root)
        assert structure_validation.check_structure(context) == []
        assert (repo_root / manifest_module.REGISTRY_REL_PATH).exists()


def _structure_structure_check_reports_missing_paths() -> None:
    """Structure check should flag missing structure entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)
        assert violations
        assert violations[0].policy_id == "structure-validation"


def _structure_structure_check_uses_manifest_docs() -> None:
    """Structure check should use enabled doc lists when present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        manifest = manifest_module.build_manifest()
        manifest_module.write_manifest(repo_root, manifest)
        for rel_path in manifest["core"]["dirs"]:
            (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
        for rel_path in manifest["core"]["files"]:
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("#\n", encoding="utf-8")
        docs = manifest["docs"]["enabled"]
        for rel_path in docs:
            if rel_path == "README.md":
                continue
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#\n", encoding="utf-8")
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)
        assert violations
        assert "README.md" in violations[0].message


def _structure_structure_check_reports_repo_bytecode() -> None:
    """Structure check should flag repo-local bytecode for devcovrepo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _repository_validation_structure_seed_required_structure(repo_root)
        _repository_validation_structure_write_active_profiles(
            repo_root, ["devcovrepo"]
        )
        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)
        assert violations
        assert "bytecode" in violations[0].message


def _structure_structure_check_skips_repo_bytecode_without_profile() -> None:
    """Structure check should ignore bytecode when devcovrepo is inactive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _repository_validation_structure_seed_required_structure(repo_root)
        _repository_validation_structure_write_active_profiles(
            repo_root, ["global"]
        )
        pycache = repo_root / "devcovenant" / "__pycache__"
        pycache.mkdir(parents=True, exist_ok=True)
        (pycache / "demo.cpython-314.pyc").write_bytes(b"x")
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)
        assert violations == []


def _structure_structure_check_requires_logs_readme() -> None:
    """Structure check should require the tracked logs README skeleton."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        _repository_validation_structure_seed_required_structure(repo_root)
        logs_readme = repo_root / "devcovenant" / "logs" / "README.md"
        logs_readme.unlink()
        context = CheckContext(repo_root=repo_root)
        violations = structure_validation.check_structure(context)
        assert violations
        assert "devcovenant/logs/README.md" in violations[0].message


def _structure_structure_check_ignores_available_but_disabled_docs() -> None:
    """Structure check should ignore docs that are only available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        manifest = manifest_module.build_manifest(
            available_docs=["AGENTS.md", "SECURITY.md"],
            enabled_docs=["AGENTS.md"],
        )
        manifest_module.write_manifest(repo_root, manifest)
        for rel_path in manifest["core"]["dirs"]:
            (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
        for rel_path in manifest["core"]["files"]:
            path = repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("#\n", encoding="utf-8")
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.write_text(
            "doc_assets:\n  autogen:\n    - AGENTS.md\n  user: []\n",
            encoding="utf-8",
        )
        (repo_root / "AGENTS.md").write_text("#\n", encoding="utf-8")
        context = CheckContext(repo_root=repo_root)
        assert structure_validation.check_structure(context) == []


class RepositoryValidationStructureTests(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_structure_check_passes_with_required_paths(self):
        """Run structure pass assertions."""
        _structure_structure_check_passes_with_required_paths()

    def test_structure_check_reports_missing_paths(self):
        """Run missing-path structure assertions."""
        _structure_structure_check_reports_missing_paths()

    def test_structure_check_uses_manifest_docs(self):
        """Run enabled-doc structure assertions."""
        _structure_structure_check_uses_manifest_docs()

    def test_structure_check_reports_repo_bytecode(self):
        """Run repo-bytecode structure assertions."""
        _structure_structure_check_reports_repo_bytecode()

    def test_structure_check_skips_repo_bytecode_without_profile(self):
        """Run non-devcovrepo bytecode assertions."""
        _structure_structure_check_skips_repo_bytecode_without_profile()

    def test_structure_check_requires_logs_readme(self):
        """Run logs README structure assertions."""
        _structure_structure_check_requires_logs_readme()

    def test_structure_check_ignores_available_but_disabled_docs(self):
        """Run available-but-disabled doc structure assertions."""
        _structure_structure_check_ignores_available_but_disabled_docs()


if __name__ == "__main__":
    unittest.main()
