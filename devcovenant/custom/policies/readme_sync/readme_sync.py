"""
Policy: README Sync

Ensure devcovenant/README.md mirrors README.md with repo-only blocks removed
and package-facing public links rewritten safely.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[assignment]

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)


class ReadmeSyncCheck(PolicyCheck):
    """Verify devcovenant/README.md matches README.md.

    Repo-only blocks are removed before comparison and repo-relative Markdown
    links are rewritten from repository package metadata for the packaged
    README surface.
    """

    policy_id = "readme-sync"
    version = "0.1.0"
    MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
    MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
    ABSOLUTE_TARGET_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

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

        rewritten, link_error = self._rewrite_packaged_links(
            repo_root,
            stripped,
        )
        if link_error:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=source_path,
                    message=link_error,
                )
            )
            return violations
        expected = self._normalize_text(rewritten)
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

    def _rewrite_packaged_links(
        self,
        repo_root: Path,
        text: str,
    ) -> Tuple[str | None, str | None]:
        """Rewrite repo-relative public Markdown links for packaged README."""
        has_repo_relative_links = any(
            self._is_repo_relative_target(match.group(2).strip())
            for match in self.MARKDOWN_LINK_PATTERN.finditer(text)
        )
        has_repo_relative_images = any(
            self._is_repo_relative_target(match.group(2).strip())
            for match in self.MARKDOWN_IMAGE_PATTERN.finditer(text)
        )
        if not has_repo_relative_links and not has_repo_relative_images:
            return text, None

        blob_base, raw_base, error = self._resolve_repository_link_bases(
            repo_root
        )
        if error:
            return None, error

        # Rewrite repo-relative public Markdown targets for the packaged README
        # so released packages point at release-stable docs and assets.
        def _replace_image(match: re.Match[str]) -> str:
            label = match.group(1)
            target = match.group(2).strip()
            if not self._is_repo_relative_target(target):
                return match.group(0)
            normalized = target[2:] if target.startswith("./") else target
            return f"![{label}]({raw_base}{normalized})"

        # Non-image Markdown links should resolve to the tagged repository tree
        # so packaged docs stay on the released version instead of branch head.
        def _replace(match: re.Match[str]) -> str:
            label = match.group(1)
            target = match.group(2).strip()
            if not self._is_repo_relative_target(target):
                return match.group(0)
            normalized = target[2:] if target.startswith("./") else target
            return f"[{label}]({blob_base}{normalized})"

        rewritten = self.MARKDOWN_IMAGE_PATTERN.sub(_replace_image, text)
        rewritten = self.MARKDOWN_LINK_PATTERN.sub(_replace, rewritten)
        return rewritten, None

    def _resolve_repository_link_bases(
        self,
        repo_root: Path,
    ) -> Tuple[str | None, str | None, str | None]:
        """Resolve release-stable link bases from `pyproject.toml` metadata."""
        pyproject_path = repo_root / "pyproject.toml"
        if not pyproject_path.exists():
            return (
                None,
                None,
                "README.md contains repo-relative public links, but "
                "`pyproject.toml` is missing.",
            )
        try:
            with pyproject_path.open("rb") as handle:
                payload = tomllib.load(handle)
        except OSError as exc:
            return None, None, f"Failed to read `pyproject.toml`: {exc}."

        project = payload.get("project")
        if not isinstance(project, dict):
            return (
                None,
                None,
                "README.md contains repo-relative public links, but "
                "`pyproject.toml` is missing `[project]` metadata.",
            )
        version = str(project.get("version") or "").strip()
        if not version:
            return (
                None,
                None,
                "README.md contains repo-relative public links, but "
                "`pyproject.toml` is missing `project.version`.",
            )
        urls = project.get("urls")
        if not isinstance(urls, dict):
            urls = {}
        repository_url = str(
            urls.get("Repository") or urls.get("Homepage") or ""
        ).strip()
        if not repository_url:
            return (
                None,
                None,
                "README.md contains repo-relative public links, but "
                "`pyproject.toml` is missing `project.urls.Repository` "
                "or `project.urls.Homepage`.",
            )
        normalized = repository_url.removesuffix(".git").rstrip("/")
        version_tag = f"v{version}"
        blob_base = f"{normalized}/blob/{version_tag}/"
        if normalized.startswith("https://github.com/"):
            owner_repo = normalized.removeprefix("https://github.com/")
            raw_base = (
                f"https://raw.githubusercontent.com/{owner_repo}/"
                f"{version_tag}/"
            )
        else:
            raw_base = f"{normalized}/raw/{version_tag}/"
        return blob_base, raw_base, None

    def _is_repo_relative_target(self, target: str) -> bool:
        """Return True when one Markdown link target is repo-relative."""
        if target.startswith("#"):
            return False
        return not self.ABSOLUTE_TARGET_PATTERN.match(target)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(lines).rstrip() + "\n"
