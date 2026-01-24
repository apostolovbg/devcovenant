#!/usr/bin/env python3
"""Update DevCovenant in a target repository."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from devcovenant.core import cli_options, install
from devcovenant.core import manifest as manifest_module
from devcovenant.core import metadata_normalizer, policy_replacements
from devcovenant.core.parser import PolicyParser

_POLICY_BLOCK_RE = re.compile(
    r"(##\s+Policy:\s+[^\n]+\n\n)```policy-def\n(.*?)\n```\n\n"
    r"(.*?)(?=\n---\n|\n##|\Z)",
    re.DOTALL,
)


@dataclass(frozen=True)
class ReplacementPlan:
    """Plan for policy replacements during update."""

    migrate: Tuple[str, ...]
    remove: Tuple[str, ...]
    new_stock: Tuple[str, ...]


@dataclass
class PolicySources:
    """Captured policy sources for migration."""

    scripts: Dict[str, str]
    fixers: Dict[str, str]


def _utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _parse_metadata_block(
    block: str,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered keys and per-key line values from a policy-def block."""
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


def _render_metadata_block(
    keys: List[str], values: Dict[str, List[str]]
) -> str:
    """Render a policy-def block from ordered keys and values."""
    lines: List[str] = []
    for key in keys:
        entries = values.get(key, [])
        if not entries:
            lines.append(f"{key}:")
            continue
        first = entries[0]
        if first:
            lines.append(f"{key}: {first}")
        else:
            lines.append(f"{key}:")
        for extra in entries[1:]:
            lines.append(f"  {extra}")
    return "\n".join(lines)


def _ensure_key(
    keys: List[str], values: Dict[str, List[str]], key: str
) -> None:
    """Ensure a metadata key exists in order and value map."""
    if key not in values:
        values[key] = []
    if key not in keys:
        keys.append(key)


def _cleanup_policy_separators(text: str) -> str:
    """Collapse duplicate separators after policy removals."""
    cleaned = re.sub(r"\n---\n(?:\s*\n---\n)+", "\n---\n", text)
    cleaned = re.sub(r"\n---\n(\s*\n)+\Z", "\n", cleaned)
    return cleaned


def _collect_policies(agents_path: Path) -> Dict[str, object]:
    """Return policy definitions keyed by id."""
    if not agents_path.exists():
        return {}
    parser = PolicyParser(agents_path)
    policies = {
        policy.policy_id: policy
        for policy in parser.parse_agents_md()
        if policy.policy_id
    }
    return policies


def _collect_new_stock_policies(
    template_path: Path, existing_ids: set[str]
) -> Tuple[str, ...]:
    """Return new stock policy IDs that were not present before update."""
    parser = PolicyParser(template_path)
    template_ids = {
        policy.policy_id
        for policy in parser.parse_agents_md()
        if policy.policy_id and policy.status != "deleted"
    }
    new_ids = sorted(template_ids - existing_ids)
    return tuple(new_ids)


def _build_replacement_plan(
    target_policies: Dict[str, object],
    replacements: Dict[str, policy_replacements.PolicyReplacement],
    template_path: Path,
) -> ReplacementPlan:
    """Determine which policies to migrate or remove."""
    migrate: List[str] = []
    remove: List[str] = []
    for policy_id, replacement in replacements.items():
        policy = target_policies.get(policy_id)
        if not policy:
            continue
        if getattr(policy, "apply", False):
            migrate.append(replacement.policy_id)
        else:
            remove.append(replacement.policy_id)

    new_stock = _collect_new_stock_policies(
        template_path, set(target_policies.keys())
    )
    return ReplacementPlan(
        migrate=tuple(migrate),
        remove=tuple(remove),
        new_stock=new_stock,
    )


def _policy_script_name(policy_id: str) -> str:
    """Return the script name for a policy id."""
    return policy_id.replace("-", "_")


def _snapshot_policy_sources(
    repo_root: Path, policy_ids: Tuple[str, ...]
) -> PolicySources:
    """Capture existing core policy scripts and fixers for migration."""
    scripts: Dict[str, str] = {}
    fixers: Dict[str, str] = {}
    for policy_id in policy_ids:
        script_name = _policy_script_name(policy_id)
        script_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "policies"
            / script_name
            / f"{script_name}.py"
        )
        if script_path.exists():
            scripts[policy_id] = script_path.read_text(encoding="utf-8")
        fixer_path = (
            repo_root
            / "devcovenant"
            / "core"
            / "policies"
            / script_name
            / "fixers"
            / "global.py"
        )
        if fixer_path.exists():
            fixers[policy_id] = fixer_path.read_text(encoding="utf-8")
    return PolicySources(scripts=scripts, fixers=fixers)


