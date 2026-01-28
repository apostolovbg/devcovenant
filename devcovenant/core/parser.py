"""
Parser for extracting policy definitions from AGENTS.md.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PolicyDefinition:
    """
    A policy definition parsed from AGENTS.md.

    Attributes:
        policy_id: Unique identifier for the policy
        name: Human-readable name
        status: Policy status (new, active, updated, deprecated, deleted)
        severity: Enforcement level (critical, error, warning, info)
        auto_fix: Whether auto-fixing is enabled
        updated: Whether the policy has been updated (triggers script sync)
        apply: Whether the policy should be evaluated
        custom: Whether the policy uses custom enforcement text
        description: Full policy text
        hash_from_file: Hash stored in AGENTS.md (if present)
        raw_metadata: Raw metadata dict from the policy-def block
    """

    policy_id: str
    name: str
    status: str
    severity: str
    auto_fix: bool
    updated: bool
    apply: bool
    custom: bool
    description: str
    hash_from_file: Optional[str] = None
    raw_metadata: Dict[str, str] = field(default_factory=dict)


class PolicyParser:
    """
    Parses AGENTS.md to extract policy definitions.
    """

    def __init__(self, agents_md_path: Path):
        """
        Initialize the parser.

        Args:
            agents_md_path: Path to AGENTS.md file
        """
        self.agents_md_path = agents_md_path

    def parse_agents_md(self) -> List[PolicyDefinition]:
        """
        Parse AGENTS.md and extract all policy definitions.

        Returns:
            List of PolicyDefinition objects
        """
        with open(self.agents_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        policies = []

        # Find all policy blocks
        # Pattern: ## Policy: Name followed by policy-def and description
        policy_pattern = re.compile(
            r"##\s+Policy:\s+([^\n]+)\n\n```policy-def\n(.*?)\n```\n\n"
            r"(.*?)(?=\n---\n|\n##|\Z)",
            re.DOTALL,
        )

        for match in policy_pattern.finditer(content):
            name = match.group(1).strip()
            metadata_block = match.group(2).strip()
            description = match.group(3).strip()

            # Parse metadata
            metadata = self._parse_metadata_block(metadata_block)
            apply_raw = metadata.get("apply", "true")
            apply_flag = apply_raw.strip().lower() == "true"
            custom_raw = metadata.get("custom", "false")
            custom_flag = custom_raw.strip().lower() == "true"

            # Create policy definition
            policy = PolicyDefinition(
                policy_id=metadata.get("id", ""),
                name=name,
                status=metadata.get("status", "active"),
                severity=metadata.get("severity", "warning"),
                auto_fix=metadata.get("auto_fix", "false").lower() == "true",
                updated=metadata.get("updated", "false").lower() == "true",
                apply=apply_flag,
                custom=custom_flag,
                description=description,
                hash_from_file=metadata.get("hash"),
                raw_metadata=metadata,
            )

            policies.append(policy)

        return policies

    def _parse_metadata_block(self, block: str) -> Dict[str, str]:
        """
        Parse a metadata block from a policy-def code fence.

        Args:
            block: The metadata block content

        Returns:
            Dictionary of key-value pairs
        """
        metadata = {}
        current_key: Optional[str] = None

        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue

            if ":" in line:
                key, metadata_value = line.split(":", 1)
                current_key = key.strip()
                metadata[current_key] = metadata_value.strip()
            elif current_key:
                continuation = line
                existing = metadata.get(current_key, "")
                if existing:
                    if existing.endswith(",") or continuation.startswith(","):
                        metadata[current_key] = f"{existing}{continuation}"
                    else:
                        metadata[current_key] = f"{existing},{continuation}"
                else:
                    metadata[current_key] = continuation

        return metadata

    def calculate_policy_text_hash(self, policy: PolicyDefinition) -> str:
        """
        Calculate hash of policy text (for comparison with script hash).

        This only hashes the policy description text, not the script.
        The full hash (text + script) is calculated in the registry.

        Args:
            policy: The policy definition

        Returns:
            SHA256 hash of the policy description
        """
        # Normalize whitespace
        normalized = policy.description.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
