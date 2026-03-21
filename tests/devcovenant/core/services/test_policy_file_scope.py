"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from tests.devcovenant.support import MonkeyPatch

MODULE = "devcovenant.core.services.policy_file_scope"


def _unit_test_module_importable() -> None:
    """Module should import without engine wrappers."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_symbol_contract_is_stable() -> None:
    """File-scope helper seam symbols should remain callable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "collect_all_files",
        "config_ignore_patterns",
        "configured_ignore_dir_names",
        "core_exclusion_paths",
        "discover_custom_policy_overrides",
        "is_ignored_path",
        "matches_config_ignore_pattern",
        "profile_ignored_dir_names",
        "resolve_engine_file_suffixes",
        "should_descend_dir",
    ]:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))


def _unit_test_symbol_assertions_cover_file_scope_seam() -> None:
    """Tests should assert each file-scope helper seam symbol directly."""
    module = importlib.import_module(MODULE)
    assert module.collect_all_files
    assert module.config_ignore_patterns
    assert module.configured_ignore_dir_names
    assert module.core_exclusion_paths
    assert module.discover_custom_policy_overrides
    assert module.is_ignored_path
    assert module.matches_config_ignore_pattern
    assert module.profile_ignored_dir_names
    assert module.resolve_engine_file_suffixes
    assert module.should_descend_dir


def _unit_test_config_ignore_patterns_normalize_comments_and_dirs() -> None:
    """Config ignore patterns should normalize separators and dir markers."""
    module = importlib.import_module(MODULE)
    config = {
        "ignore": {
            "patterns": [
                " docs/generated/ ",
                "#comment",
                r"tmp\cache" "\\",
                "",
            ]
        }
    }
    assert module.config_ignore_patterns(config) == [
        "docs/generated/**",
        "tmp/cache/**",
    ]


def _unit_test_matches_config_ignore_pattern_matches_dir_token() -> None:
    """Pattern matcher should treat `foo/**` as matching `foo` too."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    patterns = ["docs/generated/**"]
    assert (
        module.matches_config_ignore_pattern(
            repo_root,
            repo_root / "docs" / "generated",
            patterns,
        )
        is True
    )
    assert (
        module.matches_config_ignore_pattern(
            repo_root,
            repo_root / "docs" / "generated" / "page.md",
            patterns,
        )
        is True
    )
    assert (
        module.matches_config_ignore_pattern(
            repo_root,
            repo_root / "docs" / "guide.md",
            patterns,
        )
        is False
    )


def _unit_test_core_exclusion_paths_respect_include_toggle() -> None:
    """Core exclusion helper should honor `developer_mode`."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    disabled = module.core_exclusion_paths(
        repo_root,
        {
            "developer_mode": False,
            "profiles": {
                "generated": {
                    "devcov_core_paths": [
                        "devcovenant/core",
                        "devcovenant/builtin",
                    ]
                }
            },
        },
    )
    enabled = module.core_exclusion_paths(
        repo_root,
        {"developer_mode": True},
    )
    assert disabled == [
        repo_root / "devcovenant/core",
        repo_root / "devcovenant/builtin",
    ]
    assert enabled == []


def _unit_test_discover_custom_policy_overrides_finds_script_dirs() -> None:
    """Custom policy override discovery should require matching script file."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        custom_root = repo_root / "devcovenant" / "custom" / "policies"
        demo_dir = custom_root / "demo_policy"
        empty_dir = custom_root / "empty_policy"
        demo_dir.mkdir(parents=True)
        empty_dir.mkdir(parents=True)
        (demo_dir / "demo_policy.py").write_text("# demo\n", encoding="utf-8")
        overrides = module.discover_custom_policy_overrides(repo_root)
    assert overrides == {"demo-policy"}


def _unit_test_is_ignored_path_checks_patterns_names_and_prefixes() -> None:
    """Ignore helper should apply pattern/name/prefix ignore rules."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    ignored_dirs = {"node_modules"}
    ignored_paths = [repo_root / "build"]
    patterns = ["docs/generated/**"]
    assert (
        module.is_ignored_path(
            repo_root / "docs" / "generated" / "out.md",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "site" / "node_modules" / "x.js",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "build" / "artifact.py",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is True
    )
    assert (
        module.is_ignored_path(
            repo_root / "src" / "main.py",
            repo_root=repo_root,
            ignored_dirs=ignored_dirs,
            ignored_paths=ignored_paths,
            config_ignore_patterns=patterns,
        )
        is False
    )


def _unit_test_profile_ignored_dir_names_normalize_entries() -> None:
    """Profile ignore-dir helper should normalize resolver output."""
    module = importlib.import_module(MODULE)
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "resolve_profile_ignore_dirs",
            lambda _registry, _profiles: [" build ", "", "tmp"],
        )
        result = module.profile_ignored_dir_names({}, ["global"])
    finally:
        monkeypatch.undo()
    assert result == ["build", "tmp"]