def _write_custom_sources(
    repo_root: Path,
    policy_id: str,
    sources: PolicySources,
) -> None:
    """Write captured policy sources into custom directories."""
    script_name = _policy_script_name(policy_id)
    policy_dir = (
        repo_root / "devcovenant" / "custom" / "policies" / script_name
    )
    if policy_id in sources.scripts:
        policy_dir.mkdir(parents=True, exist_ok=True)
        custom_path = policy_dir / f"{script_name}.py"
        if not custom_path.exists():
            custom_path.write_text(
                sources.scripts[policy_id], encoding="utf-8"
            )
    if policy_id in sources.fixers:
        fixer_dir = policy_dir / "fixers"
        fixer_dir.mkdir(parents=True, exist_ok=True)
        fixer_path = fixer_dir / "global.py"
        if not fixer_path.exists():
            fixer_path.write_text(sources.fixers[policy_id], encoding="utf-8")


def _remove_custom_sources(repo_root: Path, policy_id: str) -> None:
    """Remove custom policy sources for a policy."""
    script_name = _policy_script_name(policy_id)
    for rel_path in (
        f"devcovenant/custom/policies/{script_name}/{script_name}.py",
        f"devcovenant/custom/policies/{script_name}/fixers/global.py",
    ):
        target = repo_root / rel_path
        if target.exists():
            target.unlink()


def _rewrite_agents_for_replacements(
    agents_path: Path,
    migrate_ids: Tuple[str, ...],
    remove_ids: Tuple[str, ...],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Apply replacement metadata changes and removals to AGENTS.md."""
    if not agents_path.exists():
        return (), ()

    migrate_set = set(migrate_ids)
    remove_set = set(remove_ids)
    migrated: List[str] = []
    removed: List[str] = []
    content = agents_path.read_text(encoding="utf-8")

    # Policy block rewriter for replacement actions.
    def _replace(match: re.Match[str]) -> str:
        heading = match.group(1)
        metadata_block = match.group(2).strip()
        description = match.group(3)
        order, values = _parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0]
        if policy_id in remove_set:
            removed.append(policy_id)
            return ""
        if policy_id in migrate_set:
            _ensure_key(order, values, "status")
            _ensure_key(order, values, "custom")
            values["status"] = ["deprecated"]
            values["custom"] = ["true"]
            rendered = _render_metadata_block(order, values)
            migrated.append(policy_id)
            return f"{heading}```policy-def\n{rendered}\n```\n\n{description}"
        return match.group(0)

    updated, _count = _POLICY_BLOCK_RE.subn(_replace, content)
    updated = _cleanup_policy_separators(updated)
    if updated != content:
        agents_path.write_text(updated, encoding="utf-8")
    return tuple(migrated), tuple(removed)


def _record_notifications(target_root: Path, messages: List[str]) -> None:
    """Persist update notifications in the manifest."""
    if not messages:
        return
    manifest = manifest_module.load_manifest(target_root)
    if not manifest:
        return
    notifications = manifest.get("notifications", [])
    timestamp = _utc_now()
    for message in messages:
        notifications.append({"timestamp": timestamp, "message": message})
    manifest["notifications"] = notifications
    manifest_module.write_manifest(target_root, manifest)


def _print_notifications(messages: List[str]) -> None:
    """Print update notifications to stdout."""
    if not messages:
        return
    print("\nPolicy update notices:")
    for message in messages:
        print(f"- {message}")


def main(argv=None) -> None:
    """CLI entry point for updates."""
    parser = argparse.ArgumentParser(
        description="Update DevCovenant in a target repository."
    )
    cli_options.add_install_update_args(
        parser,
        defaults=cli_options.DEFAULT_UPDATE_DEFAULTS,
    )
    args = parser.parse_args(argv)

    target_root = Path(args.target).resolve()
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "AGENTS.md"
    )
    agents_path = target_root / "AGENTS.md"

    existing_policies = _collect_policies(agents_path)
    replacements = policy_replacements.load_policy_replacements(
        Path(__file__).resolve().parents[2]
    )
    plan = _build_replacement_plan(
        existing_policies, replacements, schema_path
    )
    sources = _snapshot_policy_sources(target_root, plan.migrate)

    install_args = cli_options.build_install_args(
        args,
        mode="existing",
        allow_existing=True,
    )
    install.main(install_args)

    migrated, removed = _rewrite_agents_for_replacements(
        agents_path, plan.migrate, plan.remove
    )
    for policy_id in migrated:
        _write_custom_sources(target_root, policy_id, sources)
    for policy_id in removed:
        _remove_custom_sources(target_root, policy_id)

    notifications: List[str] = []
    for policy_id in migrated:
        replacement = replacements.get(policy_id)
        if replacement:
            notifications.append(
                (
                    f"Policy '{policy_id}' replaced by"
                    f" '{replacement.replaced_by}' and moved to"
                    " custom (deprecated)."
                )
            )
    for policy_id in removed:
        replacement = replacements.get(policy_id)
        if replacement:
            notifications.append(
                (
                    f"Policy '{policy_id}' replaced by"
                    f" '{replacement.replaced_by}' and removed"
                    " because it was disabled."
                )
            )
    if plan.new_stock:
        joined = ", ".join(plan.new_stock)
        notifications.append(f"New stock policies available: {joined}.")

    _record_notifications(target_root, notifications)
    _print_notifications(notifications)

    metadata_normalizer.normalize_agents_metadata(
        agents_path, schema_path, set_updated=True
    )


if __name__ == "__main__":
    main()
