"""Consistency checks for descriptor and registry policy inventory."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_REGISTRY_PATH = (
    REPO_ROOT / "devcovenant" / "registry" / "local" / "policy_registry.yaml"
)


def _load_descriptor_policy_ids() -> set[str]:
    """Return policy IDs declared by core and custom descriptors."""
    policy_ids: set[str] = set()
    for root in (
        REPO_ROOT / "devcovenant" / "core" / "policies",
        REPO_ROOT / "devcovenant" / "custom" / "policies",
    ):
        for descriptor_path in sorted(root.glob("*/*.yaml")):
            payload = yaml.safe_load(
                descriptor_path.read_text(encoding="utf-8")
            )
            if not isinstance(payload, dict):
                continue
            policy_id = payload.get("id")
            if isinstance(policy_id, str) and policy_id:
                policy_ids.add(policy_id)
    return policy_ids


def test_policy_registry_lists_exact_policy_inventory() -> None:
    """Local policy registry should match descriptor inventory."""
    descriptor_ids = _load_descriptor_policy_ids()
    payload = (
        yaml.safe_load(POLICY_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    )
    policies = payload.get("policies")
    assert isinstance(policies, dict)
    registry_ids = set(policies.keys())

    assert registry_ids == descriptor_ids, (
        "policy_registry.yaml policy IDs drifted.\n"
        f"Missing: {sorted(descriptor_ids - registry_ids)}\n"
        f"Unexpected: {sorted(registry_ids - descriptor_ids)}"
    )
