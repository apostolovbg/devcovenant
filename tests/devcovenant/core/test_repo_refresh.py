"""Unit tests for devcovenant.core.repo_refresh orchestration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core import repo_refresh as core_refresh


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    """Write YAML mapping payload to disk."""
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _profile_manifest_path(repo_root: Path, profile_name: str) -> Path:
    """Return a profile manifest path from a profile name."""
    return (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / profile_name
        / f"{profile_name}.yaml"
    )


def _append_profile_pre_commit_repo(
    repo_root: Path,
    profile_name: str,
    repo_name: str,
    hook_id: str,
    *,
    hook_args: list[str] | None = None,
) -> None:
    """Append a deterministic pre-commit repo fragment to a profile."""
    manifest_path = _profile_manifest_path(repo_root, profile_name)
    payload = _read_yaml(manifest_path)
    pre_commit = payload.get("pre_commit")
    if not isinstance(pre_commit, dict):
        pre_commit = {}
    repos = pre_commit.get("repos")
    if not isinstance(repos, list):
        repos = []

    hook_payload: dict[str, object] = {"id": hook_id}
    if hook_args:
        hook_payload["args"] = list(hook_args)
    repos.append({"repo": repo_name, "rev": "v1.0.0", "hooks": [hook_payload]})
    pre_commit["repos"] = repos
    payload["pre_commit"] = pre_commit
    _write_yaml(manifest_path, payload)


def _unit_test_refresh_repo_builds_policy_registry() -> None:
    """core refresh should materialize local policy registry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        registry_path = (
            repo_root
            / "devcovenant"
            / "registry"
            / "local"
            / "policy_registry.yaml"
        )
        assert registry_path.exists()


def _unit_test_refresh_repo_updates_agents_policy_block() -> None:
    """core refresh should keep AGENTS policy block populated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        agents_path = repo_root / "AGENTS.md"
        content = agents_path.read_text(encoding="utf-8")
        assert "<!-- DEVCOV-POLICIES:BEGIN -->" in content
        assert "<!-- DEVCOV-WORKFLOW:BEGIN -->" in content
        assert "## Policy:" in content


def _unit_test_refresh_repo_ignores_inline_marker_mentions() -> None:
    """Refresh should not treat inline marker text as real block markers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        initial = core_refresh.refresh_repo(repo_root)
        assert initial == 0

        agents_path = repo_root / "AGENTS.md"
        content = agents_path.read_text(encoding="utf-8")
        content = content.replace(
            (
                "\n<!-- DEVCOV-WORKFLOW:END -->\n"
                "<!-- DEVCOV-POLICIES:BEGIN -->"
            ),
            (
                "\n<!-- DEVCOV-WORKFLOW:END -->`. Install/update scripts\n"
                "refresh those blocks while leaving\n"
                "surrounding text intact.\n\n"
                "<!-- DEVCOV-WORKFLOW:END -->\n"
                "<!-- DEVCOV-POLICIES:BEGIN -->"
            ),
            1,
        )
        agents_path.write_text(content, encoding="utf-8")

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        repaired = agents_path.read_text(encoding="utf-8")
        assert (
            "<!-- DEVCOV-WORKFLOW:END -->`. Install/update scripts "
            "refresh those" not in (repaired)
        )
        assert "<!-- DEVCOV-POLICIES:BEGIN -->" in repaired
        end_markers = [
            line.strip()
            for line in repaired.splitlines()
            if line.strip() == core_refresh.BLOCK_END
        ]
        assert len(end_markers) == 1


