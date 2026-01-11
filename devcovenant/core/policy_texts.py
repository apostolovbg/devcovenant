"""Helpers for managing canonical policy text."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

from devcovenant.core.parser import PolicyParser

_POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n```policy-def\n(.*?)\n```\n\n)"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)
_DEFAULT_STOCK_TEXTS = Path("devcovenant/core/stock_policy_texts.json")


def _parse_metadata_block(block: str) -> Dict[str, str]:
    """Parse a policy-def metadata block."""
    metadata: Dict[str, str] = {}
    current_key: str | None = None

    for line in block.splitlines():
        text = line.strip()
        if not text:
            continue
        if ":" in text:
            key, raw_value = text.split(":", 1)
            current_key = key.strip()
            metadata[current_key] = raw_value.strip()
            continue
        if current_key:
            metadata[current_key] = f"{metadata[current_key]} {text}".strip()
    return metadata


def _normalize_text(text: str) -> str:
    """Normalize policy text for comparison."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines).strip()


def stock_texts_path(
    repo_root: Path, stock_texts_rel: str | None = None
) -> Path:
    """Return the resolved stock policy text path."""
    rel_path = (
        Path(stock_texts_rel) if stock_texts_rel else _DEFAULT_STOCK_TEXTS
    )
    return repo_root / rel_path


def load_stock_texts(
    repo_root: Path, stock_texts_rel: str | None = None
) -> Dict[str, str]:
    """Load stock policy text mapping."""
    path = stock_texts_path(repo_root, stock_texts_rel)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_stock_texts(agents_path: Path) -> Dict[str, str]:
    """Build the stock policy text map from an AGENTS file."""
    parser = PolicyParser(agents_path)
    texts: Dict[str, str] = {}
    for policy in parser.parse_agents_md():
        if policy.policy_id:
            texts[policy.policy_id] = _normalize_text(policy.description)
    return texts


def save_stock_texts(
    repo_root: Path,
    texts: Dict[str, str],
    stock_texts_rel: str | None = None,
) -> Path:
    """Write the stock policy text map to disk."""
    path = stock_texts_path(repo_root, stock_texts_rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(texts, indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")
    return path


def restore_stock_texts(
    repo_root: Path,
    policy_ids: Iterable[str] | None = None,
    agents_rel: str = "AGENTS.md",
    stock_texts_rel: str | None = None,
) -> List[str]:
    """Restore stock policy text for selected policy IDs."""
    agents_path = repo_root / agents_rel
    if not agents_path.exists():
        return []

    stock_texts = load_stock_texts(repo_root, stock_texts_rel)
    if not stock_texts:
        return []

    if policy_ids is None:
        allowed_ids = set(stock_texts.keys())
    else:
        allowed_ids = set(policy_ids)

    if policy_ids is not None and not allowed_ids.issubset(stock_texts):
        return []

    content = agents_path.read_text(encoding="utf-8")
    restored: List[str] = []

    def _replace(match: re.Match[str]) -> str:
        """Inject stock policy text into the matched policy block."""
        metadata = _parse_metadata_block(match.group(2))
        policy_id = metadata.get("id", "")
        if policy_id not in allowed_ids:
            return match.group(0)
        if policy_id not in stock_texts:
            return match.group(0)
        restored.append(policy_id)
        description = stock_texts[policy_id].rstrip()
        return f"{match.group(1)}{description}\n"

    updated = _POLICY_BLOCK_RE.sub(_replace, content)
    if restored:
        agents_path.write_text(updated, encoding="utf-8")
    return restored
