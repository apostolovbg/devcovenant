"""Base contracts for non-customizable DevCovenant core invariants."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from devcovenant.core.contracts.policy import CheckContext, Violation


@dataclass(frozen=True)
class CoreInvariantDefinition:
    """Resolved metadata and descriptive text for one core invariant."""

    invariant_id: str
    name: str
    severity: str
    description: str
    raw_metadata: Dict[str, str] = field(default_factory=dict)


class CoreInvariantCheck(ABC):
    """Base class for DevCovenant-owned invariant checks."""

    invariant_id: str = ""
    version: str = "1.0.0"

    def __init__(self) -> None:
        """Initialize invariant metadata/config option storage."""
        self.metadata_options: Dict[str, Any] = {}
        self.config_overrides: Dict[str, Any] = {}

    @property
    def policy_id(self) -> str:
        """Compatibility property for shared violation/report helpers."""
        return self.invariant_id

    @abstractmethod
    def check(self, context: CheckContext) -> List[Violation]:
        """Return invariant violations for the provided runtime context."""

    def get_metadata(self) -> Dict[str, Any]:
        """Return basic runtime metadata for the invariant instance."""
        return {
            "invariant_id": self.invariant_id,
            "version": self.version,
            "class": self.__class__.__name__,
        }

    def set_options(
        self,
        metadata_options: Dict[str, Any] | None,
        config_overrides: Dict[str, Any] | None,
    ) -> None:
        """Store resolved invariant metadata and config overrides."""
        self.metadata_options = metadata_options or {}
        self.config_overrides = config_overrides or {}

    def get_option(self, key: str, default: Any = None) -> Any:
        """Return one merged invariant option value."""

        def _is_empty(candidate: Any) -> bool:
            """Return True when one option value is an empty placeholder."""
            # Invariant options may arrive as strings, mappings, or selector
            # lists, so emptiness has to be typed rather than truthy-only.
            if candidate is None:
                return True
            if isinstance(candidate, str):
                return candidate.strip() == ""
            if isinstance(candidate, dict):
                return not candidate
            if isinstance(candidate, (list, tuple, set)):
                if not candidate:
                    return True
                return all(not str(item).strip() for item in candidate)
            return False

        if key in self.config_overrides:
            candidate = self.config_overrides[key]
            if not _is_empty(candidate):
                return candidate
        if key in self.metadata_options:
            candidate = self.metadata_options[key]
            if not _is_empty(candidate):
                return candidate
        return default

    def scoped_changed_files(self, context: CheckContext) -> List[Path]:
        """Return changed files from the active gate session scope."""
        state = context.change_state
        if state.phase == "start":
            return []
        if not state.session_valid:
            top_command = (
                str(os.environ.get("DEVCOV_TOP_COMMAND", "")).strip().lower()
            )
            reason = str(state.session_reason_code or "").strip().lower()
            if (
                top_command == "check"
                and not str(state.phase or "").strip()
                and reason == "missing_gate_status"
            ):
                return []
            message = state.session_error.strip()
            if not message:
                message = (
                    "Session scope requested but gate-start snapshot is "
                    "not available."
                )
            raise ValueError(message)
        return list(state.session_paths)
