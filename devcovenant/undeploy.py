#!/usr/bin/env python3
"""Remove deployed DevCovenant generated artifacts while keeping core."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import shutil
from pathlib import Path

import yaml

from devcovenant.core.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
POLICY_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
POLICY_END = "<!-- DEVCOV-POLICIES:END -->"

DEFAULT_MANAGED_DOCS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "devcovenant/README.md",
]


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _normalize_doc_name(name: str) -> str:
    """Normalize configured doc names to canonical markdown paths."""
    mapping = {
        "AGENTS": "AGENTS.md",
        "README": "README.md",
        "CONTRIBUTING": "CONTRIBUTING.md",
        "SPEC": "SPEC.md",
        "PLAN": "PLAN.md",
        "CHANGELOG": "CHANGELOG.md",
    }
    token = str(name or "").strip()
    if not token:
        return ""
    upper = token.upper()
    if upper in mapping:
        return mapping[upper]
    if upper.endswith(".MD") and upper[:-3] in mapping:
        return mapping[upper[:-3]]
    return token


def _managed_docs_from_config(repo_root: Path) -> list[str]:
    """Resolve managed docs from config doc_assets."""
    config = _read_yaml(repo_root / "devcovenant" / "config.yaml")
    doc_assets = config.get("doc_assets")
    if not isinstance(doc_assets, dict):
        return list(DEFAULT_MANAGED_DOCS)

    autogen_raw = doc_assets.get("autogen")
    user_raw = doc_assets.get("user")

    autogen = []
    if isinstance(autogen_raw, list):
        autogen = [_normalize_doc_name(item) for item in autogen_raw]

    user_docs = set()
    if isinstance(user_raw, list):
        user_docs = {_normalize_doc_name(item) for item in user_raw if item}

    selected = [doc for doc in autogen if doc and doc not in user_docs]
    if not selected:
        selected = list(DEFAULT_MANAGED_DOCS)

    ordered = []
    for doc in selected:
        if doc not in ordered:
            ordered.append(doc)
    return ordered


def _strip_blocks(text: str, begin: str, end: str) -> str:
    """Remove all begin/end managed block ranges from text."""
    updated = text
    while begin in updated and end in updated:
        start = updated.find(begin)
        stop = updated.find(end, start)
        if stop < 0:
            break
        updated = updated[:start] + updated[stop + len(end) :]
    return updated


def undeploy_repo(repo_root: Path) -> int:
    """Remove managed blocks and local registry state."""
    docs = _managed_docs_from_config(repo_root)
    stripped_docs = []

    for doc_name in docs:
        path = repo_root / doc_name
        if not path.exists():
            continue

        original = path.read_text(encoding="utf-8")
        updated = _strip_blocks(original, BLOCK_BEGIN, BLOCK_END)
        updated = _strip_blocks(updated, POLICY_BEGIN, POLICY_END)
        if updated == original:
            continue

        path.write_text(updated.strip() + "\n", encoding="utf-8")
        stripped_docs.append(doc_name)

    registry_local = repo_root / "devcovenant" / "registry" / "local"
    if registry_local.exists():
        shutil.rmtree(registry_local)

    if stripped_docs:
        print_step(
            f"Removed managed blocks from: {', '.join(stripped_docs)}",
            "✅",
        )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for undeploy command."""
    return argparse.ArgumentParser(
        description="Remove deployed managed artifacts and keep core files."
    )


def run(args: argparse.Namespace) -> int:
    """Execute undeploy command."""
    del args
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: undeploy", "🧭")
    print_banner("Undeploy", "📤")

    return undeploy_repo(repo_root)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
