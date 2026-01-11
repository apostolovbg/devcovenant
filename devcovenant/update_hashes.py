"""Update DevCovenant policy script hashes in registry.json.

This utility automatically computes SHA256 hashes for all policy scripts
combined with their policy text from AGENTS.md and updates the registry.json
file.
"""

import re
import sys
from pathlib import Path

from .parser import PolicyParser
from .registry import PolicyRegistry

_UPDATED_PATTERN = re.compile(r"^(\s*updated:\s*)true\s*$", re.MULTILINE)


def _reset_updated_flags(agents_md_path: Path) -> bool:
    """Reset updated flags in AGENTS.md after hashes are refreshed."""
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


def update_registry_hashes(repo_root: Path | None = None) -> int:
    """Update all policy script hashes in registry.json.

    Args:
        repo_root: Repository root path (defaults to script parent directory)

    Returns:
        0 on success, 1 on error
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = repo_root / "devcovenant" / "registry.json"

    if not agents_md_path.exists():
        print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    if not registry_path.exists():
        print(
            f"Error: Registry not found at {registry_path}",
            file=sys.stderr,
        )
        return 1

    # Parse policies from AGENTS.md
    parser = PolicyParser(agents_md_path)
    policies = parser.parse_agents_md()

    # Load registry
    registry = PolicyRegistry(registry_path, repo_root)

    # Update each policy's hash
    updated = 0
    for policy in policies:
        # Skip deleted or deprecated policies
        if policy.status in ["deleted", "deprecated"]:
            continue

        # Determine script path
        script_name = policy.policy_id.replace("-", "_")
        script_path = (
            repo_root / "devcovenant" / "policy_scripts" / f"{script_name}.py"
        )

        if not script_path.exists():
            print(
                f"Warning: Policy script not found: {script_path}",
                file=sys.stderr,
            )
            continue

        # Update hash using the correct calculation (policy text + script)
        registry.update_policy_hash(
            policy.policy_id, policy.description, script_path
        )
        updated += 1
        print(f"Updated {policy.policy_id}: {script_path.name}")

    if updated == 0:
        print("All policy hashes are up to date.")
    if updated == 0:
        reset = _reset_updated_flags(agents_md_path)
        if reset:
            print("Reset updated flags in AGENTS.md.")
        if _ensure_trailing_newline(registry_path):
            print("Ensured trailing newline in registry.json.")
        return 0

    print(f"\nUpdated {updated} policy hash(es) in registry.json")
    reset = _reset_updated_flags(agents_md_path)
    if reset:
        print("Reset updated flags in AGENTS.md.")
    if _ensure_trailing_newline(registry_path):
        print("Ensured trailing newline in registry.json.")
    return 0


def main() -> int:
    """CLI entry point."""
    return update_registry_hashes()


if __name__ == "__main__":
    sys.exit(main())
