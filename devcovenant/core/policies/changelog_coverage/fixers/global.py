"""
Auto-fixer for changelog-coverage file lists.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

from devcovenant.core.base import FixResult, PolicyFixer, Violation

_DATE_PATTERN = re.compile(r"^\s*-\s*(\d{4}-\d{2}-\d{2})\b")


class ChangelogCoverageFixer(PolicyFixer):
    """Fill the Files block for the latest changelog entry."""

    policy_id = "changelog-coverage"

    def can_fix(self, violation: Violation) -> bool:
        """Handle changelog-coverage violations with expected file data."""
        expected = violation.context.get("expected_files")
        return (
            violation.policy_id == self.policy_id
            and bool(expected)
            and violation.file_path is not None
        )

    def fix(self, violation: Violation) -> FixResult:
        """Rewrite the Files block to match the expected paths."""
        path = Path(violation.file_path) if violation.file_path else None
        if path is None or not path.exists():
            return FixResult(success=False, message="Missing changelog file")

        expected = violation.context.get("expected_files", [])
        expected_files = [str(item) for item in expected if str(item).strip()]
        if not expected_files:
            return FixResult(success=False, message="No files to write")

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return FixResult(success=False, message=str(exc))

        updated = _apply_files_block(text, expected_files)
        if updated == text:
            return FixResult(
                success=False, message="Files block already up to date"
            )

        path.write_text(updated, encoding="utf-8")
        return FixResult(
            success=True,
            message=f"Updated Files block in {path}",
            files_modified=[path],
        )


def _apply_files_block(text: str, expected_files: List[str]) -> str:
    """Return changelog text with the latest Files block rewritten."""
    start, end = _latest_section_bounds(text)
    section = text[start:end]
    lines = section.splitlines()
    entry_bounds = _first_entry_bounds(lines)
    if entry_bounds is None:
        return text
    entry_start, entry_end = entry_bounds
    entry_lines = lines[entry_start:entry_end]
    new_entry = _rewrite_entry_files(entry_lines, expected_files)
    updated_lines = lines[:entry_start] + new_entry + lines[entry_end:]
    updated_section = "\n".join(updated_lines)
    if section.endswith("\n") and not updated_section.endswith("\n"):
        updated_section += "\n"
    return text[:start] + updated_section + text[end:]


def _find_markers(content: str) -> Tuple[int | None, List[int]]:
    """Return the log-marker position and version header positions."""
    log_index = None
    version_positions: List[int] = []
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


def _latest_section_bounds(content: str) -> Tuple[int, int]:
    """Return the start/end offsets for the newest version section."""
    log_index, version_positions = _find_markers(content)
    if not version_positions:
        return 0, len(content)
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
    end = next_start if next_start is not None else len(content)
    return start, end


def _first_entry_bounds(lines: List[str]) -> Tuple[int, int] | None:
    """Return the line bounds for the newest entry."""
    start = None
    for idx, line in enumerate(lines):
        if _DATE_PATTERN.match(line):
            start = idx
            break
    if start is None:
        return None
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if _DATE_PATTERN.match(lines[idx]):
            end = idx
            break
    return start, end


def _rewrite_entry_files(
    entry_lines: List[str], expected_files: List[str]
) -> List[str]:
    """Return entry lines with a rewritten Files block."""
    files_index = None
    for idx, line in enumerate(entry_lines):
        if line.strip().lower().startswith("files:"):
            files_index = idx
            break

    file_lines = ["  Files:"]
    for line in _wrap_paths(expected_files):
        file_lines.append(line)

    if files_index is None:
        return _wrap_entry_lines(entry_lines + file_lines)

    end_index = files_index + 1
    while end_index < len(entry_lines):
        if not entry_lines[end_index].strip():
            break
        end_index += 1
    updated = entry_lines[:files_index] + file_lines + entry_lines[end_index:]
    return _wrap_entry_lines(updated)


def _wrap_paths(paths: Iterable[str], max_len: int = 79) -> List[str]:
    """Wrap long file paths to satisfy line-length limits."""
    lines: List[str] = []
    for path in paths:
        lines.extend(_wrap_single_path(path, max_len))
    return lines


def _wrap_single_path(path: str, max_len: int) -> List[str]:
    """Wrap a single file path into one or more lines."""
    indent = "  "
    continuation = "    "
    remaining = path
    output: List[str] = []
    # Bound iterations to guarantee forward progress even on malformed input.
    for _ in range(max(len(path), 1)):
        current = f"{indent}{remaining}"
        if len(current) <= max_len or "/" not in remaining:
            output.append(current)
            return output
        available = max_len - len(indent) - 1
        break_at = remaining.rfind("/", 0, max(available, 1))
        if break_at <= 0:
            output.append(current)
            return output
        head = remaining[: break_at + 1]
        tail = remaining[break_at + 1 :]
        output.append(f"{indent}{head}\\")
        remaining = tail
        indent = continuation
    output.append(f"{indent}{remaining}")
    return output


def _wrap_entry_lines(lines: List[str], max_len: int = 79) -> List[str]:
    """Wrap long summary lines with backslash continuations."""
    wrapped: List[str] = []
    for line in lines:
        stripped = line.strip()
        if len(line) <= max_len:
            wrapped.append(line)
            continue
        if stripped.lower().startswith("files:"):
            wrapped.append(line)
            continue
        if stripped.startswith("- "):
            wrapped.append(line)
            continue
        if ":" not in line:
            wrapped.append(line)
            continue
        wrapped.extend(_wrap_text_line(line, max_len))
    return wrapped


def _wrap_text_line(line: str, max_len: int) -> List[str]:
    """Wrap a single summary line at word boundaries."""
    indent_match = re.match(r"^(\s*)", line)
    indent = indent_match.group(1) if indent_match else ""
    content = line[len(indent) :].strip()
    continuation_indent = f"{indent}  "
    if not content:
        return [indent]

    tokens = content.split()
    output: List[str] = []
    current_indent = indent
    current_text = ""

    for token in tokens:
        candidate = token if not current_text else f"{current_text} {token}"
        available = max_len - len(current_indent)
        if available <= 0:
            output.append(f"{current_indent}{current_text}".rstrip())
            current_indent = continuation_indent
            current_text = token
            continue
        if len(candidate) <= available:
            current_text = candidate
            continue
        if not current_text:
            # Token itself is longer than the available space; keep progress.
            output.append(f"{current_indent}{token}")
            current_indent = continuation_indent
            current_text = ""
            continue
        output.append(f"{current_indent}{current_text}\\")
        current_indent = continuation_indent
        current_text = token

    if current_text:
        output.append(f"{current_indent}{current_text}")

    return output or [line.rstrip()]
