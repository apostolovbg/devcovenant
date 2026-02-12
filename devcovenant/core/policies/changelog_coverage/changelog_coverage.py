"""
Policy: Changelog Coverage

Routes each changed file to the proper changelog based on the metadata-defined
`main_changelog`, `skipped_files` and `collections` options.
"""

import fnmatch
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation


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
_HUNK_PATTERN = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_MANAGED_MARKERS = [
    ("<!-- DEVCOV:BEGIN -->", "<!-- DEVCOV:END -->"),
    (
        "<!-- DEVCOV-WORKFLOW:BEGIN -->",
        "<!-- DEVCOV-WORKFLOW:END -->",
    ),
    (
        "<!-- DEVCOV-POLICIES:BEGIN -->",
        "<!-- DEVCOV-POLICIES:END -->",
    ),
]


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


def _normalize_verbs(raw_value: object, default: list[str]) -> list[str]:
    """Normalize summary verb metadata into a lowercased list."""
    if raw_value is None:
        return [verb.lower() for verb in default if verb]
    if isinstance(raw_value, str):
        entries = [item.strip() for item in raw_value.split(",") if item]
    elif isinstance(raw_value, list):
        entries = [
            str(item).strip() for item in raw_value if str(item).strip()
        ]
    else:
        entries = [str(raw_value).strip()]
    verbs = [verb.lower() for verb in entries if verb]
    return verbs or [verb.lower() for verb in default if verb]


def _line_has_verb(line: str, verbs: list[str]) -> bool:
    """Return True if any configured verb appears as a whole word."""
    if not line or not verbs:
        return False
    lower_line = line.lower()
    for verb in verbs:
        if not verb:
            continue
        if re.search(rf"\b{re.escape(verb)}\b", lower_line):
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


def _parse_hunks(patch_text: str) -> list[tuple[int, int, int, int]]:
    """Return changed old/new line ranges from a unified diff."""
    hunks: list[tuple[int, int, int, int]] = []
    for line in patch_text.splitlines():
        match = _HUNK_PATTERN.match(line)
        if not match:
            continue
        old_start = int(match.group(1))
        old_count = int(match.group(2) or "1")
        new_start = int(match.group(3))
        new_count = int(match.group(4) or "1")
        hunks.append((old_start, old_count, new_start, new_count))
    return hunks


def _managed_ranges(content: str) -> list[tuple[int, int]]:
    """Return line ranges covered by managed block markers."""
    ranges: list[tuple[int, int]] = []
    lines = content.splitlines()
    for begin_marker, end_marker in _MANAGED_MARKERS:
        start_line: int | None = None
        for index, line in enumerate(lines, start=1):
            if start_line is None and begin_marker in line:
                start_line = index
            elif start_line is not None and end_marker in line:
                ranges.append((start_line, index))
                start_line = None
    return ranges


def _line_in_ranges(line_number: int, ranges: list[tuple[int, int]]) -> bool:
    """Return True when the line number falls inside any managed range."""
    for start, end in ranges:
        if start <= line_number <= end:
            return True
    return False


def _is_managed_block_only_change(
    repo_root: Path,
    relative_path: str,
) -> bool:
    """Return True when the file diff only touches managed marker blocks."""
    path = repo_root / relative_path
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--unified=0", "--", relative_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return False
    hunks = _parse_hunks(diff_result.stdout)
    if not hunks:
        return False

    old_content = ""
    try:
        old_result = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        old_content = old_result.stdout
    except Exception:
        old_content = ""
    new_content = path.read_text(encoding="utf-8") if path.exists() else ""

    old_ranges = _managed_ranges(old_content)
    new_ranges = _managed_ranges(new_content)
    if not old_ranges and not new_ranges:
        return False

    for old_start, old_count, new_start, new_count in hunks:
        if old_count > 0:
            for line_number in range(old_start, old_start + old_count):
                if not _line_in_ranges(line_number, old_ranges):
                    return False
        if new_count > 0:
            for line_number in range(new_start, new_start + new_count):
                if not _line_in_ranges(line_number, new_ranges):
                    return False
    return True


