"""Workflow-contract resolution for reserved anchors and declared phases."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Mapping, Sequence

from devcovenant.core.services import (
    profile_registry as profile_registry_service,
)
from devcovenant.core.services import yaml_cache as yaml_cache_service

SCHEMA_VERSION = 3
ANCHOR_IDS = ("start", "mid", "end")
_FRESHNESS_KINDS = {"ignore_paths", "any_change"}
_RUNNER_KINDS = {
    "command_group",
    "runtime_action",
    "policy_command",
    "manual_attestation",
}
_SUCCESS_CONTRACT_KINDS = {
    "all_commands_exit_zero",
    "runtime_action_success",
    "policy_command_success",
    "manual_attested",
    "external_artifact_check",
}
_DEFAULT_TESTS_PHASE_ID = "tests"
_DEFAULT_FRESHNESS_IGNORED_FILES = ("CHANGELOG.md",)


def _load_config_payload(repo_root: Path) -> dict[str, object]:
    """Load `devcovenant/config.yaml` into a mapping."""

    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        raise ValueError(f"Missing config file: {config_path}")
    payload = yaml_cache_service.load_yaml(config_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a YAML mapping: {config_path}")
    return payload


def _normalize_bool(raw_value: object, *, default: bool) -> bool:
    """Normalize a loose YAML-ish boolean token."""

    if isinstance(raw_value, bool):
        return raw_value
    token = str(raw_value or "").strip().lower()
    if not token:
        return default
    if token in {"true", "1", "yes", "on"}:
        return True
    if token in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean token `{raw_value}`.")


def _normalize_int(raw_value: object, *, default: int) -> int:
    """Normalize one ordering integer."""

    if raw_value in {None, ""}:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer token `{raw_value}`.") from exc


def _normalize_commands(raw_value: object, *, field_name: str) -> list[str]:
    """Normalize a command-group payload into an ordered string list."""

    if isinstance(raw_value, str):
        values = [raw_value]
    elif isinstance(raw_value, list):
        values = list(raw_value)
    else:
        raise ValueError(
            f"Invalid `{field_name}` payload: expected string or list."
        )
    commands: list[str] = []
    for entry in values:
        token = str(entry or "").strip()
        if token and token not in commands:
            commands.append(token)
    if not commands:
        raise ValueError(f"`{field_name}` must declare at least one command.")
    return commands


def _normalize_string_list(
    raw_value: object,
    *,
    field_name: str,
) -> list[str]:
    """Normalize one optional string-or-list payload into unique strings."""

    if raw_value in {None, ""}:
        return []
    if isinstance(raw_value, str):
        values = [raw_value]
    elif isinstance(raw_value, list):
        values = list(raw_value)
    else:
        raise ValueError(
            f"Invalid `{field_name}` payload: expected string or list."
        )
    normalized: list[str] = []
    for entry in values:
        token = str(entry or "").strip()
        if token and token not in normalized:
            normalized.append(token)
    return normalized


def _normalize_phase_entry(
    profile_name: str,
    raw_entry: Mapping[str, object],
) -> dict[str, object]:
    """Normalize one workflow-phase manifest entry."""

    phase_id = str(raw_entry.get("id") or "").strip().lower()
    if not phase_id:
        raise ValueError(
            f"Profile `{profile_name}` has a workflow phase without id."
        )
    enabled = _normalize_bool(raw_entry.get("enabled"), default=True)
    required = _normalize_bool(raw_entry.get("required"), default=True)
    after = str(raw_entry.get("after") or "mid").strip().lower() or "mid"
    before = str(raw_entry.get("before") or "end").strip().lower() or "end"
    order = _normalize_int(raw_entry.get("order"), default=100)

    runner_raw = raw_entry.get("runner")
    if not isinstance(runner_raw, Mapping):
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` "
            "must define runner as a mapping."
        )
    runner_kind = str(runner_raw.get("kind") or "").strip().lower()
    if runner_kind not in _RUNNER_KINDS:
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` uses "
            f"unsupported runner kind `{runner_kind}`."
        )
    runner: dict[str, object] = {"kind": runner_kind}
    if runner_kind == "command_group":
        runner["commands"] = _normalize_commands(
            runner_raw.get("commands"),
            field_name=f"workflow_phases[{phase_id}].runner.commands",
        )
    elif runner_kind in {"runtime_action", "policy_command"}:
        target = str(runner_raw.get("target") or "").strip()
        if not target:
            raise ValueError(
                f"Workflow phase `{phase_id}` in profile `{profile_name}` "
                f"must define runner.target for `{runner_kind}`."
            )
        runner["target"] = target
        payload_raw = runner_raw.get("payload")
        if payload_raw is None:
            payload = {}
        elif isinstance(payload_raw, Mapping):
            payload = dict(payload_raw)
        else:
            raise ValueError(
                f"Workflow phase `{phase_id}` in profile `{profile_name}` "
                "must define runner.payload as a mapping when present."
            )
        if payload:
            runner["payload"] = payload
        if runner_kind == "policy_command":
            runner["args"] = _normalize_string_list(
                runner_raw.get("args"),
                field_name=f"workflow_phases[{phase_id}].runner.args",
            )
    elif runner_kind == "manual_attestation":
        attestation_key = str(runner_raw.get("attestation_key") or "").strip()
        if not attestation_key:
            raise ValueError(
                f"Workflow phase `{phase_id}` in profile `{profile_name}` "
                "must define runner.attestation_key for manual attestation."
            )
        runner["attestation_key"] = attestation_key

    success_raw = raw_entry.get("success_contract")
    if not isinstance(success_raw, Mapping):
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` "
            "must define success_contract as a mapping."
        )
    success_kind = str(success_raw.get("kind") or "").strip().lower()
    if success_kind not in _SUCCESS_CONTRACT_KINDS:
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` uses "
            f"unsupported success contract `{success_kind}`."
        )
    success_contract: dict[str, object] = {"kind": success_kind}
    if success_kind == "external_artifact_check":
        base_dir = str(success_raw.get("base_dir") or ".").strip() or "."
        required_files = _normalize_string_list(
            success_raw.get("required_files"),
            field_name=(
                f"workflow_phases[{phase_id}].success_contract.required_files"
            ),
        )
        required_globs = _normalize_string_list(
            success_raw.get("required_globs"),
            field_name=(
                f"workflow_phases[{phase_id}].success_contract.required_globs"
            ),
        )
        forbidden_globs = _normalize_string_list(
            success_raw.get("forbidden_globs"),
            field_name=(
                f"workflow_phases[{phase_id}].success_contract."
                "forbidden_globs"
            ),
        )
        minimum_matches = _normalize_int(
            success_raw.get("minimum_matches"),
            default=1,
        )
        if minimum_matches < 0:
            raise ValueError(
                f"Workflow phase `{phase_id}` in profile `{profile_name}` "
                "must define a non-negative minimum_matches value."
            )
        if not (required_files or required_globs or forbidden_globs):
            raise ValueError(
                f"Workflow phase `{phase_id}` in profile `{profile_name}` "
                "must define required_files, required_globs, or "
                "forbidden_globs for external_artifact_check."
            )
        success_contract.update(
            {
                "base_dir": base_dir,
                "required_files": required_files,
                "required_globs": required_globs,
                "forbidden_globs": forbidden_globs,
                "minimum_matches": minimum_matches,
            }
        )

    recording_raw = raw_entry.get("recording")
    if recording_raw is None:
        recording_raw = {}
    if not isinstance(recording_raw, Mapping):
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` "
            "must define recording as a mapping when present."
        )
    recording = {
        "record_in_session": _normalize_bool(
            recording_raw.get("record_in_session"),
            default=True,
        ),
        "summary_label": (
            str(recording_raw.get("summary_label") or phase_id).strip().title()
            or phase_id.title()
        ),
        "output_mode_config_field": str(
            recording_raw.get("output_mode_config_field") or ""
        ).strip(),
        "event_adapter_group": str(
            recording_raw.get("event_adapter_group") or ""
        ).strip(),
        "write_runtime_profile": _normalize_bool(
            recording_raw.get("write_runtime_profile"),
            default=False,
        ),
    }
    freshness_raw = raw_entry.get("freshness")
    if freshness_raw is None:
        freshness_raw = {}
    if not isinstance(freshness_raw, Mapping):
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` "
            "must define freshness as a mapping when present."
        )
    freshness_kind = (
        str(freshness_raw.get("kind") or "ignore_paths").strip().lower()
        or "ignore_paths"
    )
    if freshness_kind not in _FRESHNESS_KINDS:
        raise ValueError(
            f"Workflow phase `{phase_id}` in profile `{profile_name}` uses "
            f"unsupported freshness kind `{freshness_kind}`."
        )
    freshness: dict[str, object] = {"kind": freshness_kind}
    if freshness_kind == "ignore_paths":
        ignored_files = _normalize_string_list(
            freshness_raw.get("ignored_files"),
            field_name=f"workflow_phases[{phase_id}].freshness.ignored_files",
        )
        ignored_globs = _normalize_string_list(
            freshness_raw.get("ignored_globs"),
            field_name=f"workflow_phases[{phase_id}].freshness.ignored_globs",
        )
        if not ignored_files and not ignored_globs:
            ignored_files = list(_DEFAULT_FRESHNESS_IGNORED_FILES)
        freshness.update(
            {
                "ignored_files": ignored_files,
                "ignored_globs": ignored_globs,
            }
        )

    phase = {
        "id": phase_id,
        "owner": "profile",
        "owner_id": profile_name,
        "enabled": enabled,
        "required": required,
        "position": {
            "after": after,
            "before": before,
            "order": order,
        },
        "runner": runner,
        "success_contract": success_contract,
        "recording": recording,
        "freshness": freshness,
        "source_field": "workflow_phases",
    }
    return phase


def _normalize_manifest_phases(
    profile_name: str,
    raw_value: object,
) -> list[dict[str, object]]:
    """Normalize workflow phases declared in one profile manifest."""

    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise ValueError(
            f"Profile `{profile_name}` must define workflow_phases as a list."
        )
    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for raw_entry in raw_value:
        if not isinstance(raw_entry, Mapping):
            raise ValueError(
                f"Profile `{profile_name}` has non-mapping workflow phase "
                "entries."
            )
        entry = _normalize_phase_entry(profile_name, raw_entry)
        phase_id = str(entry["id"])
        if phase_id in seen_ids:
            raise ValueError(
                f"Profile `{profile_name}` defines duplicate workflow phase "
                f"`{phase_id}`."
            )
        seen_ids.add(phase_id)
        normalized.append(entry)
    return normalized


def _phase_sort_key(phase: Mapping[str, object]) -> tuple[int, str, str]:
    """Return deterministic sort key for resolved phase entries."""

    position = phase.get("position")
    if isinstance(position, Mapping):
        order = _normalize_int(position.get("order"), default=100)
    else:
        order = 100
    owner = str(phase.get("owner_id") or "").strip().lower()
    phase_id = str(phase.get("id") or "").strip().lower()
    return (order, owner, phase_id)


def _default_anchor_rows() -> list[dict[str, object]]:
    """Return the reserved anchor definitions for every contract."""

    return [
        {
            "id": anchor_id,
            "owner": "core",
            "required": True,
            "phase_kind": "gate_anchor",
        }
        for anchor_id in ANCHOR_IDS
    ]


def build_workflow_contract(
    repo_root: Path,
    profiles_registry: Mapping[str, Mapping[str, object]],
    active_profiles: Sequence[str],
) -> dict[str, object]:
    """Build the resolved workflow contract for the active profile set."""

    phase_map: dict[str, dict[str, object]] = {}
    active_names = profile_registry_service._active_profile_names(
        active_profiles
    )
    for profile_name in active_names:
        profile_meta = profiles_registry.get(profile_name, {})
        if not isinstance(profile_meta, Mapping):
            continue
        for phase in _normalize_manifest_phases(
            profile_name,
            profile_meta.get("workflow_phases"),
        ):
            phase_map[str(phase["id"])] = phase
    phases = sorted(phase_map.values(), key=_phase_sort_key)
    required_phase_ids = [
        str(phase.get("id") or "")
        for phase in phases
        if bool(phase.get("enabled")) and bool(phase.get("required"))
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "anchors": _default_anchor_rows(),
        "phases": phases,
        "required_phase_ids": required_phase_ids,
        "active_profiles": list(active_names),
    }


def load_workflow_contract(repo_root: Path) -> dict[str, object]:
    """Resolve the active workflow contract from config and profiles."""

    config = _load_config_payload(repo_root)
    active_profiles = profile_registry_service.parse_active_profiles(
        config,
        include_global=True,
    )
    registry = profile_registry_service.load_profile_registry(repo_root)
    return build_workflow_contract(repo_root, registry, active_profiles)


def resolve_phase(
    contract: Mapping[str, object],
    phase_id: str,
) -> dict[str, object] | None:
    """Return one phase definition by id from a workflow contract."""

    token = str(phase_id or "").strip().lower()
    raw_phases = contract.get("phases")
    if not isinstance(raw_phases, list):
        return None
    for raw_phase in raw_phases:
        if not isinstance(raw_phase, Mapping):
            continue
        if str(raw_phase.get("id") or "").strip().lower() != token:
            continue
        return dict(raw_phase)
    return None


def required_phase_ids(contract: Mapping[str, object]) -> list[str]:
    """Return enabled required phase ids from a workflow contract."""

    raw_ids = contract.get("required_phase_ids")
    if isinstance(raw_ids, list):
        return [
            str(entry or "").strip().lower()
            for entry in raw_ids
            if str(entry or "").strip()
        ]
    raw_phases = contract.get("phases")
    if not isinstance(raw_phases, list):
        return []
    resolved: list[str] = []
    for raw_phase in raw_phases:
        if not isinstance(raw_phase, Mapping):
            continue
        phase_id = str(raw_phase.get("id") or "").strip().lower()
        if not phase_id:
            continue
        if not _normalize_bool(raw_phase.get("enabled"), default=True):
            continue
        if not _normalize_bool(raw_phase.get("required"), default=True):
            continue
        resolved.append(phase_id)
    return resolved


def resolve_tests_phase(repo_root: Path) -> dict[str, object]:
    """Return the resolved `tests` phase or raise when absent."""

    contract = load_workflow_contract(repo_root)
    phase = resolve_phase(contract, _DEFAULT_TESTS_PHASE_ID)
    if phase is None:
        raise ValueError(
            "No `tests` workflow phase is configured for the active profiles."
        )
    runner = phase.get("runner")
    if not isinstance(runner, Mapping) or str(runner.get("kind") or "") != (
        "command_group"
    ):
        raise ValueError(
            "The `tests` workflow phase must use runner.kind: command_group."
        )
    return phase


def phase_relevant_paths_changed(
    phase: Mapping[str, object],
    changed_paths: Sequence[str],
) -> bool:
    """Return whether changed paths invalidate one phase result."""

    if not changed_paths:
        return False
    freshness = phase.get("freshness")
    freshness_map = dict(freshness) if isinstance(freshness, Mapping) else {}
    freshness_kind = (
        str(freshness_map.get("kind") or "ignore_paths").strip().lower()
        or "ignore_paths"
    )
    if freshness_kind == "any_change":
        return True
    ignored_files = {
        str(entry).replace("\\", "/").strip().lower()
        for entry in freshness_map.get("ignored_files") or ()
        if str(entry).strip()
    }
    if not ignored_files:
        ignored_files = {
            token.lower() for token in _DEFAULT_FRESHNESS_IGNORED_FILES
        }
    ignored_globs = [
        str(entry).replace("\\", "/").strip().lower()
        for entry in freshness_map.get("ignored_globs") or ()
        if str(entry).strip()
    ]
    for raw_path in changed_paths:
        normalized_path = str(raw_path).replace("\\", "/").strip().lower()
        if not normalized_path:
            continue
        leaf = normalized_path.rsplit("/", 1)[-1]
        if normalized_path in ignored_files or leaf in ignored_files:
            continue
        if any(
            fnmatch.fnmatch(normalized_path, pattern)
            or fnmatch.fnmatch(leaf, pattern)
            for pattern in ignored_globs
        ):
            continue
        return True
    return False
