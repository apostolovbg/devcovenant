"""Ensure in-scope modules carry tests using metadata-driven watch rules."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.selector_helpers import SelectorSet, build_watchlists

ADAPTER_BY_SUFFIX: Dict[str, str] = {
    ".py": ("devcovenant.core.policies.modules_need_tests.adapters.python"),
    ".pyi": ("devcovenant.core.policies.modules_need_tests.adapters.python"),
    ".pyw": ("devcovenant.core.policies.modules_need_tests.adapters.python"),
    ".js": (
        "devcovenant.core.policies.modules_need_tests.adapters.javascript"
    ),
    ".jsx": (
        "devcovenant.core.policies.modules_need_tests.adapters.javascript"
    ),
    ".ts": (
        "devcovenant.core.policies.modules_need_tests.adapters.typescript"
    ),
    ".tsx": (
        "devcovenant.core.policies.modules_need_tests.adapters.typescript"
    ),
    ".go": "devcovenant.core.policies.modules_need_tests.adapters.go",
    ".rs": "devcovenant.core.policies.modules_need_tests.adapters.rust",
    ".java": "devcovenant.core.policies.modules_need_tests.adapters.java",
    ".cs": "devcovenant.core.policies.modules_need_tests.adapters.csharp",
}


def _adapter_for(path: Path):
    """Return adapter module for a given file path, or None."""
    module_path = ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if not module_path:
        return None
    return importlib.import_module(module_path)


def _normalize_mirror_roots(
    raw_value: object,
) -> List[Tuple[str, str]]:
    """Parse ``mirror_roots`` metadata into ``(source, tests_root)`` pairs."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        entries = [raw_value]
    elif isinstance(raw_value, list):
        entries = [str(entry).strip() for entry in raw_value]
    else:
        entries = [str(raw_value).strip()]

    rules: List[Tuple[str, str]] = []
    for raw_entry in entries:
        token = raw_entry.strip()
        if not token:
            continue
        if "=>" in token:
            source, target = token.split("=>", 1)
        elif ":" in token:
            source, target = token.split(":", 1)
        else:
            continue
        source_prefix = source.strip().replace("\\", "/").strip("/")
        target_prefix = target.strip().replace("\\", "/").strip("/")
        if not source_prefix or not target_prefix:
            continue
        rules.append((source_prefix, target_prefix))
    return rules


class ModulesNeedTestsCheck(PolicyCheck):
    """Ensure in-scope modules ship with accompanying tests via adapters."""

    policy_id = "modules-need-tests"
    version = "1.4.0"

    def _collect_repo_files(self, repo_root: Path) -> Set[Path]:
        """Return tracked and untracked repository files."""
        files: Set[Path] = set()
        try:
            output = subprocess.check_output(
                [
                    "git",
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                ],
                cwd=repo_root,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            for candidate in repo_root.rglob("*"):
                if candidate.is_file():
                    files.add(candidate)
            return files

        for line in output.splitlines():
            normalized = line.strip()
            if not normalized:
                continue
            # Accept both `git ls-files` output and status-like fixtures.
            if len(line) >= 4 and line[2] == " " and line[:2].strip():
                normalized = line[3:].strip()
            candidate = repo_root / normalized
            if candidate.is_file():
                files.add(candidate)
        return files

    def check(self, context: CheckContext) -> List[Violation]:
        """Check that in-scope modules have corresponding tests."""
        violations: List[Violation] = []
        repo_files = self._collect_repo_files(context.repo_root)

        module_selector = SelectorSet.from_policy(self)
        _, configured_watch_dirs = build_watchlists(
            self, defaults={"watch_dirs": ["tests"]}
        )
        _, prefixed_tests_dirs = build_watchlists(
            self,
            prefix="tests_",
            defaults={"watch_dirs": configured_watch_dirs or ["tests"]},
        )
        if prefixed_tests_dirs:
            tests_dirs = prefixed_tests_dirs
        elif configured_watch_dirs:
            tests_dirs = configured_watch_dirs
        else:
            tests_dirs = ["tests"]
        mirror_roots = _normalize_mirror_roots(
            self.get_option("mirror_roots", [])
        )

        adapters_cache: Dict[str, object] = {}

        for path in repo_files:
            adapter = _adapter_for(path)
            if adapter:
                adapters_cache.setdefault(path.suffix.lower(), adapter)

        for adapter in set(adapters_cache.values()) or [
            importlib.import_module(
                "devcovenant.core.policies.modules_need_tests."
                "adapters.python"
            )
        ]:
            violations.extend(
                adapter.check_changes(
                    context=context,
                    policy_id=self.policy_id,
                    selector=module_selector,
                    tests_dirs=tests_dirs,
                    mirror_roots=mirror_roots,
                    added=repo_files,
                    modified=set(),
                    deleted=set(),
                )
            )

        return violations
