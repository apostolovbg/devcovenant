"""Unit tests for refresh command behavior."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

import devcovenant.core.refresh_runtime as refresh_flow
import devcovenant.core.repository_validation as manifest_module
from devcovenant import deploy, install, refresh
from tests import (
    copy_installed_repo,
    copy_refreshed_repo,
    current_devcovenant_version,
    current_project_version,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_PROJECT_VERSION = current_project_version()
CURRENT_DEVCOVENANT_VERSION = current_devcovenant_version()


def _unit_test_refresh_builds_tracked_registry_and_agents() -> None:
    """refresh_repo should build tracked registry content and render AGENTS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        profile_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        agents_path = repo_root / "AGENTS.md"
        config_path = repo_root / "devcovenant" / "config.yaml"

        assert policy_registry.exists()
        assert profile_registry.exists()
        assert agents_path.exists()
        config_payload = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        policy_state = config_payload.get("policy_state", {})
        assert isinstance(policy_state, dict)
        assert policy_state["changelog-coverage"] is True
        assert policy_state["dependency-management"] is True
        assert policy_state["managed-environment"] is False
        assert policy_state["version-governance"] is False
        changelog_path = repo_root / "CHANGELOG.md"
        spec_path = repo_root / "SPEC.md"
        assert changelog_path.exists()
        assert "## Unreleased" in changelog_path.read_text(encoding="utf-8")
        spec_text = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** prototype" in spec_text
        assert "**Versioning Mode:** unversioned" in spec_text
        agents_text = agents_path.read_text(encoding="utf-8")
        assert "## Project Governance" in agents_text
        assert agents_text.index("## Project Governance") < agents_text.index(
            "<!-- DEVCOV-POLICIES:BEGIN -->"
        )
        registry_payload = yaml.safe_load(
            policy_registry.read_text(encoding="utf-8")
        )
        assert "project-governance" in registry_payload
        assert (
            registry_payload["project-governance"]["versioning_mode"]
            == "unversioned"
        )
        assert "workflow_contract" in registry_payload
        assert "tests" in registry_payload["workflow_contract"]["run_ids"]
        assert "managed-docs" in registry_payload
        spec_entry = registry_payload["managed-docs"]["descriptors"]["SPEC.md"]
        assert spec_entry["body_fingerprint"]
        assert "legacy_generic_body_fingerprints" not in spec_entry
        assert "project-governance" not in registry_payload["policies"]


def _unit_test_refresh_updates_managed_block_only() -> None:
    """refresh_repo should update managed block without replacing full doc."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        readme = repo_root / "README.md"
        readme.write_text(
            "# User README\n\n"
            "<!-- DEVCOV:BEGIN -->\nold\n<!-- DEVCOV:END -->\n\n"
            "User body\n",
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = readme.read_text(encoding="utf-8")
        assert "User body" in updated
        assert "Doc ID:" in updated


def _unit_test_refresh_syncs_project_identity() -> None:
    """refresh_repo should render README and pyproject identity."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        governance = payload["project-governance"]
        governance["project_name"] = "Example Product"
        governance["project_description"] = (
            "Example Product keeps repository governance explicit."
        )
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        readme = (repo_root / "README.md").read_text(encoding="utf-8")
        assert readme.startswith("# Example Product\n")
        assert (
            "Example Product keeps repository governance explicit." in readme
        )

        pyproject_payload = tomllib.loads(
            (repo_root / "pyproject.toml").read_text(encoding="utf-8")
        )
        assert pyproject_payload["project"]["name"] == "Example Product"
        assert (
            pyproject_payload["project"]["description"]
            == "Example Product keeps repository governance explicit."
        )


def _unit_test_refresh_rewrites_pyproject_identity() -> None:
    """refresh_repo should rewrite existing pyproject identity fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        governance = payload["project-governance"]
        governance["project_name"] = "Example Product"
        governance["project_description"] = (
            "Describe the project this repository ships: what it does, "
            "who it helps, and what problem it solves."
        )
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )
        (repo_root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "wrong-name"\n'
            'version = "0.0.0"\n'
            'description = "wrong description"\n'
            'readme = "README.md"\n',
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        pyproject_text = (repo_root / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        pyproject_payload = tomllib.loads(pyproject_text)
        assert pyproject_payload["project"]["name"] == "Example Product"
        assert (
            pyproject_payload["project"]["description"]
            == "Describe the project this repository ships: what it does, "
            "who it helps, and what problem it solves."
        )
        assert max(len(line) for line in pyproject_text.splitlines()) <= 79


_REFRESH_PYPROJECT_IDENTITY_CALLBACK = (
    _unit_test_refresh_rewrites_pyproject_identity
)


def _unit_test_refresh_renders_current_clean_and_ci_commentary() -> None:
    """refresh_repo should render current clean and ci commentary."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        config_text = (repo_root / "devcovenant" / "config.yaml").read_text(
            encoding="utf-8"
        )
        assert "# CI-and-test workflow generation" in config_text
        assert "# Governance-and-test generation" not in config_text
        assert (
            "managed environment roots resolved from "
            "managed-environment metadata."
        ) in config_text
        assert "Activate the `github` profile" in config_text
        assert "always protects .git, .venv" not in config_text


def _unit_test_refresh_calls_dependency_refresh_once() -> None:
    """refresh_repo should invoke dependency refresh exactly once."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        with patch.object(
            refresh_flow,
            "_refresh_dependency_artifacts",
            return_value=[],
        ) as mock_refresh_dependencies:
            result = refresh_flow.refresh_repo(repo_root)

    assert result == 0
    mock_refresh_dependencies.assert_called_once_with(repo_root)


def _unit_test_refresh_builds_profile_registry_once() -> None:
    """refresh_repo should reuse one profile-registry build per call."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)
        build_calls = 0
        original_build = (
            refresh_flow.profile_registry_service.build_profile_registry
        )

        def _counted_build(*args, **kwargs):
            """Count registry builds while delegating to the real helper."""
            nonlocal build_calls
            build_calls += 1
            return original_build(*args, **kwargs)

        with patch.object(
            refresh_flow.profile_registry_service,
            "build_profile_registry",
            side_effect=_counted_build,
        ):
            result = refresh_flow.refresh_repo(repo_root)

    assert result == 0
    assert build_calls == 1


