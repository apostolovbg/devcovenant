"""Custom policy that guards against core micro-module drift."""

from __future__ import annotations

from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation


class NoSpaghettiCheck(PolicyCheck):
    """Enforce core module count and minimum module size baselines."""

    policy_id = "no-spaghetti"
    version = "0.1.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Run no-spaghetti checks against top-level core Python modules."""
        repo_root = context.repo_root
        module_paths = self._top_level_core_modules(repo_root)
        violations: List[Violation] = []

        max_modules = self._int_option("max_top_level_modules", 999)
        if len(module_paths) > max_modules:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=repo_root / "devcovenant" / "core",
                    message=(
                        "Top-level core module count exceeds baseline: "
                        f"{len(module_paths)} > {max_modules}."
                    ),
                    suggestion=(
                        "Merge helper scriplets or move logic into existing "
                        "core modules before adding new top-level files."
                    ),
                )
            )

        min_lines = self._int_option("min_module_lines", 120)
        for module_path in module_paths:
            rel_path = module_path.relative_to(repo_root).as_posix()
            line_count = self._line_count(module_path)
            if line_count >= min_lines:
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=module_path,
                    message=(
                        "Top-level core module is too small for the baseline: "
                        f"{rel_path} has {line_count} lines (< {min_lines})."
                    ),
                    suggestion=(
                        "Inline this helper into an owner module or grow the "
                        "module to hold cohesive logic."
                    ),
                )
            )

        return violations

    def _top_level_core_modules(self, repo_root: Path) -> List[Path]:
        """Return top-level Python modules in devcovenant/core."""
        core_root = repo_root / "devcovenant" / "core"
        module_paths = sorted(core_root.glob("*.py"))
        return [path for path in module_paths if path.name != "__init__.py"]

    def _int_option(self, key: str, default: int) -> int:
        """Parse an integer metadata option with fallback."""
        raw_value = self.get_option(key, default)
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return default

    def _line_count(self, path: Path) -> int:
        """Return physical line count for a module path."""
        return len(path.read_text(encoding="utf-8").splitlines())
