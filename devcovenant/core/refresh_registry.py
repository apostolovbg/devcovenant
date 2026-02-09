"""Refresh DevCovenant policy registry.

Uses devcovenant/registry/local/policy_registry.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List

from . import manifest as manifest_module
from . import policy_freeze
from .parser import PolicyDefinition
from .policy_descriptor import load_policy_descriptor
from .policy_locations import iter_script_locations, resolve_script_location
from .refresh_policies import (
    build_metadata_context,
    resolve_policy_metadata_map,
)
from .registry import PolicyRegistry


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


def _discover_policy_sources(repo_root: Path) -> Dict[str, Dict[str, bool]]:
    """Return discovered policy ids and whether core/custom scripts exist."""

    discovered: Dict[str, Dict[str, bool]] = {}
    for source in ("core", "custom"):
        source_root = repo_root / "devcovenant" / source / "policies"
        if not source_root.exists():
            continue
        for entry in source_root.iterdir():
            if not entry.is_dir():
                continue
            script = entry / f"{entry.name}.py"
            if not script.exists():
                continue
            policy_id = entry.name.replace("_", "-").strip()
            record = discovered.setdefault(
                policy_id, {"core": False, "custom": False}
            )
            if source == "core":
                record["core"] = True
            else:
                record["custom"] = True
    return discovered


def _descriptor_values(raw_value: object | None) -> List[str]:
    """Normalize descriptor metadata values into a list of strings."""

    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    text = str(raw_value).strip()
    return [text] if text else []


def _as_bool(raw_value: str | None, *, default: bool) -> bool:
    """Interpret a resolved metadata value as a boolean."""

    if raw_value is None:
        return default
    token = raw_value.strip().lower()
    if token in {"true", "1", "yes", "on"}:
        return True
    if token in {"false", "0", "no", "off"}:
        return False
    return default


def refresh_registry(
    repo_root: Path | None = None,
    *,
    rerun: bool = False,
    skip_freeze: bool = False,
) -> int:
    """Refresh policy hashes.

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

    context = build_metadata_context(repo_root)
    discovered = _discover_policy_sources(repo_root)

    registry = PolicyRegistry(registry_path, repo_root)

    updated = 0
    policies: List[PolicyDefinition] = []
    seen_policy_ids: set[str] = set()
    for policy_id, source_flags in sorted(discovered.items()):
        location = resolve_script_location(repo_root, policy_id)
        core_available = any(
            loc.kind == "core" and loc.path.exists()
            for loc in iter_script_locations(repo_root, policy_id)
        )
        custom_available = any(
            loc.kind == "custom" and loc.path.exists()
            for loc in iter_script_locations(repo_root, policy_id)
        )
        if location is None:
            print(
                f"Notice: Policy script missing for {policy_id}. "
                "Entry will be updated without a hash.",
                file=sys.stderr,
            )
        else:
            updated += 1
        descriptor = load_policy_descriptor(repo_root, policy_id)
        if descriptor is None:
            print(
                (
                    f"Notice: Descriptor missing for {policy_id}. "
                    "Skipping registry entry."
                ),
                file=sys.stderr,
            )
            continue
        policy_text = str(descriptor.text or "").strip()
        if not policy_text:
            print(
                (
                    f"Notice: Descriptor text missing for {policy_id}. "
                    "Skipping registry entry."
                ),
                file=sys.stderr,
            )
            continue

        current_order = list(descriptor.metadata.keys())
        current_values = {
            key: _descriptor_values(descriptor.metadata.get(key))
            for key in current_order
        }
        resolved_order, resolved_metadata = resolve_policy_metadata_map(
            policy_id,
            current_order,
            current_values,
            descriptor,
            context,
            core_available=core_available,
            custom_policy=bool(custom_available and not core_available),
        )
        ordered_metadata = {
            key: str(resolved_metadata.get(key, "")).strip()
            for key in resolved_order
        }
        status = ordered_metadata.get("status") or "active"
        severity = ordered_metadata.get("severity") or "warning"
        enabled = _as_bool(ordered_metadata.get("enabled"), default=True)
        custom = _as_bool(ordered_metadata.get("custom"), default=False)
        auto_fix = _as_bool(ordered_metadata.get("auto_fix"), default=False)
        freeze = _as_bool(ordered_metadata.get("freeze"), default=False)
        policy_name = policy_id.replace("-", " ").title()
        policy = PolicyDefinition(
            policy_id=policy_id,
            name=policy_name,
            status=status,
            severity=severity,
            auto_fix=auto_fix,
            enabled=enabled,
            custom=custom,
            description=policy_text,
            freeze=freeze,
            raw_metadata=dict(ordered_metadata),
        )
        seen_policy_ids.add(policy_id)
        policies.append(policy)
        registry.update_policy_entry(
            policy,
            location,
            descriptor,
            resolved_metadata=ordered_metadata,
        )
        script_name = (
            location.path.name if location is not None else "<missing>"
        )
        print(f"Recorded {policy_id}: {script_name}")

    stale_ids = sorted(
        set(registry._data.get("policies", {}).keys()) - seen_policy_ids
    )
    for stale_id in stale_ids:
        registry._data["policies"].pop(stale_id, None)
        print(f"Removed stale policy entry: {stale_id}")
    if stale_ids:
        registry.save()

    if updated == 0:
        print("All policy hashes are up to date.")
    else:
        print("\nUpdated " f"{updated} policy hash(es) in {registry_path}")

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
            return refresh_registry(
                repo_root,
                rerun=True,
                skip_freeze=True,
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
    return refresh_registry()


if __name__ == "__main__":
    sys.exit(main())
