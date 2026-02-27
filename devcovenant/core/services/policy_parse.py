"""Policy definition parsing helpers for runtime engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


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
    raw_metadata: Dict[str, str] = field(default_factory=dict)


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
    def _parse_metadata_block(block: str) -> Dict[str, str]:
        """Parse key/value metadata from a policy-def block."""
        metadata: dict[str, str] = {}
        current_key: str | None = None
        for line in block.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current_key = key.strip()
                metadata[current_key] = value.strip()
                continue
            if not current_key:
                continue
            continuation = stripped
            existing = metadata.get(current_key, "")
            if not existing:
                metadata[current_key] = continuation
                continue
            if existing.endswith(",") or continuation.startswith(","):
                metadata[current_key] = f"{existing}{continuation}"
                continue
            metadata[current_key] = f"{existing},{continuation}"
        return metadata

    @staticmethod
    def _required_metadata(metadata: Dict[str, str], key: str) -> str:
        """Return required metadata key value or raise parse error."""
        raw = str(metadata.get(key, "")).strip()
        if raw:
            return raw
        raise ValueError(f"Missing required metadata key `{key}`.")

    @staticmethod
    def _parse_bool_metadata(
        metadata: Dict[str, str],
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
