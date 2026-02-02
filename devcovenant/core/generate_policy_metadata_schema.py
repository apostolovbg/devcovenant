"""Generate the canonical policy metadata schema from policy descriptors.

This keeps `devcovenant/registry/global/policy_metadata_schema.yaml`
in sync with the `metadata:` blocks declared in each policy YAML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence, Tuple

import yaml

POLICY_METADATA_SCHEMA_FILENAME = "policy_metadata_schema.yaml"


def _policy_files(repo_root: Path) -> Sequence[Path]:
    """Return all core and custom policy descriptor paths."""
    policy_dirs = [
        repo_root / "devcovenant" / "core" / "policies",
        repo_root / "devcovenant" / "custom" / "policies",
    ]
    paths: List[Path] = []
    for base in policy_dirs:
        if not base.exists():
            continue
        for child in base.iterdir():
            if not child.is_dir():
                continue
            candidate = child / f"{child.name}.yaml"
            if candidate.exists():
                paths.append(candidate)
    return sorted(paths, key=lambda p: p.stem)


def _normalize_default(metadata_value) -> List:
    """Represent a metadata value as the schema's list form."""
    if isinstance(metadata_value, list):
        return metadata_value
    return [metadata_value]


def _build_schema(
    repo_root: Path,
) -> MutableMapping[str, MutableMapping[str, object]]:
    """Construct the schema mapping for all discovered policies."""
    schema: MutableMapping[str, MutableMapping[str, object]] = {"policies": {}}
    for policy_file in _policy_files(repo_root):
        policy_data = yaml.safe_load(policy_file.read_text()) or {}
        metadata: Mapping[str, object] = policy_data.get("metadata", {})
        policy_id = policy_data.get("id") or policy_file.stem.replace("_", "-")
        keys = list(metadata.keys())
        defaults: Dict[str, List[object]] = {
            key: _normalize_default(metadata_value)
            for key, metadata_value in metadata.items()
        }
        schema["policies"][policy_id] = {
            "keys": keys,
            "defaults": defaults,
        }
    return schema


def write_schema(repo_root: Path) -> Path:
    """Generate and write the canonical policy metadata schema file."""
    schema = _build_schema(repo_root)
    out_path = (
        repo_root
        / "devcovenant"
        / "registry"
        / "global"
        / POLICY_METADATA_SCHEMA_FILENAME
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(schema, sort_keys=True, allow_unicode=False),
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    """CLI entry point."""
    write_schema(Path.cwd())


if __name__ == "__main__":
    main()
