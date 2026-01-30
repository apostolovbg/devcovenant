"""Update DevCovenant policy registry.

Uses devcovenant/registry/local/policy_registry.yaml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

from . import manifest as manifest_module
from . import policy_freeze
from .parser import PolicyParser
from .policy_descriptor import load_policy_descriptor
from .policy_locations import resolve_script_location
from .refresh_policies import load_metadata_schema
from .registry import PolicyRegistry

_UPDATED_PATTERN = re.compile(r"^(\s*updated:\s*)true\s*$", re.MULTILINE)


def _reset_updated_flags(agents_md_path: Path) -> bool:
    """Reset updated flags in AGENTS.md after registry refresh."""
    text = agents_md_path.read_text(encoding="utf-8")
    updated = _UPDATED_PATTERN.sub(r"\1false", text)
    if updated == text:
        return False
    agents_md_path.write_text(updated, encoding="utf-8")
    return True


def _ensure_trailing_newline(path: Path) -> bool:
    """Ensure the given file ends with a newline."""
    if not path.exists():
        return False
    contents = path.read_bytes()
    if not contents:
        path.write_text("\n", encoding="utf-8")
        return True
    if contents.endswith(b"\n"):
        return False
    path.write_bytes(contents + b"\n")
    return True


def update_policy_registry(
    repo_root: Path | None = None,
    *,
    rerun: bool = False,
    skip_freeze: bool = False,
) -> int:
    """Update policy hashes.

    Writes devcovenant/registry/local/policy_registry.yaml.
    """

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = manifest_module.policy_registry_path(repo_root)

    if not agents_md_path.exists():
        print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    parser = PolicyParser(agents_md_path)
    policies = parser.parse_agents_md()
    schema_map = load_metadata_schema(repo_root)

    registry = PolicyRegistry(registry_path, repo_root)

    updated = 0
    for policy in policies:
        location = resolve_script_location(repo_root, policy.policy_id)
        if location is None:
            print(
                f"Notice: Policy script missing for {policy.policy_id}. "
                "Entry will be updated without a hash.",
                file=sys.stderr,
            )
        else:
            updated += 1
        descriptor = load_policy_descriptor(repo_root, policy.policy_id)
        registry.update_policy_entry(
            policy,
            location,
            descriptor,
            schema=schema_map.get(policy.policy_id),
        )
        script_name = (
            location.path.name if location is not None else "<missing>"
        )
        print(f"Recorded {policy.policy_id}: {script_name}")

    if updated == 0:
        print("All policy hashes are up to date.")
    else:
        print("\nUpdated " f"{updated} policy hash(es) in {registry_path}")

    if _reset_updated_flags(agents_md_path):
        print("Reset updated flags in AGENTS.md.")
    if _ensure_trailing_newline(registry_path):
        print(f"Ensured trailing newline in {registry_path}.")

    if not skip_freeze:
        freeze_changed, freeze_messages = policy_freeze.apply_policy_freeze(
            repo_root, policies
        )
        if freeze_messages:
            manifest_module.append_notifications(repo_root, freeze_messages)
            _print_freeze_messages(freeze_messages)
        if freeze_changed and not rerun:
            return update_policy_registry(
                repo_root, rerun=True, skip_freeze=True
            )

    return 0


def _print_freeze_messages(messages: Iterable[str]) -> None:
    """Print freeze-related notifications."""
    if not messages:
        return
    print("\nPolicy freeze notices:")
    for message in messages:
        print(f"- {message}")


def main() -> int:
    """CLI entry point."""
    return update_policy_registry()


if __name__ == "__main__":
    sys.exit(main())
