"""Tests for the builtin test blueprint sync policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.policy_contract import CheckContext
from devcovenant.custom.policies.builtin_test_blueprint_sync import (
    builtin_test_blueprint_sync as policy_module,
)

BuiltinTestBlueprintSyncCheck = policy_module.BuiltinTestBlueprintSyncCheck

MIRROR_ROOTS = [
    "devcovenant/builtin=>tests/devcovenant/builtin",
    "devcovenant/custom=>tests/devcovenant/custom",
]


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


def _policy_tree_root(repo_root: Path, kind: str) -> Path:
    """Return one policy tree root for builtin or custom content."""
    return repo_root / "devcovenant" / kind / "policies" / "demo_policy"


def _policy_test_root(repo_root: Path, kind: str) -> Path:
    """Return one policy test mirror root for builtin or custom content."""
    return (
        repo_root / "tests" / "devcovenant" / kind / "policies" / "demo_policy"
    )


def _profile_tree_root(repo_root: Path, kind: str) -> Path:
    """Return one profile tree root for builtin or custom content."""
    return repo_root / "devcovenant" / kind / "profiles" / "demo_profile"


def _profile_test_root(repo_root: Path, kind: str) -> Path:
    """Return one profile test mirror root for builtin or custom content."""
    return (
        repo_root
        / "tests"
        / "devcovenant"
        / kind
        / "profiles"
        / "demo_profile"
    )


def _seed_policy_repo(repo_root: Path, kind: str) -> None:
    """Seed one policy tree with shipped test blueprints and tests."""
    policy_root = _policy_tree_root(repo_root, kind)
    test_root = _policy_test_root(repo_root, kind)
    _write_text(
        policy_root / "demo_policy.py",
        "class DemoPolicyCheck:\n" "    pass\n",
    )
    _write_text(policy_root / "demo_policy.yaml", _policy_descriptor())
    _write_text(policy_root / "test_blueprints.yaml", _policy_blueprints())
    _write_text(test_root / "__init__.py", '"""Demo policy tests."""\n')
    _write_text(
        test_root / "test_demo_policy.py",
        (
            '"""Unit tests for demo policy."""\n'
            "from __future__ import annotations\n\n"
            "def test_demo_policy_placeholder():\n"
            "    assert True\n"
        ),
    )


def _seed_profile_repo(repo_root: Path, kind: str) -> None:
    """Seed one profile tree with shipped test blueprints and tests."""
    profile_root = _profile_tree_root(repo_root, kind)
    test_root = _profile_test_root(repo_root, kind)
    _write_text(profile_root / "demo_profile.yaml", _profile_descriptor())
    _write_text(profile_root / "test_blueprints.yaml", _profile_blueprints())
    _write_text(test_root / "__init__.py", '"""Demo profile tests."""\n')
    _write_text(
        test_root / "test_demo_profile.py",
        (
            '"""Unit tests for demo profile."""\n'
            "from __future__ import annotations\n\n"
            "def test_demo_profile_placeholder():\n"
            "    assert True\n"
        ),
    )


def _seed_blueprint_repo(repo_root: Path) -> None:
    """Create builtin and custom trees with matching blueprint mirrors."""
    _seed_policy_repo(repo_root, "builtin")
    _seed_policy_repo(repo_root, "custom")
    _seed_profile_repo(repo_root, "builtin")
    _seed_profile_repo(repo_root, "custom")


def _check_options() -> dict[str, object]:
    """Return the metadata options needed by the sync policy."""
    return {
        "mirror_roots": MIRROR_ROOTS,
        "blueprint_directories": [
            "policies/demo_policy",
            "profiles/demo_profile",
        ],
        "blueprint_name": "test_blueprints.yaml",
    }


def _unit_test_policy_passes_when_mirrors_match_blueprints() -> None:
    """Policy should pass when every mirrored tree matches its blueprint."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _seed_blueprint_repo(repo_root)
        check = BuiltinTestBlueprintSyncCheck()
        check.set_options(_check_options(), {})
        violations = check.check(CheckContext(repo_root=repo_root))
        assert violations == []


def _unit_test_policy_flags_custom_mirror_content_drift() -> None:
    """Policy should reject diverged custom mirrors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _seed_blueprint_repo(repo_root)
        _write_text(
            _profile_test_root(repo_root, "custom") / "test_demo_profile.py",
            "different\n",
        )
        check = BuiltinTestBlueprintSyncCheck()
        check.set_options(_check_options(), {})
        violations = check.check(CheckContext(repo_root=repo_root))
        assert violations
        assert any(
            "out of sync" in violation.message.lower()
            or "does not describe" in violation.message.lower()
            for violation in violations
        )


class BuiltinTestBlueprintSyncTests(unittest.TestCase):
    """unittest wrappers for the policy sync checks."""

    def test_policy_passes_when_mirrors_match_blueprints(self):
        """Run mirrored-tree blueprint sync pass assertions."""
        _unit_test_policy_passes_when_mirrors_match_blueprints()

    def test_policy_flags_custom_mirror_content_drift(self):
        """Run custom-mirror drift rejection assertions."""
        _unit_test_policy_flags_custom_mirror_content_drift()
