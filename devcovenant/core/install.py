#!/usr/bin/env python3
"""Install or update DevCovenant in a target repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEV_COVENANT_DIR = "devcovenant"
CORE_PATHS = [
    DEV_COVENANT_DIR,
    "devcov_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]

CONFIG_PATHS = [
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    ".gitignore",
]

DOC_PATHS = [
    "AGENTS.md",
    "README.md",
    "DEVCOVENANT.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
]

METADATA_PATHS = [
    "VERSION",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
]

MANIFEST_PATH = ".devcov/install_manifest.json"
LEGACY_MANIFEST_PATH = ".devcovenant/install_manifest.json"
BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
LICENSE_TEMPLATE = "tools/templates/LICENSE_GPL-3.0.txt"
TEMPLATE_ROOT_NAME = "templates"
GITIGNORE_USER_BEGIN = "# --- User entries (preserved) ---"
GITIGNORE_USER_END = "# --- End user entries ---"
DEFAULT_PRESERVE_PATHS = [
    "custom/policy_scripts",
    "common_policy_patches",
    "config.yaml",
]

_CORE_CONFIG_INCLUDE_KEY = "devcov_core_include:"
_CORE_CONFIG_PATHS_KEY = "devcov_core_paths:"
_DEFAULT_CORE_PATHS = [
    "devcovenant/core",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcov_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
    "tools/install_devcovenant.py",
    "tools/uninstall_devcovenant.py",
]

_VERSION_INPUT_PATTERN = re.compile(r"^\d+\.\d+(\.\d+)?$")
_LAST_UPDATED_PATTERN = re.compile(
    r"^\s*(\*\*Last Updated:\*\*|Last Updated:|# Last Updated)",
    re.IGNORECASE,
)
_VERSION_PATTERN = re.compile(r"^\s*\*\*Version:\*\*", re.IGNORECASE)


def _utc_today() -> str:
    """Return today's UTC date as an ISO string."""
    return datetime.now(timezone.utc).date().isoformat()


def _normalize_version(version_text: str) -> str:
    """Normalize user version input to MAJOR.MINOR.PATCH."""
    text = version_text.strip()
    if not _VERSION_INPUT_PATTERN.match(text):
        raise ValueError(
            "Version must be in MAJOR.MINOR or MAJOR.MINOR.PATCH format."
        )
    if text.count(".") == 1:
        return f"{text}.0"
    return text


