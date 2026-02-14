"""
Policy: README Sync

Ensure devcovenant/README.md mirrors README.md with repo-only blocks removed.
"""

from __future__ import annotations

from typing import List, Tuple

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)


class ReadmeSyncCheck(PolicyCheck):
    """Verify devcovenant/README.md matches README.md.

    Repo-only blocks are removed before comparison.
    """

    policy_id = "readme-sync"
    version = "0.1.0"

    REPO_ONLY_BEGIN = "<!-- REPO-ONLY:BEGIN -->"
    REPO_ONLY_END = "<!-- REPO-ONLY:END -->"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check README mirroring and repo-only marker presence."""
        violations: List[Violation] = []
        repo_root = context.repo_root
        source_path = repo_root / "README.md"
        target_path = repo_root / "devcovenant" / "README.md"

        if not source_path.exists():
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=source_path,
                    message="README.md is missing from the repo root.",
                )
            )
            return violations

        source_text = source_path.read_text(encoding="utf-8")
        stripped, error = self._strip_repo_only_blocks(source_text)
        if error:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=source_path,
                    message=error,
                )
            )
            return violations

        expected = self._normalize_text(stripped)
        if not target_path.exists():
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=target_path,
                    message="devcovenant/README.md is missing.",
                    suggestion=(
                        "Rebuild devcovenant/README.md from README.md "
                        "without repo-only blocks."
                    ),
                    can_auto_fix=True,
                    context={
                        "expected_text": expected,
                        "target_path": str(target_path),
                    },
                )
            )
            return violations

        target_text = target_path.read_text(encoding="utf-8")
        if self._normalize_text(target_text) != expected:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=target_path,
                    message=(
                        "devcovenant/README.md diverges from README.md "
                        "after removing repo-only blocks."
                    ),
                    suggestion=(
                        "Sync devcovenant/README.md from README.md "
                        "(excluding repo-only blocks)."
                    ),
                    can_auto_fix=True,
                    context={
                        "expected_text": expected,
                        "target_path": str(target_path),
                    },
                )
            )

        return violations

    def _strip_repo_only_blocks(
        self, text: str
    ) -> Tuple[str | None, str | None]:
        """Remove repo-only blocks and return the stripped text."""
        begin = self.REPO_ONLY_BEGIN
        end = self.REPO_ONLY_END

        has_begin = begin in text
        has_end = end in text
        if not has_begin and not has_end:
            return None, "README.md is missing repo-only block markers."
        if has_begin and not has_end:
            return None, "README.md has an unclosed repo-only block."
        if has_end and not has_begin:
            return (
                None,
                "README.md has a repo-only end marker without a begin.",
            )

        stripped = text
        while True:
            start = stripped.find(begin)
            if start == -1:
                break
            finish = stripped.find(end, start)
            if finish == -1:
                return None, "README.md has an unclosed repo-only block."
            finish += len(end)
            before = stripped[:start].rstrip()
            after = stripped[finish:].lstrip()
            if before and after:
                stripped = before + "\n\n" + after
            else:
                stripped = (before + "\n" + after).strip("\n")
            stripped = stripped.rstrip() + "\n"

        return stripped, None

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(lines).rstrip() + "\n"
