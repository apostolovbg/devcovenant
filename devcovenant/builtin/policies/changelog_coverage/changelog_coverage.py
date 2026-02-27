"""
Policy: Changelog Coverage

Routes each changed file to the proper changelog based on the metadata-defined
`main_changelog`, `skipped_files` and `collections` options.
"""

import fnmatch
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, List

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.lib import document_exemptions as document_exemptions_lib
from devcovenant.core.lib.document_exemptions import (
    DEFAULT_HEADER_DOC_SUFFIXES,
    DEFAULT_HEADER_KEYS,
    DEFAULT_HEADER_SCAN_LINES,
)
from devcovenant.core.lib.document_exemptions import (
    document_exemption_fingerprint_for_path as _allowlist_fingerprint_for_path,
)
from devcovenant.core.lib.document_exemptions import (
    normalize_document_exemption_entry as _normalize_exemption_entry,
)
from devcovenant.core.runtime import execution as execution_runtime_module

# Compatibility alias used by tests that monkeypatch runtime snapshot capture.
capture_current_numstat_snapshot = (
    execution_runtime_module.capture_current_numstat_snapshot
)


def _find_markers(content: str) -> tuple[int | None, list[int]]:
    """Return the log-marker position and version header positions."""

    log_index = None
    version_positions: list[int] = []
    in_fence = False
    offset = 0
    for line in content.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            if stripped.startswith("## Log changes here"):
                log_index = offset
            if stripped.startswith("## Version"):
                version_positions.append(offset)
        offset += len(line)
    return log_index, version_positions


def _collapse_line_continuations(section: str) -> str:
    """Collapse backslash-continued lines into full strings."""
    lines = section.splitlines()
    merged: list[str] = []
    buffer = ""
    for line in lines:
        current = line
        if buffer:
            current = buffer + current.lstrip()
            buffer = ""
        if current.rstrip().endswith("\\"):
            buffer = current.rstrip()[:-1]
            continue
        merged.append(current)
    if buffer:
        merged.append(buffer)
    return "\n".join(merged)


def _latest_section(content: str) -> str:
    """Return the newest version section from a changelog."""

    log_index, version_positions = _find_markers(content)
    if not version_positions:
        return content
    start = None
    if log_index is not None:
        for pos in version_positions:
            if pos >= log_index:
                start = pos
                break
    if start is None:
        start = version_positions[0]
    next_start = None
    for pos in version_positions:
        if pos > start:
            next_start = pos
            break
    if next_start is None:
        return content[start:]
    return content[start:next_start]


def _first_entry(section: str) -> tuple[str | None, str]:
    """
    Return (date, entry_text) for the newest entry in a section.

    Assumes entries start with "- YYYY-MM-DD:"; returns (None, "") if none.
    """
    lines = section.splitlines()
    start = None
    for idx, line in enumerate(lines):
        date_match = _DATE_PATTERN.match(line)
        if date_match:
            start = idx
            entry_date = date_match.group(1)
            break
    if start is None:
        return None, ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _DATE_PATTERN.match(lines[j]):
            end = j
            break
    entry_text = "\n".join(lines[start:end])
    return entry_date, entry_text


_DATE_PATTERN = re.compile(r"^\s*-\s*(\d{4}-\d{2}-\d{2})\b")
_DEFAULT_GATE_STATUS_PATH = (
    Path("devcovenant") / "registry" / "local" / "gate_status.json"
)
_ALLOWLIST_DOC_SUFFIXES = set(DEFAULT_HEADER_DOC_SUFFIXES)
_ALLOWLIST_HEADER_KEYS = set(DEFAULT_HEADER_KEYS)
_ALLOWLIST_HEADER_SCAN_LINES = DEFAULT_HEADER_SCAN_LINES
_marker_signature = document_exemptions_lib.managed_marker_signature
_non_exempt_content_hash = document_exemptions_lib.non_exempt_content_hash


def _extract_summary_lines(
    entry_text: str, labels: list[str]
) -> dict[str, str]:
    """Return a mapping of summary labels to their text."""
    summaries: dict[str, str] = {}
    if not labels:
        return summaries
    lower_labels = {label.lower(): label for label in labels}
    after_date = False
    for raw_line in entry_text.splitlines():
        if not after_date:
            if _DATE_PATTERN.match(raw_line):
                after_date = True
            continue
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("files:"):
            break
        for lower_label, label in lower_labels.items():
            prefix = f"{lower_label}:"
            if stripped.lower().startswith(prefix):
                summary_value = stripped.split(":", 1)[1].strip()
                if summary_value:
                    summaries[label] = summary_value
                break
    return summaries


