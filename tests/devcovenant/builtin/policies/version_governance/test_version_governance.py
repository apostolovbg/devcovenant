"""Tests for the version-governance policy."""

import tempfile
import unittest
from pathlib import Path

import yaml

from devcovenant.builtin.policies.version_governance import version_governance
from devcovenant.core.contracts.policy import CheckContext


def _write_version_files(
    tmp_path: Path,
    current_version: str,
    previous_version: str,
    latest_lines: str,
    *,
    header_prefix: str = "## Version",
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
                f"{header_prefix} {current_version}",
                latest_lines,
                "",
                f"{header_prefix} {previous_version}",
                "- 2025-12-24 [semver:patch]: previous release",
            ]
        ),
        encoding="utf-8",
    )

    other_file = tmp_path / "project_lib" / "module.py"
    other_file.write_text("# helper\n", encoding="utf-8")
    return version_file, changelog, other_file


def _configured_policy(
    **overrides,
) -> version_governance.VersionGovernanceCheck:
    """Return a version-governance policy configured for project_lib."""
    policy = version_governance.VersionGovernanceCheck()
    options = {
        "version_file": "project_lib/VERSION",
        "changelog_file": "CHANGELOG.md",
        "changelog_header_prefix": "## Version",
        "scheme": "semver",
        "enforce_bumping": True,
        "semver_scope_tags_required": True,
        "ignored_prefixes": ["devcovenant"],
    }
    options.update(overrides)
    policy.set_options(options, {})
    return policy


def _repo_root() -> Path:
    """Return the repository root for runtime-resolution tests."""
    return Path(__file__).resolve().parents[5]


def _unit_test_common_interface_exposes_scheme_contract() -> None:
    """Shared policy module should expose the scheme contract types."""
    versionreleasecontext = version_governance.VersionReleaseContext
    release = version_governance.VersionReleaseContext(
        repo_root=Path("."),
        policy_id="version-governance",
        version_label="project_lib/VERSION",
        version_path=Path("project_lib/VERSION"),
        changelog_path=Path("CHANGELOG.md"),
        changed_files=[Path("project_lib/VERSION"), Path("CHANGELOG.md")],
        latest_block="## Version 1.0.1",
        current_version="1.0.1",
        current_parsed="current",
        previous_version="1.0.0",
        previous_parsed="previous",
    )
    assert versionreleasecontext is version_governance.VersionReleaseContext
    assert release.version_label == "project_lib/VERSION"
    assert "preflight" in version_governance.VersionScheme.__dict__
    assert "version_pattern" in version_governance.VersionScheme.__dict__
    assert "parse_version" in version_governance.VersionScheme.__dict__
    assert "compare_versions" in version_governance.VersionScheme.__dict__
    assert "validate_release" in version_governance.VersionScheme.__dict__
    assert issubclass(version_governance.VersionGovernanceCheck, object)


def _unit_test_runtime_check_resolves_effective_options() -> None:
    """Runtime helper should build one configured governance checker."""
    repo_root = _repo_root()
    config_payload = yaml.safe_load(
        (repo_root / "devcovenant" / "config.yaml").read_text(encoding="utf-8")
    )
    assert version_governance.resolve_runtime_check is not None
    check = version_governance.resolve_runtime_check(
        repo_root,
        config_payload=config_payload,
    )
    assert isinstance(check, version_governance.VersionGovernanceCheck)
    assert check.get_option("version_file") == "devcovenant/VERSION"
    assert check._scheme_name() == "semver"


def _unit_test_runtime_scheme_resolves_override_scheme() -> None:
    """Runtime helper should expose the configured adapter identity."""
    repo_root = _repo_root()
    config_payload = yaml.safe_load(
        (repo_root / "devcovenant" / "config.yaml").read_text(encoding="utf-8")
    )
    overrides = config_payload.setdefault("user_metadata_overrides", {})
    overrides["version-governance"] = {
        "scheme": "pep440",
        "enforce_bumping": "false",
    }
    assert version_governance.resolve_runtime_scheme is not None
    scheme_name, scheme, check = version_governance.resolve_runtime_scheme(
        repo_root,
        config_payload=config_payload,
    )
    assert scheme_name == "pep440"
    assert scheme.name == "pep440"
    assert check._scheme_name() == "pep440"


