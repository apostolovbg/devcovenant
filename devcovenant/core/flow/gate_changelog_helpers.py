"""Internal helpers for gate changelog/session baseline metadata."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from devcovenant.core.services import registry as registry_runtime_module

_DATE_ENTRY_PATTERN = re.compile(r"^\s*-\s*\d{4}-\d{2}-\d{2}\b")
_MANAGED_BEGIN = "<!-- DEVCOV:BEGIN -->"
_MANAGED_END = "<!-- DEVCOV:END -->"
_LOG_MARKER = "## Log changes here"


def _visible_changelog_lines(changelog_text: str) -> list[str]:
    """Return changelog lines outside managed blocks and fenced examples."""
    start = changelog_text.find(_LOG_MARKER)
    content = changelog_text[start:] if start >= 0 else changelog_text
    visible: list[str] = []
    in_managed = False
    in_fence = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == _MANAGED_BEGIN:
            in_managed = True
            continue
        if stripped == _MANAGED_END:
            in_managed = False
            continue
        if in_managed:
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        visible.append(line)
    return visible


def _latest_changelog_entry(repo_root: Path) -> str:
    """Return the topmost changelog entry from the latest version section."""
    changelog_path = repo_root / _resolve_main_changelog(repo_root)
    if not changelog_path.exists():
        return ""
    lines = _visible_changelog_lines(
        changelog_path.read_text(encoding="utf-8")
    )

    version_start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith("## Version"):
            version_start = index
            break
    if version_start is None:
        return ""

    entry_start: int | None = None
    for index in range(version_start + 1, len(lines)):
        if _DATE_ENTRY_PATTERN.match(lines[index]):
            entry_start = index
            break
    if entry_start is None:
        return ""

    entry_end = len(lines)
    for index in range(entry_start + 1, len(lines)):
        if _DATE_ENTRY_PATTERN.match(lines[index]):
            entry_end = index
            break

    return "\n".join(lines[entry_start:entry_end]).strip()


def _resolve_main_changelog(repo_root: Path) -> Path:
    """Resolve main changelog path from changelog-coverage metadata."""
    metadata = _load_changelog_metadata(repo_root)
    raw_target = metadata.get("main_changelog", "")
    if isinstance(raw_target, list):
        target = ""
        for entry in raw_target:
            token = str(entry).strip()
            if token:
                target = token
                break
    else:
        target = str(raw_target).strip()
    if not target:
        raise ValueError(
            (
                "`changelog-coverage.main_changelog` is missing in "
                "policy metadata."
            )
        )
    return Path(target)


def _load_changelog_metadata(repo_root: Path) -> dict[str, object]:
    """Return changelog-coverage metadata mapping from policy registry."""
    registry_path = registry_runtime_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        raise ValueError(
            f"Missing policy registry file: {registry_path}. "
            "Run `devcovenant refresh`."
        )
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in policy registry {registry_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Unable to read policy registry {registry_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Invalid policy registry payload in {registry_path}: "
            "expected a mapping."
        )
    policies = payload.get("policies", {})
    if not isinstance(policies, dict):
        raise ValueError(
            f"Invalid policy registry payload in {registry_path}: "
            "`policies` must be a mapping."
        )
    changelog_coverage = policies.get("changelog-coverage", {})
    if not isinstance(changelog_coverage, dict):
        raise ValueError(
            "Missing `changelog-coverage` policy entry in policy registry."
        )
    metadata = changelog_coverage.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(
            "Invalid `changelog-coverage.metadata` payload in policy registry."
        )
    return metadata


def _normalize_list_option(
    value: object,
    default: list[str],
) -> list[str]:
    """Normalize metadata value into non-empty string list."""
    if value is None:
        source: list[str] = default
    elif isinstance(value, str):
        source = [entry.strip() for entry in value.split(",") if entry.strip()]
    elif isinstance(value, list):
        source = [str(entry).strip() for entry in value if str(entry).strip()]
    else:
        source = [str(value).strip()]
    normalized = [entry for entry in source if entry]
    return normalized or default


def _resolve_doc_exemption_options(
    repo_root: Path,
) -> tuple[list[str], list[str], int]:
    """Resolve doc allowlist metadata from changelog-coverage descriptor."""
    metadata = _load_changelog_metadata(repo_root)
    suffixes = _normalize_list_option(
        metadata.get("header_doc_suffixes"),
        [".md", ".rst", ".txt"],
    )
    header_keys = _normalize_list_option(
        metadata.get("header_keys"),
        ["Last Updated", "Project Version", "DevCovenant Version"],
    )
    raw_scan = metadata.get("header_scan_lines", 4)
    try:
        scan_lines = int(raw_scan)
    except (TypeError, ValueError):
        scan_lines = 4
    if scan_lines < 0:
        scan_lines = 0
    return suffixes, header_keys, scan_lines


def _entry_fingerprint(entry_text: str) -> str:
    """Return a deterministic hash for an entry block."""
    if not entry_text.strip():
        return ""
    normalized = "\n".join(
        line.rstrip() for line in entry_text.strip().splitlines()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
