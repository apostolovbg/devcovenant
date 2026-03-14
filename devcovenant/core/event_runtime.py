"""Test-event schema, adapters, and runtime helpers."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from devcovenant.core import profile_runtime

EVENT_SCHEMA_VERSION = "1.0"
_LAST_ADAPTER_LOAD_WARNINGS: list[str] = []


def _current_timestamp() -> str:
    """Return ISO timestamp with UTC timezone for events."""
    return datetime.now(timezone.utc).isoformat()


def _set_adapter_load_warnings(warnings: list[str]) -> None:
    """Persist adapter-load warnings for runtime consumers."""
    global _LAST_ADAPTER_LOAD_WARNINGS
    _LAST_ADAPTER_LOAD_WARNINGS = list(warnings)


def consume_test_event_adapter_warnings() -> list[str]:
    """Return and clear warnings produced during adapter loading."""
    global _LAST_ADAPTER_LOAD_WARNINGS
    warnings = list(_LAST_ADAPTER_LOAD_WARNINGS)
    _LAST_ADAPTER_LOAD_WARNINGS = []
    return warnings


@dataclass(frozen=True)
class TestEvent:
    """Normalized test lifecycle event emitted by adapters."""

    schema_version: str
    adapter_id: str
    command: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize event as a primitive mapping."""
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "command": self.command,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "metadata": dict(self.metadata),
        }


class TestEventAdapter:
    """Base adapter for emitting normalized test events."""

    def __init__(
        self,
        adapter_id: str,
        *,
        schema_version: str | None = None,
        config: Mapping[str, Any] | None = None,
        profile_name: str | None = None,
    ) -> None:
        """Initialize the adapter identifier, schema version, and config."""
        self.adapter_id = adapter_id
        self.schema_version = schema_version or EVENT_SCHEMA_VERSION
        self.profile_name = profile_name or ""
        self.config = dict(config) if config else {}

    def handles(self, command: Sequence[str]) -> bool:
        """Return True when this adapter handles the command."""
        raise NotImplementedError

    def build_event(
        self,
        *,
        command: Sequence[str],
        command_str: str,
        started: datetime,
        finished: datetime,
        exit_code: int,
    ) -> TestEvent:
        """Build a `TestEvent` representing the command execution."""
        status = "success" if exit_code == 0 else "failure"
        duration = (finished - started).total_seconds()
        return TestEvent(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            command=command_str,
            status=status,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            duration_seconds=duration,
            metadata={"exit_code": exit_code},
        )


class GenericTestEventAdapter(TestEventAdapter):
    """Fallback adapter that handles any test command."""

    def handles(self, command: Sequence[str]) -> bool:
        """Always handle the command as a generic fallback."""
        return True


class PythonTestEventAdapter(TestEventAdapter):
    """Adapter that recognizes Python-based test commands."""

    DEFAULT_MATCHERS = ("pytest", "-m unittest")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with optional matcher overrides from config."""
        super().__init__(*args, **kwargs)
        configured = self.config.get("matchers")
        if isinstance(configured, list):
            matchers = [
                str(entry).strip().lower()
                for entry in configured
                if str(entry).strip()
            ]
            self._matchers = tuple(matchers) or self.DEFAULT_MATCHERS
        else:
            self._matchers = self.DEFAULT_MATCHERS

    def handles(self, command: Sequence[str]) -> bool:
        """Return True when any matcher is present in the command text."""
        joined = " ".join(command).lower()
        return any(token in joined for token in self._matchers)


def python_test_event_adapter_factory(
    *,
    adapter_id: str,
    profile_name: str,
    config: Mapping[str, Any] | None = None,
) -> TestEventAdapter:
    """Factory used by profiles to construct the Python test adapter."""

    return PythonTestEventAdapter(
        adapter_id,
        profile_name=profile_name,
        config=config,
    )


class TestEventManager:
    """Collect test events via configured adapters."""

    def __init__(self, adapters: Iterable[TestEventAdapter]) -> None:
        """Store adapters and prepare the fallback event emitter."""
        self.adapters = list(adapters)
        self.events: list[TestEvent] = []
        self._fallback = GenericTestEventAdapter(
            "generic",
            schema_version=EVENT_SCHEMA_VERSION,
        )

    def record_command(
        self,
        *,
        command: Sequence[str],
        command_str: str,
        started: datetime,
        finished: datetime,
        exit_code: int,
    ) -> None:
        """Record one event for the provided command execution."""
        adapter = next(
            (
                candidate
                for candidate in self.adapters
                if candidate.handles(command)
            ),
            self._fallback,
        )
        event = adapter.build_event(
            command=command,
            command_str=command_str,
            started=started,
            finished=finished,
            exit_code=exit_code,
        )
        self.events.append(event)


def _load_config(repo_root: Path) -> Mapping[str, Any]:
    """Load `devcovenant/config.yaml` contents."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    with config_path.open("rb") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid config payload: {config_path}")
    return payload