def _prompt_version() -> str:
    """Prompt for a version until the input is valid."""
    while True:
        raw = input("Enter current version (x.x or x.x.x): ").strip()
        try:
            return _normalize_version(raw)
        except ValueError:
            print("Invalid version. Use x.x or x.x.x.")


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for a yes/no answer and return the response."""
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def _resolve_source_path(
    repo_root: Path, template_root: Path, rel_path: str
) -> Path:
    """Return the source path for rel_path with template fallback."""
    candidate = repo_root / rel_path
    if candidate.exists():
        return candidate
    template = template_root / rel_path
    if template.exists():
        return template
    return candidate


def _strip_devcov_block(text: str) -> str:
    """Return text without any DevCovenant managed block."""
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, rest = text.split(BLOCK_BEGIN, 1)
        _block, after = rest.split(BLOCK_END, 1)
        return f"{before}{after}"
    return text


def _has_heading(text: str, heading: str) -> bool:
    """Return True if text includes a markdown heading."""
    pattern = re.compile(
        rf"^#+\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE
    )
    return bool(pattern.search(text))


def _ensure_standard_header(
    text: str, last_updated: str, version: str, title: str | None = None
) -> str:
    """Ensure Last Updated and Version lines appear near the top."""
    lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        if _LAST_UPDATED_PATTERN.match(line):
            continue
        if _VERSION_PATTERN.match(line):
            continue
        cleaned.append(line.rstrip())

    title_line = None
    remaining = cleaned
    if cleaned and cleaned[0].lstrip().startswith("#"):
        title_line = cleaned[0]
        remaining = cleaned[1:]
    elif title:
        title_line = f"# {title}"

    header_lines: list[str] = []
    if title_line is not None:
        header_lines.append(title_line)
    header_lines.append(f"**Last Updated:** {last_updated}")
    header_lines.append(f"**Version:** {version}")

    if remaining and remaining[0].strip() != "":
        header_lines.append("")
    elif not remaining:
        header_lines.append("")

    updated = "\n".join(header_lines + remaining).rstrip() + "\n"
    return updated


def _apply_standard_header(
    path: Path, last_updated: str, version: str, title: str | None = None
) -> bool:
    """Update a file with the standard header."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = _ensure_standard_header(text, last_updated, version, title)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def _update_devcovenant_version(path: Path, devcov_version: str) -> bool:
    """Update the DevCovenant Version line in a doc if present."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^\s*\*\*DevCovenant Version:\*\*.*$",
        re.IGNORECASE | re.MULTILINE,
    )
    updated = pattern.sub(
        f"**DevCovenant Version:** {devcov_version}", text, count=1
    )
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def _extract_user_gitignore(text: str) -> str:
    """Extract user entries from an existing gitignore."""
    if GITIGNORE_USER_BEGIN in text and GITIGNORE_USER_END in text:
        _, rest = text.split(GITIGNORE_USER_BEGIN, 1)
        user_block, _tail = rest.split(GITIGNORE_USER_END, 1)
        return user_block.strip("\n")
    return text.strip("\n")


def _render_gitignore(user_text: str) -> str:
    """Render a universal gitignore and append preserved user entries."""
    base_lines = [
        "# DevCovenant standard ignores",
        "",
        "# OS artifacts",
        ".DS_Store",
        ".AppleDouble",
        ".LSOverride",
        "Thumbs.db",
        "Desktop.ini",
        "ehthumbs.db",
        "Icon?",
        "*.lnk",
        "",
        "# Editor settings",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*.swn",
        "*.tmp",
        "*.bak",
        "",
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".tox/",
        ".nox/",
        ".venv/",
        "venv/",
        ".env",
        ".env.*",
        "!.env.example",
        ".coverage",
        ".coverage.*",
        "htmlcov/",
        "dist/",
        "build/",
        "*.egg-info/",
        ".eggs/",
        "",
        "# Node",
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "pnpm-debug.log*",
        "",
        "# Go",
        "bin/",
        "pkg/",
        "",
        "# Rust",
        "target/",
        "",
        "# Logs",
        "*.log",
        "",
        "# Misc",
        ".cache/",
        "tmp/",
        "temp/",
    ]
    base_text = "\n".join(base_lines).rstrip() + "\n"
    user_block = _extract_user_gitignore(user_text)
    return (
        f"{base_text}\n{GITIGNORE_USER_BEGIN}\n{user_block}\n"
        f"{GITIGNORE_USER_END}\n"
    )


def _render_spec_template(version: str, date_stamp: str) -> str:
    """Return a minimal SPEC.md template."""
    return (
        "# Specification\n"
        f"**Last Updated:** {date_stamp}\n"
        f"**Version:** {version}\n\n"
        "This specification captures the required behavior for this "
        "repository.\n"
        "It describes what the system must do, the constraints it must "
        "respect,\n"
        "and the workflow expectations that keep policy text and "
        "implementation\n"
        "aligned.\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n"
        "3. [Functional Requirements](#functional-requirements)\n"
        "4. [Non-Functional Requirements](#non-functional-requirements)\n\n"
        "## Overview\n"
        "This document defines the scope, goals, and user-facing outcomes "
        "for\n"
        "the project. Keep it concise but specific, and update it whenever "
        "the\n"
        "behavior, interfaces, or integration points change so contributors "
        "can\n"
        "trust it.\n\n"
        "## Workflow\n"
        "DevCovenant requires the gated workflow for every change. Run the "
        "pre-\n"
        "commit start, tests, and pre-commit end steps in order, then record "
        "the\n"
        "change in `CHANGELOG.md` with the files touched during\n"
        "the update.\n\n"
        "## Functional Requirements\n"
        "- Describe the primary behaviors the system must implement.\n"
        "- List the critical APIs, commands, or automation outcomes that must "
        "exist.\n\n"
        "## Non-Functional Requirements\n"
        "- Document performance, reliability, or security constraints.\n"
        "- Note any compliance or operational requirements for production "
        "use.\n"
    )


def _render_plan_template(version: str, date_stamp: str) -> str:
    """Return a minimal PLAN.md template."""
    return (
        "# Plan\n"
        f"**Last Updated:** {date_stamp}\n"
        f"**Version:** {version}\n\n"
        "This plan tracks the roadmap for the repository. It should "
        "enumerate\n"
        "upcoming milestones, sequencing decisions, and the work needed to "
        "keep\n"
        "docs, policies, and implementation aligned.\n\n"
        "## Table of Contents\n"
        "1. [Overview](#overview)\n"
        "2. [Workflow](#workflow)\n"
        "3. [Roadmap](#roadmap)\n"
        "4. [Near-Term Tasks](#near-term-tasks)\n\n"
        "## Overview\n"
        "Use this plan to describe the scope of upcoming releases and major "
        "efforts.\n"
        "Update it whenever priorities change so contributors can see the "
        "current\n"
        "direction at a glance.\n\n"
        "## Workflow\n"
        "DevCovenant expects the gated workflow for every change. Log each "
        "step in\n"
        "`CHANGELOG.md` and keep this plan consistent with the active "
        "policies in\n"
        "`AGENTS.md`.\n\n"
        "## Roadmap\n"
        "- Outline multi-week or multi-release initiatives.\n"
        "- Record dependencies or prerequisites that drive sequencing.\n\n"
        "## Near-Term Tasks\n"
        "- List the next concrete milestones and their owners.\n"
        "- Note any open questions that block delivery.\n"
    )


def _render_changelog_template(version: str, date_stamp: str) -> str:
    """Return a standard CHANGELOG.md template."""
    return (
        "# Changelog\n\n"
        "## How to Log Changes\n"
        "Add one line for each substantive change under the current version "
        "header.\n"
        "Keep entries newest-first and record dates in ISO format "
        "(`YYYY-MM-DD`).\n"
        "Example entry:\n"
        f"- {date_stamp}: Updated dependency manifests and license report.\n"
        "  Files:\n"
        "  requirements.in\n"
        "  requirements.lock\n"
        "  THIRD_PARTY_LICENSES.md\n\n"
        "## Log changes here\n\n"
        f"## Version {version}\n"
        f"- {date_stamp}: Initialized DevCovenant policy scaffolding and "
        "tooling.\n"
        "  Files:\n"
        "  AGENTS.md\n"
        "  README.md\n"
        "  SPEC.md\n"
        "  PLAN.md\n"
        "  CHANGELOG.md\n"
        "  CONTRIBUTING.md\n"
        "  DEVCOVENANT.md\n"
        "  devcovenant/\n"
        "  tools/\n"
        "  .github/\n"
        "  .pre-commit-config.yaml\n"
    )


def _render_citation_template(repo_name: str, version: str) -> str:
    """Return a CITATION.cff template for the target repo."""
    return (
        "cff-version: 1.2.0\n"
        'message: "If you use this software, please cite it."\n'
        f'title: "{repo_name}"\n'
        f'version: "{version}"\n'
        "preferred-citation:\n"
        "  type: software\n"
        f'  title: "{repo_name}"\n'
        f'  version: "{version}"\n'
    )


def _build_readme_block(
    has_overview: bool,
    has_workflow: bool,
    has_toc: bool,
    has_devcovenant: bool,
) -> str:
    """Build a managed README block with missing sections."""
    include_overview = not has_overview
    include_workflow = not has_workflow
    include_devcovenant = not has_devcovenant
    include_toc = not has_toc

    toc_headings: list[str] = []
    if has_overview or include_overview:
        toc_headings.append("Overview")
    if has_workflow or include_workflow:
        toc_headings.append("Workflow")
    if has_devcovenant or include_devcovenant:
        toc_headings.append("DevCovenant")

    lines = [
        BLOCK_BEGIN,
        "**DevCovenant:** `AGENTS.md` is canonical. See "
        "`devcovenant/README.md`.",
    ]

    if include_toc:
        lines.extend(["", "## Table of Contents"])
        for index, heading in enumerate(toc_headings, start=1):
            anchor = heading.lower().replace(" ", "-")
            lines.append(f"{index}. [{heading}](#{anchor})")

    if include_overview:
        lines.extend(
            [
                "",
                "## Overview",
                "This README describes the repository's purpose and the "
                "expectations",
                "for contributors. Replace this overview with a project-"
                "specific",
                "summary that covers scope, audience, and the most important "
                "interfaces.",
            ]
        )

    if include_workflow:
        lines.extend(
            [
                "",
                "## Workflow",
                "DevCovenant enforces a gated workflow for every change, "
                "including docs:",
                "1. `python3 tools/run_pre_commit.py --phase start`",
                "2. `python3 tools/run_tests.py`",
                "3. `python3 tools/run_pre_commit.py --phase end`",
                "Record changes in `CHANGELOG.md` and keep `AGENTS.md` in "
                "sync with",
                "policy updates.",
            ]
        )

    if include_devcovenant:
        lines.extend(
            [
                "",
                "## DevCovenant",
                "`AGENTS.md` is the canonical policy source for this repo. "
                "See",
                "`devcovenant/README.md` for the local workflow guide and "
                "policy",
                "routines. Keep repo-specific decisions in the editable "
                "section",
                "of `AGENTS.md`.",
            ]
        )

    lines.append(BLOCK_END)
    return "\n".join(lines) + "\n"


def _update_policy_block_value(
    text: str, policy_id: str, key: str, field_value: str
) -> str:
    """Update a policy-def block field value."""
    marker = "```policy-def"
    position = 0
    while True:
        start = text.find(marker, position)
        if start == -1:
            break
        end = text.find("```", start + len(marker))
        if end == -1:
            break
        block = text[start:end]
        if f"id: {policy_id}" not in block:
            position = end + 3
            continue
        lines = block.splitlines()
        updated_lines: list[str] = []
        found_key = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"{key}:"):
                prefix = line[: line.find(stripped)]
                updated_lines.append(f"{prefix}{key}: {field_value}")
                found_key = True
            else:
                updated_lines.append(line)
        if not found_key:
            updated_lines.append(f"{key}: {field_value}")
        updated_block = "\n".join(updated_lines)
        return text[:start] + updated_block + text[end:]
    return text


def _disable_citation_in_agents(path: Path) -> bool:
    """Disable citation enforcement in AGENTS.md."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = _update_policy_block_value(
        text,
        policy_id="version-sync",
        key="citation_file",
        field_value="__none__",
    )
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def _normalize_core_paths(paths: list[str]) -> list[str]:
    """Return cleaned core path entries."""
    cleaned: list[str] = []
    for entry in paths:
        text = str(entry).strip()
        if text:
            cleaned.append(text)
    return cleaned or list(_DEFAULT_CORE_PATHS)