def _unit_test_runtime_scheme_requires_explicit_scheme() -> None:
    """Runtime helper should fail when no governance scheme is configured."""
    repo_root = _repo_root()
    config_payload = yaml.safe_load(
        (repo_root / "devcovenant" / "config.yaml").read_text(encoding="utf-8")
    )
    overrides = config_payload.setdefault("user_metadata_overrides", {})
    overrides["version-governance"] = {
        "scheme": "",
    }
    try:
        version_governance.resolve_runtime_scheme(
            repo_root,
            config_payload=config_payload,
        )
    except ValueError as error:
        message = str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError(
            "Expected version-governance scheme resolution to fail."
        )
    assert "version-governance.scheme" in message


def _unit_test_semver_minor_marker_requires_minor_bump(tmp_path: Path) -> None:
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


def _unit_test_semver_minor_bump_passes_with_matching_marker(
    tmp_path: Path,
) -> None:
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


def _unit_test_missing_semver_marker_requires_tag(tmp_path: Path) -> None:
    """Missing semver markers should trigger a violation when required."""
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


def _unit_test_semver_marker_is_optional_without_bump_enforcement(
    tmp_path: Path,
) -> None:
    """Format-only semver mode should not require semver scope tags."""
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
    check = _configured_policy(
        enforce_bumping=False,
        semver_scope_tags_required=False,
    )
    assert check.check(context) == []


def _unit_test_policy_skips_when_only_ignored_prefix_changes(
    tmp_path: Path,
) -> None:
    """Changes scoped to ignored prefixes should not trigger version checks."""
    version_file, _, _ = _write_version_files(
        tmp_path,
        "3.0.1",
        "3.0.0",
        "- 2025-12-28 [semver:patch]",
    )
    ignored_file = tmp_path / "devcovenant" / "engine.py"
    ignored_file.parent.mkdir(parents=True, exist_ok=True)
    ignored_file.write_text("# engine\n", encoding="utf-8")
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, ignored_file],
    )
    check = _configured_policy()
    assert check.check(context) == []


def _unit_test_requires_version_bump_when_changelog_changes(
    tmp_path: Path,
) -> None:
    """SemVer release tags still require the version file to move too."""
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
    assert any("version file alongside" in v.message for v in violations)


def _unit_test_mixed_semver_scope_markers_are_rejected(tmp_path: Path) -> None:
    """Multiple semver scope markers in one release cause a violation."""
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


def _unit_test_rejects_non_forward_version_when_bumping_enabled(
    tmp_path: Path,
) -> None:
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


def _unit_test_calver_bump_passes_without_semver_markers(
    tmp_path: Path,
) -> None:
    """CalVer should validate format and forward bumping without tags."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "2026.03.16",
        "2026.03.15",
        "- 2026-03-16: daily release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="calver",
        enforce_bumping=True,
        semver_scope_tags_required=False,
    )
    assert check.check(context) == []


def _unit_test_calver_invalid_format_is_rejected(tmp_path: Path) -> None:
    """CalVer mode should reject non-calver version strings."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.2.3",
        "2026.03.15",
        "- 2026-03-16: invalid format",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="calver",
        enforce_bumping=False,
        semver_scope_tags_required=False,
    )
    violations = check.check(context)
    assert violations
    assert any(
        "calver" in violation.message.lower() for violation in violations
    )


def _unit_test_integer_bump_passes(tmp_path: Path) -> None:
    """Integer versioning should accept forward numeric bumps."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "43",
        "42",
        "- 2026-03-16: build release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="integer",
        enforce_bumping=True,
        semver_scope_tags_required=False,
    )
    assert check.check(context) == []


def _unit_test_pep440_prerelease_bump_passes(tmp_path: Path) -> None:
    """PEP 440 should accept forward prerelease progression."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.2.0rc1",
        "1.2.0b3",
        "- 2026-03-16: prerelease candidate",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="pep440",
        enforce_bumping=True,
        semver_scope_tags_required=False,
    )
    assert check.check(context) == []


