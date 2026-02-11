"""Policy descriptor, script-location, and metadata-block helpers."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml

from .parser import PolicyDefinition, PolicyParser

POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)


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
    """Yield candidate script locations in priority order."""
    script_name = _script_name(policy_id)
    devcov_dir = repo_root / "devcovenant"
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


def _descriptor_path_for(repo_root: Path, policy: PolicyDefinition) -> Path:
    """Return the YAML descriptor path for a given policy definition."""
    location = resolve_script_location(repo_root, policy.policy_id)
    if location is not None:
        return location.path.with_suffix(".yaml")
    policy_dir = (
        repo_root
        / "devcovenant"
        / "core"
        / "policies"
        / policy.policy_id.replace("-", "_")
    )
    policy_dir.mkdir(parents=True, exist_ok=True)
    return policy_dir / f"{policy.policy_id.replace('-', '_')}.yaml"


def generate_descriptors(
    repo_root: Path,
    *,
    overwrite: bool = False,
) -> Iterable[Path]:
    """Generate YAML descriptors for every policy defined in AGENTS.md."""

    agents_path = repo_root / "AGENTS.md"
    parser = PolicyParser(agents_path)
    for policy in parser.parse_agents_md():
        descriptor_path = _descriptor_path_for(repo_root, policy)
        descriptor_path.parent.mkdir(parents=True, exist_ok=True)
        if descriptor_path.exists() and not overwrite:
            continue
        contents = {
            "id": policy.policy_id,
            "text": policy.description,
            "metadata": policy.raw_metadata,
        }
        descriptor_path.write_text(
            yaml.safe_dump(contents, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        yield descriptor_path


def main() -> int:
    """Generate descriptors whenever invoked as a script."""

    parser = argparse.ArgumentParser(
        description="Generate per-policy descriptor YAML files."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate descriptors even if files already exist.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    generated = list(generate_descriptors(repo_root, overwrite=args.overwrite))
    if generated:
        print(f"Generated {len(generated)} descriptors.")
    else:
        print("No descriptors generated (files already existed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
