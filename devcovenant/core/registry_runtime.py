"""
Registry for tracking policy hashes and sync status.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from .parser import PolicyDefinition

DEV_COVENANT_DIR = "devcovenant"
GLOBAL_REGISTRY_DIR = f"{DEV_COVENANT_DIR}/registry/global"
LOCAL_REGISTRY_DIR = f"{DEV_COVENANT_DIR}/registry/local"
POLICY_REGISTRY_FILENAME = "policy_registry.yaml"
PROFILE_REGISTRY_FILENAME = "profile_registry.yaml"
TEST_STATUS_FILENAME = "test_status.json"
POLICY_REPLACEMENTS_FILENAME = "policy_replacements.yaml"
MANIFEST_FILENAME = "manifest.json"
MANIFEST_REL_PATH = f"{LOCAL_REGISTRY_DIR}/{MANIFEST_FILENAME}"
POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)


def _registry_root(repo_root: Path, rel_dir: str) -> Path:
    """Return a registry root path for the given repo and subdir."""
    return repo_root / rel_dir


def global_registry_root(repo_root: Path) -> Path:
    """Return the path to the global registry directory."""
    return _registry_root(repo_root, GLOBAL_REGISTRY_DIR)


def local_registry_root(repo_root: Path) -> Path:
    """Return the path to the local registry directory."""
    return _registry_root(repo_root, LOCAL_REGISTRY_DIR)


def policy_registry_path(repo_root: Path) -> Path:
    """Return the policy registry path inside the local registry."""
    return local_registry_root(repo_root) / POLICY_REGISTRY_FILENAME


def profile_registry_path(repo_root: Path) -> Path:
    """Return the profile registry path inside the local registry."""
    return local_registry_root(repo_root) / PROFILE_REGISTRY_FILENAME


def test_status_path(repo_root: Path) -> Path:
    """Return the test running status file path inside the local registry."""
    return local_registry_root(repo_root) / TEST_STATUS_FILENAME


@dataclass(frozen=True)
class PolicyScriptLocation:
    """Resolved policy script location."""

    kind: str
    path: Path
    module: str


@dataclass
class PolicyDescriptor:
    """Metadata descriptor shipped with a policy."""

    policy_id: str
    text: str
    metadata: Dict[str, object]


def parse_metadata_block(
    block: str,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered keys and per-key line values from a metadata block."""
    order: List[str] = []
    values: Dict[str, List[str]] = {}
    current_key = ""
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped:
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            value_text = raw_value.strip()
            order.append(key)
            values[key] = [] if not value_text else [value_text]
            current_key = key
            continue
        if current_key:
            values[current_key].append(stripped)
    return order, values


def _script_name(policy_id: str) -> str:
    """Return the Python module name for a policy id."""
    return policy_id.replace("-", "_")


def iter_script_locations(
    repo_root: Path,
    policy_id: str,
) -> Iterable[PolicyScriptLocation]:
    """Yield candidate policy script locations in priority order."""
    script_name = _script_name(policy_id)
    devcov_dir = repo_root / DEV_COVENANT_DIR
    candidates = [
        (
            "custom",
            devcov_dir
            / "custom"
            / "policies"
            / script_name
            / f"{script_name}.py",
            f"devcovenant.custom.policies.{script_name}.{script_name}",
        ),
        (
            "core",
            devcov_dir
            / "core"
            / "policies"
            / script_name
            / f"{script_name}.py",
            f"devcovenant.core.policies.{script_name}.{script_name}",
        ),
    ]
    for kind, path, module in candidates:
        yield PolicyScriptLocation(kind=kind, path=path, module=module)


def resolve_script_location(
    repo_root: Path, policy_id: str
) -> PolicyScriptLocation | None:
    """Return the first existing policy script location, if any."""
    for location in iter_script_locations(repo_root, policy_id):
        if location.path.exists():
            return location
    return None


def load_policy_descriptor(
    repo_root: Path, policy_id: str
) -> Optional[PolicyDescriptor]:
    """Return the descriptor for a policy if it exists."""
    for location in iter_script_locations(repo_root, policy_id):
        descriptor_path = location.path.with_suffix(".yaml")
        if not descriptor_path.exists():
            continue
        try:
            contents = yaml.safe_load(
                descriptor_path.read_text(encoding="utf-8")
            )
        except yaml.YAMLError:
            continue
        if not isinstance(contents, dict):
            continue
        descriptor_id = contents.get("id", policy_id)
        text = contents.get("text", "")
        metadata = contents.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return PolicyDescriptor(
            policy_id=descriptor_id, text=text, metadata=metadata
        )
    return None


def policy_replacements_path(repo_root: Path) -> Path:
    """Return the policy replacements metadata path."""
    return global_registry_root(repo_root) / POLICY_REPLACEMENTS_FILENAME


