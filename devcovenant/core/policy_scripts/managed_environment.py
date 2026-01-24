"""Ensure DevCovenant runs inside a declared managed environment."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation


class ManagedEnvironmentCheck(PolicyCheck):
    """Verify the active interpreter matches the managed environment."""

    policy_id = "managed-environment"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Error when DevCovenant runs outside configured environments."""
        repo_root = context.repo_root.resolve()
        expected_paths = self._normalize_entries(
            self.get_option("expected_paths", [])
        )
        expected_interpreters = self._normalize_entries(
            self.get_option("expected_interpreters", [])
        )
        command_hints = self._normalize_entries(
            self.get_option("command_hints", [])
        )
        required_commands = self._normalize_entries(
            self.get_option("required_commands", [])
        )

        warnings: list[Violation] = []
        if not expected_paths and not expected_interpreters:
            warnings.append(
                self._warning(
                    repo_root,
                    "managed-environment is enabled, but no expected_paths or "
                    "expected_interpreters are configured.",
                )
            )
        if not required_commands and not command_hints:
            warnings.append(
                self._warning(
                    repo_root,
                    "managed-environment is enabled, but no command_hints or "
                    "required_commands are configured.",
                )
            )
        if required_commands:
            missing = [
                cmd
                for cmd in required_commands
                if cmd and shutil.which(cmd) is None
            ]
            if missing:
                warnings.append(
                    self._warning(
                        repo_root,
                        "Required commands are missing from PATH: "
                        f"{', '.join(missing)}.",
                    )
                )

        resolved_paths = self._resolve_paths(repo_root, expected_paths)
        resolved_interpreters = self._resolve_paths(
            repo_root, expected_interpreters
        )

        if not resolved_paths and not resolved_interpreters:
            return warnings

        if resolved_paths and not any(
            path.exists() for path in resolved_paths
        ):
            warnings.append(
                self._warning(
                    repo_root,
                    "managed-environment expected_paths do not exist on disk.",
                )
            )

        if self._matches_environment(resolved_paths, resolved_interpreters):
            return warnings

        guidance = " "
        if command_hints:
            guidance = f" Hints: {' | '.join(command_hints)}"

        message = (
            "DevCovenant must run from the managed environment declared by "
            "managed-environment metadata." + guidance
        )
        primary_path = resolved_paths[0] if resolved_paths else repo_root
        return warnings + [
            Violation(
                policy_id=self.policy_id,
                severity="error",
                file_path=primary_path,
                line_number=1,
                message=message,
            )
        ]

    def _normalize_entries(self, entries: object) -> list[str]:
        """Normalize metadata entries into a list of strings."""
        if isinstance(entries, str):
            return [
                entry.strip() for entry in entries.split(",") if entry.strip()
            ]
        if isinstance(entries, (list, tuple, set)):
            return [
                str(entry).strip() for entry in entries if str(entry).strip()
            ]
        return []

    def _resolve_paths(
        self, repo_root: Path, entries: list[str]
    ) -> List[Path]:
        """Resolve metadata paths relative to the repo root when needed."""
        resolved: list[Path] = []
        for entry in entries:
            entry_path = Path(entry)
            if not entry_path.is_absolute():
                entry_path = repo_root / entry_path
            try:
                resolved.append(entry_path.resolve())
            except OSError:
                resolved.append(entry_path)
        return resolved

    def _matches_environment(
        self, expected_paths: List[Path], expected_interpreters: List[Path]
    ) -> bool:
        """Return True when the active interpreter matches expectations."""
        candidates = []
        env_path = os.environ.get("VIRTUAL_ENV")
        if env_path:
            candidates.append(Path(env_path))
        candidates.append(Path(sys.executable))
        candidates.append(Path(sys.executable).parent)

        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                resolved = candidate
            for interpreter in expected_interpreters:
                if resolved == interpreter:
                    return True
            for directory in expected_paths:
                if directory in resolved.parents or resolved == directory:
                    return True
        return False

    def _warning(self, repo_root: Path, message: str) -> Violation:
        """Return a warning-level violation for config guidance."""
        return Violation(
            policy_id=self.policy_id,
            severity="warning",
            file_path=repo_root,
            line_number=1,
            message=message,
        )