def _unit_test_pep440_invalid_format_is_rejected(tmp_path: Path) -> None:
    """PEP 440 mode should reject non-PEP 440 strings."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "3.4.8v6",
        "3.4.8",
        "- 2026-03-16: invalid pep440",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="pep440",
        enforce_bumping=False,
        semver_scope_tags_required=False,
    )
    violations = check.check(context)
    assert violations
    assert any(
        "pep440" in violation.message.lower() for violation in violations
    )


def _write_custom_adapter_module(tmp_path: Path) -> Path:
    """Create one repo-local Roman numeral adapter module."""
    module_path = tmp_path / "project_lib" / "roman_scheme.py"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(
        "\n".join(
            [
                '"""Roman numeral adapter fixture for tests."""',
                "",
                "_ROMAN_DIGITS = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}",
                "",
                "",
                "def _roman_to_int(token: str) -> int:",
                "    total = 0",
                "    previous = 0",
                "    for char in reversed(token):",
                "        value = _ROMAN_DIGITS[char]",
                "        if value < previous:",
                "            total -= value",
                "        else:",
                "            total += value",
                "            previous = value",
                "    return total",
                "",
                "",
                "class RomanScheme:",
                '    name = "roman"',
                "",
                "    def preflight(self, check, repo_root, version_path):",
                "        return []",
                "",
                "    def version_pattern(self, check, repo_root):",
                '        return r"[IVXLC]+"',
                "",
                "    def parse_version(self, value, check, repo_root):",
                "        return _roman_to_int(str(value or '').strip())",
                "",
                "    def compare_versions(self, left, right):",
                "        if left < right:",
                "            return -1",
                "        if left > right:",
                "            return 1",
                "        return 0",
                "",
                "    def validate_release(self, check, release):",
                "        return []",
                "",
                "",
                "SCHEME = RomanScheme()",
            ]
        ),
        encoding="utf-8",
    )
    return module_path


def _unit_test_custom_regex_accepts_roman_format(tmp_path: Path) -> None:
    """custom_regex should validate exotic formats when bumping is off."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "IV",
        "III",
        "- 2026-03-16: roman release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="custom_regex",
        enforce_bumping=False,
        semver_scope_tags_required=False,
        custom_regex_pattern=r"[IVXLC]+",
    )
    assert check.check(context) == []


def _unit_test_custom_regex_rejects_bump_enforcement(
    tmp_path: Path,
) -> None:
    """custom_regex should fail when ordered bump enforcement is requested."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "IV",
        "III",
        "- 2026-03-16: roman release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="custom_regex",
        enforce_bumping=True,
        semver_scope_tags_required=False,
        custom_regex_pattern=r"[IVXLC]+",
    )
    violations = check.check(context)
    assert violations
    assert any("custom_adapter" in v.message for v in violations)


def _unit_test_custom_adapter_accepts_roman_bump(tmp_path: Path) -> None:
    """custom_adapter should allow repo-local ordering rules."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "IV",
        "III",
        "- 2026-03-16: roman release",
    )
    adapter_path = _write_custom_adapter_module(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file, adapter_path],
    )
    check = _configured_policy(
        scheme="custom_adapter",
        enforce_bumping=True,
        semver_scope_tags_required=False,
        custom_adapter_path="project_lib/roman_scheme.py",
    )
    assert check.check(context) == []


def _unit_test_int_alias_resolves_to_integer_scheme(tmp_path: Path) -> None:
    """`int` should normalize to the integer versioning adapter."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "43",
        "42",
        "- 2026-03-16: build release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="int",
        enforce_bumping=True,
        semver_scope_tags_required=False,
    )
    assert check.check(context) == []


def _unit_test_requires_explicit_scheme_when_enabled(tmp_path: Path) -> None:
    """Enabled governance should fail clearly when scheme is omitted."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.0.0",
        "0.9.0",
        "- 2026-03-16: release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="",
        enforce_bumping=False,
        semver_scope_tags_required=False,
    )
    violations = check.check(context)
    assert violations
    assert any("version-governance.scheme" in v.message for v in violations)