def _unit_test_resolve_engine_file_suffixes_merges_and_cleans() -> None:
    """Suffix helper should merge configured and profile suffixes."""
    module = importlib.import_module(MODULE)
    monkeypatch = MonkeyPatch()
    try:
        monkeypatch.setattr(
            module,
            "resolve_profile_suffixes",
            lambda _registry, _profiles: [".json", "  ", ".toml"],
        )
        suffixes = module.resolve_engine_file_suffixes(
            {"engine": {"file_suffixes": [".py", " .md ", ""]}},
            {},
            ["global"],
        )
    finally:
        monkeypatch.undo()
    assert suffixes == [".py", ".md", ".json", ".toml"]


def _unit_test_should_descend_dir_skips_ignored_and_pycache() -> None:
    """Walk helper should skip ignored names, patterns, and pycache dirs."""
    module = importlib.import_module(MODULE)
    repo_root = Path("/tmp/devcovenant")
    common_kwargs = {
        "repo_root": repo_root,
        "ignored_dirs": {"node_modules"},
        "ignored_paths": [repo_root / "build"],
        "config_ignore_patterns": ["docs/generated/**"],
    }
    assert (
        module.should_descend_dir(repo_root / "node_modules", **common_kwargs)
        is False
    )
    assert (
        module.should_descend_dir(
            repo_root / "docs" / "generated",
            **common_kwargs,
        )
        is False
    )
    assert (
        module.should_descend_dir(
            repo_root / "__pycache__",
            **common_kwargs,
        )
        is False
    )
    assert (
        module.should_descend_dir(repo_root / "src", **common_kwargs) is True
    )


def _unit_test_collect_all_files_honors_ignore_rules() -> None:
    """File collection should honor suffix filters and ignore helpers."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / "build").mkdir()
        (repo_root / "tmp").mkdir()
        (repo_root / "node_modules").mkdir()
        (repo_root / "pkg" / "__pycache__").mkdir(parents=True)
        (repo_root / "src" / "main.py").write_text("x=1\n", encoding="utf-8")
        (repo_root / "docs" / "guide.md").write_text(
            "# guide\n",
            encoding="utf-8",
        )
        (repo_root / "build" / "skip.py").write_text("x=1\n", encoding="utf-8")
        (repo_root / "tmp" / "skip.yml").write_text("a: 1\n", encoding="utf-8")
        (repo_root / "node_modules" / "skip.py").write_text(
            "x=1\n",
            encoding="utf-8",
        )
        (repo_root / "pkg" / "__pycache__" / "skip.py").write_text(
            "x=1\n",
            encoding="utf-8",
        )
        matched = module.collect_all_files(
            repo_root,
            {".py", ".md", ".yml"},
            ignored_dirs={"node_modules"},
            ignored_paths=[repo_root / "build"],
            config_ignore_patterns=["tmp/**"],
        )
    rel = sorted(path.relative_to(repo_root).as_posix() for path in matched)
    assert rel == ["docs/guide.md", "src/main.py"]


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for policy file-scope helper checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_symbol_contract_is_stable(self):
        """Run file-scope helper symbol contract assertions."""
        _unit_test_symbol_contract_is_stable()

    def test_symbol_assertions_cover_file_scope_seam(self):
        """Run explicit file-scope helper symbol assertions."""
        _unit_test_symbol_assertions_cover_file_scope_seam()

    def test_config_ignore_patterns_normalize_comments_and_dirs(self):
        """Run config-ignore normalization assertions."""
        _unit_test_config_ignore_patterns_normalize_comments_and_dirs()

    def test_matches_config_ignore_pattern_matches_dir_token(self):
        """Run config-ignore pattern matching assertions."""
        _unit_test_matches_config_ignore_pattern_matches_dir_token()

    def test_core_exclusion_paths_respect_include_toggle(self):
        """Run core-exclusion path toggle assertions."""
        _unit_test_core_exclusion_paths_respect_include_toggle()

    def test_discover_custom_policy_overrides_finds_script_dirs(self):
        """Run custom-policy override discovery assertions."""
        _unit_test_discover_custom_policy_overrides_finds_script_dirs()

    def test_is_ignored_path_checks_patterns_names_and_prefixes(self):
        """Run ignore-path helper rule assertions."""
        _unit_test_is_ignored_path_checks_patterns_names_and_prefixes()

    def test_profile_ignored_dir_names_normalize_entries(self):
        """Run profile ignore-dir normalization assertions."""
        _unit_test_profile_ignored_dir_names_normalize_entries()

    def test_resolve_engine_file_suffixes_merges_and_cleans(self):
        """Run suffix merge/cleanup helper assertions."""
        _unit_test_resolve_engine_file_suffixes_merges_and_cleans()

    def test_should_descend_dir_skips_ignored_and_pycache(self):
        """Run directory-walk decision helper assertions."""
        _unit_test_should_descend_dir_skips_ignored_and_pycache()

    def test_collect_all_files_honors_ignore_rules(self):
        """Run file collection helper ignore/suffix assertions."""
        _unit_test_collect_all_files_honors_ignore_rules()
