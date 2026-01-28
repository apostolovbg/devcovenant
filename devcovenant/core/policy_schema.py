"""Policy metadata schema helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)


@dataclass(frozen=True)
class PolicySchema:
    """Schema for a policy metadata block."""

    keys: Tuple[str, ...]
    defaults: Dict[str, List[str]]


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


def build_schema(template_path: Path) -> Dict[str, PolicySchema]:
    """Build policy schema mapping from the template AGENTS file."""
    schema: Dict[str, PolicySchema] = {}
    if not template_path.exists():
        return schema
    content = template_path.read_text(encoding="utf-8")
    for match in POLICY_BLOCK_RE.finditer(content):
        metadata_block = match.group(2).strip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = ""
        if "id" in values and values["id"]:
            policy_id = values["id"][0]
        if not policy_id:
            continue
        schema[policy_id] = PolicySchema(tuple(order), values)
    return schema