DEFAULT_CORE_DIRS = [
    "devcovenant",
    "devcovenant/core",
    "devcovenant/core/policies",
    "devcovenant/core/profiles",
    "devcovenant/core/profiles/global",
    "devcovenant/core/profiles/global/assets",
    GLOBAL_REGISTRY_DIR,
]
DEFAULT_CORE_FILES = [
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcovenant/check.py",
    "devcovenant/gate.py",
    "devcovenant/test.py",
    "devcovenant/install.py",
    "devcovenant/deploy.py",
    "devcovenant/upgrade.py",
    "devcovenant/refresh.py",
    "devcovenant/uninstall.py",
    "devcovenant/undeploy.py",
    "devcovenant/update_lock.py",
    "devcovenant/config.yaml",
    "devcovenant/README.md",
    "devcovenant/VERSION",
    f"{GLOBAL_REGISTRY_DIR}/policy_replacements.yaml",
    "devcovenant/core/profiles/global/assets/.pre-commit-config.yaml",
    "devcovenant/core/profiles/global/assets/.github/workflows/ci.yml",
    "devcovenant/core/profiles/global/assets/gitignore_base.txt",
    "devcovenant/core/profiles/global/assets/gitignore_os.txt",
    "devcovenant/core/profiles/README.md",
    "devcovenant/core/policies/README.md",
]
DEFAULT_DOCS_CORE = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
]
DEFAULT_DOCS_OPTIONAL = [
    "SPEC.md",
    "PLAN.md",
]
DEFAULT_DOCS_CUSTOM: List[str] = []
DEFAULT_CUSTOM_DIRS = [
    "devcovenant/custom",
    "devcovenant/custom/policies",
    "devcovenant/custom/profiles",
]
DEFAULT_CUSTOM_FILES = [
    "devcovenant/custom/profiles/README.md",
    "devcovenant/custom/policies/README.md",
]
DEFAULT_GENERATED_FILES = [
    f"{LOCAL_REGISTRY_DIR}/{POLICY_REGISTRY_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{TEST_STATUS_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{MANIFEST_FILENAME}",
    f"{LOCAL_REGISTRY_DIR}/{PROFILE_REGISTRY_FILENAME}",
]
DEFAULT_GENERATED_DIRS: List[str] = [LOCAL_REGISTRY_DIR]


def _utc_now() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(timezone.utc).isoformat()


def manifest_path(repo_root: Path) -> Path:
    """Return the manifest path for a repo."""
    return repo_root / MANIFEST_REL_PATH


def build_manifest(
    *,
    options: Dict[str, Any] | None = None,
    installed: Dict[str, Any] | None = None,
    doc_blocks: List[str] | None = None,
    mode: str | None = None,
) -> Dict[str, Any]:
    """Build a default manifest payload."""
    manifest: Dict[str, Any] = {
        "schema_version": 2,
        "updated_at": _utc_now(),
        "core": {
            "dirs": list(DEFAULT_CORE_DIRS),
            "files": list(DEFAULT_CORE_FILES),
        },
        "docs": {
            "core": list(DEFAULT_DOCS_CORE),
            "optional": list(DEFAULT_DOCS_OPTIONAL),
            "custom": list(DEFAULT_DOCS_CUSTOM),
        },
        "custom": {
            "dirs": list(DEFAULT_CUSTOM_DIRS),
            "files": list(DEFAULT_CUSTOM_FILES),
        },
        "generated": {
            "dirs": list(DEFAULT_GENERATED_DIRS),
            "files": list(DEFAULT_GENERATED_FILES),
        },
        "profiles": {
            "active": [],
            "registry": [],
        },
    }
    if mode:
        manifest["mode"] = mode
    if options is not None:
        manifest["options"] = options
    if installed is not None:
        manifest["installed"] = installed
    if "notifications" not in manifest:
        manifest["notifications"] = []
    if doc_blocks is not None:
        manifest["doc_blocks"] = doc_blocks
    return manifest


def load_manifest(repo_root: Path) -> Dict[str, Any] | None:
    """Load the manifest if present, otherwise return None."""
    path = manifest_path(repo_root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def write_manifest(repo_root: Path, manifest: Dict[str, Any]) -> Path:
    """Write the manifest to disk and return its path."""
    path = manifest_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def append_notifications(repo_root: Path, messages: Iterable[str]) -> None:
    """Append notification messages to the manifest."""
    manifest = ensure_manifest(repo_root)
    if not manifest:
        return
    notifications = manifest.setdefault("notifications", [])
    timestamp = datetime.now(timezone.utc).isoformat()
    for message in messages:
        notifications.append({"timestamp": timestamp, "message": message})
    write_manifest(repo_root, manifest)


def _normalize_manifest_sections(
    manifest: Dict[str, Any],
) -> tuple[Dict[str, Any], bool]:
    """Normalize manifest sections to the current default inventories."""
    normalized = dict(manifest)
    changed = False
    defaults_manifest = build_manifest()
    for section_name in ("core", "docs", "custom", "generated"):
        defaults = defaults_manifest.get(section_name, {})
        current = normalized.get(section_name, {})
        if not isinstance(defaults, dict):
            continue
        if not isinstance(current, dict):
            normalized[section_name] = defaults
            changed = True
            continue
        merged = dict(current)
        for key, default_value in defaults.items():
            target_value = (
                list(default_value)
                if isinstance(default_value, list)
                else default_value
            )
            if merged.get(key) != target_value:
                merged[key] = target_value
                changed = True
        normalized[section_name] = merged
    return normalized, changed


def ensure_manifest(repo_root: Path) -> Dict[str, Any] | None:
    """Create the manifest when missing and DevCovenant is installed."""
    path = manifest_path(repo_root)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        normalized, changed = _normalize_manifest_sections(payload)
        if changed:
            normalized["updated_at"] = _utc_now()
            write_manifest(repo_root, normalized)
        return normalized
    if not (repo_root / DEV_COVENANT_DIR).exists():
        return None
    manifest = build_manifest()
    write_manifest(repo_root, manifest)
    return manifest


class _RegistryYamlDumper(yaml.SafeDumper):
    """YAML dumper for registry files with readable multiline strings."""


def _represent_registry_string(
    dumper: yaml.Dumper, text_value: str
) -> yaml.nodes.ScalarNode:
    """Render multiline strings as literal blocks."""
    style = "|" if "\n" in text_value else None
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", text_value, style=style
    )


