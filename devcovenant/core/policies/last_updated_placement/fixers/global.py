"""
Fixer for Last Updated Marker Placement policy.

Ensures the header is stamped with the current UTC date near the top of the
document so readers can trust the recency recorded by DevCovenant.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from devcovenant.core.policy_contracts import FixResult, PolicyFixer, Violation


class LastUpdatedPlacementFixer(PolicyFixer):
    """
    Keep Last Updated markers current in allowlisted managed documents.
    """

    policy_id = "last-updated-placement"

    LAST_UPDATED_PATTERN = re.compile(
        r"^\s*(\*\*Last Updated:\*\*|Last Updated:|# Last Updated).*",
        re.IGNORECASE,
    )
    YAML_MARKER_PATTERN = re.compile(
        r"^(?P<prefix>\s*-\s*)(?P<quote>['\"]?)"
        r"(\*\*Last Updated:\*\*|Last Updated:|# Last Updated)"
        r"(?P<rest>.*?)(?P=quote)\s*$",
        re.IGNORECASE,
    )

    def can_fix(self, violation: Violation) -> bool:
        """Return True when the violation references a valid file."""
        return (
            violation.policy_id == self.policy_id
            and violation.file_path is not None
        )

    def fix(self, violation: Violation) -> FixResult:
        """Insert or refresh the UTC Last Updated marker near the top."""
        if not violation.file_path:
            return FixResult(
                success=False, message="No file path provided in violation"
            )

        marker = self._format_marker()
        file_path = Path(violation.file_path)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            return FixResult(
                success=False,
                message=f"Unable to read {file_path}: {exc}",
            )

        lines = content.splitlines()
        if file_path.suffix in {".yaml", ".yml"}:
            updated, new_lines = self._update_yaml_header_lines(lines, marker)
            if updated:
                new_content = "\n".join(new_lines).rstrip() + "\n"
                try:
                    file_path.write_text(new_content, encoding="utf-8")
                except Exception as exc:
                    return FixResult(
                        success=False,
                        message=f"Unable to write {file_path}: {exc}",
                    )
                human_date = marker.split(":", 1)[1].strip()
                return FixResult(
                    success=True,
                    message=(
                        "Set Last Updated header to "
                        + human_date
                        + f" in {file_path}"
                    ),
                    files_modified=[file_path],
                )
        existing_idx = self._find_marker_index(lines)
        modified = False

        if existing_idx is not None:
            if lines[existing_idx].strip() != marker:
                lines[existing_idx] = marker
                modified = True
        else:
            insert_pos = self._insert_position(lines)
            lines.insert(insert_pos + 1, marker)
            if insert_pos + 2 >= len(lines) or lines[insert_pos + 2].strip():
                lines.insert(insert_pos + 2, "")
            modified = True

        if not modified:
            return FixResult(
                success=True,
                message=(
                    f"Last Updated header already current in {file_path}"
                ),
            )

        new_content = "\n".join(lines).rstrip() + "\n"
        try:
            file_path.write_text(new_content, encoding="utf-8")
        except Exception as exc:
            return FixResult(
                success=False,
                message=f"Unable to write {file_path}: {exc}",
            )

        human_date = marker.split(":", 1)[1].strip()
        message = (
            "Set Last Updated header to " + human_date + f" in {file_path}"
        )
        return FixResult(
            success=True,
            message=message,
            files_modified=[file_path],
        )

    def _format_marker(self) -> str:
        """Render the marker line with today's UTC date."""
        today = datetime.now(timezone.utc).date().isoformat()
        return f"**Last Updated:** {today}"

    def _find_marker_index(self, lines: list[str]) -> int | None:
        """Return the first index containing an existing marker."""
        for idx, line in enumerate(lines):
            if self.LAST_UPDATED_PATTERN.match(line):
                return idx
        return None

    def _insert_position(self, lines: list[str]) -> int:
        """Find where to insert the new marker.
        After the first non-empty line."""
        for idx, line in enumerate(lines):
            if line.strip():
                return idx
        return -1

    def _update_yaml_header_lines(
        self, lines: list[str], marker: str
    ) -> tuple[bool, list[str]]:
        """Update header_lines markers in YAML descriptor assets."""
        header_index = None
        for idx, line in enumerate(lines):
            if line.strip() == "header_lines:":
                header_index = idx
                break
        if header_index is None:
            return False, lines

        list_indices: list[int] = []
        for idx in range(header_index + 1, len(lines)):
            line = lines[idx]
            if not line.strip():
                continue
            if line.lstrip().startswith("- "):
                list_indices.append(idx)
                continue
            break

        for idx in list_indices:
            match = self.YAML_MARKER_PATTERN.match(lines[idx])
            if match:
                prefix = match.group("prefix")
                quote = match.group("quote")
                lines[idx] = f"{prefix}{quote}{marker}{quote}"
                return True, lines

        if list_indices:
            insert_at = list_indices[0] + 1
            first_line = lines[list_indices[0]]
            prefix = first_line.split("-", 1)[0] + "- "
        else:
            insert_at = header_index + 1
            prefix = "- "
        lines.insert(insert_at, f"{prefix}'{marker}'")
        return True, lines
