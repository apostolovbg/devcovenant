"""Policy: GCV Script Naming

Ensure each Python file under our custom app uses the `gcv_` prefix.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set, Tuple

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet


class GcvScriptNamingCheck(PolicyCheck):
    """Verify custom app Python files follow the `gcv_` prefix rule."""

    policy_id = "gcv-script-naming"
    version = "1.1.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Return violations for files missing the configured prefix."""
        files = context.all_files or context.changed_files or []
        if not files:
            return []

        selector = self._build_selector()
        prefix = str(self.get_option("required_prefix", "gcv_"))
        exceptions = self._parse_exceptions()
        violations: List[Violation] = []

        for path in files:
            if path.suffix != ".py":
                continue
            try:
                rel = path.relative_to(context.repo_root)
            except ValueError:
                continue
            if not selector.matches(path, context.repo_root):
                continue
            rel_parts = tuple(rel.parts)
            name = rel.name
            if name in exceptions or not prefix:
                continue
            if self._is_doctype_controller(rel_parts):
                continue
            if not name.startswith(prefix):
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=rel,
                        message=(
                            f"{rel.as_posix()} is missing the required "
                            f"prefix `{prefix}`."
                        ),
                        suggestion=(
                            f"Rename {rel.as_posix()} so the filename "
                            f"starts with `{prefix}`."
                        ),
                    )
                )
        return violations

    def _build_selector(self) -> SelectorSet:
        """Return the selector for matching custom app files."""
        target = str(self.get_option("target_directory", "app/gcv_erp_custom"))
        defaults = {"include_prefixes": [target]}
        return SelectorSet.from_policy(self, defaults=defaults)

    def _parse_exceptions(self) -> Set[str]:
        """Return the set of filenames exempt from the prefix rule."""
        raw = self.get_option("exceptions", "__init__.py")
        if isinstance(raw, str):
            candidates = [
                entry.strip() for entry in raw.split(",") if entry.strip()
            ]
        elif isinstance(raw, Iterable):
            candidates = [
                str(entry).strip() for entry in raw if str(entry).strip()
            ]
        else:
            candidates = []
        return set(candidates)

    @staticmethod
    def _is_doctype_controller(rel_parts: Tuple[str, ...]) -> bool:
        """Return True when path points to a DocType controller module."""
        if "doctype" not in rel_parts:
            return False
        try:
            idx = rel_parts.index("doctype")
        except ValueError:
            return False
        if idx + 2 >= len(rel_parts):
            return False
        doctype_name = rel_parts[idx + 1]
        filename = rel_parts[idx + 2]
        return Path(filename).stem == doctype_name
