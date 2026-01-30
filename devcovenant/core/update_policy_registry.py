"""Update DevCovenant policy registry.

Uses devcovenant/registry/local/policy_registry.yaml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import yaml

from . import manifest as manifest_module
from . import policy_freeze
from .parser import PolicyDefinition, PolicyParser
from .policy_descriptor import PolicyDescriptor, load_policy_descriptor
from .policy_locations import resolve_script_location
from .refresh_policies import (
    PolicyControl,
    apply_policy_control_overrides,
    descriptor_metadata_order_values,
    load_metadata_schema,
    load_policy_control_config,
)
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


def _split_metadata_values(raw_value: object | None) -> List[str]:
    """Split metadata values on commas and newlines."""

    items: List[str] = []
    text = str(raw_value) if raw_value is not None else ""
    for part in text.replace("\n", ",").split(","):
        normalized = part.strip()
        if normalized:
            items.append(normalized)
    return items


def _normalize_profile_name(raw: object | None) -> str:
    """Return a normalized profile name for comparison."""

    return str(raw or "").strip().lower()


def _load_active_profiles(repo_root: Path) -> List[str]:
    """Return the list of active profiles from config.yaml."""

    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return ["global"]
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return ["global"]
    profiles_block = {}
    if isinstance(payload, dict):
        profiles_block = payload.get("profiles", {}) or {}
    active = profiles_block.get("active", [])
    if isinstance(active, str):
        candidates = [active]
    elif isinstance(active, list):
        candidates = active
    else:
        candidates = [active] if active else []
    normalized: List[str] = []
    for candidate in candidates:
        normalized_name = _normalize_profile_name(candidate)
        if normalized_name and normalized_name != "__none__":
            normalized.append(normalized_name)
    if "global" not in normalized:
        normalized.append("global")
    return sorted(dict.fromkeys(normalized))


def _filter_profile_scopes(raw_value: str, active_profiles: List[str]) -> str:
    """Keep only scopes that match the active profiles."""

    normalized_targets = set(active_profiles)
    filtered: List[str] = []
    seen: set[str] = set()
    for scope in _split_metadata_values(raw_value):
        normalized = _normalize_profile_name(scope)
        if not normalized:
            continue
        if normalized == "global" or normalized in normalized_targets:
            if scope not in seen:
                filtered.append(scope)
                seen.add(scope)
    if not filtered:
        filtered = ["global"]
    return ", ".join(filtered)


def _resolve_policy_metadata(
    policy: PolicyDefinition,
    descriptor: PolicyDescriptor | None,
    control: PolicyControl,
    core_available: bool,
) -> Dict[str, str]:
    """Return the resolved metadata map after applying config overrides."""

    if descriptor:
        base_order, base_values = descriptor_metadata_order_values(descriptor)
    else:
        base_order = list(policy.raw_metadata.keys())
        base_values = {
            key: _split_metadata_values(policy.raw_metadata.get(key))
            for key in base_order
        }
        if not base_order:
            base_order = ["id"]
            base_values = {"id": [policy.policy_id]}

    base_order = list(base_order)
    base_values = {
        key: list(vals) if vals is not None else []
        for key, vals in base_values.items()
    }
    override_order, resolved = apply_policy_control_overrides(
        base_order,
        base_values,
        policy.policy_id,
        control,
        core_available=core_available,
    )
    if not override_order:
        override_order = base_order
    result: Dict[str, str] = {}
    for key in override_order:
        entries = resolved.get(key, [])
        result[key] = ", ".join(entries)
    return result


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
    control = load_policy_control_config(repo_root)
    active_profiles = _load_active_profiles(repo_root)

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
        core_available = bool(location is not None and location.kind == "core")
        resolved_metadata = _resolve_policy_metadata(
            policy,
            descriptor,
            control,
            core_available,
        )
        resolved_metadata["profile_scopes"] = _filter_profile_scopes(
            resolved_metadata.get("profile_scopes", ""), active_profiles
        )
        registry.update_policy_entry(
            policy,
            location,
            descriptor,
            schema=schema_map.get(policy.policy_id),
            resolved_metadata=resolved_metadata,
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
