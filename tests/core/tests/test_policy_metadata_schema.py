"""Ensure the metadata schema mirrors all policy descriptors."""

from __future__ import annotations

from pathlib import Path

import yaml


def _normalize(metadata_value):
    """Normalize metadata defaults to list form for comparison."""
    if isinstance(metadata_value, list):
        return metadata_value
    return [metadata_value]


def test_policy_metadata_schema_matches_descriptors():
    """Schema lists exactly the metadata keys/defaults from every policy YAML."""
    repo = Path(__file__).resolve().parents[3]
    schema_path = repo / "devcovenant" / "registry" / "global"
    schema_path = schema_path / "policy_metadata_schema.yaml"
    schema = yaml.safe_load(schema_path.read_text())["policies"]

    policy_dirs = [
        repo / "devcovenant" / "core" / "policies",
        repo / "devcovenant" / "custom" / "policies",
    ]

    for base in policy_dirs:
        if not base.exists():
            continue
        for entry in base.iterdir():
            if not entry.is_dir():
                continue
            descriptor = entry / f"{entry.name}.yaml"
            if not descriptor.exists():
                continue
            descriptor_data = yaml.safe_load(descriptor.read_text()) or {}
            metadata = descriptor_data.get("metadata", {})
            policy_id = descriptor_data.get("id")
            if not policy_id:
                policy_id = entry.name.replace("_", "-")
            assert policy_id in schema, (
                f"Schema missing policy {policy_id} described in {descriptor}"
            )
            schema_entry = schema[policy_id]
            assert set(schema_entry["keys"]) == set(
                metadata.keys()
            ), f"Key mismatch for {policy_id}"
            for key, metadata_value in metadata.items():
                assert (
                    _normalize(metadata_value) == schema_entry["defaults"][key]
                ), f"Default mismatch for {policy_id}:{key}"
