"""Generate low-token policy/workflow audit digest artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from devcovenant.core.services import registry as registry_runtime_module

_WORKFLOW_BEGIN = "<!-- DEVCOV-WORKFLOW:BEGIN -->"
_WORKFLOW_END = "<!-- DEVCOV-WORKFLOW:END -->"
_POLICIES_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
_POLICIES_END = "<!-- DEVCOV-POLICIES:END -->"
_EXECUTION_ORDER_HEADING = "## Execution Order (Mandatory)"
_SECTION_HEADING_PREFIX = "## "
_STEP_RE = re.compile(r"^\s*(\d+)\.\s+(.*?)\s*$")
_SEVERITY_KEYS = ("critical", "error", "warning", "info")


def _read_text(path: Path) -> str:
    """Read one UTF-8 text file, raising ValueError on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read {path}: {exc}") from exc


def _between_markers(
    text: str,
    begin_marker: str,
    end_marker: str,
    *,
    section_name: str,
) -> str:
    """Extract text between two markers, raising ValueError if missing."""
    start = text.find(begin_marker)
    if start < 0:
        raise ValueError(f"Missing {section_name} begin marker.")
    content_start = start + len(begin_marker)
    end = text.find(end_marker, content_start)
    if end < 0:
        raise ValueError(f"Missing {section_name} end marker.")
    return text[content_start:end].strip("\n")


def _hash_text(text: str) -> str:
    """Return deterministic SHA-256 hash for one text payload."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _workflow_execution_steps(workflow_block: str) -> list[str]:
    """Extract numbered execution-order steps from workflow block text."""
    steps: list[str] = []
    in_execution_order = False
    for raw_line in workflow_block.splitlines():
        stripped = raw_line.strip()
        if not in_execution_order:
            if stripped == _EXECUTION_ORDER_HEADING:
                in_execution_order = True
            continue
        if stripped.startswith(_SECTION_HEADING_PREFIX):
            break
        match = _STEP_RE.match(raw_line)
        if match is None:
            continue
        step_text = match.group(2).strip()
        if step_text:
            steps.append(step_text)
    if not steps:
        raise ValueError(
            "AGENTS workflow block is missing numbered execution-order steps."
        )
    return steps


def _as_bool(raw_value: object, *, default: bool = False) -> bool:
    """Return deterministic bool for metadata-like values."""
    if isinstance(raw_value, bool):
        return raw_value
    token = str(raw_value or "").strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    return default


def _policy_rows(
    policy_registry_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return sorted policy rows from registry payload."""
    rows: list[dict[str, Any]] = []
    raw_policies = policy_registry_payload.get("policies")
    if not isinstance(raw_policies, dict):
        raise ValueError(
            "Invalid policy registry payload: `policies` must be a mapping."
        )
    for policy_id in sorted(raw_policies):
        raw_entry = raw_policies.get(policy_id)
        if not isinstance(raw_entry, dict):
            continue
        severity = str(raw_entry.get("severity", "warning")).strip().lower()
        if severity not in _SEVERITY_KEYS:
            severity = "warning"
        rows.append(
            {
                "id": str(policy_id).strip(),
                "enabled": _as_bool(raw_entry.get("enabled"), default=True),
                "severity": severity,
                "auto_fix": _as_bool(raw_entry.get("auto_fix"), default=False),
                "custom": _as_bool(raw_entry.get("custom"), default=False),
            }
        )
    return rows


