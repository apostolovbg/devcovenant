"""Runtime output-mode policy helpers for console and child command output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OutputMode = Literal["normal", "verbose", "quiet"]
ChildOutputChannel = Literal[
    "gate_child",
    "test_child",
    "managed_child",
    "generic_child",
]

OUTPUT_MODE_DEFAULT: OutputMode = "verbose"
OUTPUT_MODE_ALLOWED = frozenset({"normal", "verbose", "quiet"})
WAIT_PROGRESS_MESSAGE = "Please wait. In progress..."
_NORMAL_MODE_SUPPRESSED_CHANNELS = frozenset({"managed_child", "test_child"})
_QUIET_MODE_SUPPRESSED_CHANNELS = frozenset(
    {"gate_child", "test_child", "managed_child", "generic_child"}
)


@dataclass(frozen=True)
class ChildOutputPlan:
    """Resolved child-command output behavior for one mode/channel pair."""

    emit_console: bool
    heartbeat_message: str | None

    @property
    def child_output_suppressed(self) -> bool:
        """Return True when child output is hidden from console."""
        return not self.emit_console


def normalize_output_mode(
    raw_value: str | None,
    *,
    default: OutputMode = OUTPUT_MODE_DEFAULT,
) -> OutputMode:
    """Normalize one output-mode token to an allowed runtime mode."""
    token = str(raw_value or "").strip().lower()
    if token in OUTPUT_MODE_ALLOWED:
        return token  # type: ignore[return-value]
    return default


def resolve_child_output_plan(
    output_mode: OutputMode,
    channel: ChildOutputChannel,
) -> ChildOutputPlan:
    """Resolve child-output emission behavior for one command channel."""
    normalized_mode = normalize_output_mode(output_mode)
    normalized_channel = str(channel or "").strip().lower()
    if normalized_mode == "quiet":
        emit_console = (
            normalized_channel not in _QUIET_MODE_SUPPRESSED_CHANNELS
        )
        return ChildOutputPlan(
            emit_console=emit_console,
            heartbeat_message=None,
        )
    if normalized_mode != "normal":
        return ChildOutputPlan(
            emit_console=True,
            heartbeat_message=None,
        )
    emit_console = normalized_channel not in _NORMAL_MODE_SUPPRESSED_CHANNELS
    return ChildOutputPlan(
        emit_console=emit_console,
        heartbeat_message=WAIT_PROGRESS_MESSAGE,
    )


def channel_suppresses_child_output(
    output_mode: OutputMode,
    channel: ChildOutputChannel,
) -> bool:
    """Return True when child output should be hidden for mode/channel."""
    return resolve_child_output_plan(
        output_mode, channel
    ).child_output_suppressed
