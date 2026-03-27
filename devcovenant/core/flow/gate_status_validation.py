"""Flow-owned parsing and validation helpers for gate-status payloads."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def load_gate_status_payload(path: Path) -> dict[str, object]:
    """Load one gate-status payload, returning empty mapping when missing."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid gate status JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Gate status payload must be a mapping: {path}")
    return payload


def validate_gate_status_payload(path: Path) -> dict[str, object]:
    """Raise `ValueError` when one gate-status payload is malformed."""
    if not path.exists():
        raise ValueError(f"Gate status payload is missing: {path}")

    payload = load_gate_status_payload(path)
    last_run_utc = str(payload.get("last_run_utc", "")).strip()
    try:
        datetime.fromisoformat(last_run_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            "Field 'last_run_utc' must be an ISO-8601 timestamp."
        ) from exc

    commands = payload.get("commands")
    if not isinstance(commands, list):
        raise ValueError(
            "Field 'commands' must record the executed workflow command "
            "list."
        )
    normalized_commands = [
        str(entry or "").strip()
        for entry in commands
        if str(entry or "").strip()
    ]
    if not normalized_commands:
        raise ValueError(
            "Field 'commands' must record at least one executed workflow "
            "command."
        )
    return payload
