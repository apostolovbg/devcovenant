"""Remind contributors to grow documentation for user-facing changes."""

from pathlib import Path, PurePosixPath
from typing import Iterable, List

from devcovenant.base import CheckContext, PolicyCheck, Violation
from devcovenant.selectors import SelectorSet


def _normalize_list(raw: object | None) -> List[str]:
    """Return a flattened list of non-empty strings."""
    if raw is None:
        return []
    if isinstance(raw, str):
        candidates: Iterable[str] = raw.split(",")
    elif isinstance(raw, Iterable):
        candidates = raw  # type: ignore[assignment]
    else:
        candidates = [str(raw)]
    normalized: List[str] = []
    for entry in candidates:
        text = str(entry).strip()
        if text:
            normalized.append(text)
    return normalized


def _matches_doc_target(rel_path: PurePosixPath, targets: List[str]) -> bool:
    """Return True when rel_path matches a configured documentation target."""
    for raw_target in targets:
        target = raw_target.strip().replace("\\", "/")
        if not target:
            continue
        target_path = PurePosixPath(target)
        if "/" in target and rel_path.as_posix() == target_path.as_posix():
            return True
        if rel_path.name == target_path.name:
            return True
    return False


class DocumentationGrowthTrackingCheck(PolicyCheck):
    """Fiducial reminder to add prose when user-visible elements change."""

    policy_id = "documentation-growth-tracking"
    version = "1.1.0"

    def check(self, context: CheckContext):
        """Remind contributors to expand documentation alongside code."""
        files = context.changed_files or []
        selector = SelectorSet.from_policy(self)
        doc_targets = _normalize_list(
            self.get_option("user_visible_files", [])
        )

        doc_touched: List[PurePosixPath] = []
        code_touched: List[PurePosixPath] = []

        for path in files:
            rel = self._relative_path(path, context.repo_root)
            if rel is None:
                continue
            if selector.matches(path, context.repo_root):
                code_touched.append(rel)
            if _matches_doc_target(rel, doc_targets):
                doc_touched.append(rel)

        if not code_touched or doc_touched:
            return []

        targets = ", ".join(sorted(doc_targets)) or "the docs set"
        return [
            Violation(
                policy_id=self.policy_id,
                severity="info",
                message=(
                    "User-facing code changed without doc updates. Expand "
                    f"{targets} before committing."
                ),
            )
        ]

    @staticmethod
    def _relative_path(path: Path, repo_root: Path) -> PurePosixPath | None:
        """Return a posix relative path when possible."""
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            return None
        return PurePosixPath(rel.as_posix())
