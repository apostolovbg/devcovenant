#!/usr/bin/env python3
"""Upgrade DevCovenant core in the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import re
from pathlib import Path

from devcovenant import install
from devcovenant.core import manifest as manifest_module
from devcovenant.core import policy_freeze as policy_replacements
from devcovenant.core.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)
from devcovenant.core.repo_refresh import refresh_repo

_POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)


def _read_version(path: Path) -> str:
    """Read version text from a file, falling back to 0.0.0."""
    if not path.exists():
        return "0.0.0"
    version_text = path.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0"


def _version_key(raw: str) -> tuple[int, int, int]:
    """Convert a version string into a sortable tuple."""
    parts = [token.strip() for token in raw.split(".") if token.strip()]
    numbers = []
    for token in parts[:3]:
        try:
            numbers.append(int(token))
        except ValueError:
            numbers.append(0)
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)


def _extract_policy_id(metadata: str) -> str:
    """Extract `id` from a policy-def metadata block."""
    for line in metadata.splitlines():
        stripped = line.strip()
        if not stripped.startswith("id:"):
            continue
        _, policy_value = stripped.split(":", 1)
        return policy_value.strip()
    return ""


def _set_metadata_value(metadata: str, key: str, metadata_value: str) -> str:
    """Set or append a single scalar policy metadata key."""
    pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", re.MULTILINE)
    if pattern.search(metadata):
        return pattern.sub(f"{key}: {metadata_value}", metadata)
    joined = metadata.rstrip()
    if joined:
        return f"{joined}\n{key}: {metadata_value}"
    return f"{key}: {metadata_value}"


def _rewrite_policy_block_for_replacement(metadata: str) -> str:
    """Mark a replaced policy as deprecated custom."""
    updated = _set_metadata_value(metadata, "status", "deprecated")
    updated = _set_metadata_value(updated, "custom", "true")
    return updated


def _apply_policy_replacements(repo_root: Path) -> list[str]:
    """Apply policy replacement annotations in AGENTS policy blocks."""
    replacements = policy_replacements.load_policy_replacements(repo_root)
    if not replacements:
        return []

    agents_path = repo_root / "AGENTS.md"
    if not agents_path.exists():
        return []

    original = agents_path.read_text(encoding="utf-8")
    updated_ids: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        """Rewrite a matched policy block when replacement metadata exists."""
        heading = match.group(1)
        metadata = match.group(2).strip()
        description = match.group(3).strip()
        policy_id = _extract_policy_id(metadata)
        if policy_id not in replacements:
            return match.group(0)

        rewritten = _rewrite_policy_block_for_replacement(metadata)
        updated_ids.append(policy_id)
        return f"{heading}```policy-def\n{rewritten}\n```\n\n{description}\n"

    updated = _POLICY_BLOCK_RE.sub(_replace, original)
    if updated_ids and updated != original:
        agents_path.write_text(updated, encoding="utf-8")

    if updated_ids:
        messages = [
            (
                "Policy "
                f"'{policy_id}' marked deprecated and custom after replacement"
            )
            for policy_id in updated_ids
        ]
        manifest_module.append_notifications(repo_root, messages)

    return updated_ids


def upgrade_repo(repo_root: Path) -> int:
    """Upgrade DevCovenant core and run full refresh."""
    source_version_path = Path(__file__).resolve().parent / "VERSION"
    target_version_path = repo_root / "devcovenant" / "VERSION"

    source_version = _read_version(source_version_path)
    target_version = _read_version(target_version_path)
    if _version_key(source_version) > _version_key(target_version):
        install.replace_core_package(repo_root)
        target_version_path.write_text(f"{source_version}\n", encoding="utf-8")
        print_step("Core package replaced with newer version", "✅")
    else:
        print_step("Core already up to date", "ℹ️")

    replaced = _apply_policy_replacements(repo_root)
    if replaced:
        print_step(
            f"Applied policy replacements: {', '.join(sorted(set(replaced)))}",
            "✅",
        )

    return refresh_repo(repo_root)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for upgrade command."""
    return argparse.ArgumentParser(
        description="Upgrade DevCovenant core in the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute upgrade command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: upgrade", "🧭")
    print_banner("Upgrade", "⬆️")

    return upgrade_repo(repo_root)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
