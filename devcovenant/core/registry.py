"""
Registry for tracking policy hashes and sync status.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .parser import PolicyDefinition
from .policy_locations import resolve_script_location
from .policy_schema import PolicySchema


@dataclass
class PolicySyncIssue:
    """
    Represents a policy that is out of sync with its script.

    Attributes:
        policy_id: ID of the policy
        policy_text: Current policy text from AGENTS.md
        policy_hash: Hash of current policy text
        script_path: Path to the policy script
        script_exists: Whether the script exists
        issue_type: Type of sync issue
            (hash_mismatch, script_missing, new_policy)
        current_hash: Current hash from registry (if any)
    """

    policy_id: str
    policy_text: str
    policy_hash: str
    script_path: Path
    script_exists: bool
    issue_type: str
    current_hash: Optional[str] = None


class PolicyRegistry:
    """
    Manages the policy registry (tracking hashes and sync status).
    """

    def __init__(self, registry_path: Path, repo_root: Path):
        """
        Initialize the registry.

        Args:
            registry_path: Path to policy_registry.yaml
            repo_root: Root directory of the repository
        """
        self.registry_path = registry_path
        self.repo_root = repo_root
        self._data: Dict = {}
        self.load()

    def load(self):
        """Load the registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}
        if "policies" not in self._data:
            self._data["policies"] = {}
        if "metadata" not in self._data:
            self._data["metadata"] = {"version": "1.0.0"}

    def _normalize_registry_hashes(self) -> None:
        """Normalize stored hashes to string form."""
        policies = self._data.get("policies", {})
        for policy_data in policies.values():
            raw_hash = policy_data.get("hash")
            normalized = self._normalize_hash_value(raw_hash)
            if normalized:
                policy_data["hash"] = normalized

    def save(self):
        """Save the registry to disk."""
        self._normalize_registry_hashes()
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._data, f, sort_keys=False)

    def _normalize_hash_value(self, hash_value: object) -> str | None:
        """Normalize stored hash values to a string."""
        if isinstance(hash_value, list):
            return "".join(str(part) for part in hash_value)
        if isinstance(hash_value, str):
            return hash_value
        return None

    def calculate_full_hash(
        self, policy_text: str, script_content: str
    ) -> str:
        """
        Calculate the full hash (policy text + script content).

        Args:
            policy_text: The policy description from AGENTS.md
            script_content: The Python script content

        Returns:
            SHA256 hash of combined content
        """
        # Normalize both
        normalized_policy = policy_text.strip()
        normalized_script = script_content.strip()

        # Combine
        combined = f"{normalized_policy}\n---\n{normalized_script}"

        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def check_policy_sync(
        self, policies: List[PolicyDefinition]
    ) -> List[PolicySyncIssue]:
        """
        Check which policies are out of sync with their scripts.

        Args:
            policies: List of policies from AGENTS.md

        Returns:
            List of PolicySyncIssue objects for policies that need updating
        """
        issues = []

        for policy in policies:
            # Skip deleted or deprecated policies
            if policy.status in ["deleted", "deprecated"] or not policy.apply:
                continue

            # Skip policies explicitly turned off
            if not policy.apply:
                continue

            # Determine script path
            # Convert hyphens to underscores for Python module names
            location = resolve_script_location(
                self.repo_root, policy.policy_id
            )
            script_path = location.path if location else Path()

            # Check if script exists
            script_exists = location is not None and script_path.exists()

            # Get current hash from registry
            current_hash = None
            if policy.policy_id in self._data.get("policies", {}):
                raw_hash = self._data["policies"][policy.policy_id].get("hash")
                current_hash = self._normalize_hash_value(raw_hash)

            # Determine if there's an issue
            issue_type = None

            if policy.status == "new" or not script_exists:
                if not script_exists:
                    issue_type = "script_missing"
                else:
                    issue_type = "new_policy"
                issues.append(
                    PolicySyncIssue(
                        policy_id=policy.policy_id,
                        policy_text=policy.description,
                        policy_hash="",
                        script_path=script_path,
                        script_exists=script_exists,
                        issue_type=issue_type,
                        current_hash=current_hash,
                    )
                )
                continue

            # If policy is marked as updated, it needs sync
            if policy.updated:
                issue_type = "hash_mismatch"
                issues.append(
                    PolicySyncIssue(
                        policy_id=policy.policy_id,
                        policy_text=policy.description,
                        policy_hash="",
                        script_path=script_path,
                        script_exists=script_exists,
                        issue_type=issue_type,
                        current_hash=current_hash,
                    )
                )
                continue

            # Calculate current hash if script exists
            if script_exists:
                with open(script_path, "r", encoding="utf-8") as f:
                    script_content = f.read()

                calculated_hash = self.calculate_full_hash(
                    policy.description, script_content
                )

                # Compare with stored hash
                if current_hash and calculated_hash != current_hash:
                    issue_type = "hash_mismatch"
                    issues.append(
                        PolicySyncIssue(
                            policy_id=policy.policy_id,
                            policy_text=policy.description,
                            policy_hash=calculated_hash,
                            script_path=script_path,
                            script_exists=script_exists,
                            issue_type=issue_type,
                            current_hash=current_hash,
                        )
                    )

        return issues

    def _compact_script_path(self, script_path: Path) -> str:
        """Return a shorter script path for registry storage."""
        devcov_root = self.repo_root / "devcovenant"
        try:
            relative = script_path.relative_to(devcov_root)
        except ValueError:
            try:
                return str(script_path.relative_to(self.repo_root))
            except ValueError:
                return str(script_path)

        parts = relative.parts
        if len(parts) >= 4 and parts[1] == "policies":
            scope = parts[0]
            policy_name = parts[2]
            if relative.name == f"{policy_name}.py":
                return f"{scope}/{policy_name}.py"
        return str(relative)

    def _split_metadata_values(self, raw_value: object) -> List[str]:
        """Split metadata values on commas and newlines."""
        items: List[str] = []
        text = str(raw_value) if raw_value is not None else ""
        for part in text.replace("\n", ",").split(","):
            normalized = part.strip()
            if normalized:
                items.append(normalized)
        return items

    def _extract_asset_values(self, metadata: Dict[str, str]) -> List[str]:
        """Return metadata values that look like asset paths."""
        candidates: List[str] = []
        for metadata_value in metadata.values():
            for token in self._split_metadata_values(metadata_value):
                normalized = token.strip()
                lowered = normalized.lower()
                if "/" in normalized or lowered.endswith(
                    (".md", ".yaml", ".yml", ".json", ".zip")
                ):
                    candidates.append(normalized)
        return sorted(dict.fromkeys(candidates))

    def _split_profiles(self, raw_value: str) -> List[str]:
        """Return normalized profile scopes."""
        return [
            scope.strip()
            for scope in raw_value.replace("\n", ",").split(",")
            if scope.strip()
        ]

    def update_policy_entry(
        self,
        policy: PolicyDefinition,
        script_location,
        descriptor=None,
        schema: PolicySchema | None = None,
    ):
        """
        Update a policy entry in the registry.

        Args:
            policy: Policy metadata from AGENTS.md.
            script_location: Located script info (or None).
        """
        entry = self._data["policies"].setdefault(policy.policy_id, {})
        entry["status"] = policy.status
        entry["enabled"] = policy.apply
        entry["custom"] = policy.custom
        entry["description"] = policy.name
        entry["policy_text"] = policy.description
        ordered_keys: List[str] = []
        if schema:
            ordered_keys.extend(schema.keys)
        elif descriptor:
            ordered_keys.extend(descriptor.metadata.keys())
        extras = [
            key for key in policy.raw_metadata if key not in ordered_keys
        ]
        ordered_keys.extend(extras)
        entry["metadata_handles"] = list(ordered_keys)
        entry["profiles"] = self._split_profiles(
            policy.raw_metadata.get("profile_scopes", "")
        )
        metadata_values: Dict[str, List[str]] = {}
        for key in ordered_keys:
            metadata_values[key] = self._split_metadata_values(
                policy.raw_metadata.get(key, "")
            )
        entry["metadata_schema"] = list(ordered_keys)
        entry["metadata_values"] = metadata_values
        entry["metadata"] = dict(policy.raw_metadata)
        entry["assets"] = self._extract_asset_values(policy.raw_metadata)
        entry["core"] = False
        entry["script_exists"] = False
        entry["last_updated"] = entry.get("last_updated")

        if script_location and script_location.path.exists():
            script_path = script_location.path
            script_content = script_path.read_text(encoding="utf-8")
            entry["hash"] = self.calculate_full_hash(
                policy.description, script_content
            )
            entry["script_path"] = self._compact_script_path(script_path)
            entry["script_exists"] = True
            entry["core"] = script_location.kind == "core"
            entry["last_updated"] = datetime.now(timezone.utc).isoformat()
        else:
            entry["hash"] = entry.get("hash")
            entry["script_path"] = None

        self.save()

    def get_policy_hash(self, policy_id: str) -> Optional[str]:
        """
        Get the stored hash for a policy.

        Args:
            policy_id: ID of the policy

        Returns:
            Hash string or None if not found
        """
        raw_hash = (
            self._data.get("policies", {}).get(policy_id, {}).get("hash")
        )
        return self._normalize_hash_value(raw_hash)