def _normalize_labels(raw_value: object, default: list[str]) -> list[str]:
    """Normalize summary labels metadata into a list."""
    if raw_value is None:
        return default
    if isinstance(raw_value, str):
        entries = [item.strip() for item in raw_value.split(",") if item]
        return entries or default
    if isinstance(raw_value, list):
        entries = [
            str(item).strip() for item in raw_value if str(item).strip()
        ]
        return entries or default
    return default


def _normalize_verbs(raw_value: object) -> list[str]:
    """Normalize summary verb metadata into a lowercased list."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        entries = [item.strip() for item in raw_value.split(",") if item]
    elif isinstance(raw_value, list):
        entries = [
            str(item).strip() for item in raw_value if str(item).strip()
        ]
    else:
        entries = [str(raw_value).strip()]
    verbs = [verb.lower() for verb in entries if verb]
    return verbs


def _line_has_verb(line: str, verbs: list[str]) -> bool:
    """Return True if any configured verb root appears at word-start."""
    if not line or not verbs:
        return False
    lower_line = line.lower()
    words = re.findall(r"\b[\w'-]+\b", lower_line)
    for verb in (entry for entry in verbs if entry):
        roots = {verb}
        if len(verb) > 2 and verb.endswith("e"):
            roots.add(verb[:-1])
        if len(verb) > 2 and verb.endswith("y"):
            roots.add(f"{verb[:-1]}i")
        if any(word.startswith(root) for word in words for root in roots):
            return True
    return False


def _normalize_globs(raw_value: object) -> list[str]:
    """Normalize a metadata glob value into a list."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [entry.strip() for entry in raw_value.split(",") if entry]
    if isinstance(raw_value, list):
        return [
            str(entry).strip() for entry in raw_value if str(entry).strip()
        ]
    return [str(raw_value).strip()]


def _normalize_paths(raw_value: object, default: list[str]) -> list[str]:
    """Normalize path metadata into a list of POSIX-style paths."""
    if raw_value is None:
        source = default
    elif isinstance(raw_value, str):
        source = [entry for entry in raw_value.split(",") if entry]
    elif isinstance(raw_value, list):
        source = [str(entry) for entry in raw_value if str(entry)]
    else:
        source = [str(raw_value)]
    normalized: list[str] = []
    for entry in source:
        token = str(entry).strip().replace("\\", "/")
        if token:
            normalized.append(token)
    return normalized


def _session_deleted_paths(
    *,
    gate_status: dict[str, object],
    current_snapshot_paths: set[str],
) -> set[str]:
    """
    Return session-scoped deleted paths from the gate-start snapshot.

    Deleted-file coverage is derived from the session snapshot baseline and
    never from git working-tree/HEAD diff state.
    """
    raw_snapshot = gate_status.get("session_start_snapshot")
    if not isinstance(raw_snapshot, dict):
        return set()
    start_paths: set[str] = set()
    for raw_path in raw_snapshot:
        token = str(raw_path).strip().replace("\\", "/")
        if token:
            start_paths.add(token)
    return start_paths.difference(current_snapshot_paths)


def _deleted_paths_for_changelog_coverage(
    context: CheckContext,
    *,
    phase: str,
    gate_status: dict[str, object],
) -> set[str]:
    """
    Return deleted paths relevant to the current coverage scope.

    `gate --start` validates the pre-edit baseline and must not import deleted
    paths. Non-start checks require a valid gate session and derive deletions
    from the gate-start snapshot only.
    """
    if phase == "start":
        return set()
    if not context.change_state.session_valid:
        return set()
    current_snapshot_paths = {
        str(path).replace("\\", "/")
        for path in context.change_state.current_snapshot_numstat.keys()
    }
    return _session_deleted_paths(
        gate_status=gate_status,
        current_snapshot_paths=current_snapshot_paths,
    )


def _is_skipped_coverage_path(
    relative_path: str,
    *,
    skip_files: list[str],
    skip_prefixes: list[str],
    skip_globs: list[str],
) -> bool:
    """Return True when a path is out of scope via changelog skip metadata."""
    normalized_path = relative_path.replace("\\", "/")
    if normalized_path in skip_files:
        return True
    if any(
        normalized_path == prefix or normalized_path.startswith(f"{prefix}/")
        for prefix in skip_prefixes
    ):
        return True
    if skip_globs and any(
        fnmatch.fnmatch(normalized_path, pattern) for pattern in skip_globs
    ):
        return True
    return False


