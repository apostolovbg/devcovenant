"""
Tests for the devcovenant engine.
"""

import tempfile
from pathlib import Path

from devcovenant.core.engine import DevCovenantEngine


def test_engine_initialization():
    """Test that the engine initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir).resolve()

        # Create minimal structure
        (repo_root / "devcovenant").mkdir()
        (repo_root / "AGENTS.md").write_text("# Test")

        engine = DevCovenantEngine(repo_root=repo_root)

        assert engine.repo_root == repo_root
        assert engine.agents_md_path.exists()


def test_engine_check_no_violations():
    """Test engine check with no violations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create structure
        devcov_dir = repo_root / "devcovenant"
        devcov_dir.mkdir()
        (devcov_dir / "core" / "policies" / "test_policy").mkdir(parents=True)
        config_text = "engine:\n  fail_threshold: error"
        (devcov_dir / "config.yaml").write_text(config_text)

        # Create AGENTS.md with no policies
        agents_text = "# Development Guide\n\nNo policies yet."
        (repo_root / "AGENTS.md").write_text(agents_text)

        engine = DevCovenantEngine(repo_root=repo_root)
        result = engine.check(mode="normal")

        # Should have no violations and not block
        assert result.should_block is False


def test_engine_respects_profile_ignore_dirs(tmp_path: Path) -> None:
    """Profile ignore_dirs should exclude matching paths."""
    repo_root = tmp_path
    devcov_dir = repo_root / "devcovenant"
    profile_dir = devcov_dir / "custom" / "profiles" / "demo"
    profile_dir.mkdir(parents=True)
    profile_manifest = (
        "version: 1\n"
        "profile: demo\n"
        "category: custom\n"
        "suffixes: []\n"
        "ignore_dirs:\n"
        "  - vendor\n"
        "policies: []\n"
    )
    (profile_dir / "demo.yaml").write_text(profile_manifest, encoding="utf-8")
    (devcov_dir / "config.yaml").write_text(
        "profiles:\n  active:\n    - demo\n",
        encoding="utf-8",
    )
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")

    engine = DevCovenantEngine(repo_root=repo_root)
    assert engine._is_ignored_path(repo_root / "vendor" / "file.py")
    assert not engine._is_ignored_path(repo_root / "src" / "file.py")


def test_custom_override_skips_core_fixers(tmp_path: Path) -> None:
    """Core fixers should be skipped when a custom override exists."""
    repo_root = tmp_path
    (
        repo_root / "devcovenant" / "custom" / "policies" / "no_future_dates"
    ).mkdir(parents=True)
    (
        repo_root
        / "devcovenant"
        / "custom"
        / "policies"
        / "no_future_dates"
        / "no_future_dates.py"
    ).write_text("# custom override\n", encoding="utf-8")
    (repo_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")

    engine = DevCovenantEngine(repo_root=repo_root)
    core_fixers = [
        fixer
        for fixer in engine.fixers
        if fixer.policy_id == "no-future-dates"
        and getattr(fixer, "_origin", "") == "core"
    ]
    assert not core_fixers