_RegistryYamlDumper.add_representer(str, _represent_registry_string)


@dataclass(frozen=True)
class PolicyReplacement:
    """Replacement metadata for a policy."""

    policy_id: str
    replaced_by: str
    note: str | None = None


def load_policy_replacements(repo_root: Path) -> Dict[str, PolicyReplacement]:
    """Load policy replacement mappings from global registry YAML."""
    path = policy_replacements_path(repo_root)
    if not path.exists():
        return {}
    replacements_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = (
        replacements_data.get("replacements", {})
        if isinstance(replacements_data, dict)
        else {}
    )
    replacements: Dict[str, PolicyReplacement] = {}
    for policy_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        replaced_by = str(payload.get("replaced_by", "")).strip()
        if not replaced_by:
            continue
        replacements[policy_id] = PolicyReplacement(
            policy_id=str(policy_id),
            replaced_by=replaced_by,
            note=payload.get("note"),
        )
    return replacements


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
        payload = yaml.dump(
            self._data,
            Dumper=_RegistryYamlDumper,
            sort_keys=False,
            allow_unicode=False,
        )
        if self.registry_path.exists():
            existing = self.registry_path.read_text(encoding="utf-8")
            if existing == payload:
                return
        self.registry_path.write_text(payload, encoding="utf-8")

    def policy_ids(self) -> set[str]:
        """Return policy IDs currently stored in the registry."""
        policies = self._data.get("policies", {})
        if not isinstance(policies, dict):
            return set()
        return {str(policy_id) for policy_id in policies.keys()}

    def prune_policies(self, keep_ids: set[str]) -> list[str]:
        """Remove policy entries not present in keep_ids."""
        policies = self._data.get("policies", {})
        if not isinstance(policies, dict):
            self._data["policies"] = {}
            return []
        removed = sorted(
            policy_id for policy_id in policies if policy_id not in keep_ids
        )
        for policy_id in removed:
            policies.pop(policy_id, None)
        if removed:
            self.save()
        return removed

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
            if (
                policy.status in ["deleted", "deprecated"]
                or not policy.enabled
            ):
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

    def update_policy_entry(
        self,
        policy: PolicyDefinition,
        script_location,
        descriptor: PolicyDescriptor | None = None,
        *,
        resolved_metadata: Dict[str, str] | None = None,
    ):
        """
        Update a policy entry in the registry.

        Args:
            policy: Policy metadata from AGENTS.md.
            script_location: Located script info (or None).
        """
        entry = self._data["policies"].setdefault(policy.policy_id, {})
        previous_entry = dict(entry)
        previous_hash = entry.get("hash")
        previous_last_updated = entry.get("last_updated")
        entry.clear()
        entry["status"] = policy.status
        entry["enabled"] = policy.enabled
        entry["custom"] = policy.custom
        entry["description"] = policy.name
        entry["policy_text"] = policy.description
        metadata_map = dict(resolved_metadata or policy.raw_metadata)
        entry["metadata"] = dict(metadata_map)
        entry["assets"] = self._extract_asset_values(metadata_map)
        entry["core"] = False
        entry["script_exists"] = False

        if script_location and script_location.path.exists():
            script_path = script_location.path
            script_content = script_path.read_text(encoding="utf-8")
            entry["hash"] = self.calculate_full_hash(
                policy.description, script_content
            )
            entry["script_path"] = self._compact_script_path(script_path)
            entry["script_exists"] = True
            entry["core"] = script_location.kind == "core"
        else:
            entry["hash"] = previous_hash
            entry["script_path"] = None

        previous_compare = dict(previous_entry)
        previous_compare.pop("last_updated", None)
        current_compare = dict(entry)
        current_compare.pop("last_updated", None)
        if (
            current_compare != previous_compare
            or previous_last_updated is None
        ):
            entry["last_updated"] = datetime.now(timezone.utc).isoformat()
        else:
            entry["last_updated"] = previous_last_updated

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
