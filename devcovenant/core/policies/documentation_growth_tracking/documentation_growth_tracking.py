"""Remind contributors to grow and maintain documentation quality."""

import fnmatch
import re
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.selector_runtime import SelectorSet


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


def _extract_headings(text: str) -> List[str]:
    """Return lower-cased Markdown heading text."""
    headings: List[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("#"):
            continue
        title = line.lstrip("#").strip()
        if title:
            headings.append(title.lower())
    return headings


def _count_sections(text: str) -> int:
    """Count Markdown section headings (level 2 or deeper)."""
    return sum(
        1 for line in text.splitlines() if line.lstrip().startswith("##")
    )


def _word_count(text: str) -> int:
    """Return a simple word count."""
    return len([word for word in text.split() if word.strip()])


def _normalize_headings(raw: object | None) -> List[str]:
    """Return lower-cased required headings."""
    return [heading.lower() for heading in _normalize_list(raw)]


def _matches_prefixes(rel_path: PurePosixPath, prefixes: List[str]) -> bool:
    """Return True when rel_path starts with any prefix."""
    if not prefixes:
        return False
    rel = rel_path.as_posix()
    for prefix in prefixes:
        cleaned = prefix.strip().rstrip("/")
        if cleaned and (rel == cleaned or rel.startswith(f"{cleaned}/")):
            return True
    return False


def _matches_globs(rel_path: PurePosixPath, globs: List[str]) -> bool:
    """Return True when rel_path matches any glob pattern."""
    if not globs:
        return False
    rel = rel_path.as_posix()
    return any(fnmatch.fnmatch(rel, glob) for glob in globs if glob)


def _matches_suffixes(rel_path: PurePosixPath, suffixes: List[str]) -> bool:
    """Return True when rel_path ends with any configured suffix."""
    if not suffixes:
        return False
    return rel_path.suffix in {suffix for suffix in suffixes if suffix}


def _matches_files(rel_path: PurePosixPath, files: List[str]) -> bool:
    """Return True when rel_path matches any filename or path."""
    if not files:
        return False
    rel = rel_path.as_posix()
    for entry in files:
        cleaned = entry.strip().replace("\\", "/")
        if not cleaned:
            continue
        if "/" in cleaned and rel == cleaned:
            return True
        if rel_path.name == cleaned:
            return True
    return False


def _matches_keywords(rel_path: PurePosixPath, keywords: List[str]) -> bool:
    """Return True when rel_path contains any user-facing keyword."""
    if not keywords:
        return False
    tokens = {
        token.lower()
        for token in re.split(r"[\\/._-]+", rel_path.as_posix())
        if token
    }
    keyword_set = {word.lower() for word in keywords if word}
    return bool(tokens & keyword_set)


def _tokenize_path(
    rel_path: PurePosixPath,
    min_length: int,
    stopwords: List[str],
) -> List[str]:
    """Return mention tokens derived from a path."""
    tokens: set[str] = set()
    stopset = {word.lower() for word in stopwords}
    text = "/".join(rel_path.parts)
    for raw in re.split(r"[\\/._-]+", text):
        token = raw.strip().lower()
        if not token or token in stopset:
            continue
        if len(token) < min_length:
            continue
        tokens.add(token)
    return sorted(tokens)


class DocumentationGrowthTrackingCheck(PolicyCheck):
    """Remind contributors to add and maintain documentation quality."""

    policy_id = "documentation-growth-tracking"
    version = "1.2.0"

    def check(self, context: CheckContext):
        """Remind contributors to expand and maintain documentation."""
        files = context.changed_files or []
        selector = SelectorSet.from_policy(self)
        doc_targets = _normalize_list(
            self.get_option("user_visible_files", [])
        )
        quality_targets = _normalize_list(
            self.get_option("doc_quality_files", [])
        )
        user_prefixes = _normalize_list(
            self.get_option("user_facing_prefixes", [])
        )
        user_globs = _normalize_list(self.get_option("user_facing_globs", []))
        user_suffixes = _normalize_list(
            self.get_option("user_facing_suffixes", [])
        )
        user_keywords = _normalize_list(
            self.get_option("user_facing_keywords", [])
        )
        user_files = _normalize_list(self.get_option("user_facing_files", []))
        exclude_prefixes = _normalize_list(
            self.get_option("user_facing_exclude_prefixes", [])
        )
        exclude_globs = _normalize_list(
            self.get_option("user_facing_exclude_globs", [])
        )
        exclude_suffixes = _normalize_list(
            self.get_option("user_facing_exclude_suffixes", [])
        )
        required_headings = _normalize_headings(
            self.get_option("required_headings", [])
        )
        require_toc = bool(self.get_option("require_toc", False))
        min_sections = int(self.get_option("min_section_count", 0) or 0)
        min_words = int(self.get_option("min_word_count", 0) or 0)
        quality_severity = self.get_option("quality_severity", "warning")
        mention_required = bool(self.get_option("require_mentions", True))
        mention_severity = self.get_option("mention_severity", "warning")
        mention_min_length = int(self.get_option("mention_min_length", 3) or 3)
        mention_stopwords = _normalize_list(
            self.get_option("mention_stopwords", [])
        )

        if not quality_targets:
            quality_targets = doc_targets

        doc_touched: List[PurePosixPath] = []
        user_facing_touched: List[PurePosixPath] = []
        doc_quality_violations: List[Violation] = []
        has_user_facing_config = any(
            [
                user_prefixes,
                user_globs,
                user_suffixes,
                user_keywords,
                user_files,
            ]
        )
        scope_selectors = any(
            [user_prefixes, user_globs, user_files, user_keywords]
        )

        for path in files:
            rel = self._relative_path(path, context.repo_root)
            if rel is None:
                continue
            if _matches_doc_target(rel, doc_targets):
                doc_touched.append(rel)
                continue
            if _matches_prefixes(rel, exclude_prefixes):
                continue
            if _matches_globs(rel, exclude_globs):
                continue
            if _matches_suffixes(rel, exclude_suffixes):
                continue
            if has_user_facing_config:
                file_match = _matches_files(rel, user_files)
                prefix_match = _matches_prefixes(rel, user_prefixes)
                glob_match = _matches_globs(rel, user_globs)
                suffix_match = _matches_suffixes(rel, user_suffixes)
                keyword_match = _matches_keywords(rel, user_keywords)
                if scope_selectors:
                    if file_match:
                        user_facing_touched.append(rel)
                    elif keyword_match and (not user_suffixes or suffix_match):
                        user_facing_touched.append(rel)
                    elif (prefix_match or glob_match) and (
                        not user_suffixes or suffix_match
                    ):
                        user_facing_touched.append(rel)
                elif suffix_match:
                    user_facing_touched.append(rel)
            elif selector.matches(path, context.repo_root):
                user_facing_touched.append(rel)

        doc_candidates: Sequence[Path] = context.all_files or files
        doc_texts: dict[PurePosixPath, str] = {}
        for path in doc_candidates:
            rel = self._relative_path(path, context.repo_root)
            if rel is None:
                continue
            if not _matches_doc_target(rel, quality_targets):
                continue
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            doc_texts[rel] = text.lower()
            headings = _extract_headings(text)
            section_count = _count_sections(text)
            word_count = _word_count(text)

            missing = [
                heading
                for heading in required_headings
                if heading not in headings
            ]
            if require_toc and "table of contents" not in headings:
                missing.append("table of contents")

            quality_messages: List[str] = []
            if missing:
                missing_list = ", ".join(sorted(set(missing)))
                quality_messages.append(f"missing headings: {missing_list}")
            if min_sections and section_count < min_sections:
                quality_messages.append(
                    "requires at least "
                    f"{min_sections} sections (found {section_count})"
                )
            if min_words and word_count < min_words:
                quality_messages.append(
                    "requires at least "
                    f"{min_words} words (found {word_count})"
                )

            if quality_messages:
                doc_quality_violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity=quality_severity,
                        message=(
                            "Documentation quality issue: "
                            + "; ".join(quality_messages)
                        ),
                        file_path=path,
                    )
                )

        violations = doc_quality_violations
        if not user_facing_touched:
            return violations
        if not doc_touched:
            targets = ", ".join(sorted(doc_targets)) or "the docs set"
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="info",
                    message=(
                        "User-facing changes detected without doc updates. "
                        f"Expand {targets} before committing."
                    ),
                )
            )
            return violations
        if mention_required:
            doc_values = list(doc_texts.values())
            for rel in user_facing_touched:
                tokens = _tokenize_path(
                    rel,
                    mention_min_length,
                    mention_stopwords,
                )
                if not tokens:
                    continue
                if any(
                    any(token in doc for token in tokens) for doc in doc_values
                ):
                    continue
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity=mention_severity,
                        file_path=context.repo_root / rel,
                        message=(
                            "Docs updated but missing references to "
                            f"user-facing change `{rel}`. Mention at least "
                            f"one of: {', '.join(tokens)}."
                        ),
                    )
                )

        return violations

    @staticmethod
    def _relative_path(path: Path, repo_root: Path) -> PurePosixPath | None:
        """Return a posix relative path when possible."""
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            return None
        return PurePosixPath(rel.as_posix())
