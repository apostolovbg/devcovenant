"""Tests for the semantic-version-scope policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.builtin.policies.semantic_version_scope import (
    semantic_version_scope,
)
from devcovenant.core.contracts.policy import CheckContext


def _write_version_files(
    tmp_path: Path,
    current_version: str,
    previous_version: str,
    marker: str,
) -> tuple[Path, Path, Path]:
    """Create VERSION and CHANGELOG fixtures."""
    version_file = tmp_path / "project_lib" / "VERSION"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(current_version, encoding="utf-8")

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                f"## Version {current_version}",
                marker,
                "",
                f"## Version {previous_version}",
                "- 2025-12-24 [semver:patch]: previous release",
            ]
        ),
        encoding="utf-8",
    )

    other_file = tmp_path / "project_lib" / "module.py"
    other_file.write_text("# helper\n", encoding="utf-8")
    return version_file, changelog, other_file


def _configured_policy() -> semantic_version_scope.SemanticVersionScopeCheck:
    """Return a policy configured for project_lib."""
    policy = semantic_version_scope.SemanticVersionScopeCheck()
    policy.set_options(
        {
            "version_file": "project_lib/VERSION",
            "ignored_prefixes": ["devcovenant"],
        },
        {},
    )
    return policy


def _unit_test_minor_marker_requires_minor_bump(tmp_path: Path) -> None:
    """A patch bump should fail when the changelog requests a minor bump."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.2.4",
        "1.2.3",
        "- 2025-12-28 [semver:minor]: latest release",
    )

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy()
    violations = check.check(context)

    assert violations
    assert any("minor" in violation.message for violation in violations)


def _unit_test_minor_bump_passes_with_matching_marker(tmp_path: Path) -> None:
    """A minor bump should pass when the changelog tags it as minor."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.3.0",
        "1.2.4",
        "- 2025-12-28 [semver:minor]: latest release",
    )

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy()

    assert check.check(context) == []


def _unit_test_missing_marker_requires_tag(tmp_path: Path) -> None:
    """Missing semver markers should trigger a violation."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "2.0.1",
        "2.0.0",
        "- 2025-12-28 no marker",
    )

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )

    check = _configured_policy()
    violations = check.check(context)

    assert violations
    assert any(
        "semver" in violation.message.lower() for violation in violations
    )


def _unit_test_policy_skips_when_only_devconvenant_changes(
    tmp_path: Path,
) -> None:
    """Changes scoped to devcovenant should not trigger version bumps."""
    version_file, _, _ = _write_version_files(
        tmp_path,
        "3.0.1",
        "3.0.0",
        "- 2025-12-28 [semver:patch]",
    )
    devcov_file = tmp_path / "devcovenant" / "engine.py"
    devcov_file.parent.mkdir(parents=True, exist_ok=True)
    devcov_file.write_text("# engine\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, devcov_file],
    )

    check = _configured_policy()
    assert check.check(context) == []


def _unit_test_requires_version_bump_when_changelog_changes(
    tmp_path: Path,
) -> None:
    """Changelog releases must update the version file."""
    _, changelog, other_file = _write_version_files(
        tmp_path,
        "4.0.0",
        "3.5.0",
        "- 2025-12-28 [semver:patch]: docs refresh",
    )

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[changelog, other_file],
    )
    check = _configured_policy()
    violations = check.check(context)

    assert violations
    assert any("VERSION was not updated" in v.message for v in violations)


def _unit_test_mixed_scope_markers_are_rejected(tmp_path: Path) -> None:
    """Multiple scope markers in one release cause a violation."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "5.0.0",
        "4.9.0",
        "- 2025-12-28 [semver:major]: breaking change\n"
        "- 2025-12-28 [semver:patch]: docs tweak",
    )

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy()
    violations = check.check(context)

    assert violations
    assert any("mixes multiple SemVer scopes" in v.message for v in violations)


def _unit_test_rejects_non_forward_version(tmp_path: Path) -> None:
    """Version file must advance beyond the previous changelog version."""
    version_file = tmp_path / "project_lib" / "VERSION"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text("1.0.0", encoding="utf-8")

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "## Version 1.0.0",
                "- 2025-12-28 [semver:patch]: attempted rollback",
                "",
                "## Version 1.0.1",
                "- 2025-12-24 [semver:patch]: prior release",
            ]
        ),
        encoding="utf-8",
    )
    changed_module = tmp_path / "project_lib" / "module.py"
    changed_module.write_text("# helper\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, changed_module],
    )
    check = _configured_policy()
    violations = check.check(context)

    assert violations
    assert any("must be greater than" in v.message for v in violations)


def _unit_test_ignores_managed_block_version_examples(tmp_path: Path) -> None:
    """Version parsing should ignore managed-block examples."""
    version_file = tmp_path / "project_lib" / "VERSION"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text("1.0.1", encoding="utf-8")

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "<!-- DEVCOV:BEGIN -->",
                "## How to Log Changes",
                "```",
                "## Version 9.9.9",
                "- 2026-01-23 [semver:major]: example only",
                "```",
                "<!-- DEVCOV:END -->",
                "",
                "## Log changes here",
                "",
                "## Version 1.0.1",
                "- 2026-02-15 [semver:patch]: bug fix",
                "",
                "## Version 1.0.0",
                "- 2026-02-14 [semver:patch]: first release",
            ]
        ),
        encoding="utf-8",
    )
    other_file = tmp_path / "project_lib" / "module.py"
    other_file.write_text("# helper\n", encoding="utf-8")

    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy()
    assert check.check(context) == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_minor_marker_requires_minor_bump(self):
        """Run test_minor_marker_requires_minor_bump."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_minor_marker_requires_minor_bump(tmp_path=tmp_path)

    def test_minor_bump_passes_with_matching_marker(self):
        """Run test_minor_bump_passes_with_matching_marker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_minor_bump_passes_with_matching_marker(
                tmp_path=tmp_path
            )

    def test_missing_marker_requires_tag(self):
        """Run test_missing_marker_requires_tag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_missing_marker_requires_tag(tmp_path=tmp_path)

    def test_policy_skips_when_only_devconvenant_changes(self):
        """Run test_policy_skips_when_only_devconvenant_changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_policy_skips_when_only_devconvenant_changes(
                tmp_path=tmp_path
            )

    def test_requires_version_bump_when_changelog_changes(self):
        """Run test_requires_version_bump_when_changelog_changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_requires_version_bump_when_changelog_changes(
                tmp_path=tmp_path
            )

    def test_mixed_scope_markers_are_rejected(self):
        """Run test_mixed_scope_markers_are_rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_mixed_scope_markers_are_rejected(tmp_path=tmp_path)

    def test_rejects_non_forward_version(self):
        """Run test_rejects_non_forward_version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_rejects_non_forward_version(tmp_path=tmp_path)

    def test_ignores_managed_block_version_examples(self):
        """Run test_ignores_managed_block_version_examples."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ignores_managed_block_version_examples(
                tmp_path=tmp_path
            )
