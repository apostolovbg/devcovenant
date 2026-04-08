"""Tests for the `devcovenant custom` command surface."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import devcovenant.custom as custom_command


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


def _build_policy_repo(repo_root: Path) -> None:
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


def _build_profile_repo(repo_root: Path) -> None:
    """Seed one builtin profile tree with shipped test blueprints."""
    profile_root = (
        repo_root / "devcovenant" / "builtin" / "profiles" / "demo_profile"
    )
    _write_text(profile_root / "demo_profile.yaml", _profile_descriptor())
    _write_text(profile_root / "test_blueprints.yaml", _profile_blueprints())


def _patch_custom_runtime(repo_root: Path):
    """Patch command runtime helpers for one isolated repository root."""
    return patch.multiple(
        "devcovenant.core.execution",
        resolve_repo_root=lambda require_install=True: repo_root,
        devcovenant_banner_title=lambda: "DevCovenant custom",
        print_banner=lambda *_args, **_kwargs: None,
        print_step=lambda *_args, **_kwargs: None,
    )


def _patch_refresh():
    """Patch refresh to avoid running the full repository refresh stack."""
    return patch(
        "devcovenant.core.refresh_runtime.refresh_repo",
        lambda _repo_root: 0,
    )


def _unit_test_custom_do_materializes_policy_copy_and_tests() -> None:
    """`custom --policy --do` should copy the builtin tree and tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _build_policy_repo(repo_root)
        with _patch_custom_runtime(repo_root), _patch_refresh():
            code = custom_command.run(
                SimpleNamespace(
                    policy_id="demo-policy",
                    profile_name=None,
                    do=True,
                    undo=False,
                )
            )

        assert code == 0
        custom_policy_root = (
            repo_root / "devcovenant" / "custom" / "policies" / "demo_policy"
        )
        custom_test_root = (
            repo_root
            / "tests"
            / "devcovenant"
            / "custom"
            / "policies"
            / "demo_policy"
        )
        assert (custom_policy_root / "demo_policy.py").exists()
        assert (custom_policy_root / "demo_policy.yaml").exists()
        assert (custom_policy_root / "test_blueprints.yaml").exists()
        assert (
            (custom_test_root / "__init__.py")
            .read_text(encoding="utf-8")
            .startswith('"""Demo policy tests.')
        )
        assert (
            (custom_test_root / "test_demo_policy.py")
            .read_text(encoding="utf-8")
            .startswith('"""Unit tests for demo policy."""')
        )


def _unit_test_custom_undo_removes_profile_copy_and_tests() -> None:
    """`custom --profile --undo` should remove custom trees and mirrors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _build_profile_repo(repo_root)
        custom_profile_root = (
            repo_root / "devcovenant" / "custom" / "profiles" / "demo_profile"
        )
        custom_tests_root = (
            repo_root
            / "tests"
            / "devcovenant"
            / "custom"
            / "profiles"
            / "demo_profile"
        )
        _write_text(custom_profile_root / "demo_profile.yaml", "custom\n")
        _write_text(custom_tests_root / "test_demo_profile.py", "custom\n")
        with _patch_custom_runtime(repo_root), _patch_refresh():
            code = custom_command.run(
                SimpleNamespace(
                    policy_id=None,
                    profile_name="demo_profile",
                    do=False,
                    undo=True,
                )
            )

        assert code == 0
        assert not custom_profile_root.exists()
        assert not custom_tests_root.exists()


class CustomCommandTests(unittest.TestCase):
    """unittest wrappers for custom-command checks."""

    def test_custom_do_materializes_policy_copy_and_tests(self):
        """Run policy-copy materialization assertions."""
        _unit_test_custom_do_materializes_policy_copy_and_tests()

    def test_custom_undo_removes_profile_copy_and_tests(self):
        """Run profile-copy removal assertions."""
        _unit_test_custom_undo_removes_profile_copy_and_tests()
