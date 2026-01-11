"""Ensure patch modules are registered in patches.txt."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from devcovenant.base import CheckContext, PolicyCheck, Violation
from devcovenant.selectors import SelectorSet


class PatchesTxtSyncCheck(PolicyCheck):
    """Verify patch files are synchronized with patches.txt."""

    policy_id = "patches-txt-sync"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Return violations when patch entries drift from patches.txt."""
        patches_file = Path(
            self.get_option(
                "patches_file",
                "app/gcv_erp_custom/patches.txt",
            )
        )
        patches_path = context.repo_root / patches_file

        if not patches_path.exists():
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=patches_path,
                    message=(
                        f"Patch registry not found at "
                        f"{patches_file.as_posix()}."
                    ),
                )
            ]

        section_names = self._parse_sections()
        sections, stray_entries, unknown_sections = self._read_patches_file(
            patches_path, section_names
        )
        entries = [entry for items in sections.values() for entry in items]

        selector = SelectorSet.from_policy(
            self,
            defaults={
                "include_globs": ["app/gcv_erp_custom/patches/**/gcv_*.py"]
            },
        )
        files_pool = context.all_files or context.changed_files or []
        patch_files = [
            path
            for path in files_pool
            if path.is_file() and selector.matches(path, context.repo_root)
        ]
        patch_modules = [
            self._module_path(path, context.repo_root) for path in patch_files
        ]
        patch_modules = [entry for entry in patch_modules if entry]

        violations: List[Violation] = []

        enforce_missing = bool(self.get_option("enforce_missing", True))
        enforce_unused = bool(self.get_option("enforce_unused", True))
        enforce_duplicates = bool(self.get_option("enforce_duplicates", True))
        enforce_sorted = bool(self.get_option("enforce_sorted", True))
        enforce_sections = bool(self.get_option("enforce_sections", True))

        if enforce_sections:
            for entry in stray_entries:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=patches_path,
                        message=(
                            "Patch entry is outside a section header: "
                            f"{entry}"
                        ),
                    )
                )
            for entry in unknown_sections:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=patches_path,
                        message=(
                            "Patch entry is under an unknown section: "
                            f"{entry}"
                        ),
                    )
                )

        if enforce_duplicates:
            duplicates = self._find_duplicates(entries)
            for entry in duplicates:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=patches_path,
                        message=(
                            "Patch entry is duplicated in patches.txt: "
                            f"{entry}"
                        ),
                    )
                )

        if enforce_missing:
            missing = sorted(
                entry for entry in patch_modules if entry not in entries
            )
            for entry in missing:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=patches_path,
                        message=(
                            "Patch file is missing from patches.txt: "
                            f"{entry}"
                        ),
                    )
                )

        if enforce_unused:
            unused = sorted(
                entry for entry in entries if entry not in patch_modules
            )
            for entry in unused:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=patches_path,
                        message=(
                            "Patch entry has no matching file on disk: "
                            f"{entry}"
                        ),
                    )
                )

        if enforce_sorted:
            for section, items in sections.items():
                expected = sorted(items)
                if items != expected:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=patches_path,
                            message=(
                                "Patch entries must be sorted within "
                                f"[{section}]."
                            ),
                        )
                    )

        return violations

    def _parse_sections(self) -> List[str]:
        """Return the configured list of valid sections."""
        raw = self.get_option("sections", "pre_model_sync,post_model_sync")
        if isinstance(raw, str):
            items = [
                entry.strip() for entry in raw.split(",") if entry.strip()
            ]
        elif isinstance(raw, Iterable):
            items = [str(entry).strip() for entry in raw if str(entry).strip()]
        else:
            items = []
        return items

    def _read_patches_file(
        self, path: Path, valid_sections: List[str]
    ) -> Tuple[Dict[str, List[str]], List[str], List[str]]:
        """Parse patches.txt into sections and collect stray entries."""
        sections: Dict[str, List[str]] = {name: [] for name in valid_sections}
        stray_entries: List[str] = []
        unknown_sections: List[str] = []
        current: Optional[str] = None

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                current = stripped[1:-1].strip()
                if current not in sections:
                    sections[current] = []
                continue
            if not current:
                stray_entries.append(stripped)
                continue
            if current in valid_sections:
                sections[current].append(stripped)
            else:
                unknown_sections.append(stripped)
        return sections, stray_entries, unknown_sections

    @staticmethod
    def _find_duplicates(entries: List[str]) -> List[str]:
        """Return duplicated entries in their original order."""
        seen: Set[str] = set()
        duplicates: List[str] = []
        for entry in entries:
            if entry in seen and entry not in duplicates:
                duplicates.append(entry)
            seen.add(entry)
        return duplicates

    @staticmethod
    def _module_path(path: Path, repo_root: Path) -> str:
        """Convert a patch file path to its dotted module path."""
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        if rel.startswith("app/"):
            rel = rel[len("app/") :]
        if rel.endswith(".py"):
            rel = rel[:-3]
        return rel.replace("/", ".")