def _normalize_doc_suffixes(raw_value: object) -> set[str]:
    """Normalize metadata suffixes used for header-only exemptions."""
    values = _normalize_paths(raw_value, list(_ALLOWLIST_DOC_SUFFIXES))
    normalized = {
        entry.lower() if entry.startswith(".") else f".{entry.lower()}"
        for entry in values
        if entry
    }
    return normalized or set(_ALLOWLIST_DOC_SUFFIXES)


def _normalize_header_keys(raw_value: object) -> set[str]:
    """Normalize metadata header keys used for header-only exemptions."""
    values = _normalize_paths(raw_value, list(_ALLOWLIST_HEADER_KEYS))
    normalized = {entry.strip().lower() for entry in values if entry.strip()}
    return normalized or set(_ALLOWLIST_HEADER_KEYS)


def _normalize_header_scan_lines(raw_value: object) -> int:
    """Normalize metadata line window used for header-only exemptions."""
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = _ALLOWLIST_HEADER_SCAN_LINES
    if value < 0:
        value = 0
    return value


# Shared exemption fingerprint helpers are imported from
# `devcovenant.core.lib.document_exemptions` to keep gate-session baseline
# capture and changelog-coverage checks on one canonical implementation.


def _load_document_exemption_baseline(
    gate_status: dict[str, object],
) -> dict[str, dict[str, str]]:
    """Return optional validated document allowlist baseline mapping."""
    snapshot_key = "document_exemption_baseline"
    if snapshot_key not in gate_status:
        return {}
    raw_snapshot = gate_status[snapshot_key]
    if not isinstance(raw_snapshot, dict):
        raise ValueError(
            "Invalid gate status payload: "
            "`document_exemption_baseline` must be a mapping."
        )
    snapshot: dict[str, dict[str, str]] = {}
    for raw_path, raw_entry in raw_snapshot.items():
        path = str(raw_path).strip()
        if not path:
            raise ValueError(
                "Invalid gate status payload: "
                "`document_exemption_baseline` contains empty "
                "paths."
            )
        snapshot[path] = _normalize_exemption_entry(
            raw_entry,
            relative_path=path,
        )
    return snapshot


def _is_exempt_range_only_change(
    repo_root: Path,
    relative_path: str,
    *,
    start_exemption_fingerprints: dict[str, dict[str, str]],
    header_doc_suffixes: set[str],
    header_keys: set[str],
    header_scan_lines: int,
) -> bool:
    """Return True when only managed/header ranges changed in one file."""
    start_entry = start_exemption_fingerprints.get(relative_path)
    if start_entry is None:
        return False
    current_entry = _allowlist_fingerprint_for_path(
        repo_root,
        relative_path,
        header_doc_suffixes=header_doc_suffixes,
        header_keys=header_keys,
        header_scan_lines=header_scan_lines,
    )
    if current_entry is None:
        return False
    if start_entry.get("managed_marker_signature") != current_entry.get(
        "managed_marker_signature"
    ):
        return False
    return start_entry.get("non_exempt_content_sha256") == current_entry.get(
        "non_exempt_content_sha256"
    )


_DEFAULT_SUMMARY_LABELS = ["Change", "Why", "Impact"]


def _extract_entry_files(entry_text: str) -> list[str]:
    """Extract file paths from a Files: block inside an entry."""
    files: list[str] = []
    lines = entry_text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith("files:"):
            remainder = line.split(":", 1)[1].strip()
            if remainder:
                files.append(remainder)
            for follow in lines[idx + 1 :]:
                if _DATE_PATTERN.match(follow) or follow.lstrip().startswith(
                    "##"
                ):
                    return files
                stripped = follow.strip()
                if not stripped:
                    continue
                if stripped.startswith("-"):
                    stripped = stripped[1:].strip()
                if stripped:
                    files.append(stripped)
            return files
    return files


def _entry_blocks(section: str) -> list[str]:
    """Return dated entry blocks from the latest changelog section."""
    lines = section.splitlines()
    starts = [
        index for index, line in enumerate(lines) if _DATE_PATTERN.match(line)
    ]
    blocks: list[str] = []
    for position, start in enumerate(starts):
        end = (
            starts[position + 1] if position + 1 < len(starts) else len(lines)
        )
        block = "\n".join(lines[start:end]).strip()
        if block:
            blocks.append(block)
    return blocks


