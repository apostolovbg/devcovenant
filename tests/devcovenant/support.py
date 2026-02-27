"""Test utilities shared across unittest-based test modules."""

from __future__ import annotations

import os
from unittest.mock import patch


class MonkeyPatch:
    """Minimal monkeypatch helper compatible with unittest workflows."""

    def __init__(self) -> None:
        """Initialize the patch stack used for cleanup."""
        self._patchers: list[object] = []

    def setattr(
        self,
        target: object | str,
        name_or_replacement: str | object,
        replacement_value: object | None = None,
    ) -> None:
        """Patch a dotted attribute path or object attribute."""
        if replacement_value is None:
            patcher = patch(str(target), name_or_replacement)
        else:
            patcher = patch.object(
                target, str(name_or_replacement), replacement_value
            )
        patcher.start()
        self._patchers.append(patcher)

    def setenv(self, key: str, env_value: str) -> None:
        """Patch one environment variable for the current process."""
        patcher = patch.dict(os.environ, {key: env_value})
        patcher.start()
        self._patchers.append(patcher)

    def undo(self) -> None:
        """Undo all active patches in reverse order."""
        while self._patchers:
            patcher = self._patchers.pop()
            patcher.stop()
