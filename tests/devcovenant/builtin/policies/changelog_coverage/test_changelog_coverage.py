"""
Tests for changelog-coverage policy.
"""

import hashlib
import json
import subprocess
import tempfile
import unittest
from datetime import date
from importlib import import_module
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

from devcovenant.core.contracts.policy import ChangeState, CheckContext
from tests.devcovenant.support import MonkeyPatch

ChangelogCoverageModule = import_module(
    "devcovenant.builtin.policies.changelog_coverage.changelog_coverage"
)
ChangelogCoverageCheck = ChangelogCoverageModule.ChangelogCoverageCheck
_marker_signature = ChangelogCoverageModule._marker_signature
_non_exempt_content_hash = ChangelogCoverageModule._non_exempt_content_hash
_SESSION_SNAPSHOT_REL = "devcovenant/registry/runtime/session_snapshot.json"


def _summary_block() -> str:
    """Return a valid Change/Why/Impact summary block."""
    return (
        "  Change: Updated docs to cover new behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
    )


def _fingerprint(entry_text: str) -> str:
    """Return the changelog entry fingerprint used by gate snapshots."""
    normalized = "\n".join(
        line.rstrip() for line in entry_text.strip().splitlines()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _write_gate_status(
    tmp_path: Path,
    fingerprint: str,
    *,
    start_exemption_fingerprints: dict[str, dict[str, str]] | None = None,
    include_start_exemption_fingerprints: bool = True,
    session_state: str = "open",
    session_snapshot: dict[str, object] | None = None,
) -> None:
    """Write gate-status fixture with a changelog start snapshot."""
    status_path = (
        tmp_path / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_payload = dict(session_snapshot or {})
    if include_start_exemption_fingerprints:
        snapshot_payload["document_exemption_baseline"] = dict(
            start_exemption_fingerprints or {}
        )
    snapshot_path = tmp_path / _SESSION_SNAPSHOT_REL
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(snapshot_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = {
        "changelog_start_top_entry_fingerprint": fingerprint,
        "changelog_start_top_entry_present": bool(fingerprint),
        "session_state": session_state,
        "session_snapshot_file": _SESSION_SNAPSHOT_REL,
    }
    status_path.write_text(json.dumps(payload), encoding="utf-8")


def _allowlist_fingerprint_payload(
    *,
    relative_path: str,
    content: str,
) -> dict[str, str]:
    """Return one gate-status allowlist fingerprint payload entry."""
    return {
        "non_exempt_content_sha256": _non_exempt_content_hash(
            content,
            relative_path,
            header_doc_suffixes={".md", ".rst", ".txt"},
            header_keys={
                "last updated",
                "project version",
                "devcovenant version",
            },
            header_scan_lines=4,
        ),
        "managed_marker_signature": _marker_signature(content),
    }


def _set_scoped_changed_files(
    monkeypatch: MonkeyPatch,
    *,
    changed_paths: list[str],
    current_snapshot: dict[str, str],
) -> None:
    """Monkeypatch scoped_changed_files for direct policy unit tests."""

    def _scoped_changed_files(_self, context):
        """Resolve changed paths using session state when provided."""
        state = context.change_state
        if state.phase == "start":
            return []
        if state.session_valid:
            return list(state.session_paths)
        session_paths = set(changed_paths)
        return [context.repo_root / path for path in sorted(session_paths)]

    monkeypatch.setattr(
        "devcovenant.builtin.policies.changelog_coverage."
        "changelog_coverage.ChangelogCoverageCheck.scoped_changed_files",
        _scoped_changed_files,
    )


def _set_git_diff(monkeypatch: MonkeyPatch, output: str) -> None:
    """Monkeypatch subprocess.run to return the provided diff output."""

    changed_paths = [line for line in output.splitlines() if line.strip()]
    numstat_output = "".join(f"1\t1\t{path}\n" for path in changed_paths)
    snapshot = {
        path: f"1\t1\t{path}" for path in changed_paths if path.strip()
    }

    monkeypatch.setattr(
        "devcovenant.builtin.policies.changelog_coverage."
        "changelog_coverage.execution_runtime_module."
        "capture_current_numstat_snapshot",
        lambda _repo_root, _snapshot=snapshot: dict(_snapshot),
    )
    _set_scoped_changed_files(
        monkeypatch,
        changed_paths=changed_paths,
        current_snapshot=snapshot,
    )

    def _fake_run(*_args, **_kwargs):
        """Return a fake subprocess result with the requested output."""
        cmd = _args[0] if _args else []
        if cmd[:3] == ["git", "diff", "--name-only"]:
            return SimpleNamespace(stdout=output, returncode=0)
        if cmd[:4] == ["git", "diff", "--numstat", "HEAD"]:
            return SimpleNamespace(stdout=numstat_output, returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr("subprocess.run", _fake_run)


def _make_checker(
    tmp_path: Path, options: dict[str, object] | None = None
) -> ChangelogCoverageCheck:
    """Return a checker with required metadata and gate-status defaults."""
    checker = ChangelogCoverageCheck()
    merged_options: dict[str, object] = {
        "summary_verbs": ["update", "clarify", "see", "saw"],
    }
    if options:
        merged_options.update(options)
    checker.set_options(merged_options, {})
    status_path = (
        tmp_path / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )
    if not status_path.exists():
        _write_gate_status(tmp_path, "")
    return checker


def _set_git_diff_with_numstat(
    monkeypatch: MonkeyPatch,
    *,
    changed_files: str,
    numstat: str,
) -> None:
    """Monkeypatch subprocess.run for name-only and numstat diffs."""

    snapshot: dict[str, str] = {}
    changed_paths = [
        line.strip() for line in changed_files.splitlines() if line.strip()
    ]
    for line in numstat.splitlines():
        columns = line.split("\t")
        if len(columns) < 3:
            continue
        path = "\t".join(columns[2:]).strip()
        if not path:
            continue
        snapshot[path] = line.strip()

    monkeypatch.setattr(
        "devcovenant.builtin.policies.changelog_coverage."
        "changelog_coverage.execution_runtime_module."
        "capture_current_numstat_snapshot",
        lambda _repo_root, _snapshot=snapshot: dict(_snapshot),
    )
    _set_scoped_changed_files(
        monkeypatch,
        changed_paths=changed_paths,
        current_snapshot=snapshot,
    )

    def _fake_run(cmd, *_args, **_kwargs):
        """Return fake output for git diff subcommands used by the policy."""
        if cmd[:3] == ["git", "diff", "--name-only"]:
            return SimpleNamespace(stdout=changed_files, returncode=0)
        if cmd[:4] == ["git", "diff", "--numstat", "HEAD"]:
            return SimpleNamespace(stdout=numstat, returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr("subprocess.run", _fake_run)


def _set_git_diff_with_patches(
    monkeypatch: MonkeyPatch,
    *,
    changed_files: str,
    patches: dict[str, str],
    head_files: dict[str, str] | None = None,
) -> None:
    """Monkeypatch subprocess.run for name-only, patch, and HEAD lookups."""

    head_files = head_files or {}
    changed_paths = [line for line in changed_files.splitlines() if line]
    numstat_output = "".join(f"1\t1\t{path}\n" for path in changed_paths)
    snapshot = {
        path: f"1\t1\t{path}" for path in changed_paths if path.strip()
    }

    monkeypatch.setattr(
        "devcovenant.builtin.policies.changelog_coverage."
        "changelog_coverage.execution_runtime_module."
        "capture_current_numstat_snapshot",
        lambda _repo_root, _snapshot=snapshot: dict(_snapshot),
    )
    _set_scoped_changed_files(
        monkeypatch,
        changed_paths=changed_paths,
        current_snapshot=snapshot,
    )
    exemption_fingerprints = {
        rel_path: _allowlist_fingerprint_payload(
            relative_path=rel_path,
            content=content,
        )
        for rel_path, content in head_files.items()
    }
    monkeypatch.setattr(
        "devcovenant.builtin.policies.changelog_coverage."
        "changelog_coverage._load_document_exemption_baseline",
        (
            lambda _gate_status, _fingerprints=exemption_fingerprints: dict(
                _fingerprints
            )
        ),
    )

    def _fake_run(cmd, *_args, **_kwargs):
        """Return a fake subprocess result keyed by the git subcommand."""

        if cmd[:3] == ["git", "diff", "--name-only"]:
            return SimpleNamespace(stdout=changed_files, returncode=0)
        if cmd[:4] == ["git", "diff", "--numstat", "HEAD"]:
            return SimpleNamespace(stdout=numstat_output, returncode=0)
        if cmd[:4] == ["git", "diff", "--unified=0", "HEAD"]:
            rel_path = cmd[-1]
            return SimpleNamespace(
                stdout=patches.get(rel_path, ""),
                returncode=0,
            )
        if cmd[:2] == ["git", "show"] and cmd[2].startswith("HEAD:"):
            rel_path = cmd[2].split("HEAD:", 1)[1]
            if rel_path in head_files:
                return SimpleNamespace(
                    stdout=head_files[rel_path],
                    returncode=0,
                )
            raise subprocess.CalledProcessError(1, cmd)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr("subprocess.run", _fake_run)


def _unit_test_no_changes_passes(tmp_path: Path, monkeypatch: MonkeyPatch):
    """Empty diffs should yield no violations."""

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    assert checker.check(context) == []


def _unit_test_skipped_prefixes_ignore_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured skipped prefixes should bypass coverage checks."""

    checker = _make_checker(
        tmp_path, {"skipped_prefixes": ["devcovenant/core"]}
    )
    _set_git_diff(monkeypatch, "devcovenant/core/check.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_skipped_globs_ignore_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured skipped globs should bypass coverage checks."""

    checker = _make_checker(tmp_path, {"skipped_globs": ["*_old.*"]})
    _set_git_diff(monkeypatch, "devcovenant/config_old.yaml\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_skipped_generated_files_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured generated governance files should bypass coverage."""

    checker = _make_checker(
        tmp_path,
        {
            "skipped_files": [
                ".gitignore",
                ".pre-commit-config.yaml",
                ".github/workflows/governance-and-test.yml",
            ]
        },
    )
    _set_git_diff(
        monkeypatch,
        "\n".join(
            [
                ".gitignore",
                ".pre-commit-config.yaml",
                ".github/workflows/governance-and-test.yml",
            ]
        )
        + "\n",
    )
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_root_changelog_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Non-RNG files must be listed in the root changelog."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"{_summary_block()}"
        "  Files:\n"
        "  docs/readme.md\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    messages = " ".join(v.message for v in violations)
    assert "src/module.py" in messages
    assert "docs/readme.md" in messages


def _unit_test_rng_changelog_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """RNG files must be documented in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "rng_minigames/CHANGELOG.md" in violations[0].message


def _unit_test_collections_disabled_route_to_root(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """When collections are disabled, prefixed paths go to root."""

    today = date.today().isoformat()
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n- {today}:\n{_summary_block()}",
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path, {"collections": "none"})
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    messages = " ".join(v.message for v in violations)
    assert "CHANGELOG.md" in messages
    assert "Files" in messages


def _unit_test_changelog_requires_summary_labels(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Latest entry must include labeled summary lines."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("summary lines" in v.message for v in violations)


def _unit_test_summary_requires_action_verbs(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Summary lines must include an action verb from the list."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: New behavior here\n"
        "  Why: Explanation present\n"
        "  Impact: Some effect\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path, {"summary_verbs": ["updated"]})
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("action verb" in v.message for v in violations)


def _unit_test_summary_root_matches_inflected_forms(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Configured verb roots should match word-start inflected forms."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: Updated behavior here\n"
        "  Why: Updating guidance keeps contributors aligned\n"
        "  Impact: Updates improve reviewer clarity\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path, {"summary_verbs": ["update"]})
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_summary_root_ignores_inner_substrings(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Verb roots should not match substrings inside other words."""

    today = date.today().isoformat()
    changelog_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        "  Change: Prefix handling changed here\n"
        "  Why: Prefix notation confused contributors\n"
        "  Impact: Prefix usage became easier to follow\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        changelog_text,
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path, {"summary_verbs": ["fix"]})
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("action verb" in item.message for item in violations)


def _unit_test_rng_changelog_entry_found(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """RNG files pass when mentioned in rng_minigames/CHANGELOG.md."""

    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rng_text = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"{_summary_block()}"
        "  Files:\n"
        "  rng_minigames/emoji_meteors/game.py\n"
    )
    rng_changelog.write_text(
        rng_text,
        encoding="utf-8",
    )

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_rng_files_not_logged_in_root(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """RNG files should not appear in the root changelog."""

    root_changelog = tmp_path / "CHANGELOG.md"
    today = date.today().isoformat()
    rng_entry = (
        "## Version 1.0.0\n"
        f"- {today}:\n"
        f"{_summary_block()}"
        "  Files:\n"
        "  rng_minigames/emoji_meteors/game.py\n"
    )
    root_changelog.write_text(
        rng_entry,
        encoding="utf-8",
    )
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    rng_changelog.write_text(
        rng_entry,
        encoding="utf-8",
    )

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert len(violations) == 1
    assert "root changelog" in violations[0].message


def _unit_test_rng_entries_ignore_old_root_sections(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Old root entries mentioning RNG files should not trigger violations."""

    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## Version 2.0.0
            - entry about docs/readme.md

            ## Version 1.0.0
            - 2026-01-07:
              Change: Updated rng event behavior
              Why: Clarified event logging for QA
              Impact: Reviewers see updated rng logs
            """
        ).strip(),
        encoding="utf-8",
    )
    rng_changelog = tmp_path / "rng_minigames" / "CHANGELOG.md"
    rng_changelog.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rng_changelog.write_text(
        (
            "## Version 2.0.0\n"
            f"- {today}:\n"
            f"{_summary_block()}"
            "  Files:\n"
            "  rng_minigames/emoji_meteors/game.py\n"
        ),
        encoding="utf-8",
    )

    checker = _make_checker(
        tmp_path,
        {"collections": ["rng_minigames/:rng_minigames/CHANGELOG.md:true"]},
    )
    _set_git_diff(monkeypatch, "rng_minigames/emoji_meteors/game.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_template_code_block_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Template code blocks should not count as latest entries."""

    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## How to Log Changes
            ```
            ## Version 0.1.0
            - 2026-01-07: Template entry (Contributor)
              Files:
              docs/readme.md
            ```

            ## Log changes here

            ## Version 0.2.0
            - 2026-01-08: Update src/module.py (AI assistant)
            """
        ).strip(),
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path)
    _set_git_diff(monkeypatch, "")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_changelog_entries_newest_first(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Latest changelog section should list newest entries first."""
    root_changelog = tmp_path / "CHANGELOG.md"
    root_changelog.write_text(
        dedent(
            """
            ## Version 1.0.0
            - 2026-01-05:
              Change: Updated src/module.py behavior
              Why: Clarified coverage expectations
              Impact: Users see updated module behavior
            - 2026-01-07:
              Change: Updated src/module.py behavior
              Why: Clarified coverage expectations
              Impact: Users see updated module behavior
            """
        ).strip(),
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path)
    _set_git_diff(monkeypatch, "src/module.py\n")
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any("newest-first" in v.message for v in violations)


def _unit_test_line_continuation_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Backslash-wrapped paths should satisfy changelog coverage."""

    root_changelog = tmp_path / "CHANGELOG.md"
    changelog = "\n".join(
        [
            "## Version 1.0.0",
            f"- {date.today().isoformat()}:",
            "  Change: Updated docs with extra guidance for coverage tests",
            "  Why: Clarified expectations for contributors",
            "  Impact: Users see updated coverage notes now",
            "  Files:",
            "  devcovenant/builtin/policies/dependency_license_sync/assets/\\",
            "    licenses/README.md",
        ]
    )
    root_changelog.write_text(changelog, encoding="utf-8")
    diff_path = (
        "devcovenant/builtin/policies/"
        "dependency_license_sync/assets/licenses/README.md\n"
    )
    _set_git_diff(monkeypatch, diff_path)

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_managed_doc_changes_inside_managed_blocks_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-doc diffs confined to DEVCOV blocks should skip coverage."""

    old_agents = (
        "# AGENTS\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old managed text.\n"
        "<!-- DEVCOV:END -->\n"
        "User text.\n"
    )
    new_agents = old_agents.replace("Old managed text.", "New managed text.")
    (tmp_path / "AGENTS.md").write_text(new_agents, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="AGENTS.md\n",
        patches={
            "AGENTS.md": (
                "@@ -3 +3 @@\n" "-Old managed text.\n" "+New managed text.\n"
            )
        },
        head_files={"AGENTS.md": old_agents},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_skipped_files_listed_in_entry_are_tolerated(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Skipped-file extras should not trigger mismatch errors."""

    (tmp_path / "CHANGELOG.md").write_text(
        "".join(
            [
                "## Version 1.0.0\n",
                f"- {date.today().isoformat()}:\n",
                _summary_block(),
                "  Files:\n",
                "  src/module.py\n",
                "  .gitignore\n",
                "  devcovenant/config.yaml\n",
            ]
        ),
        encoding="utf-8",
    )

    _set_git_diff(monkeypatch, "src/module.py\n")
    checker = _make_checker(
        tmp_path,
        {
            "skipped_files": [
                ".gitignore",
                "devcovenant/config.yaml",
                "CHANGELOG.md",
            ]
        },
    )
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "not in the current change" in item.message for item in violations
    )


def _unit_test_any_file_changes_inside_managed_blocks_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-block-only diffs should be ignored for any file path."""

    old_doc = (
        "Notes\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old block text.\n"
        "<!-- DEVCOV:END -->\n"
        "Body text.\n"
    )
    new_doc = old_doc.replace("Old block text.", "New block text.")
    (tmp_path / "docs" / "notes.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "notes.md").write_text(new_doc, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="docs/notes.md\n",
        patches={
            "docs/notes.md": (
                "@@ -3 +3 @@\n-Old block text.\n+New block text.\n"
            )
        },
        head_files={"docs/notes.md": old_doc},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_managed_yml_regen_changes_are_ignored_in_open_session(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-only `.yml` regen changes should skip session coverage."""

    del monkeypatch  # Session-scoped path resolution avoids subprocess mocks.
    rel_path = ".github/workflows/sample.yml"
    old_workflow = (
        "name: Sample\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "managed: old\n"
        "<!-- DEVCOV:END -->\n"
        "jobs: {}\n"
    )
    new_workflow = old_workflow.replace("managed: old", "managed: new")
    workflow_path = tmp_path / rel_path
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(new_workflow, encoding="utf-8")

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="end",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[workflow_path],
            current_snapshot_numstat={rel_path: f"1\t1\t{rel_path}"},
            gate_status_payload={"session_state": "open"},
            session_snapshot_payload={
                "document_exemption_baseline": {
                    rel_path: _allowlist_fingerprint_payload(
                        relative_path=rel_path,
                        content=old_workflow,
                    )
                },
                "session_start_snapshot": {rel_path: f"1\t1\t{rel_path}"},
            },
        ),
    )
    violations = checker.check(context)

    assert not violations


def _unit_test_managed_yaml_regen_changes_are_ignored_in_open_session(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-only `.yaml` regen changes should skip session coverage."""

    del monkeypatch  # Session-scoped path resolution avoids subprocess mocks.
    rel_path = ".github/workflows/sample.yaml"
    old_workflow = (
        "name: Sample\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "managed: old\n"
        "<!-- DEVCOV:END -->\n"
        "jobs: {}\n"
    )
    new_workflow = old_workflow.replace("managed: old", "managed: new")
    workflow_path = tmp_path / rel_path
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(new_workflow, encoding="utf-8")

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="end",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[workflow_path],
            current_snapshot_numstat={rel_path: f"1\t1\t{rel_path}"},
            gate_status_payload={"session_state": "open"},
            session_snapshot_payload={
                "document_exemption_baseline": {
                    rel_path: _allowlist_fingerprint_payload(
                        relative_path=rel_path,
                        content=old_workflow,
                    )
                },
                "session_start_snapshot": {rel_path: f"1\t1\t{rel_path}"},
            },
        ),
    )
    violations = checker.check(context)

    assert not violations


def _unit_test_mixed_yml_managed_and_visible_changes_require_changelog(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Mixed managed/non-managed `.yml` edits must not be exemption-only."""

    del monkeypatch  # Session-scoped path resolution avoids subprocess mocks.
    rel_path = ".github/workflows/sample.yml"
    old_workflow = (
        "name: Sample\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "managed: old\n"
        "<!-- DEVCOV:END -->\n"
        "jobs: {}\n"
    )
    new_workflow = old_workflow.replace(
        "managed: old", "managed: new"
    ).replace(
        "jobs: {}",
        "jobs:\n  test: {}\n",
    )
    workflow_path = tmp_path / rel_path
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(new_workflow, encoding="utf-8")

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="end",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[workflow_path],
            current_snapshot_numstat={rel_path: f"1\t1\t{rel_path}"},
            gate_status_payload={"session_state": "open"},
            session_snapshot_payload={
                "document_exemption_baseline": {
                    rel_path: _allowlist_fingerprint_payload(
                        relative_path=rel_path,
                        content=old_workflow,
                    )
                },
                "session_start_snapshot": {rel_path: f"1\t1\t{rel_path}"},
            },
        ),
    )
    violations = checker.check(context)

    assert violations


def _unit_test_managed_block_only_files_listed_with_real_change_are_tolerated(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-only AGENTS changes may be listed without extra mismatch."""

    old_agents = (
        "# AGENTS\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old managed text.\n"
        "<!-- DEVCOV:END -->\n"
        "User text.\n"
    )
    new_agents = old_agents.replace("Old managed text.", "New managed text.")
    (tmp_path / "AGENTS.md").write_text(new_agents, encoding="utf-8")
    module_path = tmp_path / "src" / "module.py"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "".join(
            [
                "## Version 1.0.0\n",
                f"- {date.today().isoformat()}:\n",
                _summary_block(),
                "  Files:\n",
                "  src/module.py\n",
                "  AGENTS.md\n",
            ]
        ),
        encoding="utf-8",
    )

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="src/module.py\nAGENTS.md\n",
        patches={
            "AGENTS.md": (
                "@@ -3 +3 @@\n" "-Old managed text.\n" "+New managed text.\n"
            )
        },
        head_files={"AGENTS.md": old_agents},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "not in the current change" in item.message for item in violations
    )


def _unit_test_deleted_files_listed_in_changelog_are_tolerated(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Deleted files may remain listed as valid evidence in `Files:` blocks."""
    today = date.today().isoformat()
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "module.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "".join(
            [
                "## Version 1.0.0\n",
                f"- {today}:\n",
                _summary_block(),
                "  Files:\n",
                "  src/module.py\n",
                "  docs/retired.md\n",
            ]
        ),
        encoding="utf-8",
    )
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="end",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            current_snapshot_numstat={"src/module.py": "hash\tsrc/module.py"},
            session_snapshot_payload={
                "session_start_snapshot": {
                    "src/module.py": "old\tsrc/module.py",
                    "docs/retired.md": "old\tdocs/retired.md",
                }
            },
        ),
    )
    violations = checker.check(context)

    assert not any(
        "not in the current change" in item.message for item in violations
    )


def _unit_test_phase_start_ignores_head_deleted_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Start-phase coverage should not import HEAD-wide deleted paths."""

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(phase="start", session_valid=True),
    )
    violations = checker.check(context)

    assert not violations


def _unit_test_deleted_files_are_scoped_to_gate_start_snapshot(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Open-session deleted files should come from gate-start snapshot only."""
    today = date.today().isoformat()
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "module.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "".join(
            [
                "## Version 1.0.0\n",
                f"- {today}:\n",
                _summary_block(),
                "  Files:\n",
                "  src/module.py\n",
                "  docs/current-deleted.md\n",
            ]
        ),
        encoding="utf-8",
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="end",
            gate_status_path="devcovenant/registry/runtime/gate_status.json",
            session_valid=True,
            session_paths=[tmp_path / "src" / "module.py"],
            current_snapshot_numstat={"src/module.py": "1\t1\tsrc/module.py"},
            session_snapshot_payload={
                "session_start_snapshot": {
                    "src/module.py": "old",
                    "docs/current-deleted.md": "old",
                }
            },
        ),
    )
    violations = checker.check(context)

    assert not any(
        "not in the current change" in item.message for item in violations
    )


def _unit_test_managed_doc_changes_outside_managed_blocks_require_changelog(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Managed-doc diffs outside DEVCOV blocks must still hit coverage."""

    old_readme = (
        "# Old title\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Managed text.\n"
        "<!-- DEVCOV:END -->\n"
    )
    new_readme = old_readme.replace("# Old title", "# New title")
    (tmp_path / "README.md").write_text(new_readme, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="README.md\n",
        patches={"README.md": "@@ -1 +1 @@\n-# Old title\n+# New title\n"},
        head_files={"README.md": old_readme},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("CHANGELOG.md" in violation.message for violation in violations)


def _unit_test_document_header_only_changes_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Document header-only edits in first four lines should skip coverage."""

    old_notes = (
        "Project Notes\n"
        "**Last Updated:** 2026-02-16\n"
        "Context line\n"
        "**Project Version:** 0.2.6\n"
        "\n"
        "Body text.\n"
    )
    new_notes = old_notes.replace(
        "**Last Updated:** 2026-02-16",
        "**Last Updated:** 2026-02-17",
    )
    (tmp_path / "notes.rst").write_text(new_notes, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="notes.rst\n",
        patches={
            "notes.rst": (
                "@@ -2 +2 @@\n"
                "-**Last Updated:** 2026-02-16\n"
                "+**Last Updated:** 2026-02-17\n"
            )
        },
        head_files={"notes.rst": old_notes},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_header_and_managed_block_changes_are_ignored(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Header + managed-block edits in one file should skip coverage."""
    old_agents = (
        "# AGENTS\n"
        "**Last Updated:** 2026-02-17\n"
        "<!-- DEVCOV:BEGIN -->\n"
        "Old managed text.\n"
        "<!-- DEVCOV:END -->\n"
        "Body text.\n"
    )
    new_agents = old_agents.replace(
        "**Last Updated:** 2026-02-17",
        "**Last Updated:** 2026-02-18",
    ).replace("Old managed text.", "New managed text.")
    (tmp_path / "AGENTS.md").write_text(new_agents, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="AGENTS.md\n",
        patches={
            "AGENTS.md": (
                "@@ -2 +2 @@\n"
                "-**Last Updated:** 2026-02-17\n"
                "+**Last Updated:** 2026-02-18\n"
                "@@ -4 +4 @@\n"
                "-Old managed text.\n"
                "+New managed text.\n"
            )
        },
        head_files={"AGENTS.md": old_agents},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_document_header_line_five_requires_changelog(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Header key edits below line four should still require changelog."""

    old_doc = (
        "Line 1\n"
        "Line 2\n"
        "Line 3\n"
        "Line 4\n"
        "**Project Version:** 0.2.6\n"
        "Body\n"
    )
    new_doc = old_doc.replace(
        "**Project Version:** 0.2.6", "**Project Version:** 0.2.7"
    )
    (tmp_path / "notes.txt").write_text(new_doc, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="notes.txt\n",
        patches={
            "notes.txt": (
                "@@ -5 +5 @@\n"
                "-**Project Version:** 0.2.6\n"
                "+**Project Version:** 0.2.7\n"
            )
        },
        head_files={"notes.txt": old_doc},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("CHANGELOG.md" in item.message for item in violations)


def _unit_test_non_document_header_like_changes_require_changelog(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Header-like lines in non-doc files should not be excluded."""

    old_module = 'VERSION_LABEL = "Version: 1.0.0"\n'
    new_module = 'VERSION_LABEL = "Version: 1.0.1"\n'
    (tmp_path / "module.py").write_text(new_module, encoding="utf-8")

    _set_git_diff_with_patches(
        monkeypatch,
        changed_files="module.py\n",
        patches={
            "module.py": (
                "@@ -1 +1 @@\n"
                '-VERSION_LABEL = "Version: 1.0.0"\n'
                '+VERSION_LABEL = "Version: 1.0.1"\n'
            )
        },
        head_files={"module.py": old_module},
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("CHANGELOG.md" in item.message for item in violations)


def _unit_test_gate_snapshot_requires_new_top_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Current top entry must differ from the gate-start snapshot."""
    today = date.today().isoformat()
    top_entry = (
        f"- {today}:\n" f"{_summary_block()}" "  Files:\n" "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{top_entry}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(top_entry))
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any(
        "matches the gate-start snapshot" in item.message
        for item in violations
    )


def _unit_test_session_scope_ignores_preexisting_dirty_paths(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    """Session checks should ignore files already dirty at gate start."""
    today = date.today().isoformat()
    new_top = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{new_top}",
        encoding="utf-8",
    )
    _write_gate_status(
        tmp_path,
        "",
    )
    _set_git_diff_with_numstat(
        monkeypatch,
        changed_files="baseline/file.py\nsrc/module.py\n",
        numstat="1\t1\tbaseline/file.py\n2\t2\tsrc/module.py\n",
    )

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_gate_snapshot_requires_previous_entry_preserved(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Editing the previous top entry without prepending should fail."""
    today = date.today().isoformat()
    old_entry = (
        f"- {today}:\n" f"{_summary_block()}" "  Files:\n" "  src/module.py\n"
    )
    edited_top = (
        f"- {today}:\n"
        "  Change: Updated module behavior with edits\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{edited_top}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(old_entry))
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any("snapshot was edited" in v.message for v in violations)


def _unit_test_gate_snapshot_requires_previous_entry_second(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Gate-start entry must remain immediately below a prepended session."""
    today = date.today().isoformat()
    previous_top = (
        f"- {today}:\n"
        "  Change: Updated baseline entry for previous session\n"
        "  Why: Clarified prior behavior in docs\n"
        "  Impact: Users saw stable policy messaging\n"
        "  Files:\n"
        "  docs/old.md\n"
    )
    inserted_middle = (
        f"- {today}:\n"
        "  Change: Updated unrelated middle entry\n"
        "  Why: Clarified unrelated history ordering\n"
        "  Impact: Contributors saw an extra inserted row\n"
        "  Files:\n"
        "  docs/middle.md\n"
    )
    new_top = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{new_top}{inserted_middle}{previous_top}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(previous_top))
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any("second position" in v.message for v in violations)


def _unit_test_gate_snapshot_blocks_entry_checks_until_new_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Defer entry-shape checks until a fresh top entry is added."""
    today = date.today().isoformat()
    previous_top = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{previous_top}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(previous_top))
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any(
        "matches the gate-start snapshot" in item.message
        for item in violations
    )
    assert not any("Files: block" in item.message for item in violations)


def _unit_test_gate_snapshot_ignores_changelog_only_sessions(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Changelog-only diffs should not require a prepended session entry."""
    today = date.today().isoformat()
    top_entry = (
        f"- {today}:\n"
        "  Change: Updated changelog formatting only\n"
        "  Why: Clarified formatting rules\n"
        "  Impact: Contributors can read entries more easily\n"
        "  Files:\n"
        "  CHANGELOG.md\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{top_entry}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(top_entry))
    _set_git_diff(monkeypatch, "CHANGELOG.md\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_gate_snapshot_allows_prepended_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """A prepended top entry should pass when previous top stays below."""
    today = date.today().isoformat()
    previous_top = (
        f"- {today}:\n"
        "  Change: Updated baseline entry for previous session\n"
        "  Why: Clarified prior behavior in docs\n"
        "  Impact: Users saw stable policy messaging\n"
        "  Files:\n"
        "  docs/old.md\n"
    )
    new_top = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{new_top}{previous_top}",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, _fingerprint(previous_top))
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations == []


def _unit_test_gate_snapshot_empty_requires_new_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """When start snapshot has no entry, current run must add one."""
    (tmp_path / "CHANGELOG.md").write_text(
        "## Version 1.0.0\n",
        encoding="utf-8",
    )
    _write_gate_status(tmp_path, "")
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert any(
        "No changelog entry exists for this session" in item.message
        for item in violations
    )


def _unit_test_session_requires_start_numstat_snapshot(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Gate status no longer requires `changelog_start_diff_numstat`."""
    today = date.today().isoformat()
    entry = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{entry}",
        encoding="utf-8",
    )
    _write_gate_status(
        tmp_path,
        _fingerprint(entry),
    )
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_session_rejects_invalid_start_numstat_payload(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Invalid unsupported start numstat payload should be ignored."""
    today = date.today().isoformat()
    entry = (
        f"- {today}:\n"
        "  Change: Updated module behavior\n"
        "  Why: Clarified expectations for contributors\n"
        "  Impact: Users see updated guidance in docs\n"
        "  Files:\n"
        "  src/module.py\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Version 1.0.0\n{entry}",
        encoding="utf-8",
    )
    status_path = (
        tmp_path / "devcovenant" / "registry" / "runtime" / "gate_status.json"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(
            {
                "changelog_start_top_entry_fingerprint": _fingerprint(entry),
                "changelog_start_top_entry_present": True,
                "changelog_start_diff_numstat": [],
            }
        ),
        encoding="utf-8",
    )
    _set_git_diff(monkeypatch, "src/module.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert not any(
        "changelog_start_diff_numstat" in item.message for item in violations
    )


def _unit_test_start_phase_ignores_preexisting_dirty_tree(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    """Start phase should not require changelog coverage for baseline dirt."""
    (tmp_path / "CHANGELOG.md").write_text(
        "## Version 1.0.0\n",
        encoding="utf-8",
    )
    _set_git_diff(monkeypatch, "src/preexisting.py\n")

    checker = _make_checker(tmp_path)
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[],
        change_state=ChangeState(
            phase="start",
            current_snapshot_paths=[tmp_path / "src" / "preexisting.py"],
        ),
    )
    violations = checker.check(context)

    assert violations == []


def _unit_test_changelogcoveragecheck_symbol_contract_is_stable() -> None:
    """Policy class symbol should remain available for runtime loading."""
    changelogcoveragecheck = ChangelogCoverageCheck
    assert changelogcoveragecheck.__name__ == "ChangelogCoverageCheck"
    assert callable(changelogcoveragecheck)


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_no_changes_passes(self):
        """Run test_no_changes_passes."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_no_changes_passes(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_skipped_prefixes_ignore_paths(self):
        """Run test_skipped_prefixes_ignore_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_skipped_prefixes_ignore_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_skipped_globs_ignore_paths(self):
        """Run test_skipped_globs_ignore_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_skipped_globs_ignore_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_skipped_generated_files_are_ignored(self):
        """Run test_skipped_generated_files_are_ignored."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_skipped_generated_files_are_ignored(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_root_changelog_required(self):
        """Run test_root_changelog_required."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_root_changelog_required(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_changelog_required(self):
        """Run test_rng_changelog_required."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_changelog_required(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_collections_disabled_route_to_root(self):
        """Run test_collections_disabled_route_to_root."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_collections_disabled_route_to_root(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_changelog_requires_summary_labels(self):
        """Run test_changelog_requires_summary_labels."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_changelog_requires_summary_labels(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_summary_requires_action_verbs(self):
        """Run test_summary_requires_action_verbs."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_summary_requires_action_verbs(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_summary_root_matches_inflected_forms(self):
        """Run test_summary_root_matches_inflected_forms."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_summary_root_matches_inflected_forms(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_summary_root_ignores_inner_substrings(self):
        """Run test_summary_root_ignores_inner_substrings."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_summary_root_ignores_inner_substrings(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_changelog_entry_found(self):
        """Run test_rng_changelog_entry_found."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_changelog_entry_found(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_files_not_logged_in_root(self):
        """Run test_rng_files_not_logged_in_root."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_files_not_logged_in_root(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_rng_entries_ignore_old_root_sections(self):
        """Run test_rng_entries_ignore_old_root_sections."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_rng_entries_ignore_old_root_sections(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_template_code_block_ignored(self):
        """Run test_template_code_block_ignored."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_template_code_block_ignored(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_changelog_entries_newest_first(self):
        """Run test_changelog_entries_newest_first."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_changelog_entries_newest_first(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_line_continuation_paths(self):
        """Run test_line_continuation_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_line_continuation_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_managed_doc_changes_inside_managed_blocks_are_ignored(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_doc_changes_inside_"
                    "managed_blocks_are_ignored"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_skipped_files_listed_in_entry_are_tolerated(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_skipped_files_listed_in_entry_are_tolerated"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_any_file_changes_inside_managed_blocks_are_ignored(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_any_file_changes_inside_"
                    "managed_blocks_are_ignored"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_managed_block_only_files_listed_with_real_change_are_tolerated(
        self,
    ):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_block_only_files_listed_with_real_"
                    "change_are_tolerated"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_managed_yml_regen_changes_are_ignored_in_open_session(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_yml_regen_changes_are_ignored_in_"
                    "open_session"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_managed_yaml_regen_changes_are_ignored_in_open_session(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_yaml_regen_changes_are_ignored_in_"
                    "open_session"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_mixed_yml_managed_and_visible_changes_require_changelog(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_mixed_yml_managed_and_visible_changes_"
                    "require_changelog"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_deleted_files_listed_in_changelog_are_tolerated(self):
        """Run deleted-file Files-block tolerance assertions."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_deleted_files_listed_in_changelog_are_tolerated(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_phase_start_ignores_head_deleted_paths(self):
        """Run start-phase deleted-path scoping assertions."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_phase_start_ignores_head_deleted_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_deleted_files_are_scoped_to_gate_start_snapshot(self):
        """Run session-scoped deleted-file coverage assertions."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_deleted_files_are_scoped_to_gate_start_snapshot(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_managed_doc_changes_outside_managed_blocks_require_changelog(
        self,
    ):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_managed_doc_changes_outside_"
                    "managed_blocks_require_changelog"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_document_header_only_changes_are_ignored(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_document_header_only_changes_are_ignored"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_header_and_managed_block_changes_are_ignored(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_header_and_managed_block_changes_are_ignored"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_document_header_line_five_requires_changelog(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_document_header_line_five_requires_changelog"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_non_document_header_like_changes_require_changelog(self):
        """Run wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_non_document_header_like_changes_require_"
                    "changelog"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_requires_new_top_entry(self):
        """Run test_gate_snapshot_requires_new_top_entry."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_requires_new_top_entry(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_session_scope_ignores_preexisting_dirty_paths(self):
        """Run test_session_scope_ignores_preexisting_dirty_paths."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_session_scope_ignores_preexisting_dirty_paths(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_requires_previous_entry_preserved(self):
        """Run test_gate_snapshot_requires_previous_entry_preserved."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_requires_previous_entry_preserved(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_requires_previous_entry_second(self):
        """Run test_gate_snapshot_requires_previous_entry_second."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_requires_previous_entry_second(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_blocks_entry_checks_until_new_entry(self):
        """Run snapshot entry-check gating wrapper."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                test_case = globals()[
                    "_unit_test_gate_snapshot_blocks_entry_checks_until_"
                    "new_entry"
                ]
                test_case(tmp_path=tmp_path, monkeypatch=monkeypatch)
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_ignores_changelog_only_sessions(self):
        """Run test_gate_snapshot_ignores_changelog_only_sessions."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_ignores_changelog_only_sessions(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_allows_prepended_entry(self):
        """Run test_gate_snapshot_allows_prepended_entry."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_allows_prepended_entry(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_gate_snapshot_empty_requires_new_entry(self):
        """Run test_gate_snapshot_empty_requires_new_entry."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_gate_snapshot_empty_requires_new_entry(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_session_requires_start_numstat_snapshot(self):
        """Run test_session_requires_start_numstat_snapshot."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_session_requires_start_numstat_snapshot(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_session_rejects_invalid_start_numstat_payload(self):
        """Run test_session_rejects_invalid_start_numstat_payload."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_session_rejects_invalid_start_numstat_payload(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_start_phase_ignores_preexisting_dirty_tree(self):
        """Run test_start_phase_ignores_preexisting_dirty_tree."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                _unit_test_start_phase_ignores_preexisting_dirty_tree(
                    tmp_path=tmp_path, monkeypatch=monkeypatch
                )
        finally:
            monkeypatch.undo()

    def test_session_rejects_empty_start_numstat_row(self):
        """Run test_session_rejects_empty_start_numstat_row."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                today = date.today().isoformat()
                entry = (
                    f"- {today}:\n"
                    "  Change: Updated module behavior\n"
                    "  Why: Clarified expectations for contributors\n"
                    "  Impact: Users see updated guidance in docs\n"
                    "  Files:\n"
                    "  src/module.py\n"
                )
                (tmp_path / "CHANGELOG.md").write_text(
                    f"## Version 1.0.0\n{entry}",
                    encoding="utf-8",
                )
                status_path = (
                    tmp_path
                    / "devcovenant"
                    / "registry"
                    / "local"
                    / "gate_status.json"
                )
                status_path.parent.mkdir(parents=True, exist_ok=True)
                status_path.write_text(
                    json.dumps(
                        {
                            "changelog_start_top_entry_fingerprint": (
                                _fingerprint(entry)
                            ),
                            "changelog_start_top_entry_present": True,
                            "changelog_start_diff_numstat": {
                                "src/module.py": ""
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                _set_git_diff(monkeypatch, "src/module.py\n")
                checker = _make_checker(tmp_path)
                context = CheckContext(repo_root=tmp_path, all_files=[])
                violations = checker.check(context)
                assert not any(
                    "changelog_start_diff_numstat" in item.message
                    for item in violations
                )
        finally:
            monkeypatch.undo()

    def test_missing_gate_status_is_ignored_when_no_scoped_changes(self):
        """No-change runs should not fail on missing gate status."""
        monkeypatch = MonkeyPatch()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tmp_path = Path(temp_dir).resolve()
                checker = ChangelogCoverageCheck()
                checker.set_options(
                    {"summary_verbs": ["update", "clarify", "see", "saw"]},
                    {},
                )

                monkeypatch.setattr(
                    "devcovenant.builtin.policies.changelog_coverage."
                    "changelog_coverage.ChangelogCoverageCheck."
                    "scoped_changed_files",
                    lambda _self, _context: [],
                )

                context = CheckContext(
                    repo_root=tmp_path,
                    all_files=[],
                    change_state=ChangeState(
                        session_valid=False,
                        session_error=(
                            "Gate status file is missing: "
                            "devcovenant/registry/runtime/gate_status.json."
                        ),
                        session_reason_code="missing_gate_status",
                    ),
                )
                violations = checker.check(context)
                assert not violations
        finally:
            monkeypatch.undo()

    def test_changelogcoveragecheck_symbol_contract_is_stable(self):
        """Run test_changelogcoveragecheck_symbol_contract_is_stable."""
        _unit_test_changelogcoveragecheck_symbol_contract_is_stable()
