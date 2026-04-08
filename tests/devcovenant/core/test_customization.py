"""Tests for builtin-to-custom path and mirror helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import devcovenant.core.customization as customization_service


def _write_text(path: Path, content: str) -> None:
    """Write one text file and create parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _policy_descriptor() -> str:
    """Return one builtin policy descriptor fixture."""
    return (
        "id: demo-policy\n"
        "text: |\n"
        "  Demo policy text.\n"
        "metadata:\n"
        "  id: demo-policy\n"
    )


def _profile_descriptor() -> str:
    """Return one builtin profile descriptor fixture."""
    return "version: 1\nprofile: demo_profile\ncategory: repo\n"


def _policy_blueprints() -> str:
    """Return one builtin policy test-blueprint fixture."""
    return (
        "test_blueprints:\n"
        "  - path: __init__.py\n"
        "    content: |\n"
        '      """Demo policy tests."""\n'
        "  - path: test_demo_policy.py\n"
        "    content: |\n"
        '      """Unit tests for demo policy."""\n'
        "      from __future__ import annotations\n"
        "\n"
        "      def test_demo_policy_placeholder():\n"
        "          assert True\n"
    )


def _profile_blueprints() -> str:
    """Return one builtin profile test-blueprint fixture."""
    return (
        "test_blueprints:\n"
        "  - path: __init__.py\n"
        "    content: |\n"
        '      """Demo profile tests."""\n'
        "  - path: test_demo_profile.py\n"
        "    content: |\n"
        '      """Unit tests for demo profile."""\n'
        "      from __future__ import annotations\n"
        "\n"
        "      def test_demo_profile_placeholder():\n"
        "          assert True\n"
    )


def _seed_policy_repo(repo_root: Path) -> None:
    """Seed one builtin policy tree with shipped test blueprints."""
    policy_root = (
        repo_root / "devcovenant" / "builtin" / "policies" / "demo_policy"
    )
    _write_text(
        policy_root / "demo_policy.py",
        "class DemoPolicyCheck:\n" "    pass\n",
    )
    _write_text(policy_root / "demo_policy.yaml", _policy_descriptor())
    _write_text(policy_root / "test_blueprints.yaml", _policy_blueprints())
    _write_text(
        repo_root
        / "tests"
        / "devcovenant"
        / "builtin"
        / "policies"
        / "demo_policy"
        / "__init__.py",
        '"""Demo policy tests."""\n',
    )
    _write_text(
        repo_root
        / "tests"
        / "devcovenant"
        / "builtin"
        / "policies"
        / "demo_policy"
        / "test_demo_policy.py",
        (
            '"""Unit tests for demo policy."""\n'
            "from __future__ import annotations\n\n"
            "def test_demo_policy_placeholder():\n"
            "    assert True\n"
        ),
    )


def _seed_profile_repo(repo_root: Path) -> None:
    """Seed one builtin profile tree with shipped test blueprints."""
    profile_root = (
        repo_root / "devcovenant" / "builtin" / "profiles" / "demo_profile"
    )
    _write_text(profile_root / "demo_profile.yaml", _profile_descriptor())
    _write_text(profile_root / "test_blueprints.yaml", _profile_blueprints())
    _write_text(
        repo_root
        / "tests"
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "demo_profile"
        / "__init__.py",
        '"""Demo profile tests."""\n',
    )
    _write_text(
        repo_root
        / "tests"
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "demo_profile"
        / "test_demo_profile.py",
        (
            '"""Unit tests for demo profile."""\n'
            "from __future__ import annotations\n\n"
            "def test_demo_profile_placeholder():\n"
            "    assert True\n"
        ),
    )


def _unit_test_resolve_customization_paths_returns_expected_roots() -> None:
    """Path resolution should normalize builtin and custom directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        resolved_root = repo_root.resolve()
        policy_paths = customization_service.resolve_customization_paths(
            repo_root,
            kind="policy",
            name="Demo-Policy",
        )
        profile_paths = customization_service.resolve_customization_paths(
            repo_root,
            kind="profile",
            name="DemoProfile",
        )

        assert policy_paths.name == "demo_policy"
        assert policy_paths.builtin_source_root == (
            resolved_root
            / "devcovenant"
            / "builtin"
            / "policies"
            / "demo_policy"
        )
        assert policy_paths.custom_source_root == (
            resolved_root
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo_policy"
        )
        assert policy_paths.builtin_test_root == (
            resolved_root
            / "tests"
            / "devcovenant"
            / "builtin"
            / "policies"
            / "demo_policy"
        )
        assert policy_paths.custom_test_root == (
            resolved_root
            / "tests"
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo_policy"
        )

        assert profile_paths.name == "demoprofile"
        assert profile_paths.builtin_source_root == (
            resolved_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "demoprofile"
        )
        assert profile_paths.custom_source_root == (
            resolved_root
            / "devcovenant"
            / "custom"
            / "profiles"
            / "demoprofile"
        )


def _unit_test_copy_and_remove_customization_tree() -> None:
    """Copy and removal helpers should manage repo-owned shadow trees."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _seed_policy_repo(repo_root)
        paths = customization_service.resolve_customization_paths(
            repo_root,
            kind="policy",
            name="demo-policy",
        )

        assert customization_service.copy_builtin_customization(paths)
        assert (paths.custom_source_root / "demo_policy.py").exists()
        assert (paths.custom_source_root / "test_blueprints.yaml").exists()
        assert customization_service.remove_customization(paths)
        assert not paths.custom_source_root.exists()


def _unit_test_materialize_and_remove_custom_tests() -> None:
    """Blueprint helpers should materialize and remove custom test mirrors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _seed_profile_repo(repo_root)
        paths = customization_service.resolve_customization_paths(
            repo_root,
            kind="profile",
            name="demo_profile",
        )

        written = customization_service.materialize_custom_tests(paths)
        assert written
        assert (paths.custom_test_root / "__init__.py").exists()
        assert (paths.custom_test_root / "test_demo_profile.py").exists()
        assert customization_service.remove_custom_tests(paths)
        assert not paths.custom_test_root.exists()


class CustomizationHelperTests(unittest.TestCase):
    """unittest wrappers for customization-helper checks."""

    def test_resolve_customization_paths_returns_expected_roots(self):
        """Run path-resolution assertions."""
        _unit_test_resolve_customization_paths_returns_expected_roots()

    def test_copy_and_remove_customization_tree(self):
        """Run custom-tree copy and removal assertions."""
        _unit_test_copy_and_remove_customization_tree()

    def test_materialize_and_remove_custom_tests(self):
        """Run blueprint mirror materialization assertions."""
        _unit_test_materialize_and_remove_custom_tests()