def _instantiate_adapter(
    *,
    entrypoint: str,
    adapter_id: str,
    profile_name: str,
    config: Mapping[str, Any],
) -> TestEventAdapter:
    """Instantiate an adapter via the configured entrypoint."""
    module_spec, _, attr = entrypoint.partition(":")
    if not module_spec or not attr:
        raise ValueError(
            (
                f"Invalid entrypoint '{entrypoint}' for test event adapter "
                f"'{adapter_id}'."
            )
        )
    module = importlib.import_module(module_spec)
    factory = getattr(module, attr, None)
    if factory is None or not callable(factory):
        raise ValueError(
            (
                f"Test event adapter entrypoint '{entrypoint}' is not "
                "callable."
            )
        )
    return factory(
        adapter_id=adapter_id,
        profile_name=profile_name,
        config=config,
    )


def load_test_event_adapters(repo_root: Path) -> list[TestEventAdapter]:
    """Load adapters declared by the active profile stack."""
    warnings: list[str] = []
    try:
        payload = _load_config(repo_root)
        active_profiles = profile_runtime.parse_active_profiles(
            payload, include_global=True
        )
        registry = profile_runtime.load_profile_registry(repo_root)
    except Exception as exc:
        _set_adapter_load_warnings(
            [
                (
                    "Unable to load test-event adapters from profile "
                    f"registry: {exc}"
                )
            ]
        )
        return []

    normalized_registry = registry
    adapters: list[TestEventAdapter] = []
    registered: set[str] = set()
    for profile in active_profiles:
        metadata = normalized_registry.get(profile, {}) or {}
        if not isinstance(metadata, Mapping):
            warnings.append(
                (
                    "Skipped test-event metadata from profile "
                    f"'{profile}' because it is not a mapping."
                )
            )
            continue
        raw_entries = metadata.get("test_events", [])
        if not isinstance(raw_entries, list):
            warnings.append(
                (
                    "Skipped test-event adapter metadata from profile "
                    f"'{profile}' because test_events is not a list."
                )
            )
            continue
        for entry in raw_entries:
            if not isinstance(entry, Mapping):
                warnings.append(
                    (
                        "Skipped test-event adapter metadata from profile "
                        f"'{profile}' because one entry is not a mapping."
                    )
                )
                continue
            adapter_id = str(entry.get("id") or "").strip().lower()
            entrypoint = str(entry.get("entrypoint") or "").strip()
            config = entry.get("config") or {}
            if not adapter_id or not entrypoint:
                warnings.append(
                    (
                        "Skipped test-event adapter with missing "
                        "id/entrypoint "
                        f"from profile '{profile}'."
                    )
                )
                continue
            if adapter_id in registered:
                warnings.append(
                    (
                        f"Skipped duplicate test-event adapter id "
                        f"'{adapter_id}' from profile '{profile}'."
                    )
                )
                continue
            try:
                adapter = _instantiate_adapter(
                    entrypoint=entrypoint,
                    adapter_id=adapter_id,
                    profile_name=profile,
                    config=config if isinstance(config, Mapping) else {},
                )
            except Exception as exc:
                warnings.append(
                    (
                        f"Skipped test-event adapter '{adapter_id}' from "
                        f"profile '{profile}': {exc}"
                    )
                )
                continue
            adapters.append(adapter)
            registered.add(adapter_id)
    _set_adapter_load_warnings(warnings)
    return adapters