def _entry_fingerprint(entry_text: str) -> str:
    """Return a deterministic fingerprint for one changelog entry."""
    if not entry_text.strip():
        return ""
    normalized = "\n".join(
        line.rstrip() for line in entry_text.strip().splitlines()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_gate_status(status_path: Path) -> dict[str, object]:
    """Load gate status JSON payload from disk."""
    if not status_path.exists():
        raise ValueError(
            f"Gate status file is missing: {status_path}. "
            "Run `devcovenant gate --start` first."
        )
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid gate status JSON in {status_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Gate status payload must be a mapping: {status_path}"
        )
    return payload


_COLLECTIONS_DISABLE_TOKENS = {"none", "off", "false", "no"}


def _find_order_violation(section: str) -> tuple[str, str] | None:
    """Return the first out-of-order date pair, if any."""
    entries: list[tuple[str, date]] = []
    for line in section.splitlines():
        match = _DATE_PATTERN.match(line)
        if not match:
            continue
        raw_date = match.group(1)
        try:
            parsed = date.fromisoformat(raw_date)
        except ValueError:
            continue
        entries.append((raw_date, parsed))

    for index in range(1, len(entries)):
        prev_raw, prev_date = entries[index - 1]
        current_raw, current_date = entries[index]
        if current_date > prev_date:
            return prev_raw, current_raw
    return None


class ChangelogCoverageCheck(PolicyCheck):
    """Verify that modified files land in the appropriate changelog."""

    policy_id = "changelog-coverage"
    version = "2.4.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """
        Check if all changed files are documented in the relevant changelog.

        Args:
            context: Check context with repository info

        Returns:
            List of violations (empty if all files are documented)
        """
        violations: List[Violation] = []
        main_changelog_rel = Path(
            self.get_option("main_changelog", "CHANGELOG.md")
        )
        skip_option = self.get_option(
            "skipped_files",
            [
                "CHANGELOG.md",
                ".gitignore",
                ".pre-commit-config.yaml",
            ],
        )
        if isinstance(skip_option, str):
            skip_files = {
                entry.strip()
                for entry in skip_option.split(",")
                if entry.strip()
            }
        else:
            skip_files = set(skip_option or [])
        skip_prefix_option = self.get_option("skipped_prefixes", [])
        if isinstance(skip_prefix_option, str):
            skip_prefixes = [
                entry.strip()
                for entry in skip_prefix_option.split(",")
                if entry.strip()
            ]
        else:
            skip_prefixes = [
                str(entry).strip()
                for entry in (skip_prefix_option or [])
                if str(entry).strip()
            ]
        skip_prefixes = [entry.rstrip("/") for entry in skip_prefixes if entry]
        skip_globs = _normalize_globs(self.get_option("skipped_globs", []))
        summary_labels = _normalize_labels(
            self.get_option("summary_labels"), _DEFAULT_SUMMARY_LABELS
        )
        summary_verbs = _normalize_verbs(self.get_option("summary_verbs"))
        header_doc_suffixes = _normalize_doc_suffixes(
            self.get_option(
                "header_doc_suffixes", list(_ALLOWLIST_DOC_SUFFIXES)
            )
        )
        header_keys = _normalize_header_keys(
            self.get_option("header_keys", list(_ALLOWLIST_HEADER_KEYS))
        )
        header_scan_lines = _normalize_header_scan_lines(
            self.get_option("header_scan_lines", _ALLOWLIST_HEADER_SCAN_LINES)
        )
        if not summary_verbs:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=context.repo_root / main_changelog_rel,
                    message=(
                        "Missing `summary_verbs` metadata for "
                        "changelog-coverage."
                    ),
                    suggestion=(
                        "Define `summary_verbs` in policy metadata and rerun."
                    ),
                    can_auto_fix=False,
                )
            )
            return violations
        gate_status_rel = Path(
            self.get_option("gate_status_file", str(_DEFAULT_GATE_STATUS_PATH))
        )
        phase = (
            context.change_state.phase
            or os.environ.get("DEVCOV_DEVFLOW_PHASE", "").strip().lower()
        )

        try:
            collections = self._resolve_collections(
                self.get_option("collections", [])
            )
        except ValueError as error:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=context.repo_root / main_changelog_rel,
                    message=f"Invalid `collections` metadata: {error}",
                    can_auto_fix=False,
                )
            )
            return violations

        try:
            changed_files = [
                changed.relative_to(context.repo_root).as_posix()
                for changed in self.scoped_changed_files(context)
            ]
        except ValueError as error:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=context.repo_root / gate_status_rel,
                    message=str(error),
                    can_auto_fix=False,
                )
            )
            return violations

        gate_status: dict[str, object] = {}
        start_exemption_fingerprints: dict[str, dict[str, str]] = {}
        if phase != "start":
            default_status_rel = Path(context.change_state.gate_status_path)
            if gate_status_rel == default_status_rel:
                gate_status = dict(context.change_state.gate_status_payload)
            if not gate_status:
                try:
                    gate_status = _load_gate_status(
                        context.repo_root / gate_status_rel
                    )
                except ValueError as error:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=context.repo_root / gate_status_rel,
                            message=str(error),
                            can_auto_fix=False,
                        )
                    )
                    return violations
            try:
                start_exemption_fingerprints = (
                    _load_document_exemption_baseline(gate_status)
                )
            except ValueError as error:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=context.repo_root / gate_status_rel,
                        message=str(error),
                        can_auto_fix=False,
                    )
                )
                return violations

        try:
            deleted_file_set = _deleted_paths_for_changelog_coverage(
                context,
                phase=phase,
                gate_status=gate_status,
            )
        except ValueError as error:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=context.repo_root / gate_status_rel,
                    message=str(error),
                    can_auto_fix=False,
                )
            )
            return violations
        if deleted_file_set:
            merged_changed = set(changed_files)
            merged_changed.update(deleted_file_set)
            changed_files = sorted(merged_changed)
        if not changed_files:
            return violations
        changed_file_set = set(changed_files)

        main_files: List[str] = []
        collection_files: List[List[str]] = [[] for _ in collections]

        for file_path in changed_files:
            normalized_path = file_path.replace("\\", "/")
            if _is_exempt_range_only_change(
                context.repo_root,
                normalized_path,
                start_exemption_fingerprints=start_exemption_fingerprints,
                header_doc_suffixes=header_doc_suffixes,
                header_keys=header_keys,
                header_scan_lines=header_scan_lines,
            ):
                continue
            if _is_skipped_coverage_path(
                normalized_path,
                skip_files=skip_files,
                skip_prefixes=skip_prefixes,
                skip_globs=skip_globs,
            ):
                continue
            assigned = False
            for index, entry in enumerate(collections):
                prefix = entry.get("prefix", "")
                if prefix and file_path.startswith(prefix):
                    collection_files[index].append(file_path)
                    assigned = True
                    break
            if not assigned:
                main_files.append(file_path)

        root_changelog = context.repo_root / main_changelog_rel
        should_read_root = (
            main_files or any(collection_files)
        ) and root_changelog.exists()
        root_content = (
            root_changelog.read_text(encoding="utf-8")
            if should_read_root
            else None
        )
        root_section = (
            _latest_section(root_content) if root_content is not None else None
        )
        section_for_matching = (
            _collapse_line_continuations(root_section)
            if root_section is not None
            else ""
        )
        first_date, first_entry = (
            _first_entry(section_for_matching)
            if section_for_matching
            else (None, "")
        )
        if root_section:
            order_issue = _find_order_violation(root_section)
            if order_issue:
                older, newer = order_issue
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=root_changelog,
                        message=(
                            "Changelog entries must be newest-first "
                            f"(descending dates). Found {newer} listed "
                            f"below older entry {older}."
                        ),
                        suggestion=(
                            f"Move the {newer} entry above {older} in "
                            f"{main_changelog_rel.as_posix()}."
                        ),
                        can_auto_fix=False,
                    )
                )

        if main_files:
            if root_content is None:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        message=(
                            f"{main_changelog_rel.as_posix()} does not exist"
                        ),
                        suggestion=(
                            f"Create {main_changelog_rel.as_posix()} and "
                            "document the changes listed in the diff."
                        ),
                        can_auto_fix=False,
                    )
                )
            else:
                require_new_session_entry = False
                snapshot_preservation_failed = False
                if phase != "start":
                    session_state = (
                        str(gate_status.get("session_state", ""))
                        .strip()
                        .lower()
                    )
                    snapshot_fingerprint = ""
                    if session_state == "open":
                        snapshot_fingerprint = str(
                            gate_status.get(
                                "changelog_start_top_entry_fingerprint", ""
                            )
                        ).strip()
                    entry_blocks = _entry_blocks(root_section or "")
                    current_fingerprint = (
                        _entry_fingerprint(entry_blocks[0])
                        if entry_blocks
                        else ""
                    )
                    if snapshot_fingerprint:
                        if current_fingerprint == snapshot_fingerprint:
                            require_new_session_entry = True
                            violations.append(
                                Violation(
                                    policy_id=self.policy_id,
                                    severity="error",
                                    file_path=root_changelog,
                                    message=(
                                        "Latest changelog entry matches the "
                                        "gate-start snapshot. Add a new entry "
                                        "for this session."
                                    ),
                                    suggestion=(
                                        "Prepend a new dated changelog entry "
                                        "for this work and keep the previous "
                                        "top entry below it."
                                    ),
                                    can_auto_fix=False,
                                )
                            )
                        else:
                            expected_previous_fingerprint = (
                                _entry_fingerprint(entry_blocks[1])
                                if len(entry_blocks) > 1
                                else ""
                            )
                            if (
                                expected_previous_fingerprint
                                != snapshot_fingerprint
                            ):
                                snapshot_preservation_failed = True
                                snapshot_message = (
                                    "Gate-start changelog snapshot was "
                                    "edited, removed, or moved out of the "
                                    "second position. A new entry must be "
                                    "prepended and the prior top entry must "
                                    "remain directly below it."
                                )
                                snapshot_suggestion = (
                                    "Add a fresh top entry and keep the "
                                    "pre-session top entry intact as the "
                                    "next entry."
                                )
                                violations.append(
                                    Violation(
                                        policy_id=self.policy_id,
                                        severity="error",
                                        file_path=root_changelog,
                                        message=snapshot_message,
                                        suggestion=snapshot_suggestion,
                                        can_auto_fix=False,
                                    )
                                )
                    elif not current_fingerprint:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "No changelog entry exists for this "
                                    "session. Add a new top entry."
                                ),
                                suggestion=(
                                    "Create a dated entry at the top of the "
                                    "current version section before listing "
                                    "changed files."
                                ),
                                can_auto_fix=False,
                            )
                        )
                if not (
                    require_new_session_entry or snapshot_preservation_failed
                ):
                    # Keep snapshot enforcement deterministic: defer
                    # entry-shape checks until a fresh top entry exists.
                    today = date.today().isoformat()
                    if first_date != today:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "Log a fresh changelog entry dated today "
                                    f"({today}) for this change."
                                ),
                                suggestion=(
                                    "Add a new entry at the top of the "
                                    "current version section dated "
                                    f"{today} and list all touched files."
                                ),
                                can_auto_fix=False,
                            )
                        )
                    summary_lines = _extract_summary_lines(
                        first_entry, summary_labels
                    )
                    missing_labels = [
                        label
                        for label in summary_labels
                        if label not in summary_lines
                    ]
                    if missing_labels:
                        labels_str = ", ".join(missing_labels)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "Latest changelog entry must include "
                                    "labeled summary lines for: "
                                    f"{labels_str}."
                                ),
                                suggestion=(
                                    "Add Change/Why/Impact summary lines "
                                    "directly under the dated entry."
                                ),
                                can_auto_fix=False,
                            )
                        )
                    else:
                        missing_verbs = [
                            label
                            for label in summary_labels
                            if not _line_has_verb(
                                summary_lines.get(label, ""), summary_verbs
                            )
                        ]
                        if missing_verbs:
                            labels_str = ", ".join(missing_verbs)
                            violations.append(
                                Violation(
                                    policy_id=self.policy_id,
                                    severity="error",
                                    file_path=root_changelog,
                                    message=(
                                        "Summary lines must include an "
                                        "action verb from the configured "
                                        "list. Missing verbs in: "
                                        f"{labels_str}."
                                    ),
                                    suggestion=(
                                        "Revise the Change/Why/Impact lines "
                                        "to include a clear action verb."
                                    ),
                                    can_auto_fix=False,
                                )
                            )
                    entry_files = _extract_entry_files(first_entry)
                    if not entry_files:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "Latest changelog entry must include a "
                                    "Files: block listing all touched paths."
                                ),
                                suggestion=(
                                    "Add a Files: block under the latest "
                                    "entry and list each modified path."
                                ),
                                can_auto_fix=False,
                            )
                        )
                    missing = [
                        path for path in main_files if path not in entry_files
                    ]
                    if missing:
                        files_str = ", ".join(missing)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "The following files are not mentioned in "
                                    f"{main_changelog_rel.as_posix()}: "
                                    f"{files_str}"
                                ),
                                suggestion=(
                                    "Add entries to "
                                    f"{main_changelog_rel.as_posix()} "
                                    f"documenting changes to: {files_str}"
                                ),
                                can_auto_fix=False,
                            )
                        )
                    extra: list[str] = []
                    for path in entry_files:
                        normalized_path = path.replace("\\", "/")
                        if normalized_path in main_files:
                            continue
                        if _is_skipped_coverage_path(
                            normalized_path,
                            skip_files=skip_files,
                            skip_prefixes=skip_prefixes,
                            skip_globs=skip_globs,
                        ):
                            continue
                        if normalized_path in deleted_file_set:
                            continue
                        if (
                            normalized_path in changed_file_set
                            and _is_exempt_range_only_change(
                                context.repo_root,
                                normalized_path,
                                start_exemption_fingerprints=(
                                    start_exemption_fingerprints
                                ),
                                header_doc_suffixes=header_doc_suffixes,
                                header_keys=header_keys,
                                header_scan_lines=header_scan_lines,
                            )
                        ):
                            continue
                        extra.append(path)
                    if extra:
                        files_str = ", ".join(extra)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=root_changelog,
                                message=(
                                    "Latest changelog entry lists files "
                                    "not in the current change: "
                                    f"{files_str}"
                                ),
                                suggestion=(
                                    "Move those paths into a separate entry "
                                    "and keep the latest entry focused on "
                                    "this change only."
                                ),
                                can_auto_fix=False,
                            )
                        )

        for index, entry in enumerate(collections):
            files_for_collection = collection_files[index]
            changelog_rel = entry.get("changelog")
            changelog_path = context.repo_root / changelog_rel
            exclusive = entry.get("exclusive", True)

            changelog_content = (
                changelog_path.read_text(encoding="utf-8")
                if files_for_collection and changelog_path.exists()
                else None
            )
            changelog_section = (
                _latest_section(changelog_content)
                if changelog_content
                else None
            )
            entry_date, entry_text = (
                _first_entry(_collapse_line_continuations(changelog_section))
                if changelog_section
                else (None, "")
            )
            if changelog_section:
                order_issue = _find_order_violation(changelog_section)
                if order_issue:
                    older, newer = order_issue
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=changelog_path,
                            message=(
                                "Changelog entries must be newest-first "
                                f"(descending dates). Found {newer} listed "
                                f"below older entry {older}."
                            ),
                            suggestion=(
                                f"Move the {newer} entry above {older} in "
                                f"{changelog_rel.as_posix()}."
                            ),
                            can_auto_fix=False,
                        )
                    )

            if files_for_collection:
                if changelog_content is None:
                    prefix_label = (
                        entry.get("prefix") or "the configured prefix"
                    )
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            message=(
                                f"{changelog_rel.as_posix()} does not exist, "
                                f"but files under {prefix_label} changed"
                            ),
                            suggestion=(
                                f"Create {changelog_rel.as_posix()} and log "
                                "the updates recorded under that prefix."
                            ),
                            can_auto_fix=False,
                        )
                    )
                else:
                    today = date.today().isoformat()
                    prefix_label = entry.get("prefix", "") or "collection"
                    if entry_date != today:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=changelog_path,
                                message=(
                                    "Log a fresh entry dated "
                                    f"{today} for changes under "
                                    f"{prefix_label}."
                                ),
                                suggestion=(
                                    "Add a new dated entry at the top of the "
                                    f"{changelog_rel.as_posix()} section "
                                    "covering these files: "
                                    f"{', '.join(files_for_collection)}"
                                ),
                                can_auto_fix=False,
                            )
                        )
                    summary_lines = _extract_summary_lines(
                        entry_text, summary_labels
                    )
                    missing_labels = [
                        label
                        for label in summary_labels
                        if label not in summary_lines
                    ]
                    if missing_labels:
                        labels_str = ", ".join(missing_labels)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=changelog_path,
                                message=(
                                    "Latest changelog entry must include "
                                    "labeled summary lines for: "
                                    f"{labels_str}."
                                ),
                                suggestion=(
                                    "Add Change/Why/Impact summary lines "
                                    "directly under the dated entry."
                                ),
                                can_auto_fix=False,
                            )
                        )
                    else:
                        missing_verbs = [
                            label
                            for label in summary_labels
                            if not _line_has_verb(
                                summary_lines.get(label, ""), summary_verbs
                            )
                        ]
                        if missing_verbs:
                            labels_str = ", ".join(missing_verbs)
                            violations.append(
                                Violation(
                                    policy_id=self.policy_id,
                                    severity="error",
                                    file_path=changelog_path,
                                    message=(
                                        "Summary lines must include an action "
                                        "verb from the configured list. "
                                        f"Missing verbs in: {labels_str}."
                                    ),
                                    suggestion=(
                                        "Revise the Change/Why/Impact lines "
                                        "to include a clear action verb."
                                    ),
                                    can_auto_fix=False,
                                )
                            )
                    entry_files = _extract_entry_files(entry_text)
                    if not entry_files:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=changelog_path,
                                message=(
                                    "Latest changelog entry must include a "
                                    "Files: block listing all touched paths."
                                ),
                                suggestion=(
                                    "Add a Files: block under the latest "
                                    "entry and list each modified path."
                                ),
                                can_auto_fix=False,
                            )
                        )
                    missing_entries = [
                        path
                        for path in files_for_collection
                        if path not in entry_files
                    ]
                    if missing_entries:
                        files_str = ", ".join(missing_entries)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=changelog_path,
                                message=(
                                    "The following files are not mentioned in "
                                    f"{changelog_rel.as_posix()}: {files_str}"
                                ),
                                suggestion=(
                                    "Add entries to "
                                    f"{changelog_rel.as_posix()} documenting "
                                    f"changes to: {files_str}"
                                ),
                                can_auto_fix=False,
                            )
                        )
                    extra_entries = [
                        path
                        for path in entry_files
                        if path not in files_for_collection
                        and path.replace("\\", "/") not in deleted_file_set
                    ]
                    if extra_entries:
                        files_str = ", ".join(extra_entries)
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=changelog_path,
                                message=(
                                    "Latest changelog entry lists files not "
                                    f"in the current change: {files_str}"
                                ),
                                suggestion=(
                                    "Move those paths into a separate entry "
                                    "and keep the latest entry focused on "
                                    "this change only."
                                ),
                                can_auto_fix=False,
                            )
                        )

            if exclusive and root_section and files_for_collection:
                forbidden_mentions = [
                    path
                    for path in files_for_collection
                    if path in root_section
                ]
                if forbidden_mentions:
                    files_str = ", ".join(forbidden_mentions)
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=root_changelog,
                            message=(
                                "Files belonging to "
                                f"{changelog_rel.as_posix()} must not be "
                                "logged in the root changelog: "
                                f"{files_str}"
                            ),
                            suggestion=(
                                "Remove those entries from "
                                f"{main_changelog_rel.as_posix()} and log "
                                f"them only in {changelog_rel.as_posix()}."
                            ),
                            can_auto_fix=False,
                        )
                    )

        return violations

    def _resolve_collections(self, raw: Any) -> List[dict]:
        """Normalize metadata-configured collection entries."""
        default: list[dict[str, object]] = []
        if raw is None:
            return default
        collections: List[dict] = []
        if isinstance(raw, list):
            if not raw:
                return []
            disable_tokens = {
                str(item).strip().lower()
                for item in raw
                if not isinstance(item, dict)
            }
            if disable_tokens.intersection(_COLLECTIONS_DISABLE_TOKENS):
                return []
            entries = raw
        elif isinstance(raw, str):
            if raw.strip().lower() in _COLLECTIONS_DISABLE_TOKENS:
                return []
            entries = [item.strip() for item in raw.split(";") if item.strip()]
        else:
            entries = default
        for entry in entries:
            if isinstance(entry, dict):
                prefix = entry.get("prefix", "")
                changelog = entry.get("changelog")
                if not changelog:
                    raise ValueError(
                        "collection mapping entries must define `changelog`."
                    )
                collections.append(
                    {
                        "prefix": prefix or "",
                        "changelog": Path(changelog),
                        "exclusive": entry.get("exclusive", True),
                    }
                )
            elif isinstance(entry, str):
                parts = entry.split(":")
                if len(parts) < 2:
                    raise ValueError(
                        "string collection entries must use "
                        "`prefix:changelog[:exclusive]` format."
                    )
                prefix = parts[0]
                changelog = parts[1]
                exclusive = True
                if len(parts) >= 3:
                    exclusive = parts[2].lower() != "false"
                collections.append(
                    {
                        "prefix": prefix,
                        "changelog": Path(changelog),
                        "exclusive": exclusive,
                    }
                )
            else:
                raise ValueError(
                    "collection entries must be mapping or string."
                )
        return collections