def _unit_test_refresh_ensures_manifest_once() -> None:
    """refresh_repo should not duplicate manifest normalization work."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)
        ensure_calls = 0
        original_ensure = refresh_flow.manifest_module.ensure_manifest

        def _counted_ensure(*args, **kwargs):
            """Count manifest ensures while delegating to the real helper."""
            nonlocal ensure_calls
            ensure_calls += 1
            return original_ensure(*args, **kwargs)

        with patch.object(
            refresh_flow.manifest_module,
            "ensure_manifest",
            side_effect=_counted_ensure,
        ):
            result = refresh_flow.refresh_repo(repo_root)

    assert result == 0
    assert ensure_calls == 1


def _unit_test_refresh_builds_registry_after_generated_config() -> None:
    """refresh_repo should build registry and AGENTS after config refresh."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)
        order: list[str] = []

        def _fake_refresh_config_generated(
            repo_root_arg,
            config_path,
            config,
            user_config,
            profile_registry,
            active_profiles,
        ):
            """Record config generation before later refresh steps."""
            order.append("config")
            return config, False

        def _fake_refresh_policy_registry(
            repo_root_arg,
            config_payload=None,
            profile_registry=None,
        ):
            """Record tracked-registry persistence after config refresh."""
            del profile_registry
            order.append("registry")
            return 0

        def _fake_refresh_agents_policy_block(
            agents_path, refresh_result, repo_root=None
        ):
            """Record AGENTS block refresh after registry persistence."""
            order.append("agents")
            return None

        with (
            patch.object(
                refresh_flow,
                "_refresh_profile_assets",
                return_value=[],
            ),
            patch.object(
                refresh_flow,
                "_refresh_config_generated",
                side_effect=_fake_refresh_config_generated,
            ),
            patch.object(
                refresh_flow,
                "refresh_policy_registry",
                side_effect=_fake_refresh_policy_registry,
            ),
            patch.object(
                refresh_flow,
                "refresh_agents_policy_block",
                side_effect=_fake_refresh_agents_policy_block,
            ),
            patch.object(
                refresh_flow,
                "_refresh_dependency_artifacts",
                return_value=[],
            ),
            patch.object(
                refresh_flow,
                "_refresh_ci_and_test",
                return_value=False,
            ),
            patch.object(
                refresh_flow,
                "_refresh_pre_commit_config",
                return_value=False,
            ),
            patch.object(
                refresh_flow,
                "_refresh_gitignore",
                return_value=False,
            ),
            patch.object(
                refresh_flow,
                "_managed_docs_from_config",
                return_value=[],
            ),
            patch.object(
                refresh_flow,
                "_sync_doc",
                return_value=False,
            ),
            patch.object(
                refresh_flow,
                "_sync_project_pyproject_identity",
                return_value=False,
            ),
            patch.object(
                refresh_flow.manifest_module,
                "ensure_manifest",
                return_value=None,
            ),
        ):
            result = refresh_flow.refresh_repo(repo_root)

    assert result == 0
    assert order == ["config", "registry", "agents"]


def _unit_test_refresh_discovers_policy_sources_deterministically() -> None:
    """Policy-source discovery should not depend on filesystem iteration."""
    discovered = refresh_flow._discover_policy_sources(REPO_ROOT)
    discovered_ids = list(discovered.keys())
    expected_ids: list[str] = []
    for source in ("builtin", "custom"):
        source_root = REPO_ROOT / "devcovenant" / source / "policies"
        if not source_root.exists():
            continue
        for entry in sorted(
            source_root.iterdir(),
            key=lambda candidate: candidate.name.lower(),
        ):
            if not entry.is_dir():
                continue
            script = entry / f"{entry.name}.py"
            if not script.exists():
                continue
            expected_ids.append(entry.name.replace("_", "-").strip())
    assert discovered_ids == expected_ids


def _unit_test_refresh_keeps_root_and_packaged_readme_blocks_empty() -> None:
    """refresh_repo should keep README managed blocks intentionally empty."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        for relative_path in ("README.md", "devcovenant/README.md"):
            content = (repo_root / relative_path).read_text(encoding="utf-8")
            assert "<!-- DEVCOV:BEGIN -->\n\n<!-- DEVCOV:END -->" in content
            assert "Managed runtime note:" not in content


def _unit_test_deploy_compiles_workspace_lock_for_fresh_repo() -> None:
    """deploy should compile a usable root_workspace lock for fresh repos."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["install"]["config_reviewed"] = True
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = deploy.deploy_repo(repo_root)
        assert result == 0

        requirements_in = (repo_root / "requirements.in").read_text(
            encoding="utf-8"
        )
        requirements_lock = (repo_root / "requirements.lock").read_text(
            encoding="utf-8"
        )

        assert requirements_in.startswith(
            "-r devcovenant/runtime-requirements.lock\n"
        )
        assert "Starter lock file." not in requirements_lock
        assert "pyyaml==" in requirements_lock.lower()

        venv_root = repo_root / ".venv"
        managed_python = venv_root / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_root)],
            cwd=repo_root,
            check=True,
        )
        subprocess.run(
            [
                str(managed_python),
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                "requirements.lock",
            ],
            cwd=repo_root,
            check=True,
        )
        subprocess.run(
            [
                str(managed_python),
                "-c",
                (
                    "import yaml; "
                    "import devcovenant.cli; "
                    "import devcovenant.core.execution"
                ),
            ],
            cwd=repo_root,
            check=True,
        )