def _update_core_config_text(
    text: str, include_core: bool, core_paths: list[str]
) -> tuple[str, bool]:
    """Update devcov core configuration values in config.yaml."""
    lines = text.splitlines()
    updated_lines: list[str] = []
    found_include = False
    found_paths = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith(_CORE_CONFIG_INCLUDE_KEY):
            updated_lines.append(
                f"devcov_core_include: {'true' if include_core else 'false'}"
            )
            found_include = True
            index += 1
            continue
        if stripped.startswith(_CORE_CONFIG_PATHS_KEY):
            updated_lines.append("devcov_core_paths:")
            found_paths = True
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.strip().startswith("-"):
                    index += 1
                    continue
                break
            for path in _normalize_core_paths(core_paths):
                updated_lines.append(f"  - {path}")
            continue
        updated_lines.append(line)
        index += 1

    if found_include and found_paths:
        updated = "\n".join(updated_lines) + "\n"
        return updated, updated != text

    insert_block = [
        "# DevCovenant core exclusion guard.",
        "devcov_core_include: " + ("true" if include_core else "false"),
        "devcov_core_paths:",
    ]
    insert_block.extend(
        f"  - {path}" for path in _normalize_core_paths(core_paths)
    )
    insert_block.append("")
    insert_at = 0
    for idx, line in enumerate(updated_lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_at = idx
            break
    updated_lines[insert_at:insert_at] = insert_block
    updated = "\n".join(updated_lines) + "\n"
    return updated, updated != text


def _apply_core_config(target_root: Path, include_core: bool) -> bool:
    """Ensure devcov core config matches the install target."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_core_config_text(
        text,
        include_core=include_core,
        core_paths=_DEFAULT_CORE_PATHS,
    )
    if not changed:
        return False
    config_path.write_text(updated, encoding="utf-8")
    return True


def _copy_path(source: Path, target: Path) -> None:
    """Copy a file or directory from source to target."""
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return
    if target.exists():
        _rename_existing_file(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _rename_existing_file(target: Path) -> None:
    """Rename an existing file to preserve it before overwriting."""
    if not target.exists() or target.is_dir():
        return
    suffix = target.suffix
    stem = target.stem
    candidate = target.with_name(f"{stem}_old{suffix}")
    index = 2
    while candidate.exists():
        candidate = target.with_name(f"{stem}_old{index}{suffix}")
        index += 1
    target.rename(candidate)


def _copy_dir_contents(source: Path, target: Path) -> None:
    """Copy contents of source dir into target dir."""
    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        dest = target / entry.name
        if entry.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(entry, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, dest)


def _backup_paths(root: Path, paths: list[str], backup_root: Path) -> None:
    """Backup selected paths into backup_root."""
    for rel in paths:
        src = root / rel
        if not src.exists():
            continue
        dest = backup_root / rel
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _restore_paths(backup_root: Path, root: Path, paths: list[str]) -> None:
    """Restore backed-up paths into root."""
    for rel in paths:
        src = backup_root / rel
        if not src.exists():
            continue
        dest = root / rel
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _preserve_editable_section(target: Path, user_content: str) -> None:
    """Merge existing user AGENTS content into the new editable section."""
    if not target.exists() or not user_content.strip():
        return
    text = target.read_text(encoding="utf-8")
    start = text.find("<!-- DEVCOV:END -->")
    if start == -1:
        return
    remainder = text[start:]
    middle_end = remainder.find("<!-- DEVCOV:BEGIN -->")
    if middle_end == -1:
        return
    middle = remainder[:middle_end]
    after = remainder[middle_end:]
    marker = "# EDITABLE SECTION"
    marker_idx = middle.find(marker)
    if marker_idx == -1:
        insertion = f"{middle}{marker}\n\n{user_content.strip()}\n\n"
    else:
        prefix = middle[: marker_idx + len(marker)]
        suffix = middle[marker_idx + len(marker) :]
        rest = suffix.lstrip("\n")
        insertion = f"{prefix}\n\n{user_content.strip()}\n\n{rest}"
    updated = text[:start] + insertion + after
    target.write_text(updated, encoding="utf-8")


def _extract_editable_notes(text: str) -> str:
    """Extract editable notes from an existing AGENTS.md."""
    start = text.find("<!-- DEVCOV:END -->")
    if start == -1:
        return text.strip()
    remainder = text[start:]
    middle_end = remainder.find("<!-- DEVCOV:BEGIN -->")
    if middle_end == -1:
        return text.strip()
    middle = remainder[:middle_end]
    marker = "# EDITABLE SECTION"
    marker_idx = middle.find(marker)
    if marker_idx == -1:
        return middle.strip()
    return middle[marker_idx + len(marker) :].strip()


def _install_devcovenant_dir(
    source_root: Path,
    target_root: Path,
    preserve_paths: list[str],
    preserve_existing: bool,
) -> list[str]:
    """Install the devcovenant directory while preserving custom paths."""
    source = source_root / DEV_COVENANT_DIR
    target = target_root / DEV_COVENANT_DIR
    installed: list[str] = []
    if not source.exists():
        return installed

    if not target.exists() or not preserve_existing:
        _copy_path(source, target)
        installed.append(DEV_COVENANT_DIR)
        return installed

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_root = Path(tmpdir)
        _backup_paths(target, preserve_paths, backup_root)
        _copy_path(source, target)
        _restore_paths(backup_root, target, preserve_paths)

    installed.append(DEV_COVENANT_DIR)
    return installed


def _install_paths(
    repo_root: Path,
    target_root: Path,
    paths: list[str],
    skip_existing: bool,
    source_overrides: dict[str, Path] | None = None,
) -> list[str]:
    """Copy paths and return installed file list."""
    installed: list[str] = []
    overrides = source_overrides or {}
    for rel_path in paths:
        source = overrides.get(rel_path, repo_root / rel_path)
        target = target_root / rel_path
        if not source.exists():
            continue
        if skip_existing and target.exists():
            continue
        _copy_path(source, target)
        installed.append(rel_path)
    return installed


def _inject_block(path: Path, block: str) -> bool:
    """Insert or replace a DevCovenant block in a documentation file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, _rest = text.split(BLOCK_BEGIN, 1)
        _old_block, after = _rest.split(BLOCK_END, 1)
        updated = f"{before}{block}{after}"
        if updated == text:
            return False
        path.write_text(updated, encoding="utf-8")
        return True

    lines = text.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            insert_at = index + 1
            while insert_at < len(lines):
                candidate = lines[insert_at].strip()
                if not candidate:
                    insert_at += 1
                    continue
                if _LAST_UPDATED_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                if _VERSION_PATTERN.match(candidate):
                    insert_at += 1
                    continue
                break
            break
    lines.insert(insert_at, block)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main(argv=None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Install or update DevCovenant in a target repository."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "empty", "existing"),
        default="auto",
        help="Install mode (auto detects existing installs).",
    )
    parser.add_argument(
        "--docs-mode",
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle docs in existing repos.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle config files in existing repos.",
    )
    parser.add_argument(
        "--metadata-mode",
        choices=("preserve", "overwrite", "skip"),
        default=None,
        help="How to handle metadata files in existing repos.",
    )
    parser.add_argument(
        "--license-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for LICENSE.",
    )
    parser.add_argument(
        "--version-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for VERSION.",
    )
    parser.add_argument(
        "--version",
        dest="version_value",
        default=None,
        help="Version to use when creating VERSION for new installs.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for pyproject.toml.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the config mode for CI workflow files.",
    )
    parser.add_argument(
        "--citation-mode",
        choices=("prompt", "create", "skip"),
        default="prompt",
        help="How to handle CITATION.cff when it is missing.",
    )
    parser.add_argument(
        "--preserve-custom",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Preserve custom policy scripts and patches during updates.",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Overwrite docs and metadata on update.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite config files on update.",
    )
    args = parser.parse_args(argv)

    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parent
    template_root = package_root / TEMPLATE_ROOT_NAME
    target_root = Path(args.target).resolve()
    manifest_file = target_root / MANIFEST_PATH
    legacy_manifest = target_root / LEGACY_MANIFEST_PATH
    has_manifest = manifest_file.exists() or legacy_manifest.exists()
    has_existing = has_manifest or (target_root / DEV_COVENANT_DIR).exists()
    if args.mode == "auto":
        mode = "existing" if has_existing else "empty"
    else:
        mode = args.mode

    docs_mode = args.docs_mode
    config_mode = args.config_mode
    metadata_mode = args.metadata_mode

    if args.force_docs:
        docs_mode = "overwrite"
    if args.force_config:
        config_mode = "overwrite"

    if docs_mode is None:
        docs_mode = "overwrite" if mode == "empty" else "preserve"
    agents_path = target_root / "AGENTS.md"
    existing_agents_text = None
    if agents_path.exists():
        existing_agents_text = _extract_editable_notes(
            agents_path.read_text(encoding="utf-8")
        )
        docs_mode = "overwrite"
    if config_mode is None:
        config_mode = "overwrite" if mode == "empty" else "preserve"
    if metadata_mode is None:
        metadata_mode = "overwrite" if mode == "empty" else "preserve"

    def _resolve_override(override_value: str) -> str:
        """Return the resolved metadata mode for a CLI override."""
        return metadata_mode if override_value == "inherit" else override_value

    license_mode = _resolve_override(args.license_mode)
    version_mode = _resolve_override(args.version_mode)
    pyproject_mode = _resolve_override(args.pyproject_mode)
    ci_mode = config_mode if args.ci_mode == "inherit" else args.ci_mode

    preserve_custom = args.preserve_custom
    if preserve_custom is None:
        preserve_custom = mode == "existing"

    last_updated = _utc_today()
    repo_name = target_root.name

    source_version_path = _resolve_source_path(
        repo_root, template_root, "VERSION"
    )
    devcovenant_version = None
    if source_version_path.exists():
        devcovenant_version = source_version_path.read_text(
            encoding="utf-8"
        ).strip()
    else:
        devcovenant_version = "0.0.0"

    version_path = target_root / "VERSION"
    existing_version = None
    if version_path.exists():
        existing_version = version_path.read_text(encoding="utf-8").strip()

    requested_version = None
    if args.version_value:
        requested_version = _normalize_version(args.version_value)

    if version_mode == "overwrite":
        target_version = requested_version or _prompt_version()
    elif version_mode == "preserve" and existing_version:
        target_version = existing_version
    else:
        target_version = (
            existing_version or requested_version or _prompt_version()
        )

    installed: dict[str, list[str]] = {"core": [], "config": [], "docs": []}
    doc_blocks: list[str] = []

    core_files = [path for path in CORE_PATHS if path != DEV_COVENANT_DIR]
    core_sources = {
        path: _resolve_source_path(repo_root, template_root, path)
        for path in core_files
    }
    installed["core"].extend(
        _install_devcovenant_dir(
            repo_root,
            target_root,
            DEFAULT_PRESERVE_PATHS if preserve_custom else [],
            preserve_existing=preserve_custom,
        )
    )
    installed["core"].extend(
        _install_paths(
            repo_root,
            target_root,
            core_files,
            skip_existing=False,
            source_overrides=core_sources,
        )
    )

    config_paths = [path for path in CONFIG_PATHS if path != ".gitignore"]
    if ci_mode == "skip":
        config_paths = [
            path for path in config_paths if path != ".github/workflows/ci.yml"
        ]
    config_sources = {
        path: _resolve_source_path(repo_root, template_root, path)
        for path in config_paths
    }
    installed["config"] = _install_paths(
        repo_root,
        target_root,
        config_paths,
        skip_existing=(mode == "existing" and config_mode == "preserve"),
        source_overrides=config_sources,
    )

    gitignore_path = target_root / ".gitignore"
    existing_gitignore = (
        gitignore_path.read_text(encoding="utf-8")
        if gitignore_path.exists()
        else ""
    )
    gitignore_text = _render_gitignore(existing_gitignore)
    if not gitignore_path.exists():
        installed["config"].append(".gitignore")
    gitignore_path.parent.mkdir(parents=True, exist_ok=True)
    gitignore_path.write_text(gitignore_text, encoding="utf-8")

    include_core = target_root == repo_root
    _apply_core_config(target_root, include_core)

    version_existed = version_path.exists()
    if version_mode != "skip" and (
        version_mode == "overwrite" or not version_existed
    ):
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        if not version_existed:
            installed["docs"].append("VERSION")

    license_path = target_root / "LICENSE"
    license_existed = license_path.exists()
    if license_mode != "skip" and (
        license_mode == "overwrite" or not license_existed
    ):
        if license_existed and license_mode == "overwrite":
            _rename_existing_file(license_path)
        license_template = _resolve_source_path(
            repo_root, template_root, LICENSE_TEMPLATE
        )
        if license_template.exists():
            license_body = license_template.read_text(encoding="utf-8")
            license_text = (
                f"Project Version: {target_version}\n\n{license_body}"
            )
            license_path.write_text(license_text, encoding="utf-8")
            if not license_existed:
                installed["docs"].append("LICENSE")

    citation_path = target_root / "CITATION.cff"
    citation_existed = citation_path.exists()
    create_citation = False
    if not citation_existed and metadata_mode != "skip":
        if args.citation_mode == "create":
            create_citation = True
        elif args.citation_mode == "prompt":
            create_citation = _prompt_yes_no(
                "Create CITATION.cff for this repository?"
            )
    if create_citation:
        citation_path.write_text(
            _render_citation_template(repo_name, target_version),
            encoding="utf-8",
        )
        installed["docs"].append("CITATION.cff")

    if pyproject_mode != "skip":
        pyproject_sources = {
            "pyproject.toml": _resolve_source_path(
                repo_root, template_root, "pyproject.toml"
            )
        }
        installed["docs"].extend(
            _install_paths(
                repo_root,
                target_root,
                ["pyproject.toml"],
                skip_existing=(
                    mode == "existing" and pyproject_mode == "preserve"
                ),
                source_overrides=pyproject_sources,
            )
        )

    agents_template = _resolve_source_path(
        repo_root, template_root, "AGENTS.md"
    )
    agents_existed = agents_path.exists()
    if agents_template.exists():
        agents_text = agents_template.read_text(encoding="utf-8")
        agents_path.write_text(agents_text, encoding="utf-8")
        if not agents_existed:
            installed["docs"].append("AGENTS.md")
        _apply_standard_header(agents_path, last_updated, target_version)
        if existing_agents_text:
            _preserve_editable_section(agents_path, existing_agents_text)

    if not (citation_existed or create_citation):
        _disable_citation_in_agents(agents_path)

    readme_path = target_root / "README.md"
    if not readme_path.exists():
        base_readme = (
            f"# {repo_name}\n\n"
            "Replace this README content with a project-specific overview.\n"
        )
        base_readme = _ensure_standard_header(
            base_readme, last_updated, target_version, title=repo_name
        )
        readme_path.write_text(base_readme, encoding="utf-8")
        installed["docs"].append("README.md")

    readme_text = readme_path.read_text(encoding="utf-8")
    scan_text = _strip_devcov_block(readme_text)
    has_toc = _has_heading(scan_text, "Table of Contents")
    has_overview = _has_heading(scan_text, "Overview")
    has_workflow = _has_heading(scan_text, "Workflow")
    has_devcovenant = _has_heading(scan_text, "DevCovenant")
    readme_block = _build_readme_block(
        has_overview, has_workflow, has_toc, has_devcovenant
    )
    updated_readme = _ensure_standard_header(
        readme_text, last_updated, target_version, title=repo_name
    )
    readme_path.write_text(updated_readme, encoding="utf-8")
    _inject_block(readme_path, readme_block)
    if BLOCK_BEGIN in readme_path.read_text(encoding="utf-8"):
        doc_blocks.append("README.md")

    devcov_path = target_root / "DEVCOVENANT.md"
    devcov_template = _resolve_source_path(
        repo_root, template_root, "DEVCOVENANT.md"
    )
    if devcov_template.exists():
        if devcov_path.exists():
            _rename_existing_file(devcov_path)
        devcov_text = devcov_template.read_text(encoding="utf-8")
        devcov_text = _ensure_standard_header(
            devcov_text, last_updated, target_version
        )
        devcov_path.write_text(devcov_text, encoding="utf-8")
        installed["docs"].append("DEVCOVENANT.md")
    elif devcov_path.exists():
        _apply_standard_header(devcov_path, last_updated, target_version)

    spec_path = target_root / "SPEC.md"
    if spec_path.exists():
        _apply_standard_header(spec_path, last_updated, target_version)
    else:
        spec_path.write_text(
            _render_spec_template(target_version, last_updated),
            encoding="utf-8",
        )
        installed["docs"].append("SPEC.md")

    plan_path = target_root / "PLAN.md"
    if plan_path.exists():
        _apply_standard_header(plan_path, last_updated, target_version)
    else:
        plan_path.write_text(
            _render_plan_template(target_version, last_updated),
            encoding="utf-8",
        )
        installed["docs"].append("PLAN.md")

    changelog_path = target_root / "CHANGELOG.md"
    if changelog_path.exists():
        _rename_existing_file(changelog_path)
    changelog_path.write_text(
        _render_changelog_template(target_version, last_updated),
        encoding="utf-8",
    )
    installed["docs"].append("CHANGELOG.md")

    contributing_path = target_root / "CONTRIBUTING.md"
    contributing_template = _resolve_source_path(
        repo_root, template_root, "CONTRIBUTING.md"
    )
    if contributing_template.exists():
        if contributing_path.exists():
            _rename_existing_file(contributing_path)
        contributing_text = contributing_template.read_text(encoding="utf-8")
        contributing_text = _ensure_standard_header(
            contributing_text, last_updated, target_version
        )
        contributing_path.write_text(contributing_text, encoding="utf-8")
        installed["docs"].append("CONTRIBUTING.md")
        if BLOCK_BEGIN in contributing_text and BLOCK_END in contributing_text:
            doc_blocks.append("CONTRIBUTING.md")

    internal_docs = [
        "devcovenant/README.md",
        "devcovenant/common_policy_patches/README.md",
        "devcovenant/custom/policy_scripts/README.md",
    ]
    for rel_path in internal_docs:
        _apply_standard_header(
            target_root / rel_path, last_updated, target_version
        )
    if devcovenant_version:
        _update_devcovenant_version(
            target_root / "devcovenant/README.md", devcovenant_version
        )

    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "mode": "update" if mode == "existing" else "install",
                "installed": installed,
                "doc_blocks": doc_blocks,
                "options": {
                    "docs_mode": docs_mode,
                    "config_mode": config_mode,
                    "metadata_mode": metadata_mode,
                    "license_mode": license_mode,
                    "version_mode": version_mode,
                    "target_version": target_version,
                    "pyproject_mode": pyproject_mode,
                    "ci_mode": ci_mode,
                    "citation_mode": args.citation_mode,
                    "preserve_custom": preserve_custom,
                    "devcov_core_include": include_core,
                },
            },
            indent=2,
            sort_keys=True,
        )
        