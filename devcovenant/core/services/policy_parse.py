"""Policy definition parsing helpers for runtime engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class PolicyDefinition:
    """A policy definition parsed from AGENTS.md."""

    policy_id: str
    name: str
    severity: str
    auto_fix: bool
    enabled: bool
    custom: bool
    description: str
    hash_from_file: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyParser:
    """Parse policy definitions from the managed AGENTS policy block."""

    def __init__(self, agents_md_path: Path):
        """Store the AGENTS path used for managed policy parsing."""
        self.agents_md_path = agents_md_path

    def parse_agents_md(self) -> List[PolicyDefinition]:
        """Return policy definitions discovered in AGENTS.md."""
        with open(self.agents_md_path, "r", encoding="utf-8") as file_obj:
            content = file_obj.read()

        policy_block = self._policy_block(content)
        if not policy_block.strip():
            return []

        policies: list[PolicyDefinition] = []
        policy_pattern = re.compile(
            r"##\s+Policy:\s+([^\n]+)\n\n```policy-def\n(.*?)\n```\n\n"
            r"(.*?)(?=\n---\n|\n##|\n<!-- DEVCOV-POLICIES:END -->|\Z)",
            re.DOTALL,
        )
        for match in policy_pattern.finditer(policy_block):
            metadata = self._parse_metadata_block(match.group(2).strip())
            policy_id = self._required_metadata(metadata, "id")
            severity = self._required_metadata(metadata, "severity")
            auto_fix = self._parse_bool_metadata(
                metadata,
                "auto_fix",
                policy_id=policy_id,
            )
            enabled = self._parse_bool_metadata(
                metadata,
                "enabled",
                policy_id=policy_id,
            )
            custom = self._parse_bool_metadata(
                metadata,
                "custom",
                policy_id=policy_id,
            )
            policy = PolicyDefinition(
                policy_id=policy_id,
                name=match.group(1).strip(),
                severity=severity,
                auto_fix=auto_fix,
                enabled=enabled,
                custom=custom,
                description=match.group(3).strip(),
                hash_from_file=metadata.get("hash"),
                raw_metadata=metadata,
            )
            policies.append(policy)
        return policies

    @staticmethod
    def _policy_block(content: str) -> str:
        """Return the text inside the managed AGENTS policy block."""
        begin_marker = "<!-- DEVCOV-POLICIES:BEGIN -->"
        end_marker = "<!-- DEVCOV-POLICIES:END -->"
        try:
            begin = content.index(begin_marker) + len(begin_marker)
            end = content.index(end_marker, begin)
        except ValueError:
            return ""
        return content[begin:end]

    @staticmethod
    def _parse_metadata_block(block: str) -> Dict[str, Any]:
        """Parse YAML metadata from a policy-def block."""
        if PolicyParser._looks_like_legacy_metadata_block(block):
            payload = PolicyParser._parse_legacy_metadata_block(block)
        else:
            payload = None
        try:
            if payload is None:
                payload = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            payload = PolicyParser._parse_legacy_metadata_block(block)
            if payload is None:
                raise ValueError(
                    f"Invalid policy metadata YAML: {exc}"
                ) from exc
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise ValueError("Policy metadata block must be a YAML mapping.")
        return PolicyParser._normalize_metadata_payload(dict(payload))

    @staticmethod
    def _looks_like_legacy_metadata_block(block: str) -> bool:
        """Return True when indented lines behave like legacy continuations."""
        top_level_with_inline_value = False
        key_pattern = re.compile(r"^[A-Za-z0-9_.-]+\s*:")
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if not line[:1].isspace():
                top_level_with_inline_value = False
                if key_pattern.match(stripped):
                    _, raw_value = stripped.split(":", 1)
                    top_level_with_inline_value = bool(raw_value.strip())
                continue
            if top_level_with_inline_value and not stripped.startswith("- "):
                return True
        return False

    @staticmethod
    def _parse_legacy_metadata_block(block: str) -> Dict[str, Any] | None:
        """Parse legacy flat metadata blocks that are not valid YAML."""
        metadata: dict[str, Any] = {}
        current_key: str | None = None
        key_pattern = re.compile(r"^[A-Za-z0-9_.-]+\s*:")
        saw_key = False
        for line in block.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            is_indented = line[:1].isspace()
            if (not is_indented) and key_pattern.match(stripped):
                key, value = stripped.split(":", 1)
                current_key = key.strip()
                metadata[current_key] = value.strip()
                saw_key = True
                continue
            if not current_key:
                return None
            continuation = stripped
            existing = str(metadata.get(current_key, "")).strip()
            if not existing:
                metadata[current_key] = continuation
                continue
            if existing.endswith(",") or continuation.startswith(","):
                metadata[current_key] = f"{existing}{continuation}"
                continue
            metadata[current_key] = f"{existing},{continuation}"
        return metadata if saw_key else None

    @staticmethod
    def _normalize_metadata_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed metadata values to the runtime storage shape."""
        normalized: Dict[str, Any] = {}
        for raw_key, raw_value in payload.items():
            key = str(raw_key).strip()
            if not key:
                continue
            normalized[key] = PolicyParser._normalize_metadata_value(raw_value)
        return normalized

    @staticmethod
    def _normalize_metadata_value(raw_value: Any) -> Any:
        """Normalize one parsed metadata value recursively."""
        if isinstance(raw_value, dict):
            return PolicyParser._normalize_metadata_payload(raw_value)
        if isinstance(raw_value, list):
            normalized_list = [
                PolicyParser._normalize_metadata_value(entry)
                for entry in raw_value
            ]
            if any(
                isinstance(entry, (dict, list)) for entry in normalized_list
            ):
                return [
                    entry
                    for entry in normalized_list
                    if entry not in ("", [], {})
                ]
            return [
                str(entry).strip()
                for entry in normalized_list
                if str(entry).strip()
            ]
        if isinstance(raw_value, bool):
            return "true" if raw_value else "false"
        if raw_value is None:
            return ""
        return str(raw_value).strip()

    @staticmethod
    def _required_metadata(metadata: Dict[str, Any], key: str) -> str:
        """Return required metadata key value or raise parse error."""
        raw_value = metadata.get(key, "")
        if isinstance(raw_value, list):
            for entry in raw_value:
                raw = str(entry or "").strip()
                if raw:
                    return raw
            raise ValueError(f"Missing required metadata key `{key}`.")
        raw = str(raw_value).strip()
        if raw:
            return raw
        raise ValueError(f"Missing required metadata key `{key}`.")

    @staticmethod
    def _parse_bool_metadata(
        metadata: Dict[str, Any],
        key: str,
        *,
        policy_id: str,
    ) -> bool:
        """Parse strict bool metadata values from policy-def blocks."""
        token = PolicyParser._required_metadata(metadata, key).lower()
        if token == "true":
            return True
        if token == "false":
            return False
        raise ValueError(
            f"Invalid boolean `{key}: {token}` in policy `{policy_id}`."
        )