def _unit_test_refresh_repo_merges_pre_commit_fragments_and_overrides() -> (
    None
):
    """Refresh should merge global/profile fragments then config overrides."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "python", "docs"]
        config["profiles"] = profiles_block
        pre_commit_block = config.get("pre_commit")
        if not isinstance(pre_commit_block, dict):
            pre_commit_block = {}
        pre_commit_block["overrides"] = {
            "repos": [
                {
                    "repo": "https://example.com/shared",
                    "rev": "v3.0.0",
                    "hooks": [
                        {
                            "id": "shared-hook",
                            "args": ["--from-override"],
                        }
                    ],
                },
                {
                    "repo": "https://example.com/override-fragment",
                    "rev": "v1.0.0",
                    "hooks": [{"id": "override-hook"}],
                },
            ]
        }
        config["pre_commit"] = pre_commit_block
        _write_yaml(config_path, config)

        _append_profile_pre_commit_repo(
            repo_root,
            "global",
            "https://example.com/shared",
            "shared-hook",
            hook_args=["--from-global"],
        )
        _append_profile_pre_commit_repo(
            repo_root,
            "python",
            "https://example.com/shared",
            "python-only-hook",
        )
        _append_profile_pre_commit_repo(
            repo_root,
            "docs",
            "https://example.com/docs-fragment",
            "docs-hook",
        )

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        pre_commit_path = repo_root / ".pre-commit-config.yaml"
        payload = _read_yaml(pre_commit_path)
        repos_value = payload.get("repos")
        assert isinstance(repos_value, list)

        repo_names = [
            entry.get("repo")
            for entry in repos_value
            if isinstance(entry, dict)
        ]
        assert "https://example.com/shared" in repo_names
        assert "https://example.com/docs-fragment" in repo_names
        assert "https://example.com/override-fragment" in repo_names
        assert repo_names.index("https://example.com/docs-fragment") < (
            repo_names.index("https://example.com/override-fragment")
        )

        shared_repo = next(
            entry
            for entry in repos_value
            if isinstance(entry, dict)
            and entry.get("repo") == "https://example.com/shared"
        )
        hooks_value = shared_repo.get("hooks")
        assert isinstance(hooks_value, list)
        hooks_by_id = {
            hook.get("id"): hook
            for hook in hooks_value
            if isinstance(hook, dict)
        }
        assert hooks_by_id["shared-hook"].get("args") == ["--from-override"]
        assert "python-only-hook" in hooks_by_id


def _unit_test_refresh_repo_records_resolved_hooks_in_manifest() -> None:
    """Refresh should store resolved pre-commit hook metadata in manifest."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        _append_profile_pre_commit_repo(
            repo_root,
            "python",
            "https://example.com/python-fragment",
            "python-fragment-hook",
        )

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "python"]
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        result = core_refresh.refresh_repo(repo_root)
        assert result == 0

        manifest_path = (
            repo_root / "devcovenant" / "registry" / "local" / "manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        profiles_meta = manifest.get("profiles", {})
        assert isinstance(profiles_meta, dict)
        assert profiles_meta.get("active") == ["global", "python"]
        resolved_hooks = profiles_meta.get("resolved_pre_commit_hooks")
        assert isinstance(resolved_hooks, list)
        assert "https://example.com/python-fragment:python-fragment-hook" in (
            resolved_hooks
        )


def _unit_test_refresh_repo_regenerates_gitignore_and_preserves_user() -> None:
    """Refresh should rebuild gitignore sections and keep user lines."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        gitignore_path = repo_root / ".gitignore"
        gitignore_path.write_text(
            "\n".join(
                [
                    "# old generated content",
                    "build/",
                    "",
                    "# --- User entries (preserved) ---",
                    "",
                    "# keep-me",
                    "local-only/",
                    "",
                    "# --- End user entries ---",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = core_refresh.refresh_repo(repo_root)
        assert result == 0

        refreshed = gitignore_path.read_text(encoding="utf-8")
        assert "# DevCovenant base ignores" in refreshed
        assert "# OS-specific ignores (DevCovenant)" in refreshed
        assert "# Profile: data" not in refreshed
        assert "# Profile: python" in refreshed
        assert "data/raw" not in refreshed
        assert ".venv" in refreshed
        assert "# keep-me" in refreshed
        assert "local-only/" in refreshed
        assert "# --- User entries (preserved) ---" in refreshed
        assert "# --- End user entries ---" in refreshed


def _unit_test_refresh_repo_updates_generated_config_sections() -> None:
    """Refresh should regenerate config autogen sections and keep overrides."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        config["devcov_core_paths"] = ["stale/core/path.py"]
        config["autogen_metadata_overrides"] = {
            "dependency-license-sync": {
                "dependency_files": ["stale.lock"],
            }
        }
        config["user_metadata_overrides"] = {
            "dependency-license-sync": {
                "dependency_files": ["custom-manifest.lock"],
            }
        }
        config["doc_assets"] = {
            "autogen": ["README.md"],
            "user": ["PLAN.md"],
        }
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "python"]
        profiles_block["generated"] = {"file_suffixes": ["__none__"]}
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        result = core_refresh.refresh_repo(repo_root)
        assert result == 0

        refreshed = _read_yaml(config_path)
        assert refreshed.get("devcov_core_paths") == (
            core_refresh._default_core_paths(repo_root)
        )
        assert refreshed.get("autogen_metadata_overrides", {}).get(
            "dependency-license-sync", {}
        ).get("dependency_files") == [
            "requirements.in",
            "requirements.lock",
            "pyproject.toml",
        ]
        assert (
            refreshed.get("autogen_metadata_overrides", {})
            .get("version-sync", {})
            .get("version_file")
            == "VERSION"
        )
        assert refreshed.get("user_metadata_overrides", {}).get(
            "dependency-license-sync", {}
        ).get("dependency_files") == ["custom-manifest.lock"]
        assert refreshed.get("doc_assets", {}).get("autogen") == (
            core_refresh.DEFAULT_MANAGED_DOCS
        )
        assert refreshed.get("doc_assets", {}).get("user") == ["PLAN.md"]
        assert refreshed.get("profiles", {}).get("generated", {}).get(
            "file_suffixes"
        ) == [".ipynb", ".py", ".pyi", ".pyw"]
        rendered = config_path.read_text(encoding="utf-8")
        assert "DevCovenant Config Template" in rendered
        assert "Metadata overrides (resolution order matters)" in rendered