def _unit_test_release_metadata_keeps_support_floor_and_docs_truthful() -> (
    None
):
    """Release metadata should prove the Python floor and doc links."""
    pyproject_payload = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    project = pyproject_payload["project"]
    dependencies = [str(item) for item in project["dependencies"]]
    urls = project["urls"]

    assert project["requires-python"] == ">=3.11"
    assert (
        "Programming Language :: Python :: 3.10" not in project["classifiers"]
    )
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]
    assert not any(("tomli" in dependency for dependency in dependencies))

    requirements_in = (REPO_ROOT / "requirements.in").read_text(
        encoding="utf-8"
    )
    requirements_lock = (REPO_ROOT / "requirements.lock").read_text(
        encoding="utf-8"
    )
    runtime_requirements_lock = (
        REPO_ROOT / "devcovenant" / "runtime-requirements.lock"
    ).read_text(encoding="utf-8")
    root_license_report = (
        REPO_ROOT / "licenses" / "THIRD_PARTY_LICENSES.md"
    ).read_text(encoding="utf-8")
    packaged_license_report = (
        REPO_ROOT / "devcovenant" / "licenses" / "THIRD_PARTY_LICENSES.md"
    ).read_text(encoding="utf-8")
    active_requirements_in_lines = [
        line.strip()
        for line in requirements_in.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_requirements_in_lines[0] == (
        "-r devcovenant/runtime-requirements.lock"
    )
    assert "packaging>=26.0" not in requirements_in
    assert "pytest>=9.0.2" not in requirements_in
    assert "pip-tools>=7.5.3" not in requirements_in
    assert "bandit==" not in requirements_in
    assert "pip-audit==2.10.0" not in requirements_in
    assert "twine==6.2.0" in requirements_in
    assert "SecretStorage==3.5.0" not in requirements_in
    assert "importlib-metadata==9.0.0" not in requirements_in
    assert runtime_requirements_lock != requirements_lock
    assert "pip_audit==" not in requirements_lock
    assert "pip_audit==" not in runtime_requirements_lock
    assert "bandit==" in requirements_lock
    assert "bandit==" in runtime_requirements_lock
    assert "twine==" in requirements_lock
    assert "cryptography==46.0.6" not in requirements_lock
    assert 'python_version == "3.10"' not in requirements_lock
    assert packaged_license_report != root_license_report
    assert "- `requirements.lock`" in root_license_report
    assert (
        "- `devcovenant/runtime-requirements.lock`" in packaged_license_report
    )

    assert urls["Documentation"].endswith("/tree/main/devcovenant/docs")
    assert urls["Changelog"].endswith("/blob/main/CHANGELOG.md")

    packaged_readme = (REPO_ROOT / "devcovenant" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "/blob/main/devcovenant/docs/workflow.md" in packaged_readme
    assert (
        "https://raw.githubusercontent.com/apostolovbg/devcovenant/"
        "main/devcovenant/docs/banner.png"
    ) in packaged_readme


def _unit_test_refresh_imports_same_version_header_only_spec_doc() -> None:
    """refresh_repo should adopt a same-version preauthored SPEC body."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        spec_path = repo_root / "SPEC.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            "# Product Spec\n"
            "**Doc ID:** SPEC\n"
            "**Doc Type:** specification\n"
            "**Project Version:** 9.9.9\n"
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
            "Custom imported spec body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** prototype" in updated
        assert "**Versioning Mode:** unversioned" in updated
        assert "This opening section is managed by DevCovenant." in updated
        assert "Custom imported spec body." in updated


def _unit_test_refresh_imports_same_version_header_only_plan_doc() -> None:
    """refresh_repo should adopt a same-version preauthored PLAN body."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        plan_path = repo_root / "PLAN.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(
            "# App Plan\n"
            "**Doc ID:** PLAN\n"
            "**Doc Type:** plan\n"
            "**Project Version:** 9.9.9\n"
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
            "Custom imported planning body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = plan_path.read_text(encoding="utf-8")
        assert "This opening section is managed by DevCovenant." in updated
        assert "Custom imported planning body." in updated
        assert (
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}"
            in updated
        )


def _unit_test_refresh_preserves_existing_non_placeholder_plan_body() -> None:
    """refresh_repo should preserve existing non-placeholder PLAN content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        plan_path = repo_root / "PLAN.md"
        plan_path.write_text(
            "# Development Plan\n"
            "**Doc ID:** PLAN\n"
            "**Doc Type:** plan\n"
            f"**Project Version:** {CURRENT_PROJECT_VERSION}\n"
            "**Last Updated:** 2026-03-01\n"
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
            "This is the real planning body.\n\n"
            "## Active Work\n"
            "1. [not done] Preserve authored docs.\n",
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = plan_path.read_text(encoding="utf-8")
        assert "This is the real planning body." in updated
        assert "Preserve authored docs." in updated
        assert "Item placeholder." not in updated


def _unit_test_refresh_replaces_older_header_only_spec_doc() -> None:
    """refresh_repo should replace older DevCovenant SPEC seeds."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        spec_path = repo_root / "SPEC.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            "# Product Spec\n"
            "**Doc ID:** SPEC\n"
            "**Doc Type:** specification\n"
            "**Project Version:** 9.9.9\n"
            "**DevCovenant Version:** 0.9.0\n\n"
            "Old imported body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = spec_path.read_text(encoding="utf-8")
        assert "Old imported body." not in updated
        assert "## Project Intent" in updated
        assert "## Acceptance Criteria" in updated


def _unit_test_refresh_imports_same_version_managed_block_doc() -> None:
    """refresh_repo should adopt same-version managed-block docs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        readme_path = repo_root / "README.md"
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text(
            "# Seed README\n"
            "**Doc ID:** README\n"
            "**Doc Type:** repo-readme\n"
            "**Project Version:** 0.1.0\n"
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "stale block\n"
            "<!-- DEVCOV:END -->\n\n"
            "Imported README body.\n",
            encoding="utf-8",
        )

        install.install_repo(repo_root)
        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = readme_path.read_text(encoding="utf-8")
        assert "Imported README body." in updated
        assert "stale block" not in updated
        assert (
            f"**DevCovenant Version:** {CURRENT_DEVCOVENANT_VERSION}"
            in updated
        )


def _unit_test_refresh_supports_custom_managed_docs() -> None:
    """refresh_repo should resolve custom managed docs from active profiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        profile_root = (
            repo_root / "devcovenant" / "custom" / "profiles" / "mapsdemo"
        )
        assets_root = profile_root / "assets"
        assets_root.mkdir(parents=True, exist_ok=True)
        (profile_root / "mapsdemo.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "profile": "mapsdemo",
                    "category": "repo",
                    "suffixes": [],
                    "ignore_dirs": [],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (assets_root / "PROFILE_MAP.yaml").write_text(
            "\n".join(
                [
                    "title: Profile Map",
                    "target_path: PROFILE_MAP.md",
                    "doc_id: PROFILE_MAP",
                    "doc_type: reference-map",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: true",
                    "project_governance_headers: false",
                    "import_seed: true",
                    "authoritative_source: true",
                    "managed_block: |-",
                    "  This opening section is managed by DevCovenant.",
                    "  Use `PROFILE_MAP.md` for custom profile inventory.",
                    "body: |-",
                    "  ## Overview",
                    "  Template profile map body.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (assets_root / "POLICY_MAP.yaml").write_text(
            "\n".join(
                [
                    "title: Policy Map",
                    "target_path: POLICY_MAP.md",
                    "doc_id: POLICY_MAP",
                    "doc_type: reference-map",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: true",
                    "project_governance_headers: false",
                    "import_seed: true",
                    "authoritative_source: true",
                    "managed_block: |-",
                    "  This opening section is managed by DevCovenant.",
                    "  Use `POLICY_MAP.md` for custom policy inventory.",
                    "body: |-",
                    "  ## Overview",
                    "  Template policy map body.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["profiles"] = {"active": ["mapsdemo"]}
        payload["doc_assets"] = {
            "autogen": ["AGENTS.md", "PROFILE_MAP.md", "POLICY_MAP.md"],
            "user": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        (repo_root / "PROFILE_MAP.md").write_text(
            "# Profile Map\n\n"
            "## Purpose\n"
            "Keep this authored custom profile map body.\n",
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        profile_map = (repo_root / "PROFILE_MAP.md").read_text(
            encoding="utf-8"
        )
        policy_map = (repo_root / "POLICY_MAP.md").read_text(encoding="utf-8")

        assert "**Doc ID:** PROFILE_MAP" in profile_map
        assert "Keep this authored custom profile map body." in profile_map
        assert "**Doc ID:** POLICY_MAP" in policy_map
        assert "Template policy map body." in policy_map
        assert not (repo_root / "README.md").exists()


def _unit_test_refresh_supports_custom_trust_docs() -> None:
    """refresh_repo should let an active profile override a trust doc."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        profile_root = (
            repo_root / "devcovenant" / "custom" / "profiles" / "trustdemo"
        )
        assets_root = profile_root / "assets"
        assets_root.mkdir(parents=True, exist_ok=True)
        (profile_root / "trustdemo.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "profile": "trustdemo",
                    "category": "repo",
                    "suffixes": [],
                    "ignore_dirs": [],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (assets_root / "SECURITY.yaml").write_text(
            "\n".join(
                [
                    "title: Security Policy",
                    "target_path: SECURITY.md",
                    "doc_id: SECURITY",
                    "doc_type: security-policy",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: true",
                    "project_governance_headers: false",
                    "import_seed: true",
                    "authoritative_source: true",
                    "managed_block: |-",
                    "  This opening section is managed by DevCovenant.",
                    "body: |-",
                    "  # Security Policy",
                    "",
                    "  ## Overview",
                    "  Template security body.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["profiles"] = {"active": ["trustdemo"]}
        payload["doc_assets"] = {
            "autogen": ["AGENTS.md", "SECURITY.md"],
            "user": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        security = (repo_root / "SECURITY.md").read_text(encoding="utf-8")

        assert "**Doc ID:** SECURITY" in security
        assert "Template security body." in security
        assert (
            "Use this document for security reporting and disclosure notes."
            not in security
        )
        assert "Project Stage" not in security
        assert "Maintenance Stance" not in security
        assert "Compatibility Policy" not in security
        assert "Versioning Mode" not in security


def _unit_test_refresh_supports_global_trust_docs() -> None:
    """refresh_repo should render global trust-doc templates when enabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["doc_assets"] = {
            "autogen": [
                "AGENTS.md",
                "SECURITY.md",
                "PRIVACY.md",
                "SUPPORT.md",
            ],
            "user": [],
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        security = (repo_root / "SECURITY.md").read_text(encoding="utf-8")
        privacy = (repo_root / "PRIVACY.md").read_text(encoding="utf-8")
        support = (repo_root / "SUPPORT.md").read_text(encoding="utf-8")

        assert (
            "Use this document for security reporting and disclosure notes."
            in security
        )
        assert (
            "Use this document for privacy and local data-handling notes."
            in privacy
        )
        assert (
            "Use this document for support and maintenance expectations."
            in support
        )
        for rendered in (security, privacy, support):
            assert "Project Stage" not in rendered
            assert "Maintenance Stance" not in rendered
            assert "Compatibility Policy" not in rendered
            assert "Versioning Mode" not in rendered


def _unit_test_refresh_updates_all_managed_blocks() -> None:
    """refresh_repo should normalize AGENTS managed/workflow/policy blocks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        agents = repo_root / "AGENTS.md"
        agents.write_text(
            "# AGENTS\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old top block\n"
            "<!-- DEVCOV:END -->\n\n"
            "# EDITABLE SECTION\n\n"
            "keep me\n\n"
            "<!-- DEVCOV:BEGIN -->\n"
            "old secondary block\n"
            "<!-- DEVCOV:END -->\n\n"
            "<!-- DEVCOV-POLICIES:BEGIN -->\n"
            "<!-- DEVCOV-POLICIES:END -->\n",
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = agents.read_text(encoding="utf-8")
        assert "old top block" not in updated
        assert "old secondary block" not in updated
        assert "keep me" in updated
        assert "## THE DEV COVENANT" in updated
        assert "## Project Governance" in updated
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" in updated
        assert "<!-- DEVCOV-WORKFLOW:END -->" in updated
        assert updated.count("<!-- DEVCOV:BEGIN -->") == 2


def _unit_test_refresh_writes_ruff_cache_gitignore() -> None:
    """refresh_repo should include .ruff_cache in generated gitignore."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert ".ruff_cache/" in content


def _unit_test_refresh_writes_devcovenant_logs_gitignore_rules() -> None:
    """refresh_repo should ignore runtime logs but keep logs README tracked."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert "devcovenant/logs/**" in content
        assert "!devcovenant/logs/" in content
        assert "!devcovenant/logs/README.md" in content


def _unit_test_refresh_writes_global_artifact_ignore_defaults() -> None:
    """refresh_repo should seed shared editor/build/runtime ignore globs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        patterns = payload["ignore"]["patterns"]
        for expected in (
            ".vscode/**",
            ".idea/**",
            "*.egg-info/**",
            "pip-wheel-metadata/**",
            ".coverage.*",
            "devcovenant/logs/**",
            "devcovenant/registry/runtime/**",
        ):
            assert expected in patterns


def _unit_test_refresh_writes_clean_config_section() -> None:
    """refresh_repo should render the clean config contract and defaults."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        clean_block = payload.get("clean", {})

        assert isinstance(clean_block, dict)
        assert clean_block.get("overlays") == {
            "build_dirs": [],
            "build_globs": [],
            "cache_dirs": [],
            "cache_globs": [],
            "runtime_registry_dirs": [],
            "runtime_registry_globs": [],
            "logs_dirs": [],
            "logs_globs": [],
            "protected_dirs": [],
            "protected_globs": [],
        }
        assert clean_block.get("overrides") == {}


def _unit_test_refresh_renders_workflow_and_integrity_sections() -> None:
    """refresh_repo should render workflow and integrity runtime sections."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert "integrity" in payload
        assert payload["paths"]["gate_status_file"] == (
            "devcovenant/registry/runtime/gate_status.json"
        )
        assert payload["paths"]["workflow_session_file"] == (
            "devcovenant/registry/runtime/workflow_session.json"
        )
        assert payload["integrity"]["watch_dirs"] == []
        assert payload["integrity"]["watch_files"] == []
        assert payload["workflow"]["pre_commit_command"] == (
            "pre-commit run --all-files"
        )


def _unit_test_refresh_renders_config_ownership_comments() -> None:
    """refresh_repo should label config ownership clearly and accurately."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        config_text = (repo_root / "devcovenant" / "config.yaml").read_text(
            encoding="utf-8"
        )
        assert "# Human-owned section." in config_text
        assert "# Mixed-ownership section." in config_text
        assert "# Every key in `paths` is human-owned." in config_text
        assert (
            "# Set this to true after review to allow `devcovenant deploy`."
            in (config_text)
        )
        assert "profiles/userproject/" in config_text
        assert "{{ PROJECT_NAME_PATH }}" in config_text
        assert "cross-platform support" in config_text
        assert "values from other active profiles" in config_text
        assert "same-name custom profile" in config_text
        assert "Set this to false after review" not in config_text
        assert "integrity:" in config_text


def _unit_test_refresh_renders_devcov_managed_doc_intros() -> None:
    """refresh_repo should render the intended managed-doc intro contract."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        readme = (repo_root / "README.md").read_text(encoding="utf-8")
        package_readme = (repo_root / "devcovenant" / "README.md").read_text(
            encoding="utf-8"
        )
        contributing = (repo_root / "CONTRIBUTING.md").read_text(
            encoding="utf-8"
        )
        changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")

        assert "**Contributor note:** this repository is managed by " not in (
            readme
        )
        assert "<!-- DEVCOV:BEGIN -->\n\n<!-- DEVCOV:END -->" in readme
        assert "Describe the project this repository ships" in readme
        assert "If you already drafted DevCovenant-shaped docs" in readme
        assert "<!-- DEVCOV:BEGIN -->\n\n<!-- DEVCOV:END -->" in (
            package_readme
        )
        assert "Managed runtime note:" not in package_readme
        assert (
            "DevCovenant is a repository governance framework."
            in package_readme
        )
        assert "This opening section is managed by DevCovenant." in (
            contributing
        )
        assert "## Overview" in contributing
        assert "## Workflow" in contributing
        assert "<!-- DEVCOV:END -->\n\n## Overview" in contributing
        assert "## Repository Notes" in contributing
        assert "## DevCovenant Change Logging Rules" in changelog


def _unit_test_refresh_writes_global_artifact_gitignore_rules() -> None:
    """refresh_repo should write universal editor/build/runtime gitignores."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        for expected in (
            ".vscode/",
            ".idea/",
            "*.egg-info/",
            "pip-wheel-metadata/",
            ".coverage",
            ".coverage.*",
            "htmlcov/",
        ):
            assert expected in content


def _unit_test_refresh_writes_github_gitignore_rules() -> None:
    """refresh_repo should write github-profile gitignore rules."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = list(profiles.get("active", []))
        active_profiles.insert(2, "github")
        profiles["active"] = active_profiles
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        gitignore_path = repo_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert ".gha-pycache/" in content


def _unit_test_refresh_renders_pre_commit_excludes_for_build_outputs() -> None:
    """refresh_repo should exclude disposable build/proof dirs from hooks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        profile_root = (
            repo_root / "devcovenant" / "custom" / "profiles" / "proofdemo"
        )
        profile_root.mkdir(parents=True, exist_ok=True)
        (profile_root / "proofdemo.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "profile": "proofdemo",
                    "category": "repo",
                    "suffixes": [],
                    "ignore_dirs": [
                        "artifacts",
                        ".proof-wheel",
                        ".proof-sdist",
                        ".proof-py311",
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = list(profiles.get("active", []))
        active_profiles.append("proofdemo")
        profiles["active"] = active_profiles
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        pre_commit = (repo_root / ".pre-commit-config.yaml").read_text(
            encoding="utf-8"
        )
        assert r"[^/]+\.egg-info" in pre_commit
        assert "artifacts" in pre_commit
        assert r"\.proof\-wheel" in pre_commit
        assert r"\.proof\-sdist" in pre_commit
        assert r"\.proof\-py311" in pre_commit


def _unit_test_refresh_adds_github_pre_commit_excludes() -> None:
    """refresh_repo should add github-profile pre-commit excludes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = list(profiles.get("active", []))
        active_profiles.insert(2, "github")
        profiles["active"] = active_profiles
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        pre_commit = (repo_root / ".pre-commit-config.yaml").read_text(
            encoding="utf-8"
        )
        assert r"\.gha\-pycache" in pre_commit


def _unit_test_refresh_policy_registry_origin_metadata() -> None:
    """refresh_repo should record builtin/custom policy origins."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        payload = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policies = payload.get("policies", {})
        assert policies["changelog-coverage"]["origin"] == "builtin"
        assert policies["package-doc-sync"]["origin"] == "builtin"
        assert "core" not in policies["changelog-coverage"]


def _unit_test_refresh_policy_registry_records_metadata_resolution() -> None:
    """refresh_repo should persist per-key metadata resolution trace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        payload = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policy_entry = payload["policies"]["changelog-coverage"]
        resolution = policy_entry["metadata_resolution"]["skipped_globs"]
        enabled_resolution = policy_entry["metadata_resolution"]["enabled"]

        assert resolution["effective"]["values"]
        assert any(key != "effective" for key in resolution)
        assert enabled_resolution["policy_state"]["values"] == ["true"]
        assert enabled_resolution["policy_state"]["behavior"] == "replace"
        assert isinstance(policy_entry["metadata_warnings"], list)
        assert isinstance(policy_entry["runtime_metadata_options"], dict)
        assert isinstance(policy_entry["runtime_config_overrides"], dict)
        assert isinstance(policy_entry["runtime_effective_options"], dict)


def _unit_test_refresh_records_override_replacement_warning() -> None:
    """refresh_repo should record warnings for destructive overrides."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["user_metadata_overrides"] = {
            "changelog-coverage": {"skipped_globs": ["README.md"]}
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        policy_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        refreshed = yaml.safe_load(policy_registry.read_text(encoding="utf-8"))
        policy_entry = refreshed["policies"]["changelog-coverage"]
        warnings = policy_entry["metadata_warnings"]
        assert warnings
        assert warnings[0]["layer"] == "user_overrides"
        assert warnings[0]["key"] == "skipped_globs"
        resolution = policy_entry["metadata_resolution"]["skipped_globs"]
        assert resolution["user_overrides"]["values"] == ["README.md"]
        assert "README.md" in resolution["effective"]["values"]
        assert policy_entry["runtime_config_overrides"]["skipped_globs"] == [
            "README.md"
        ]
        assert (
            "README.md"
            in policy_entry["runtime_effective_options"]["skipped_globs"]
        )


def _unit_test_refresh_policy_registry_short_circuits_when_inputs_match() -> (
    None
):
    """refresh_policy_registry should skip rebuilding a current registry."""

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)
        assert refresh_flow.refresh_repo(repo_root) == 0

        config_path = repo_root / "devcovenant" / "config.yaml"
        config_payload = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
        assert isinstance(config_payload, dict)

        original_update = refresh_flow.PolicyRegistry.update_policy_entry

        def _unexpected_update(*args, **kwargs):
            """Fail if the current-input short-circuit still rebuilds."""

            del args, kwargs
            raise AssertionError("policy registry rebuild should be skipped")

        refresh_flow.PolicyRegistry.update_policy_entry = _unexpected_update
        try:
            result = refresh_flow.refresh_policy_registry(
                repo_root,
                config_payload=config_payload,
            )
        finally:
            refresh_flow.PolicyRegistry.update_policy_entry = original_update

        assert result == 0


def _unit_test_refresh_preserves_existing_gate_status() -> None:
    """refresh_repo should leave an open gate status file untouched."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        gate_status_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "runtime"
            / "gate_status.json"
        )
        gate_status_path.parent.mkdir(parents=True, exist_ok=True)
        expected_payload = {
            "session_id": "refresh-open-session",
            "session_state": "open",
            "pre_commit_open_utc": "2026-03-01T10:00:00+00:00",
        }
        gate_status_path.write_text(
            json.dumps(expected_payload, indent=2) + "\n",
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        assert gate_status_path.exists()
        actual_payload = json.loads(
            gate_status_path.read_text(encoding="utf-8")
        )
        assert actual_payload == expected_payload


def _unit_test_refresh_recreates_missing_tracked_registry_only() -> None:
    """refresh_repo should rebuild tracked registry without runtime state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        tracked_registry = (
            repo_root / "devcovenant" / "registry" / "registry.yaml"
        )
        runtime_registry = repo_root / "devcovenant" / "registry" / "runtime"
        if runtime_registry.exists():
            raise AssertionError(
                "Seeded repo should not include runtime state."
            )
        tracked_registry.unlink()
        assert not tracked_registry.exists()

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        assert tracked_registry.exists()
        assert not runtime_registry.exists()


def _unit_test_refresh_defaults_autofix_disabled_globally() -> None:
    """refresh_repo should default `engine.auto_fix_enabled` to false."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert payload["engine"]["auto_fix_enabled"] is False
        assert payload["engine"]["pycache_prefix_enabled"] is False
        assert payload["engine"]["pycache_prefix"] == ""


def _unit_test_refresh_seeds_autofix_for_developer_mode_when_unset() -> None:
    """refresh_repo should seed autofix for developer-mode repos when unset."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload.setdefault("profiles", {})
        payload["profiles"]["active"] = [
            "global",
            "defaults",
            "userproject",
            "devcovuser",
            "python",
            "docs",
        ]
        payload["developer_mode"] = True
        payload.setdefault("engine", {})
        payload["engine"].pop("auto_fix_enabled", None)
        payload["engine"].pop("pycache_prefix_enabled", None)
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        updated = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert updated["engine"]["auto_fix_enabled"] is True
        assert updated["engine"]["pycache_prefix_enabled"] is True


def _unit_test_refresh_rejects_missing_version_for_versioned_repo() -> None:
    """refresh_repo should fail when versioned repos lack a real version."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)
        version_path = repo_root / "VERSION"
        if version_path.exists():
            version_path.unlink()

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["project-governance"] = {
            "stage": "stable",
            "maintenance_stance": "active",
            "compatibility_policy": "breaking-allowed",
            "versioning_mode": "versioned",
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 1


def _unit_test_refresh_allows_unversioned_repo_without_version_file() -> None:
    """refresh_repo should allow missing version file for unversioned repos."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_refreshed_repo(repo_root)
        version_path = repo_root / "VERSION"
        if version_path.exists():
            version_path.unlink()

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["project-governance"] = {
            "stage": "beta",
            "maintenance_stance": "active",
            "compatibility_policy": "breaking-allowed",
            "versioning_mode": "unversioned",
            "unversioned_label": "Unversioned",
            "unreleased_heading": "## Unreleased",
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        spec_path = repo_root / "SPEC.md"
        spec_text = spec_path.read_text(encoding="utf-8")
        assert "**Project Stage:** beta" in spec_text
        assert "**Versioning Mode:** unversioned" in spec_text
        plan_text = (repo_root / "PLAN.md").read_text(encoding="utf-8")
        changelog_text = (repo_root / "CHANGELOG.md").read_text(
            encoding="utf-8"
        )
        assert "**Project Stage:** beta" in plan_text
        assert "**Project Stage:** beta" in changelog_text


def _unit_test_refresh_renders_canonical_workflow_triggers() -> None:
    """refresh_repo should render canonical GitHub trigger syntax."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = list(profiles.get("active", []))
        active_profiles.insert(2, "github")
        profiles["active"] = active_profiles
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        workflow_path = repo_root / ".github" / "workflows" / "ci.yml"
        content = workflow_path.read_text(encoding="utf-8")
        assert "\non:\n" in content
        assert "'on':" not in content
        assert '"on":' not in content
        assert "push: null" not in content
        assert "pull_request: null" not in content
        assert re.search(r"(?m)^  push:$", content)
        assert re.search(r"(?m)^  pull_request:$", content)
        assert re.search(r"(?m)^      run: \\|$", content)
        assert 'run: "python -m pytest -q' not in content
        assert "devcovenant/runtime-requirements.lock" in content
        assert "python -m pip install -r requirements.lock" not in content


def _unit_test_refresh_skips_ci_generation_without_github_profile() -> None:
    """refresh_repo should skip generated CI without a CI-owner profile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = [
            profile
            for profile in list(profiles.get("active", []))
            if str(profile).strip() != "github"
        ]
        profiles["active"] = active_profiles
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        workflow_path = repo_root / ".github" / "workflows" / "ci.yml"
        assert not workflow_path.exists()

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0
        assert not workflow_path.exists()


def _unit_test_refresh_default_core_paths_match_manifest() -> None:
    """Refresh fallback core paths should match manifest helpers."""
    assert refresh_flow._default_core_paths(REPO_ROOT) == (
        manifest_module.default_scan_excluded_core_paths()
    )


def _unit_test_refresh_rewrites_stale_generated_core_paths() -> None:
    """Refresh should rewrite stale core paths from canonical data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        assert isinstance(profiles, dict)
        generated = profiles.setdefault("generated", {})
        assert isinstance(generated, dict)
        generated["devcov_core_paths"] = ["devcovenant/test.py"]
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        refreshed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(refreshed, dict)
        refreshed_profiles = refreshed.get("profiles", {})
        assert isinstance(refreshed_profiles, dict)
        refreshed_generated = refreshed_profiles.get("generated", {})
        assert isinstance(refreshed_generated, dict)
        assert refreshed_generated.get("devcov_core_paths") == (
            manifest_module.default_scan_excluded_core_paths()
        )


def _unit_test_refresh_allows_ci_override_without_github_profile() -> None:
    """refresh_repo should allow full CI overrides without github active."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = [
            profile
            for profile in list(profiles.get("active", []))
            if str(profile).strip() != "github"
        ]
        profiles["active"] = active_profiles
        payload.setdefault("ci_and_test", {})
        payload["ci_and_test"]["overrides"] = {
            "name": "CI",
            "on": {"push": None},
            "jobs": {
                "demo": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"name": "Demo", "run": "echo demo"}],
                }
            },
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = refresh_flow.refresh_repo(repo_root)
        assert result == 0

        workflow_path = repo_root / ".github" / "workflows" / "ci.yml"
        rendered = workflow_path.read_text(encoding="utf-8")
        assert "name: CI" in rendered
        assert "demo:" in rendered
        assert "echo demo" in rendered


def _unit_test_refresh_rejects_ci_overlays_without_github_profile() -> None:
    """refresh_repo should reject CI overlays without a base CI owner."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        profiles = payload.setdefault("profiles", {})
        active_profiles = [
            profile
            for profile in list(profiles.get("active", []))
            if str(profile).strip() != "github"
        ]
        profiles["active"] = active_profiles
        payload.setdefault("ci_and_test", {})
        payload["ci_and_test"]["overlays"] = {
            "jobs": {
                "demo": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"name": "Demo", "run": "echo demo"}],
                }
            }
        }
        config_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        output = StringIO()
        with redirect_stdout(output):
            result = refresh_flow.refresh_repo(repo_root)
        assert result == 1
        assert "requires an active profile" in output.getvalue()


def _unit_test_refresh_rejects_multiline_non_block_doc_descriptor() -> None:
    """refresh_repo should fail when multiline doc fields skip block style."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "README.yaml"
        )
        descriptor_path.write_text(
            "\n".join(
                [
                    "title: README",
                    "target_path: README.md",
                    "doc_id: README",
                    "doc_type: repo-readme",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: true",
                    "managed_block: |-",
                    "  block text",
                    'body: "Line one\\nLine two"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        output = StringIO()
        with redirect_stdout(output):
            result = refresh_flow.refresh_repo(repo_root)
        assert result == 1
        assert "must use YAML literal block style" in output.getvalue()


def _unit_test_refresh_rejects_invalid_doc_descriptor_schema() -> None:
    """refresh_repo should fail when managed doc descriptor schema is wrong."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        copy_installed_repo(repo_root)

        descriptor_path = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
            / "README.yaml"
        )
        descriptor_path.write_text(
            "\n".join(
                [
                    "title: README",
                    "target_path: README.md",
                    "doc_id: README",
                    "doc_type: repo-readme",
                    "project_version: true",
                    "last_updated: true",
                    "devcovenant_version: false",
                    "managed_block: |-",
                    "  block text",
                    "body: |-",
                    "  Body text",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        output = StringIO()
        with redirect_stdout(output):
            result = refresh_flow.refresh_repo(repo_root)
        assert result == 1
        assert "field `devcovenant_version` must be true" in output.getvalue()


def _unit_test_refresh_run_calls_refresh_repo() -> None:
    """run() should resolve repo root and delegate to refresh_repo."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        with patch(
            "devcovenant.core.execution.resolve_repo_root",
            return_value=repo_root,
        ):
            with patch(
                "devcovenant.core.refresh_runtime.refresh_repo",
                return_value=0,
            ) as mock:
                result = refresh.run(SimpleNamespace())
    assert result == 0
    mock.assert_called_once_with(repo_root)


def _unit_test_refresh_main_exits_with_run_code() -> None:
    """main() should parse args, call run, and exit with its code."""
    captured: dict[str, object] = {}
    original_run = refresh.run

    def _fake_run(args):
        """Capture parsed args and return a stable exit code."""
        captured["args"] = args
        return 0

    refresh.run = _fake_run
    try:
        try:
            refresh.main([])
        except SystemExit as exc:
            code = exc.code
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected SystemExit from main().")
    finally:
        refresh.run = original_run

    assert code == 0
    assert hasattr(captured["args"], "__dict__")


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_refresh_builds_tracked_registry_and_agents(self):
        """Run test_refresh_builds_tracked_registry_and_agents."""
        _unit_test_refresh_builds_tracked_registry_and_agents()

    def test_refresh_updates_managed_block_only(self):
        """Run test_refresh_updates_managed_block_only."""
        _unit_test_refresh_updates_managed_block_only()

    def test_refresh_syncs_project_identity_into_readme_and_pyproject(self):
        """Run project-identity rendering assertions."""
        _unit_test_refresh_syncs_project_identity()

    def test_refresh_rewrites_existing_pyproject_identity_from_governance(
        self,
    ):
        """Run existing pyproject identity sync assertions."""
        _REFRESH_PYPROJECT_IDENTITY_CALLBACK()

    def test_refresh_renders_current_clean_and_ci_commentary(self):
        """Run generated-config commentary assertions."""
        _unit_test_refresh_renders_current_clean_and_ci_commentary()

    def test_refresh_calls_dependency_refresh_once(self):
        """Run single dependency-refresh invocation assertions."""
        _unit_test_refresh_calls_dependency_refresh_once()

    def test_refresh_builds_profile_registry_once(self):
        """Run single profile-registry build assertions."""
        _unit_test_refresh_builds_profile_registry_once()

    def test_refresh_ensures_manifest_once(self):
        """Run single manifest-normalization assertions."""
        _unit_test_refresh_ensures_manifest_once()

    def test_refresh_builds_registry_after_generated_config(self):
        """Run registry/AGENTS refresh-order assertions."""
        _unit_test_refresh_builds_registry_after_generated_config()

    def test_refresh_discovers_policy_sources_deterministically(self):
        """Run deterministic policy-source discovery assertions."""
        _unit_test_refresh_discovers_policy_sources_deterministically()

    def test_refresh_keeps_root_and_packaged_readme_blocks_empty(self):
        """Run README empty-managed-block assertions."""
        _unit_test_refresh_keeps_root_and_packaged_readme_blocks_empty()

    def test_release_metadata_keeps_support_floor_and_docs_truthful(self):
        """Run release metadata truthfulness assertions."""
        _unit_test_release_metadata_keeps_support_floor_and_docs_truthful()

    def test_refresh_imports_same_version_header_only_spec_doc(self):
        """Run same-version SPEC import assertions."""
        _unit_test_refresh_imports_same_version_header_only_spec_doc()

    def test_refresh_imports_same_version_header_only_plan_doc(self):
        """Run same-version PLAN import assertions."""
        _unit_test_refresh_imports_same_version_header_only_plan_doc()

    def test_refresh_preserves_existing_non_placeholder_plan_body(self):
        """Run existing PLAN preservation assertions."""
        _unit_test_refresh_preserves_existing_non_placeholder_plan_body()

    def test_refresh_replaces_older_header_only_spec_doc(self):
        """Run older SPEC replacement assertions."""
        _unit_test_refresh_replaces_older_header_only_spec_doc()

    def test_refresh_imports_same_version_managed_block_doc(self):
        """Run same-version managed-block import assertions."""
        _unit_test_refresh_imports_same_version_managed_block_doc()

    def test_refresh_updates_all_managed_blocks(self):
        """Run test_refresh_updates_all_managed_blocks."""
        _unit_test_refresh_updates_all_managed_blocks()

    def test_refresh_supports_custom_trust_docs(self):
        """Run custom trust-doc rendering assertions."""
        _unit_test_refresh_supports_custom_trust_docs()

    def test_refresh_supports_global_trust_docs(self):
        """Run global trust-doc rendering assertions."""
        _unit_test_refresh_supports_global_trust_docs()

    def test_refresh_writes_ruff_cache_gitignore(self):
        """Run test_refresh_writes_ruff_cache_gitignore."""
        _unit_test_refresh_writes_ruff_cache_gitignore()

    def test_refresh_writes_devcovenant_logs_gitignore_rules(self):
        """Run test_refresh_writes_devcovenant_logs_gitignore_rules."""
        _unit_test_refresh_writes_devcovenant_logs_gitignore_rules()

    def test_refresh_writes_global_artifact_ignore_defaults(self):
        """Run global artifact ignore default assertions."""
        _unit_test_refresh_writes_global_artifact_ignore_defaults()

    def test_refresh_writes_clean_config_section(self):
        """Run clean-config template rendering assertions."""
        _unit_test_refresh_writes_clean_config_section()

    def test_refresh_renders_workflow_and_integrity_sections(self):
        """Run workflow/integrity config placement assertions."""
        _unit_test_refresh_renders_workflow_and_integrity_sections()

    def test_refresh_renders_config_ownership_comments(self):
        """Run config ownership/comment rendering assertions."""
        _unit_test_refresh_renders_config_ownership_comments()

    def test_refresh_renders_devcov_managed_doc_intros(self):
        """Run DevCovenant managed-doc intro rendering assertions."""
        _unit_test_refresh_renders_devcov_managed_doc_intros()

    def test_deploy_compiles_workspace_lock_for_fresh_repo(self):
        """Run fresh-repo non-lock bootstrap assertions for deploy."""
        _unit_test_deploy_compiles_workspace_lock_for_fresh_repo()

    def test_refresh_writes_global_artifact_gitignore_rules(self):
        """Run global artifact gitignore assertions."""
        _unit_test_refresh_writes_global_artifact_gitignore_rules()

    def test_refresh_writes_github_gitignore_rules(self):
        """Run github-profile gitignore assertions."""
        _unit_test_refresh_writes_github_gitignore_rules()

    def test_refresh_renders_pre_commit_excludes_for_build_outputs(self):
        """Run pre-commit build/proof exclude rendering assertions."""
        _unit_test_refresh_renders_pre_commit_excludes_for_build_outputs()

    def test_refresh_adds_github_pre_commit_excludes(self):
        """Run github-profile pre-commit exclude assertions."""
        _unit_test_refresh_adds_github_pre_commit_excludes()

    def test_refresh_policy_registry_origin_metadata(self):
        """Run test_refresh_policy_registry_origin_metadata."""
        _unit_test_refresh_policy_registry_origin_metadata()

    def test_refresh_policy_registry_records_metadata_resolution(self):
        """Run metadata-resolution registry persistence assertions."""
        _unit_test_refresh_policy_registry_records_metadata_resolution()

    def test_refresh_records_override_replacement_warning(self):
        """Run destructive-override warning persistence assertions."""
        _unit_test_refresh_records_override_replacement_warning()

    def test_refresh_policy_registry_short_circuits_when_inputs_match(self):
        """Run policy-registry current-input short-circuit assertions."""
        _unit_test_refresh_policy_registry_short_circuits_when_inputs_match()

    def test_refresh_preserves_existing_gate_status(self):
        """Run open-gate preservation assertions for refresh."""
        _unit_test_refresh_preserves_existing_gate_status()

    def test_refresh_recreates_missing_tracked_registry_only(self):
        """Run tracked-registry recreation assertions for refresh."""
        _unit_test_refresh_recreates_missing_tracked_registry_only()

    def test_refresh_defaults_autofix_disabled_globally(self):
        """Run global autofix default-disabled refresh assertions."""
        _unit_test_refresh_defaults_autofix_disabled_globally()

    def test_refresh_seeds_autofix_for_developer_mode_when_unset(self):
        """Run developer-mode autofix seeding refresh assertions."""
        _unit_test_refresh_seeds_autofix_for_developer_mode_when_unset()

    def test_refresh_rejects_missing_version_for_versioned_repo(self):
        """Run missing-version explicit-failure refresh assertions."""
        _unit_test_refresh_rejects_missing_version_for_versioned_repo()

    def test_refresh_allows_unversioned_repo_without_version_file(self):
        """Run unversioned no-version refresh assertions."""
        _unit_test_refresh_allows_unversioned_repo_without_version_file()

    def test_refresh_renders_canonical_workflow_triggers(self):
        """Run canonical governance-trigger rendering refresh assertions."""
        _unit_test_refresh_renders_canonical_workflow_triggers()

    def test_refresh_skips_ci_generation_without_github_profile(self):
        """Run no-github generated-CI omission assertions."""
        _unit_test_refresh_skips_ci_generation_without_github_profile()

    def test_refresh_default_core_paths_match_manifest(self):
        """Run refresh core-path alignment assertions."""
        _unit_test_refresh_default_core_paths_match_manifest()

    def test_refresh_rewrites_stale_generated_core_paths(self):
        """Run refresh stale-generated-core-path rewrite assertions."""
        _unit_test_refresh_rewrites_stale_generated_core_paths()

    def test_refresh_allows_ci_override_without_github_profile(self):
        """Run no-github CI override rendering assertions."""
        _unit_test_refresh_allows_ci_override_without_github_profile()

    def test_refresh_rejects_ci_overlays_without_github_profile(self):
        """Run no-github CI overlay rejection assertions."""
        _unit_test_refresh_rejects_ci_overlays_without_github_profile()

    def test_refresh_rejects_multiline_non_block_doc_descriptor(self):
        """Run refresh rejection for non-block multiline descriptor strings."""
        _unit_test_refresh_rejects_multiline_non_block_doc_descriptor()

    def test_refresh_rejects_invalid_doc_descriptor_schema(self):
        """Run refresh rejection for invalid managed-doc schema."""
        _unit_test_refresh_rejects_invalid_doc_descriptor_schema()

    def test_refresh_run_calls_refresh_repo(self):
        """Run test_refresh_run_calls_refresh_repo."""
        _unit_test_refresh_run_calls_refresh_repo()

    def test_refresh_main_exits_with_run_code(self):
        """Run test_refresh_main_exits_with_run_code."""
        _unit_test_refresh_main_exits_with_run_code()