def build_audit_digest_payload(
    repo_root: Path,
    *,
    agents_text: str,
    policy_registry_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build one machine-readable informational audit digest payload."""
    workflow_block = _between_markers(
        agents_text,
        _WORKFLOW_BEGIN,
        _WORKFLOW_END,
        section_name="workflow block",
    )
    policies_block = _between_markers(
        agents_text,
        _POLICIES_BEGIN,
        _POLICIES_END,
        section_name="policies block",
    )
    execution_steps = _workflow_execution_steps(workflow_block)
    policy_rows = _policy_rows(policy_registry_payload)
    enabled_rows = [row for row in policy_rows if row["enabled"]]
    severity_counts = {token: 0 for token in _SEVERITY_KEYS}
    for row in enabled_rows:
        severity_counts[row["severity"]] += 1

    json_path = registry_runtime_module.audit_digest_json_path(repo_root)
    txt_path = registry_runtime_module.audit_digest_txt_path(repo_root)
    policy_registry_path = registry_runtime_module.policy_registry_path(
        repo_root
    )
    return {
        "schema_version": "1.0",
        "informational_only": True,
        "canonical_source": {
            "path": "AGENTS.md",
            "requirement": "Read AGENTS.md as canonical law.",
        },
        "workflow": {
            "hash_sha256": _hash_text(workflow_block),
            "step_count": len(execution_steps),
            "steps": [
                {"index": index + 1, "text": text}
                for index, text in enumerate(execution_steps)
            ],
        },
        "policies": {
            "hash_sha256": _hash_text(policies_block),
            "total_policies": len(policy_rows),
            "enabled_policies": len(enabled_rows),
            "enabled_by_severity": severity_counts,
            "enabled_ids": [row["id"] for row in enabled_rows],
            "enabled_critical_ids": [
                row["id"]
                for row in enabled_rows
                if row["severity"] == "critical"
            ],
        },
        "artifacts": {
            "audit_digest_json": json_path.relative_to(repo_root).as_posix(),
            "audit_digest_txt": txt_path.relative_to(repo_root).as_posix(),
            "policy_registry": policy_registry_path.relative_to(
                repo_root
            ).as_posix(),
        },
    }


def render_audit_digest_text(payload: dict[str, Any]) -> str:
    """Render a concise human-readable informational digest summary."""
    workflow = payload.get("workflow", {})
    policies = payload.get("policies", {})
    steps = workflow.get("steps", [])
    severity = policies.get("enabled_by_severity", {})
    critical_ids = policies.get("enabled_critical_ids", [])

    lines = [
        "DevCovenant Audit Digest (Informational, Non-Canonical)",
        "Canonical Source: AGENTS.md",
        "Notice: Read AGENTS.md as canonical law.",
        "",
        f"Workflow Hash: {workflow.get('hash_sha256', '')}",
        f"Policies Hash: {policies.get('hash_sha256', '')}",
        "",
        "Execution Order (Mandatory):",
    ]
    for step in steps:
        if not isinstance(step, dict):
            continue
        index = step.get("index", "")
        text = str(step.get("text", "")).strip()
        if text:
            lines.append(f"{index}. {text}")

    lines.extend(
        [
            "",
            "Enabled Policy Counts:",
            (
                "critical="
                f"{severity.get('critical', 0)}, "
                f"error={severity.get('error', 0)}, "
                f"warning={severity.get('warning', 0)}, "
                f"info={severity.get('info', 0)}"
            ),
            "",
            "Enabled Critical Policies:",
        ]
    )
    if isinstance(critical_ids, list) and critical_ids:
        for policy_id in critical_ids:
            lines.append(f"- {policy_id}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _write_if_changed(path: Path, content: str) -> bool:
    """Write one file only when content changed."""
    current = ""
    if path.exists():
        current = _read_text(path)
    if current == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def refresh_audit_digest_artifacts(
    repo_root: Path,
    *,
    agents_path: Path | None = None,
    policy_registry_path: Path | None = None,
) -> list[str]:
    """Refresh informational local audit digest artifacts."""
    resolved_agents = agents_path or (Path(repo_root) / "AGENTS.md")
    resolved_policy_registry = (
        policy_registry_path
        or registry_runtime_module.policy_registry_path(repo_root)
    )
    agents_text = _read_text(resolved_agents)
    try:
        policy_payload = yaml.safe_load(
            resolved_policy_registry.read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ValueError(
            f"Unable to read {resolved_policy_registry}: {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in {resolved_policy_registry}: {exc}"
        ) from exc
    if not isinstance(policy_payload, dict):
        raise ValueError(
            "Invalid policy registry payload: expected top-level mapping."
        )

    payload = build_audit_digest_payload(
        Path(repo_root),
        agents_text=agents_text,
        policy_registry_payload=policy_payload,
    )
    json_output = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    text_output = render_audit_digest_text(payload).rstrip() + "\n"

    digest_json_path = registry_runtime_module.audit_digest_json_path(
        Path(repo_root)
    )
    digest_txt_path = registry_runtime_module.audit_digest_txt_path(
        Path(repo_root)
    )
    changed: list[str] = []
    if _write_if_changed(digest_json_path, json_output):
        changed.append(digest_json_path.relative_to(repo_root).as_posix())
    if _write_if_changed(digest_txt_path, text_output):
        changed.append(digest_txt_path.relative_to(repo_root).as_posix())
    return changed
