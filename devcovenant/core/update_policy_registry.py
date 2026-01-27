"""Update DevCovenant policy registry (policy_registry.yaml)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .parser import PolicyParser
from .policy_locations import resolve_script_location
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


def update_policy_registry(repo_root: Path | None = None) -> int:
    """Update policy hashes in devcovenant/registry/policy_registry.yaml."""

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = (
        repo_root / "devcovenant" / "registry" / "policy_registry.yaml"
    )

    if not agents_md_path.exists():
        print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    parser = PolicyParser(agents_md_path)
    policies = parser.parse_agents_md()

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
        registry.update_policy_entry(policy, location)
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

    return 0


def main() -> int:
    """CLI entry point."""
    return update_policy_registry()


if __name__ == "__main__":
    sys.exit(main())
