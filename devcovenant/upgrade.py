#!/usr/bin/env python3
"""Upgrade DevCovenant core in the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

import yaml

from devcovenant import install
from devcovenant.core import metadata_runtime
from devcovenant.core import refresh_runtime as refresh_runtime_module
from devcovenant.core import registry_runtime as manifest_module
from devcovenant.core import registry_runtime as policy_replacements
from devcovenant.core.execution_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)
from devcovenant.core.refresh_runtime import refresh_repo


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


def _load_config_payload(config_path: Path) -> dict[str, object]:
    """Load config payload from disk, defaulting to an empty mapping."""
    if not config_path.exists():
        return {}
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _custom_policy_override_exists(repo_root: Path, policy_id: str) -> bool:
    """Return True when a custom policy module exists for policy_id."""
    module_name = policy_id.replace("-", "_")
    script_path = (
        repo_root
        / "devcovenant"
        / "custom"
        / "policies"
        / module_name
        / f"{module_name}.py"
    )
    return script_path.exists()


def _apply_policy_replacements(repo_root: Path) -> list[str]:
    """Migrate config.policy_state according to replacement metadata."""
    replacements = policy_replacements.load_policy_replacements(repo_root)
    if not replacements:
        return []

    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return []

    payload = _load_config_payload(config_path)
    state = metadata_runtime.normalize_policy_state(
        payload.get("policy_state")
    )
    if not state:
        return []

    notices: list[str] = []
    changed = False
    for policy_id in sorted(replacements):
        replacement = replacements[policy_id]
        if _custom_policy_override_exists(repo_root, policy_id):
            if policy_id in state:
                notices.append(
                    "Skipped policy_state migration for "
                    f"'{policy_id}' because a custom override exists."
                )
            continue
        if policy_id not in state:
            continue
        enabled = state.pop(policy_id)
        replacement_id = replacement.replaced_by
        if replacement_id not in state:
            state[replacement_id] = enabled
        changed = True
        note = str(replacement.note or "").strip()
        message = (
            "Migrated policy_state " f"'{policy_id}' -> '{replacement_id}'"
        )
        if note:
            message = f"{message} ({note})"
        notices.append(message)

    if not changed:
        if notices:
            manifest_module.append_notifications(repo_root, notices)
        return notices

    payload["policy_state"] = {
        policy_id: state[policy_id] for policy_id in sorted(state)
    }
    rendered = refresh_runtime_module._render_config_yaml(payload)
    config_path.write_text(rendered, encoding="utf-8")
    manifest_module.append_notifications(repo_root, notices)
    return notices


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

    replacement_notices = _apply_policy_replacements(repo_root)
    if replacement_notices:
        print_step(
            "Processed policy replacements",
            "✅",
        )
        for notice in replacement_notices:
            print_step(notice, "ℹ️")

    return refresh_repo(repo_root)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for upgrade command."""
    return argparse.ArgumentParser(
        description="Upgrade DevCovenant core in the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute upgrade command."""
    del args
    repo_root = resolve_repo_root(require_install=True)

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