def _unit_test_unsupported_scheme_is_rejected(tmp_path: Path) -> None:
    """Unsupported scheme names should fail explicitly."""
    version_file, changelog, other_file = _write_version_files(
        tmp_path,
        "1.0.0",
        "0.9.0",
        "- 2026-03-16: release",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[version_file, changelog, other_file],
    )
    check = _configured_policy(
        scheme="dragonfruit",
        enforce_bumping=False,
        semver_scope_tags_required=False,
    )
    violations = check.check(context)
    assert violations
    assert any(
        "Unsupported version-governance scheme" in v.message
        for v in violations
    )


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_common_interface_exposes_scheme_contract(self):
        """Run shared policy-contract coverage."""
        _unit_test_common_interface_exposes_scheme_contract()

    def test_runtime_check_resolves_effective_options(self):
        """Run runtime checker-resolution coverage."""
        _unit_test_runtime_check_resolves_effective_options()

    def test_runtime_scheme_resolves_override_scheme(self):
        """Run runtime scheme-resolution coverage."""
        _unit_test_runtime_scheme_resolves_override_scheme()

    def test_runtime_scheme_requires_explicit_scheme(self):
        """Run explicit-scheme runtime resolution coverage."""
        _unit_test_runtime_scheme_requires_explicit_scheme()

    def test_semver_minor_marker_requires_minor_bump(self):
        """Run semver minor-marker mismatch coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_semver_minor_marker_requires_minor_bump(
                Path(temp_dir).resolve()
            )

    def test_semver_minor_bump_passes_with_matching_marker(self):
        """Run matching semver minor-bump coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_semver_minor_bump_passes_with_matching_marker(
                Path(temp_dir).resolve()
            )

    def test_missing_semver_marker_requires_tag(self):
        """Run missing-semver-tag enforcement coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_missing_semver_marker_requires_tag(
                Path(temp_dir).resolve()
            )

    def test_semver_marker_is_optional_without_bump_enforcement(self):
        """Run format-only semver coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_semver_marker_is_optional_without_bump_enforcement(
                Path(temp_dir).resolve()
            )

    def test_policy_skips_when_only_ignored_prefix_changes(self):
        """Run ignored-prefix relevance coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_policy_skips_when_only_ignored_prefix_changes(
                Path(temp_dir).resolve()
            )

    def test_requires_version_bump_when_changelog_changes(self):
        """Run semver changelog/version coupling coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_requires_version_bump_when_changelog_changes(
                Path(temp_dir).resolve()
            )

    def test_mixed_semver_scope_markers_are_rejected(self):
        """Run mixed-semver-scope rejection coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_mixed_semver_scope_markers_are_rejected(
                Path(temp_dir).resolve()
            )

    def test_rejects_non_forward_version_when_bumping_enabled(self):
        """Run forward-bump enforcement coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_rejects_non_forward_version_when_bumping_enabled(
                Path(temp_dir).resolve()
            )

    def test_requires_explicit_scheme_when_enabled(self):
        """Run explicit-scheme enforcement coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_requires_explicit_scheme_when_enabled(
                Path(temp_dir).resolve()
            )

    def test_ignores_managed_block_version_examples(self):
        """Run managed-block example ignore coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_ignores_managed_block_version_examples(
                Path(temp_dir).resolve()
            )

    def test_calver_bump_passes_without_semver_markers(self):
        """Run calver forward-bump coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_calver_bump_passes_without_semver_markers(
                Path(temp_dir).resolve()
            )

    def test_calver_invalid_format_is_rejected(self):
        """Run calver format validation coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_calver_invalid_format_is_rejected(
                Path(temp_dir).resolve()
            )

    def test_integer_bump_passes(self):
        """Run integer-version bump coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_integer_bump_passes(Path(temp_dir).resolve())

    def test_pep440_prerelease_bump_passes(self):
        """Run pep440 prerelease-bump coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_pep440_prerelease_bump_passes(Path(temp_dir).resolve())

    def test_pep440_invalid_format_is_rejected(self):
        """Run pep440 format validation coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_pep440_invalid_format_is_rejected(
                Path(temp_dir).resolve()
            )

    def test_custom_regex_accepts_roman_format(self):
        """Run format-only custom_regex coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_custom_regex_accepts_roman_format(
                Path(temp_dir).resolve()
            )

    def test_custom_regex_rejects_bump_enforcement(self):
        """Run custom_regex bump-enforcement rejection coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_custom_regex_rejects_bump_enforcement(
                Path(temp_dir).resolve()
            )

    def test_custom_adapter_accepts_roman_bump(self):
        """Run repo-local custom_adapter coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_custom_adapter_accepts_roman_bump(
                Path(temp_dir).resolve()
            )

    def test_int_alias_resolves_to_integer_scheme(self):
        """Run integer-alias coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_int_alias_resolves_to_integer_scheme(
                Path(temp_dir).resolve()
            )

    def test_unsupported_scheme_is_rejected(self):
        """Run unsupported-scheme failure coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            _unit_test_unsupported_scheme_is_rejected(Path(temp_dir).resolve())