def _unit_test_refresh_repo_preserves_existing_profile_assets() -> None:
    """Refresh should preserve existing profile asset targets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = [
            "global",
            "devcovrepo",
            "docs",
            "python",
        ]
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        target = repo_root / "devcovenant" / "docs" / "profiles.md"
        target.write_text("stale\n", encoding="utf-8")

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        assert target.read_text(encoding="utf-8") == "stale\n"


def _unit_test_refresh_repo_rebuilds_config_when_missing() -> None:
    """Refresh should rebuild config from template when missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)
        config_path = repo_root / "devcovenant" / "config.yaml"
        config_path.unlink()

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        assert config_path.exists()
        config = _read_yaml(config_path)
        install_block = config.get("install")
        assert isinstance(install_block, dict)
        assert install_block.get("generic_config") is True
        rendered = config_path.read_text(encoding="utf-8")
        assert "DevCovenant Config Template" in rendered


def _unit_test_refresh_repo_materializes_missing_profile_assets() -> None:
    """Refresh should create missing profile assets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "python", "docs"]
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        requirements_in = repo_root / "requirements.in"
        requirements_in.unlink(missing_ok=True)

        expected = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "python"
            / "assets"
            / "requirements.in"
        ).read_text(encoding="utf-8")

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        assert requirements_in.read_text(encoding="utf-8") == expected


def _unit_test_refresh_repo_preserves_existing_python_assets() -> None:
    """Refresh should preserve existing python-profile asset targets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "python"]
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        pyproject = repo_root / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "preserved"\nversion = "1.2.3"\n',
            encoding="utf-8",
        )

        result = core_refresh.refresh_repo(repo_root)

        assert result == 0
        assert pyproject.read_text(encoding="utf-8") == (
            '[project]\nname = "preserved"\nversion = "1.2.3"\n'
        )


