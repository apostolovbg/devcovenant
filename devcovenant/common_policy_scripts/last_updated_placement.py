"""
Policy: Last Updated Marker Placement

Ensures Last Updated markers are only in allowlisted files or suffixes.
"""

import fnmatch
import re
from typing import List, Set

from devcovenant.base import CheckContext, PolicyCheck, Violation


class LastUpdatedPlacementCheck(PolicyCheck):
    """
    Check that Last Updated markers are only in allowlisted files/suffixes.
    """

    policy_id = "last-updated-placement"
    version = "1.0.0"

    # Pattern to detect Last Updated markers
    LAST_UPDATED_PATTERN = re.compile(
        r"(\*\*Last Updated:\*\*|Last Updated:|# Last Updated)",
        re.IGNORECASE,
    )
    DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

    def check(self, context: CheckContext) -> List[Violation]:
        """
        Check for Last Updated markers in non-allowlisted files.

        Args:
            context: Check context

        Returns:
            List of violations
        """
        violations = []

        files_to_check = context.all_files or context.changed_files or []

        def _normalize_list(raw: object) -> List[str]:
            """Return a list of strings parsed from metadata/config."""
            if raw is None:
                return []
            if isinstance(raw, str):
                candidates = raw.split(",")
            elif isinstance(raw, list):
                candidates = raw
            else:
                candidates = [raw]
            normalized: List[str] = []
            for entry in candidates:
                text = str(entry).strip()
                if not text or text == "__none__":
                    continue
                normalized.append(text)
            return normalized

        allowlist = set(_normalize_list(self.get_option("allowed_files", [])))
        allowed_suffixes = {
            suffix if suffix.startswith(".") else f".{suffix}"
            for suffix in _normalize_list(
                self.get_option("allowed_suffixes", [])
            )
        }
        allowed_globs = _normalize_list(self.get_option("allowed_globs", []))
        required_files = set(
            _normalize_list(self.get_option("required_files", []))
        )
        required_globs = _normalize_list(self.get_option("required_globs", []))

        def _glob_matches(rel_text: str, patterns: List[str]) -> bool:
            """Return True when rel_text matches any glob pattern."""
            for pattern in patterns:
                if fnmatch.fnmatch(rel_text, pattern):
                    return True
                if pattern.startswith("**/") and fnmatch.fnmatch(
                    rel_text, pattern[3:]
                ):
                    return True
            return False

        required_matches: Set[str] = set()
        for file_path in files_to_check:
            try:
                rel_path = file_path.relative_to(context.repo_root)
            except ValueError:
                continue
            rel_text = rel_path.as_posix()
            if rel_text in required_files:
                required_matches.add(rel_text)
            if required_globs and _glob_matches(rel_text, required_globs):
                required_matches.add(rel_text)

        for file_path in files_to_check:
            # Skip non-text files
            text_extensions = [
                ".md",
                ".py",
                ".yml",
                ".yaml",
                ".sh",
                ".bat",
                ".command",
                ".cff",
            ]
            if file_path.suffix not in text_extensions:
                continue

            # Check if file is in allowlist
            relative_path = str(file_path.relative_to(context.repo_root))
            is_allowlisted = relative_path in allowlist
            if not is_allowlisted and allowed_suffixes:
                is_allowlisted = file_path.suffix in allowed_suffixes
            if not is_allowlisted and allowed_globs:
                is_allowlisted = _glob_matches(relative_path, allowed_globs)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # Only check first 10 lines
                    lines = f.readlines()[:10]
            except Exception:
                continue

            marker_lines = []
            for line_num, line in enumerate(lines, start=1):
                if self.LAST_UPDATED_PATTERN.search(line):
                    marker_lines.append((line_num, line))
                    if not is_allowlisted:
                        allowed = (
                            ", ".join(sorted(allowlist | allowed_suffixes))
                            or "none"
                        )
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="warning",
                                file_path=file_path,
                                line_number=line_num,
                                message=(
                                    "Last Updated marker found in "
                                    "non-allowlisted file"
                                ),
                                suggestion=(
                                    f"Remove 'Last Updated' marker from "
                                    f"this file (only allowed in: {allowed})"
                                ),
                                can_auto_fix=True,
                            )
                        )
                        break

            has_marker_in_first_three = False
            for line_num, line in marker_lines:
                if line_num <= 3:
                    has_marker_in_first_three = True
                    if not self.DATE_PATTERN.search(line):
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="warning",
                                file_path=file_path,
                                line_number=line_num,
                                message=(
                                    "Last Updated marker missing "
                                    "ISO date (YYYY-MM-DD)."
                                ),
                            )
                        )
                    break

            if relative_path in required_matches:
                if not has_marker_in_first_three:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="warning",
                            file_path=file_path,
                            message=(
                                "Required documentation is missing a "
                                "Last Updated marker in the first three "
                                "lines."
                            ),
                            suggestion=(
                                "Add `Last Updated: YYYY-MM-DD` within "
                                "the first three lines."
                            ),
                        )
                    )
            elif is_allowlisted and marker_lines:
                first_line = marker_lines[0][0]
                if first_line > 3:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="warning",
                            file_path=file_path,
                            line_number=first_line,
                            message=(
                                "Last Updated marker must appear within "
                                "the first three lines."
                            ),
                            suggestion=(
                                "Move the Last Updated marker near the "
                                "top of the file."
                            ),
                        )
                    )

        return violations