_DEFAULT_SUMMARY_LABELS = ["Change", "Why", "Impact"]
_DEFAULT_SUMMARY_VERBS = [
    "add",
    "added",
    "adjust",
    "adjusted",
    "align",
    "aligned",
    "amend",
    "amended",
    "automate",
    "automated",
    "build",
    "built",
    "bump",
    "bumped",
    "clean",
    "cleaned",
    "clarify",
    "clarified",
    "consolidate",
    "consolidated",
    "correct",
    "corrected",
    "create",
    "created",
    "define",
    "defined",
    "deprecate",
    "deprecated",
    "document",
    "documented",
    "drop",
    "dropped",
    "enable",
    "enabled",
    "expand",
    "expanded",
    "fix",
    "fixed",
    "harden",
    "hardened",
    "improve",
    "improved",
    "introduce",
    "introduced",
    "migrate",
    "migrated",
    "normalize",
    "normalized",
    "refactor",
    "refactored",
    "remove",
    "removed",
    "rename",
    "renamed",
    "replace",
    "replaced",
    "restructure",
    "restructured",
    "revise",
    "revised",
    "streamline",
    "streamlined",
    "support",
    "supported",
    "update",
    "updated",
    "upgrade",
    "upgraded",
    "wrap",
    "wrapped",
]


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
    version = "2.2.0"

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
                "rng_minigames/CHANGELOG.md",
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
        managed_docs = set(
            _normalize_paths(
                self.get_option("managed_docs"),
                [
                    "AGENTS.md",
                    "README.md",
                    "CONTRIBUTING.md",
                    "SPEC.md",
                    "PLAN.md",
                    "CHANGELOG.md",
                    "devcovenant/README.md",
                ],
            )
        )
        summary_labels = _normalize_labels(
            self.get_option("summary_labels"), _DEFAULT_SUMMARY_LABELS
        )
        summary_verbs = _normalize_verbs(
            self.get_option("summary_verbs"), _DEFAULT_SUMMARY_VERBS
        )

        collections = self._resolve_collections(
            self.get_option(
                "collections",
                [
                    "rng_minigames/:rng_minigames/CHANGELOG.md:true",
                ],
            )
        )

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=context.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            return violations

        if not changed_files:
            return violations

        main_files: List[str] = []
        collection_files: List[List[str]] = [[] for _ in collections]

        for file_path in changed_files:
            normalized_path = file_path.replace("\\", "/")
            if (
                normalized_path in managed_docs
                and _is_managed_block_only_change(
                    context.repo_root, normalized_path
                )
            ):
                continue
            if file_path in skip_files:
                continue
            if any(
                file_path == prefix or file_path.startswith(f"{prefix}/")
                for prefix in skip_prefixes
            ):
                continue
            if skip_globs and any(
                fnmatch.fnmatch(file_path, pattern) for pattern in skip_globs
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
                                "Add a new entry at the top of the current "
                                f"version section dated {today} and list all "
                                "touched files."
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
                                "Latest changelog entry must include labeled "
                                f"summary lines for: {labels_str}."
                            ),
                            suggestion=(
                                "Add Change/Why/Impact summary lines directly "
                                "under the dated entry."
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
                                    "Summary lines must include an action "
                                    f"verb from the configured list. Missing "
                                    f"verbs in: {labels_str}."
                                ),
                                suggestion=(
                                    "Revise the Change/Why/Impact lines to "
                                    "include a clear action verb."
                                ),
                                can_auto_fix=False,
                            )
                        )
                entry_files = _extract_entry_files(first_entry)
                can_fix_files = first_date == today and bool(main_files)
                fix_context = {"expected_files": list(main_files)}
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
                                "Add a Files: block under the latest entry "
                                "and list each modified path."
                            ),
                            can_auto_fix=can_fix_files,
                            context=fix_context,
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
                            can_auto_fix=can_fix_files,
                            context=fix_context,
                        )
                    )
                extra = [
                    path for path in entry_files if path not in main_files
                ]
                if extra:
                    files_str = ", ".join(extra)
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=root_changelog,
                            message=(
                                "Latest changelog entry lists files not in "
                                f"the current change: {files_str}"
                            ),
                            suggestion=(
                                "Move those paths into a separate entry and "
                                "keep the latest entry focused on this "
                                "change only."
                            ),
                            can_auto_fix=can_fix_files,
                            context=fix_context,
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
                    can_fix_files = entry_date == today and bool(
                        files_for_collection
                    )
                    fix_context = {
                        "expected_files": list(files_for_collection)
                    }
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
                                can_auto_fix=can_fix_files,
                                context=fix_context,
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
                                can_auto_fix=can_fix_files,
                                context=fix_context,
                            )
                        )
                    extra_entries = [
                        path
                        for path in entry_files
                        if path not in files_for_collection
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
                                can_auto_fix=can_fix_files,
                                context=fix_context,
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
        default = [
            {
                "prefix": "rng_minigames/",
                "changelog": Path("rng_minigames/CHANGELOG.md"),
                "exclusive": True,
            }
        ]
        if raw is None:
            return default
        collections: List[dict] = []
        if isinstance(raw, list):
            if not raw:
                return []
            entries = raw
        elif isinstance(raw, str):
            if raw.strip().lower() in {"none", "off", "false", "no"}:
                return []
            entries = [item.strip() for item in raw.split(";") if item.strip()]
        else:
            entries = default
        for entry in entries:
            if isinstance(entry, dict):
                prefix = entry.get("prefix", "")
                changelog = entry.get("changelog")
                if not changelog:
                    continue
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
                    continue
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
        return collections or default