def _unit_test_refresh_repo_emits_scalar_path_overrides() -> None:
    """Refresh should emit scalar strings for path-valued autogen keys."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        install.install_repo(repo_root)

        config_path = repo_root / "devcovenant" / "config.yaml"
        config = _read_yaml(config_path)
        profiles_block = config.get("profiles")
        if not isinstance(profiles_block, dict):
            profiles_block = {}
        profiles_block["active"] = ["global", "devcovrepo"]
        config["profiles"] = profiles_block
        _write_yaml(config_path, config)

        result = core_refresh.refresh_repo(repo_root)
        assert result == 0

        refreshed = _read_yaml(config_path)
        autogen = refreshed.get("autogen_metadata_overrides", {})
        assert isinstance(autogen, dict)
        version_sync = autogen.get("version-sync", {})
        assert isinstance(version_sync, dict)
        assert version_sync.get("version_file") == "devcovenant/VERSION"
        semver = autogen.get("semantic-version-scope", {})
        assert isinstance(semver, dict)
        assert semver.get("version_file") == "devcovenant/VERSION"


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for core refresh coverage."""

    def test_refresh_repo_builds_policy_registry(self):
        """Run test_refresh_repo_builds_policy_registry."""
        _unit_test_refresh_repo_builds_policy_registry()

    def test_refresh_repo_updates_agents_policy_block(self):
        """Run test_refresh_repo_updates_agents_policy_block."""
        _unit_test_refresh_repo_updates_agents_policy_block()

    def test_refresh_repo_ignores_inline_marker_mentions(self):
        """Run test_refresh_repo_ignores_inline_marker_mentions."""
        _unit_test_refresh_repo_ignores_inline_marker_mentions()

    def test_refresh_repo_merges_pre_commit_fragments_and_overrides(self):
        """Run test_refresh_repo_merges_pre_commit_fragments_and_overrides."""
        _unit_test_refresh_repo_merges_pre_commit_fragments_and_overrides()

    def test_refresh_repo_records_resolved_hooks_in_manifest(self):
        """Run test_refresh_repo_records_resolved_hooks_in_manifest."""
        _unit_test_refresh_repo_records_resolved_hooks_in_manifest()

    def test_refresh_repo_regenerates_gitignore_and_preserves_user(self):
        """Run test_refresh_repo_regenerates_gitignore_and_preserves_user."""
        _unit_test_refresh_repo_regenerates_gitignore_and_preserves_user()

    def test_refresh_repo_updates_generated_config_sections(self):
        """Run test_refresh_repo_updates_generated_config_sections."""
        _unit_test_refresh_repo_updates_generated_config_sections()

    def test_refresh_repo_preserves_existing_profile_assets(self):
        """Run test_refresh_repo_preserves_existing_profile_assets."""
        _unit_test_refresh_repo_preserves_existing_profile_assets()

    def test_refresh_repo_rebuilds_config_when_missing(self):
        """Run test_refresh_repo_rebuilds_config_when_missing."""
        _unit_test_refresh_repo_rebuilds_config_when_missing()

    def test_refresh_repo_materializes_missing_profile_assets(self):
        """Run test_refresh_repo_materializes_missing_profile_assets."""
        _unit_test_refresh_repo_materializes_missing_profile_assets()

    def test_refresh_repo_preserves_existing_python_assets(self):
        """Run test_refresh_repo_preserves_existing_python_assets."""
        _unit_test_refresh_repo_preserves_existing_python_assets()

    def test_refresh_repo_emits_scalar_path_overrides(self):
        """Run test_refresh_repo_emits_scalar_path_overrides."""
        _unit_test_refresh_repo_emits_scalar_path_overrides()
