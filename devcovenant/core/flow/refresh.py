"""Full refresh orchestration for DevCovenant repositories."""

from __future__ import annotations

import copy
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import yaml

import devcovenant.core.services.metadata as metadata_runtime
import devcovenant.core.services.profile_registry as profile_runtime
import devcovenant.core.services.registry as manifest_module
from devcovenant.builtin.policies.project_governance import (
    project_governance as project_governance_runtime_module,
)
from devcovenant.core.contracts.policy import CheckContext
from devcovenant.core.runtime.execution import print_step, runtime_print
from devcovenant.core.services import (
    policy_block_refresh as refresh_policy_block_runtime_module,
)
from devcovenant.core.services import (
    policy_runtime_actions as runtime_actions_module,
)
from devcovenant.core.services.policy_parse import PolicyDefinition
from devcovenant.core.services.registry import (
    PolicyRegistry,
    iter_script_locations,
    load_policy_descriptor,
    policy_registry_path,
    resolve_script_location,
)

ProjectGovernanceState = (
    project_governance_runtime_module.ProjectGovernanceState
)

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
WORKFLOW_BEGIN = "<!-- DEVCOV-WORKFLOW:BEGIN -->"
WORKFLOW_END = "<!-- DEVCOV-WORKFLOW:END -->"
_POLICIES_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
_POLICIES_END = "<!-- DEVCOV-POLICIES:END -->"
_USER_PRESERVE_BEGIN = "<!-- DEVCOV-USER-PRESERVE:BEGIN -->"
_USER_PRESERVE_END = "<!-- DEVCOV-USER-PRESERVE:END -->"
_DOC_ID_LABEL = "**Doc ID:**"
_DOC_TYPE_LABEL = "**Doc Type:**"
_PROJECT_VERSION_LABEL = "**Project Version:**"
_PROJECT_STAGE_LABEL = "**Project Stage:**"
_DEVELOPMENT_STANCE_LABEL = "**Development Stance:**"
_VERSIONING_MODE_LABEL = "**Versioning Mode:**"
_PROJECT_CODENAME_LABEL = "**Project Codename:**"
_BUILD_IDENTITY_LABEL = "**Build Identity:**"
_LAST_UPDATED_LABEL = "**Last Updated:**"
_DEVCOV_VERSION_LABEL = "**DevCovenant Version:**"
_AGENTS_EDITABLE_HEADING = "# EDITABLE SECTION"
_AGENTS_EDITABLE_HYGIENE_HEADING = "## Editable-Section Hygiene"
_AGENTS_EDITABLE_HYGIENE_LINES = [
    "- Keep this section focused on repo-specific direction and constraints.",
    "- Do not restate standard workflow steps that are already defined "
    "elsewhere.",
    "- Update notes in the same session when decisions change.",
    "- Remove stale notes immediately; stale notes are drift.",
]
USER_GITIGNORE_BEGIN = "# --- User entries (preserved) ---"
USER_GITIGNORE_END = "# --- End user entries ---"
_MANAGED_DOC_DESCRIPTOR_KEYS = frozenset(
    {
        "title",
        "doc_id",
        "doc_type",
        "project_version",
        "last_updated",
        "devcovenant_version",
        "project_governance_headers",
        "managed_block",
        "body",
        "workflow_block",
    }
)
_MANAGED_DOC_MULTILINE_KEYS = ("managed_block", "body", "workflow_block")
_MANAGED_DOC_REQUIRED_KEYS = (
    "title",
    "doc_id",
    "doc_type",
    "project_version",
    "last_updated",
    "devcovenant_version",
    "managed_block",
    "body",
)
_MANAGED_DOC_OPTIONAL_KEYS = ("workflow_block",)
_MANAGED_DOC_REQUIRED_BOOLEAN_KEYS = (
    "project_version",
    "last_updated",
    "devcovenant_version",
)
_MANAGED_DOC_OPTIONAL_BOOLEAN_KEYS = ("project_governance_headers",)


def _utc_today() -> str:
    """Return current UTC date."""
    return datetime.now(timezone.utc).date().isoformat()


def _read_devcovenant_version(repo_root: Path) -> str:
    """Read the DevCovenant package version from devcovenant/VERSION."""
    version_path = repo_root / "devcovenant" / "VERSION"
    if not version_path.exists():
        return "0.0.0"
    version_text = version_path.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0"


def _metadata_string_token(raw: object) -> str:
    """Normalize one metadata value into a single string token."""
    if isinstance(raw, list):
        for entry in raw:
            token = str(entry).strip()
            if token:
                return token
        return ""
    return str(raw or "").strip()


def _project_version_file_from_config(config: dict[str, object]) -> str:
    """Resolve version-sync.version_file from effective config layers."""
    metadata_layers = (
        config.get("autogen_metadata_overlays"),
        config.get("user_metadata_overlays"),
        config.get("autogen_metadata_overrides"),
        config.get("user_metadata_overrides"),
    )
    resolved = ""
    for layer in metadata_layers:
        if not isinstance(layer, dict):
            continue
        version_sync = layer.get("version-sync")
        if not isinstance(version_sync, dict):
            continue
        token = _metadata_string_token(version_sync.get("version_file"))
        if token:
            resolved = token
    return resolved or "VERSION"


def _read_project_version(
    repo_root: Path,
    config: dict[str, object],
    *,
    required: bool = True,
) -> str:
    """Read the project version using version-sync.version_file."""
    version_file = _project_version_file_from_config(config)
    version_path = _resolve_path_under_root(
        repo_root,
        version_file,
        field_name="version-sync.version_file",
    )
    if not version_path.exists():
        if required:
            raise ValueError(
                f"Missing declared project version file: {version_file}"
            )
        return ""
    try:
        version_text = version_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        if required:
            raise ValueError(
                f"Unable to read declared project version file "
                f"{version_file}: {exc}"
            ) from exc
        return ""
    if version_text:
        return version_text
    if required:
        raise ValueError(
            f"Declared project version file is empty: {version_file}"
        )
    return ""


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        raise ValueError(f"Missing YAML file: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read {path}: {exc}") from exc
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"YAML file must contain a mapping: {path}")


def _normalize_doc_name(name: str) -> str:
    """Normalize configured doc names to canonical markdown paths."""
    raw = str(name or "").strip()
    if not raw:
        return ""
    mapping = {
        "AGENTS": "AGENTS.md",
        "README": "README.md",
        "CONTRIBUTING": "CONTRIBUTING.md",
        "SPEC": "SPEC.md",
        "PLAN": "PLAN.md",
        "CHANGELOG": "CHANGELOG.md",
    }
    upper = raw.upper()
    if upper in mapping:
        return mapping[upper]
    if upper.endswith(".MD") and upper[:-3] in mapping:
        return mapping[upper[:-3]]
    return raw


def _managed_docs_from_config(config: dict[str, object]) -> list[str]:
    """Resolve autogen managed docs from config doc_assets."""
    doc_assets = config.get("doc_assets")
    if not isinstance(doc_assets, dict):
        raise ValueError(
            "`doc_assets` must be a mapping in devcovenant/config.yaml."
        )

    raw_autogen = doc_assets.get("autogen")
    raw_user = doc_assets.get("user")
    if not isinstance(raw_autogen, list):
        raise ValueError("`doc_assets.autogen` must be a list.")
    if not isinstance(raw_user, list):
        raise ValueError("`doc_assets.user` must be a list.")

    autogen = [_normalize_doc_name(item) for item in raw_autogen]
    autogen = [doc for doc in autogen if doc]
    if not autogen:
        raise ValueError(
            "`doc_assets.autogen` must contain at least one document."
        )

    user_docs = {_normalize_doc_name(item) for item in raw_user if item}

    selected = [doc for doc in autogen if doc and doc not in user_docs]
    if not selected:
        raise ValueError(
            "`doc_assets.autogen` resolved to no documents after "
            "excluding `doc_assets.user` entries."
        )
    if "AGENTS.md" not in selected:
        raise ValueError(
            "`doc_assets.autogen` must include AGENTS.md as a managed doc."
        )

    ordered: list[str] = []
    for doc in selected:
        if doc not in ordered:
            ordered.append(doc)
    return ordered


def _descriptor_path(repo_root: Path, doc_name: str) -> Path:
    """Resolve YAML descriptor path for a managed doc."""
    assets_root = (
        repo_root
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "assets"
    )
    doc_path = Path(doc_name)
    if doc_path.parent != Path("."):
        return assets_root / doc_path.with_suffix(".yaml")
    return assets_root / f"{doc_path.stem}.yaml"


def _yaml_scalar_style_token(raw_yaml: str, key: str) -> str:
    """Return the inline scalar style token from one YAML key line."""
    pattern = re.compile(
        rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:[ \t]*(?P<token>[^\n]*)$"
    )
    match = pattern.search(raw_yaml)
    if match is None:
        return ""
    return str(match.group("token") or "").strip()


def _require_literal_block_scalar(
    descriptor_path: Path,
    *,
    doc_name: str,
    field_name: str,
    field_value: str,
    raw_yaml: str,
) -> None:
    """Require literal block scalar style for multiline descriptor fields."""
    if "\n" not in field_value:
        return
    style_token = _yaml_scalar_style_token(raw_yaml, field_name)
    if style_token.startswith("|"):
        return
    raise ValueError(
        "Managed doc descriptor "
        f"`{descriptor_path}` field `{field_name}` in `{doc_name}` "
        "contains multiline text and must use YAML literal block style "
        f"(`{field_name}: |-`)."
    )


def _validate_managed_doc_descriptor(
    descriptor: dict[str, object],
    *,
    descriptor_path: Path,
    doc_name: str,
    raw_yaml: str,
) -> None:
    """Validate managed-doc descriptor schema and multiline style rules."""
    descriptor_keys = [str(key) for key in descriptor.keys()]
    unknown_keys = sorted(
        str(key)
        for key in descriptor_keys
        if str(key) not in _MANAGED_DOC_DESCRIPTOR_KEYS
    )
    if unknown_keys:
        raise ValueError(
            "Managed doc descriptor "
            f"`{descriptor_path}` has unsupported keys: "
            f"{', '.join(unknown_keys)}."
        )

    required_prefix = [
        "title",
        "doc_id",
        "doc_type",
        "project_version",
        "last_updated",
        "devcovenant_version",
    ]
    for field_name in _MANAGED_DOC_OPTIONAL_BOOLEAN_KEYS:
        if field_name in descriptor:
            required_prefix.append(field_name)
    required_prefix.extend(["managed_block", "body"])
    if descriptor_keys[: len(required_prefix)] != required_prefix:
        raise ValueError(
            "Managed doc descriptor "
            f"`{descriptor_path}` must declare keys in this order: "
            f"{', '.join(required_prefix)}."
        )

    for field_name in _MANAGED_DOC_REQUIRED_KEYS:
        if field_name not in descriptor:
            raise ValueError(
                "Managed doc descriptor "
                f"`{descriptor_path}` is missing required key `{field_name}`."
            )

    for field_name in (
        "title",
        "doc_id",
        "doc_type",
        "managed_block",
        "body",
        "workflow_block",
    ):
        raw_value = descriptor.get(field_name)
        if raw_value is None:
            continue
        if not isinstance(raw_value, str):
            raise ValueError(
                "Managed doc descriptor "
                f"`{descriptor_path}` field `{field_name}` must be a string."
            )
        if field_name in _MANAGED_DOC_MULTILINE_KEYS:
            _require_literal_block_scalar(
                descriptor_path,
                doc_name=doc_name,
                field_name=field_name,
                field_value=raw_value,
                raw_yaml=raw_yaml,
            )

    for field_name in ("title", "doc_id", "doc_type"):
        if not str(descriptor.get(field_name, "")).strip():
            raise ValueError(
                "Managed doc descriptor "
                f"`{descriptor_path}` field `{field_name}` must be "
                "non-empty."
            )

    for field_name in _MANAGED_DOC_REQUIRED_BOOLEAN_KEYS:
        raw_value = descriptor.get(field_name)
        if not isinstance(raw_value, bool):
            raise ValueError(
                "Managed doc descriptor "
                f"`{descriptor_path}` field `{field_name}` must be boolean."
            )
    for field_name in _MANAGED_DOC_OPTIONAL_BOOLEAN_KEYS:
        if field_name not in descriptor:
            continue
        raw_value = descriptor.get(field_name)
        if not isinstance(raw_value, bool):
            raise ValueError(
                "Managed doc descriptor "
                f"`{descriptor_path}` field `{field_name}` must be boolean."
            )

    if descriptor.get("devcovenant_version") is not True:
        raise ValueError(
            "Managed doc descriptor "
            f"`{descriptor_path}` field `devcovenant_version` must be true."
        )


def _load_managed_doc_descriptor(
    descriptor_path: Path,
    *,
    doc_name: str,
) -> dict[str, object]:
    """Load and validate one managed-doc descriptor payload."""
    if not descriptor_path.exists():
        raise ValueError(
            "Missing managed doc descriptor for "
            f"`{doc_name}`: {descriptor_path}"
        )
    try:
        raw_yaml = descriptor_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"Unable to read managed doc descriptor {descriptor_path}: {exc}"
        ) from exc
    try:
        payload = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in managed doc descriptor {descriptor_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "Managed doc descriptor "
            f"`{descriptor_path}` must contain a YAML mapping."
        )
    _validate_managed_doc_descriptor(
        payload,
        descriptor_path=descriptor_path,
        doc_name=doc_name,
        raw_yaml=raw_yaml,
    )
    return payload


def _descriptor_bool(descriptor: dict[str, object], field_name: str) -> bool:
    """Return a required boolean field from a managed descriptor."""
    raw_value = descriptor.get(field_name)
    if not isinstance(raw_value, bool):
        raise ValueError(
            f"Managed doc descriptor field `{field_name}` must be boolean."
        )
    return raw_value


def _descriptor_optional_bool(
    descriptor: dict[str, object],
    field_name: str,
) -> bool:
    """Return an optional boolean field from a managed descriptor."""
    raw_value = descriptor.get(field_name)
    if raw_value is None:
        return False
    if not isinstance(raw_value, bool):
        raise ValueError(
            f"Managed doc descriptor field `{field_name}` must be boolean."
        )
    return raw_value


def _render_project_governance_header_lines(
    state: project_governance_runtime_module.ProjectGovernanceState,
) -> list[str]:
    """Return generated project-governance header lines."""
    if not state.enabled:
        return []
    lines = [
        f"{_PROJECT_STAGE_LABEL} {state.stage}",
        f"{_DEVELOPMENT_STANCE_LABEL} {state.development_stance}",
        f"{_VERSIONING_MODE_LABEL} {state.versioning_mode}",
    ]
    if state.codename:
        lines.append(f"{_PROJECT_CODENAME_LABEL} {state.codename}")
    if state.build_identity:
        lines.append(f"{_BUILD_IDENTITY_LABEL} {state.build_identity}")
    return lines


def _render_generated_header(
    doc_name: str,
    descriptor: dict[str, object],
    *,
    project_version: str,
    devcovenant_version: str,
    project_governance_state: ProjectGovernanceState,
) -> list[str]:
    """Render deterministic top-of-doc header lines from descriptor keys."""
    title = str(descriptor.get("title", "")).strip()
    if not title:
        raise ValueError("Managed doc descriptor field `title` is required.")
    doc_id = str(descriptor.get("doc_id", "")).strip()
    doc_type = str(descriptor.get("doc_type", "")).strip()
    lines: list[str] = [f"# {title}"]
    if doc_id:
        lines.append(f"{_DOC_ID_LABEL} {doc_id}")
    if doc_type:
        lines.append(f"{_DOC_TYPE_LABEL} {doc_type}")
    if _descriptor_bool(descriptor, "project_version"):
        lines.append(f"{_PROJECT_VERSION_LABEL} {project_version}")
    if _descriptor_optional_bool(
        descriptor,
        "project_governance_headers",
    ):
        lines.extend(
            _render_project_governance_header_lines(project_governance_state)
        )
    if _descriptor_bool(descriptor, "last_updated"):
        lines.append(f"{_LAST_UPDATED_LABEL} {_utc_today()}")
    if _descriptor_bool(descriptor, "devcovenant_version"):
        lines.append(f"{_DEVCOV_VERSION_LABEL} {devcovenant_version}")
    return lines


def _marker_line_regex(marker: str) -> re.Pattern[str]:
    """Return a line-anchored regex for marker lookup."""
    return re.compile(rf"(?m)^[ \t]*{re.escape(marker)}[ \t]*$")


def _block_spans(
    text: str,
    begin_marker: str,
    end_marker: str,
) -> list[tuple[int, int, str]]:
    """Return positional spans for marker-delimited blocks in text."""
    spans: list[tuple[int, int, str]] = []
    begin_re = _marker_line_regex(begin_marker)
    end_re = _marker_line_regex(end_marker)
    search_start = 0
    while True:
        begin_match = begin_re.search(text, search_start)
        if begin_match is None:
            return spans
        end_match = end_re.search(text, begin_match.end())
        if end_match is None:
            return spans
        block_start = begin_match.start()
        end_marker_start = text.find(
            end_marker,
            end_match.start(),
            end_match.end(),
        )
        if end_marker_start < 0:
            return spans
        block_end = end_marker_start + len(end_marker)
        spans.append((block_start, block_end, text[block_start:block_end]))
        search_start = end_match.end()


def _render_block(begin_marker: str, end_marker: str, body: str) -> str:
    """Render a managed marker block from marker pair and body."""
    return "\n".join([begin_marker, body.rstrip("\n"), end_marker])


def _validate_preserve_markers(text: str, *, doc_name: str) -> None:
    """Validate DEVCOV preserve marker structure for one document text."""
    begin_re = _marker_line_regex(_USER_PRESERVE_BEGIN)
    end_re = _marker_line_regex(_USER_PRESERVE_END)
    events: list[tuple[int, str]] = []
    for match in begin_re.finditer(text):
        events.append((match.start(), "begin"))
    for match in end_re.finditer(text):
        events.append((match.start(), "end"))
    events.sort(key=lambda item: item[0])

    depth = 0
    for _, token in events:
        if token == "begin":
            if depth != 0:
                raise ValueError(
                    f"{doc_name} contains nested DEVCOV-USER-PRESERVE blocks."
                )
            depth = 1
            continue
        if depth == 0:
            raise ValueError(
                f"{doc_name} contains DEVCOV-USER-PRESERVE end marker "
                "without begin marker."
            )
        depth = 0
    if depth != 0:
        raise ValueError(
            f"{doc_name} contains unterminated DEVCOV-USER-PRESERVE block."
        )


def _preserve_block_spans(text: str) -> list[tuple[int, int, str]]:
    """Return positional spans for DEVCOV-USER-PRESERVE blocks."""
    return _block_spans(text, _USER_PRESERVE_BEGIN, _USER_PRESERVE_END)


def _preserve_blocks(text: str) -> list[str]:
    """Return preserve blocks in encounter order."""
    return [block for _, _, block in _preserve_block_spans(text)]


def _split_leading_preserve_blocks(text: str) -> tuple[list[str], str]:
    """Split contiguous top-of-document preserve blocks from text."""
    spans = _preserve_block_spans(text)
    if not spans:
        return [], text
    leading: list[str] = []
    cursor = 0
    for start, end, block in spans:
        if text[cursor:start].strip():
            break
        leading.append(block)
        cursor = end
    if not leading:
        return [], text
    remainder = text[cursor:].lstrip("\n")
    return leading, remainder


def _merge_preserve_blocks_into_replacement(
    current_block: str,
    replacement_block: str,
) -> str:
    """Merge preserve blocks from current block into replacement block."""
    current_preserves = _preserve_blocks(current_block)
    if not current_preserves:
        return replacement_block

    missing = [
        block
        for block in current_preserves
        if block.strip() and block not in replacement_block
    ]
    if not missing:
        return replacement_block

    end_index = replacement_block.rfind(BLOCK_END)
    if end_index < 0:
        return replacement_block
    prefix = replacement_block[:end_index].rstrip("\n")
    suffix = replacement_block[end_index:].lstrip("\n")
    sections = [prefix]
    sections.extend(block.strip("\n") for block in missing)
    merged_prefix = "\n\n".join(
        section for section in sections if section.strip()
    )
    return f"{merged_prefix}\n{suffix}"


def _merge_header_with_preserves(
    current_header: str, template_header: str
) -> str:
    """Render generated header while preserving user preserve blocks."""
    leading_blocks, _ = _split_leading_preserve_blocks(current_header)
    all_blocks = _preserve_blocks(current_header)

    used = 0
    remaining_blocks: list[str] = []
    for block in all_blocks:
        if used < len(leading_blocks) and block == leading_blocks[used]:
            used += 1
            continue
        remaining_blocks.append(block)

    sections: list[str] = []
    sections.extend(block.strip("\n") for block in leading_blocks)
    sections.append(template_header.strip("\n"))
    sections.extend(block.strip("\n") for block in remaining_blocks)
    return "\n\n".join(section for section in sections if section).strip("\n")


def _normalize_managed_block_body(body: str) -> str:
    """Strip begin/end markers from descriptor-managed block body text."""
    cleaned: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped in {BLOCK_BEGIN, BLOCK_END}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip("\n")


def _compose_managed_block_body(descriptor: dict[str, object]) -> str:
    """Compose managed block body from descriptor-managed block text."""
    return _normalize_managed_block_body(
        str(descriptor.get("managed_block", ""))
    )


def _release_heading_for_render(
    project_governance_state: ProjectGovernanceState,
    project_version: str,
) -> str:
    """Return the rendered changelog release heading for one repo state."""
    if project_governance_state.is_unversioned:
        return project_governance_state.unreleased_heading
    return f"## Version {project_version}"


def _render_descriptor_body(
    doc_name: str,
    descriptor: dict[str, object],
    *,
    project_version: str,
    project_governance_state: ProjectGovernanceState,
) -> list[str]:
    """Render descriptor body lines with doc-specific substitutions."""
    body_value = descriptor.get("body")
    if not isinstance(body_value, str):
        return []
    rendered = body_value
    if doc_name == "CHANGELOG.md":
        rendered = rendered.replace(
            "{{ RELEASE_HEADING }}",
            _release_heading_for_render(
                project_governance_state,
                project_version,
            ),
        )
    return [line.rstrip() for line in rendered.splitlines()]


def _render_doc(
    repo_root: Path,
    doc_name: str,
    *,
    project_version: str,
    devcovenant_version: str,
    project_governance_state: ProjectGovernanceState,
) -> str:
    """Render managed doc text from YAML descriptor."""
    descriptor = _load_managed_doc_descriptor(
        _descriptor_path(repo_root, doc_name),
        doc_name=doc_name,
    )
    header_lines = _render_generated_header(
        doc_name,
        descriptor,
        project_version=project_version,
        devcovenant_version=devcovenant_version,
        project_governance_state=project_governance_state,
    )

    block_body = _compose_managed_block_body(descriptor)
    managed_block = ""
    if block_body:
        managed_block = _render_block(BLOCK_BEGIN, BLOCK_END, block_body)

    body_lines = _render_descriptor_body(
        doc_name,
        descriptor,
        project_version=project_version,
        project_governance_state=project_governance_state,
    )

    workflow_body = str(descriptor.get("workflow_block", "")).rstrip("\n")
    workflow_block = ""
    if workflow_body:
        workflow_block = _render_block(
            WORKFLOW_BEGIN,
            WORKFLOW_END,
            workflow_body,
        )

    parts = []
    if header_lines:
        parts.append("\n".join(header_lines))
    if managed_block:
        parts.append(managed_block)
    if body_lines:
        parts.append("\n".join(body_lines))
    if workflow_block:
        parts.append(workflow_block)
    if doc_name == "AGENTS.md":
        parts.append(f"{_POLICIES_BEGIN}\n{_POLICIES_END}")
    if not parts:
        raise ValueError(
            f"Descriptor rendered no content for managed doc '{doc_name}'."
        )
    return "\n\n".join(parts).rstrip() + "\n"


def _doc_is_placeholder(text: str) -> bool:
    """Return True for empty or effectively one-line docs."""
    lines = [line for line in text.splitlines() if line.strip()]
    return len(lines) <= 1


def _extract_managed_block(text: str) -> str | None:
    """Extract first managed block from text."""
    spans = _managed_block_spans(text)
    if not spans:
        return None
    return spans[0][2]


def _replace_managed_block(current: str, template: str) -> tuple[str, bool]:
    """Replace managed blocks in current text with template block content."""
    current_blocks = _managed_block_spans(current)
    template_blocks = _managed_block_spans(template)
    if not current_blocks:
        return current, False

    template_header, _ = _rendered_header_and_block(template)
    if not template_blocks:
        updated = current
        for start, end, current_block in reversed(current_blocks):
            preserved = "\n\n".join(
                block.strip("\n") for block in _preserve_blocks(current_block)
            ).strip("\n")
            prefix = updated[:start].rstrip("\n")
            suffix = updated[end:].lstrip("\n")
            chunks: list[str] = []
            if prefix:
                chunks.append(prefix)
            if preserved:
                chunks.append(preserved)
            if suffix:
                chunks.append(suffix)
            updated = "\n\n".join(chunks)

        first_block_start = current_blocks[0][0]
        current_header = current[:first_block_start]
        merged_header = _merge_header_with_preserves(
            current_header,
            template_header,
        )
        body = updated[first_block_start:].lstrip("\n")
        rebuilt_chunks: list[str] = [merged_header.rstrip("\n")]
        if body:
            rebuilt_chunks.append(body)
        rebuilt = "\n\n".join(
            chunk for chunk in rebuilt_chunks if chunk
        ).rstrip()
        rebuilt = rebuilt + "\n" if rebuilt else ""
        return rebuilt, rebuilt != current

    replacement_count = min(len(current_blocks), len(template_blocks))
    updated = current
    changed = False
    for index in range(replacement_count - 1, -1, -1):
        start, end, current_block = current_blocks[index]
        replacement = _merge_preserve_blocks_into_replacement(
            current_block,
            template_blocks[index][2],
        )
        if updated[start:end] == replacement:
            continue
        updated = updated[:start] + replacement + updated[end:]
        changed = True

    if template_header and current_blocks:
        first_block_start = current_blocks[0][0]
        current_header = updated[:first_block_start]
        merged_header = _merge_header_with_preserves(
            current_header,
            template_header,
        )
        if merged_header != current_header.strip("\n"):
            updated = (
                merged_header.rstrip("\n")
                + "\n\n"
                + updated[first_block_start:].lstrip("\n")
            )
            changed = True
    return updated, changed


def _rendered_header_and_block(rendered: str) -> tuple[str, str]:
    """Return rendered header text and first managed block content."""
    managed_block = _extract_managed_block(rendered)
    if managed_block is None:
        return _generated_header_text(rendered), ""
    block_start = rendered.find(managed_block)
    if block_start < 0:
        return rendered.strip("\n"), managed_block
    header_text = rendered[:block_start].strip("\n")
    return header_text, managed_block


def _generated_header_text(rendered: str) -> str:
    """Extract generated doc header lines from rendered markdown text."""
    lines = rendered.replace("\r\n", "\n").splitlines()
    if not lines:
        return ""

    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return ""

    header_lines: list[str] = []
    if lines[index].lstrip().startswith("#"):
        header_lines.append(lines[index].rstrip())
        index += 1

    header_prefixes = (
        "**doc id:**",
        "**doc type:**",
        "**project version:**",
        "**project stage:**",
        "**development stance:**",
        "**versioning mode:**",
        "**project codename:**",
        "**build identity:**",
        "**last updated:**",
        "**devcovenant version:**",
    )
    while index < len(lines):
        token = lines[index].strip()
        if not token:
            index += 1
            continue
        lowered = token.lower()
        if lowered.startswith(header_prefixes):
            header_lines.append(lines[index].rstrip())
            index += 1
            continue
        break

    return "\n".join(header_lines).strip("\n")


def _merge_first_block_preserves(
    *,
    source_text: str,
    target_text: str,
    begin_marker: str,
    end_marker: str,
) -> str:
    """Merge preserve blocks from source first block into target block."""
    source_block = _first_block_text(source_text, begin_marker, end_marker)
    if source_block is None:
        return target_text
    target_block = _first_block_text(target_text, begin_marker, end_marker)
    if target_block is None:
        return target_text
    merged_block = _merge_preserve_blocks_into_replacement(
        source_block,
        target_block,
    )
    if merged_block == target_block:
        return target_text
    block_start = target_text.find(target_block)
    if block_start < 0:
        return target_text
    block_end = block_start + len(target_block)
    return target_text[:block_start] + merged_block + target_text[block_end:]


def _strip_existing_generated_headers(current: str) -> str:
    """Strip leading generated header metadata from existing doc text."""
    lines = current.replace("\r\n", "\n").splitlines()
    if not lines:
        return ""

    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1

    if index < len(lines) and lines[index].lstrip().startswith("#"):
        index += 1

    while index < len(lines):
        token = lines[index].strip().lower()
        if not token:
            index += 1
            continue
        if token.startswith("**last updated:**"):
            index += 1
            continue
        if token.startswith("**project version:**"):
            index += 1
            continue
        if token.startswith("**project stage:**"):
            index += 1
            continue
        if token.startswith("**development stance:**"):
            index += 1
            continue
        if token.startswith("**versioning mode:**"):
            index += 1
            continue
        if token.startswith("**project codename:**"):
            index += 1
            continue
        if token.startswith("**build identity:**"):
            index += 1
            continue
        if token.startswith("**devcovenant version:**"):
            index += 1
            continue
        if token.startswith("**doc id:**"):
            index += 1
            continue
        if token.startswith("**doc type:**"):
            index += 1
            continue
        break

    trimmed = "\n".join(lines[index:]).strip("\n")
    if trimmed:
        return trimmed
    return current.strip("\n")


def _inject_managed_header_and_block(
    current: str,
    rendered: str,
) -> tuple[str, bool]:
    """Inject rendered header/managed block into unmanaged existing docs."""
    header_text, managed_block = _rendered_header_and_block(rendered)
    if not managed_block:
        return rendered, rendered != current

    preserved = _strip_existing_generated_headers(current)
    leading_preserve_blocks, preserved_remainder = (
        _split_leading_preserve_blocks(preserved)
    )
    sections: list[str] = [
        *(block.strip("\n") for block in leading_preserve_blocks),
        header_text,
        managed_block,
    ]
    if preserved_remainder:
        sections.append(preserved_remainder)
    updated = "\n\n".join(part for part in sections if part).rstrip() + "\n"
    return updated, updated != current


def _managed_block_spans(text: str) -> list[tuple[int, int, str]]:
    """Return positional spans for every managed block in text."""
    return _block_spans(text, BLOCK_BEGIN, BLOCK_END)


def _first_block_text(
    text: str,
    begin_marker: str,
    end_marker: str,
) -> str | None:
    """Return first marker-delimited block text."""
    spans = _block_spans(text, begin_marker, end_marker)
    if not spans:
        return None
    return spans[0][2]


def _first_marker_start(
    text: str,
    marker: str,
    search_start: int,
) -> int:
    """Return marker start from offset, or -1 when missing."""
    match = _marker_line_regex(marker).search(text, search_start)
    if match is None:
        return -1
    return match.start()


def _next_agents_control_block_start(text: str, search_start: int) -> int:
    """Return start of next workflow or policy block after offset."""
    starts: list[int] = []

    managed_spans = _managed_block_spans(text)
    if len(managed_spans) > 1:
        starts.append(managed_spans[1][0])

    workflow_spans = _block_spans(text, WORKFLOW_BEGIN, WORKFLOW_END)
    if workflow_spans:
        starts.append(workflow_spans[0][0])

    policy_start = _first_marker_start(text, _POLICIES_BEGIN, search_start)
    if policy_start >= 0:
        starts.append(policy_start)

    if not starts:
        return len(text)
    return min(starts)


def _sync_agents_content(current: str, rendered: str) -> tuple[str, bool]:
    """Sync AGENTS managed/workflow blocks while preserving editable text."""
    managed_spans = _managed_block_spans(current)
    if not managed_spans:
        return rendered, current != rendered

    editable_start = managed_spans[0][1]
    editable_end = _next_agents_control_block_start(current, editable_start)
    editable_section = _normalize_agents_editable_section(
        current[editable_start:editable_end]
    )

    rendered_spans = _managed_block_spans(rendered)
    if not rendered_spans:
        return rendered, current != rendered

    rendered_editable_start = rendered_spans[0][1]
    rendered_editable_end = _next_agents_control_block_start(
        rendered,
        rendered_editable_start,
    )
    updated = (
        rendered[:rendered_editable_start]
        + editable_section
        + rendered[rendered_editable_end:]
    )

    updated = _merge_first_block_preserves(
        source_text=current,
        target_text=updated,
        begin_marker=BLOCK_BEGIN,
        end_marker=BLOCK_END,
    )
    updated = _merge_first_block_preserves(
        source_text=current,
        target_text=updated,
        begin_marker=WORKFLOW_BEGIN,
        end_marker=WORKFLOW_END,
    )

    current_policy_block = _first_block_text(
        current, _POLICIES_BEGIN, _POLICIES_END
    )
    template_policy_block = _first_block_text(
        updated, _POLICIES_BEGIN, _POLICIES_END
    )
    if current_policy_block and template_policy_block:
        updated = updated.replace(
            template_policy_block, current_policy_block, 1
        )

    updated_spans = _managed_block_spans(updated)
    if managed_spans and updated_spans:
        current_header = current[: managed_spans[0][0]]
        template_header = updated[: updated_spans[0][0]]
        merged_header = _merge_header_with_preserves(
            current_header,
            template_header,
        )
        if merged_header != template_header.strip("\n"):
            updated = (
                merged_header.rstrip("\n")
                + "\n\n"
                + updated[updated_spans[0][0] :].lstrip("\n")
            )

    return updated, updated != current


def _normalize_agents_editable_section(section: str) -> str:
    """Ensure editable section starts with canonical hygiene guidance."""
    normalized = str(section).replace("\r\n", "\n")
    leading_newlines = len(normalized) - len(normalized.lstrip("\n"))
    trailing_newlines = len(normalized) - len(normalized.rstrip("\n"))
    core = normalized.strip("\n")
    lines = core.splitlines() if core else []

    index = 0
    has_heading = bool(lines) and lines[0].strip() == _AGENTS_EDITABLE_HEADING
    if has_heading:
        index = 1
        while index < len(lines) and not lines[index].strip():
            index += 1
        if (
            index < len(lines)
            and lines[index].strip() == _AGENTS_EDITABLE_HYGIENE_HEADING
        ):
            index += 1
            while index < len(lines):
                token = lines[index].strip()
                if not token or lines[index].lstrip().startswith("- "):
                    index += 1
                    continue
                break

    user_lines = lines[index:] if has_heading else lines
    while user_lines and not user_lines[0].strip():
        user_lines = user_lines[1:]

    output_lines = [
        _AGENTS_EDITABLE_HEADING,
        "",
        _AGENTS_EDITABLE_HYGIENE_HEADING,
        *_AGENTS_EDITABLE_HYGIENE_LINES,
    ]
    if user_lines:
        output_lines.extend(["", *user_lines])

    section_core = "\n".join(output_lines)
    prefix = "\n" * max(leading_newlines, 2)
    suffix = "\n" * max(trailing_newlines, 2)
    return f"{prefix}{section_core}{suffix}"


def _sync_doc(
    repo_root: Path,
    doc_name: str,
    *,
    project_version: str,
    devcovenant_version: str,
    project_governance_state: ProjectGovernanceState,
) -> bool:
    """Synchronize one managed doc from descriptor content."""
    rendered = _render_doc(
        repo_root,
        doc_name,
        project_version=project_version,
        devcovenant_version=devcovenant_version,
        project_governance_state=project_governance_state,
    )
    _validate_preserve_markers(rendered, doc_name=doc_name)

    target = repo_root / doc_name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        return True

    current = target.read_text(encoding="utf-8")
    _validate_preserve_markers(current, doc_name=doc_name)
    if _doc_is_placeholder(current):
        target.write_text(rendered, encoding="utf-8")
        return True

    if doc_name == "AGENTS.md":
        updated, changed = _sync_agents_content(current, rendered)
    else:
        if _managed_block_spans(current):
            updated, changed = _replace_managed_block(current, rendered)
        else:
            updated, changed = _inject_managed_header_and_block(
                current, rendered
            )
    if not changed:
        return False

    target.write_text(updated, encoding="utf-8")
    return True


def _active_profiles(config: dict[str, object]) -> list[str]:
    """Resolve active profiles from config, always including global."""
    return profile_runtime.parse_active_profiles(config, include_global=True)


def _profile_asset_target(
    repo_root: Path, asset_payload: dict[str, object]
) -> Path | None:
    """Return normalized target path for a profile asset entry."""
    raw_path = str(asset_payload.get("path", "")).strip()
    if not raw_path:
        return None
    return _resolve_path_under_root(
        repo_root,
        raw_path,
        field_name="profile asset target",
    )


def _profile_asset_template(
    repo_root: Path,
    profile_payload: dict[str, object],
    asset_payload: dict[str, object],
) -> Path | None:
    """Return the resolved template path for a profile asset entry."""
    raw_template = str(asset_payload.get("template", "")).strip()
    profile_path = str(profile_payload.get("path", "")).strip()
    if not raw_template or not profile_path:
        return None
    profile_name = str(profile_payload.get("profile", "")).strip() or (
        profile_path
    )
    profile_root = _resolve_path_under_root(
        repo_root,
        profile_path,
        field_name=f"profile root ({profile_name})",
    )
    assets_root = (profile_root / "assets").resolve()
    return _resolve_path_under_root(
        assets_root,
        raw_template,
        field_name=f"profile asset template ({profile_name})",
    )


def _resolve_path_under_root(
    root: Path,
    raw_path: str,
    *,
    field_name: str,
) -> Path:
    """Resolve a relative path and enforce it stays under a root."""
    token = str(raw_path or "").strip()
    if not token:
        raise ValueError(f"{field_name} path cannot be empty.")
    relative_path = Path(token)
    if relative_path.is_absolute():
        raise ValueError(f"{field_name} path must be relative, got '{token}'.")
    root_path = Path(os.path.realpath(root))
    resolved = Path(os.path.realpath(root_path / relative_path))
    common_path = os.path.commonpath([str(root_path), str(resolved)])
    if common_path != str(root_path):
        raise ValueError(
            f"{field_name} path escapes '{root_path}': '{token}'."
        )
    return resolved


def _read_text_if_exists(path: Path) -> str:
    """Read UTF-8 text when file exists, otherwise return empty string."""
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _write_text_if_changed(target: Path, content: str) -> bool:
    """Write target file only when content changes."""
    current = _read_text_if_exists(target)
    if current == content:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return True


def _materialize_profile_asset(
    *,
    target: Path,
    template_path: Path | None,
) -> bool:
    """Apply one profile asset entry and return True when modified."""
    if template_path is None or not template_path.exists():
        return False

    if target.exists():
        return False

    template_text = template_path.read_text(encoding="utf-8")
    return _write_text_if_changed(target, template_text)


def _refresh_profile_assets(
    repo_root: Path,
    profile_registry: dict[str, dict],
    active_profiles: list[str],
) -> list[str]:
    """Materialize active profile assets into the target repository."""
    changed: list[str] = []
    profiles_map = _profile_registry_profiles(profile_registry)
    for profile_name in active_profiles:
        normalized = str(profile_name or "").strip().lower()
        if not normalized:
            continue
        profile_payload = profiles_map.get(normalized, {})
        raw_assets = profile_payload.get("assets")
        if not isinstance(raw_assets, list):
            continue
        for entry in raw_assets:
            if not isinstance(entry, dict):
                continue
            target = _profile_asset_target(repo_root, entry)
            if target is None:
                continue
            template_path = _profile_asset_template(
                repo_root, profile_payload, entry
            )
            if not _materialize_profile_asset(
                target=target,
                template_path=template_path,
            ):
                continue
            rel_path = _repo_relative_path(repo_root, target)
            changed.append(rel_path)
    return changed


def _repo_relative_path(repo_root: Path, target: Path) -> str:
    """Return a target path relative to repo root across symlink aliases."""
    root_path = Path(os.path.realpath(repo_root))
    target_path = Path(os.path.realpath(target))
    relative = os.path.relpath(str(target_path), str(root_path))
    return Path(relative).as_posix()


_CONFIG_AUTOGEN_PATHS: tuple[tuple[str, ...], ...] = (
    ("profiles", "generated", "devcov_core_paths"),
    ("autogen_metadata_overlays",),
    ("autogen_metadata_overrides",),
    ("profiles", "generated"),
)


def _is_autogen_config_path(path: tuple[str, ...]) -> bool:
    """Return True when a config path is owned by autogen refresh."""
    for prefix in _CONFIG_AUTOGEN_PATHS:
        if path[: len(prefix)] == prefix:
            return True
    return False


def _merge_user_config_values(
    base: dict[str, object],
    incoming: dict[str, object],
    *,
    path: tuple[str, ...] = (),
) -> None:
    """Merge user-owned config values while skipping autogen-owned paths."""
    for raw_key, incoming_value in incoming.items():
        key = str(raw_key)
        next_path = path + (key,)
        if _is_autogen_config_path(next_path):
            continue
        current_value = base.get(key)
        if isinstance(current_value, dict) and isinstance(
            incoming_value, dict
        ):
            _merge_user_config_values(
                current_value,
                incoming_value,
                path=next_path,
            )
            continue
        base[key] = copy.deepcopy(incoming_value)


def _config_template_path(repo_root: Path) -> Path:
    """Return global config template path."""
    return (
        repo_root
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )


def _load_config_template(repo_root: Path) -> dict[str, object]:
    """Load global config template payload."""
    template_payload = _read_yaml(_config_template_path(repo_root))
    if template_payload:
        return template_payload
    raise ValueError(
        "Global config template is empty: "
        f"{_config_template_path(repo_root)}"
    )


def _yaml_block(payload: dict[str, object]) -> str:
    """Dump one YAML block while preserving key order."""
    return yaml.safe_dump(payload, sort_keys=False).rstrip()


def _config_comment_header() -> str:
    """Return static comment header used by rendered config."""
    rule = "# " + ("-" * 67)
    return "\n".join(
        [
            rule,
            "# DevCovenant Config Template (generic install baseline)",
            rule,
            (
                "# This file is copied to `devcovenant/config.yaml` by "
                "`devcovenant install`."
            ),
            "#",
            "# Install always seeds a safe generic stub:",
            "# - `install.generic_config: true`",
            "# - profile set oriented to user repositories",
            "#",
            "# Typical flow:",
            "# 1) Review/edit this config.",
            "# 2) Set `install.generic_config: false`.",
            "# 3) Run `devcovenant deploy`.",
            rule,
        ]
    )


def _config_section_header(title: str) -> str:
    """Return one titled section banner for rendered config blocks."""
    rule = "# " + ("-" * 67)
    return "\n".join([rule, f"# {title}", rule])


def _render_config_yaml(payload: dict[str, object]) -> str:
    """Render config payload with stable comments and key ordering."""
    known_keys = [
        "devcov_core_include",
        "profiles",
        "paths",
        "doc_assets",
        "install",
        "engine",
        "clean",
        "governance_and_test",
        "pre_commit",
        "policy_state",
        "ignore",
        "gitignore",
        "autogen_metadata_overlays",
        "user_metadata_overlays",
        "autogen_metadata_overrides",
        "user_metadata_overrides",
    ]
    comments = {
        "scope": _config_section_header("Scope control"),
        "profiles": _config_section_header("Profile activation"),
        "paths": _config_section_header("Canonical paths"),
        "doc_assets": _config_section_header("Managed document controls"),
        "install": _config_section_header("Install/deploy safety"),
        "engine": _config_section_header("Engine behavior"),
        "clean": _config_section_header("Cleanup targets"),
        "governance_and_test": _config_section_header(
            "Governance-and-test generation"
        ),
        "pre_commit": _config_section_header("Pre-commit generation"),
        "policy": _config_section_header(
            "Policy activation and customization"
        ),
        "ignore": _config_section_header("Global ignore patterns"),
        "gitignore": _config_section_header("Gitignore generation"),
        "metadata": _config_section_header(
            "Metadata layers (resolution order matters)"
        ),
    }

    blocks = [
        _config_comment_header(),
        comments["scope"],
        "\n".join(
            [
                (
                    "# Whether policy checks include DevCovenant's own "
                    "implementation files."
                ),
                "# - false: user-repo mode (ignore core internals)",
                ("# - true: DevCovenant-repo mode " "(enforce the full tree)"),
            ]
        ),
        _yaml_block(
            {
                "devcov_core_include": bool(
                    payload.get("devcov_core_include", False)
                ),
            }
        ),
        comments["profiles"],
        "# Ordered profile list. `global` should stay first.",
        (
            "# Profiles contribute suffixes, assets, metadata overlays, "
            "and cleanup overlays."
        ),
        "# Generated diagnostics include profile-level core path mappings.",
        (
            "# Profiles do not activate policies. "
            "Policy activation is `policy_state` for normal toggles."
        ),
        (
            "# `severity: critical` policies remain enforced even when "
            "toggled false in `policy_state`."
        ),
        _yaml_block({"profiles": payload.get("profiles", {})}),
        comments["paths"],
        "# Runtime policy source parsed by the engine.",
        "# Generated local policy registry (hashes + diagnostics).",
        _yaml_block({"paths": payload.get("paths", {})}),
        comments["doc_assets"],
        "\n".join(
            [
                (
                    "# Documents that refresh may fully materialize from "
                    "descriptor templates."
                ),
                "# Empty list means runtime backfills defaults.",
                (
                    "# Documents in `user` are excluded from full "
                    "template materialization."
                ),
                (
                    "# Managed block refresh still applies when markers are "
                    "present."
                ),
            ]
        ),
        _yaml_block({"doc_assets": payload.get("doc_assets", {})}),
        comments["install"],
        (
            "# True after install. Deploy is blocked until user reviews "
            "config."
        ),
        ("# Set this to false after review to allow `devcovenant deploy`."),
        _yaml_block({"install": payload.get("install", {})}),
        comments["engine"],
        "# Violations at or above fail_threshold fail the run.",
        "# Allowed levels: info, warning, error, critical.",
        "# auto_fix_enabled controls gate-managed policy auto-fix behavior.",
        "# `check` stays read-only.",
        "# logs_keep_last controls run-log retention (`0` keeps all runs).",
        (
            "# pycache_prefix_enabled/pycache_prefix route DevCovenant-"
            "managed Python bytecode caches away from the repo tree "
            "(empty prefix = auto temp path)."
        ),
        "# file_suffixes and ignore_dirs define broad scan boundaries.",
        _yaml_block({"engine": payload.get("engine", {})}),
        comments["clean"],
        (
            "# `clean.overlays` add repository-specific cleanup targets on "
            "top of active profile clean_overlays."
        ),
        (
            "# `clean.overrides` replace one resolved cleanup key entirely "
            "when repository ownership must take over."
        ),
        (
            "# Protected entries are additive safety fences; runtime also "
            "always protects .git, .venv, devcovenant/registry/registry.yaml, "
            "devcovenant/registry/README.md, and devcovenant/logs/README.md."
        ),
        _yaml_block({"clean": payload.get("clean", {})}),
        comments["governance_and_test"],
        "# `overlays` are merged into generated governance workflow.",
        "# `overrides` replace generated payload when non-empty.",
        _yaml_block(
            {
                "governance_and_test": payload.get(
                    "governance_and_test",
                    {},
                )
            }
        ),
        comments["pre_commit"],
        "# `overlays` are merged into generated pre-commit config.",
        "# `overrides` replace generated payload when non-empty.",
        _yaml_block({"pre_commit": payload.get("pre_commit", {})}),
        comments["policy"],
        ("# Canonical policy activation map: {policy-id: true|false}."),
        (
            "# Critical-severity policies remain enforced even when set "
            "to false here."
        ),
        _yaml_block({"policy_state": payload.get("policy_state", {})}),
        comments["ignore"],
        "# Extra glob patterns excluded from CheckContext file collections.",
        _yaml_block({"ignore": payload.get("ignore", {})}),
        comments["gitignore"],
        "# Extra entries appended to generated `.gitignore`.",
        "# Entries are applied before the preserved user block.",
        "# `overrides` replaces generated base/profile/os fragments entirely.",
        _yaml_block({"gitignore": payload.get("gitignore", {})}),
        comments["metadata"],
        "# Auto-generated metadata overlays written by refresh.",
        "# Merge semantics: list append + dedupe, scalar replace.",
        _yaml_block(
            {
                "autogen_metadata_overlays": payload.get(
                    "autogen_metadata_overlays", {}
                )
            }
        ),
        "# User-owned overlays applied after autogen overlays.",
        "# Merge semantics: list append + dedupe, scalar replace.",
        _yaml_block(
            {
                "user_metadata_overlays": payload.get(
                    "user_metadata_overlays", {}
                )
            }
        ),
        "# Auto-generated metadata overrides written by refresh.",
        "# Override semantics: full key replacement.",
        "# Do not hand-edit unless you intentionally own this layer.",
        _yaml_block(
            {
                "autogen_metadata_overrides": payload.get(
                    "autogen_metadata_overrides", {}
                )
            }
        ),
        "# User-owned overrides applied last (highest precedence).",
        "# Override semantics: full key replacement.",
        "# Shape: {policy-id: {metadata_key: value-or-list}}",
        _yaml_block(
            {
                "user_metadata_overrides": payload.get(
                    "user_metadata_overrides", {}
                )
            }
        ),
    ]

    extras = {
        key: value for key, value in payload.items() if key not in known_keys
    }
    if extras:
        rule = "# " + ("-" * 67)
        blocks.extend(
            [
                rule,
                "# Extra user-defined keys (preserved)",
                rule,
                _yaml_block(extras),
            ]
        )
    return "\n\n".join(blocks).rstrip() + "\n"


def _refresh_config_generated(
    repo_root: Path,
    config_path: Path,
    config: dict[str, object],
    user_config: dict[str, object],
    registry: dict[str, dict],
    active_profiles: list[str],
) -> tuple[dict[str, object], bool]:
    """Refresh config with autogen values while preserving user-owned keys."""
    template = _load_config_template(repo_root)
    merged = copy.deepcopy(template)
    _merge_user_config_values(merged, config)
    _apply_profile_aware_engine_defaults(merged, user_config, active_profiles)

    profile_suffixes = profile_runtime.resolve_profile_suffixes(
        registry, active_profiles
    )
    suffixes = sorted({str(item) for item in profile_suffixes if str(item)})

    profiles_block = merged.get("profiles")
    if not isinstance(profiles_block, dict):
        profiles_block = {}
    generated = profiles_block.get("generated")
    if not isinstance(generated, dict):
        generated = {}
    profiles_block["active"] = list(active_profiles)
    generated["file_suffixes"] = suffixes
    generated["devcov_core_paths"] = _default_core_paths(repo_root)
    profiles_block["generated"] = generated
    merged["profiles"] = profiles_block

    merged.pop("devcov_core_paths", None)
    merged.pop("version", None)
    merged.pop("docs", None)
    merged["autogen_metadata_overlays"] = _config_autogen_metadata_overlays(
        repo_root, active_profiles
    )
    merged["autogen_metadata_overrides"] = _config_autogen_metadata_overrides()
    merged["policy_state"] = _materialize_policy_state_map(
        repo_root,
        metadata_runtime.normalize_policy_state(merged.get("policy_state")),
    )

    doc_assets = merged.get("doc_assets")
    if not isinstance(doc_assets, dict):
        doc_assets = {}
    raw_autogen = doc_assets.get("autogen")
    if isinstance(raw_autogen, list):
        autogen = [_normalize_doc_name(item) for item in raw_autogen]
        doc_assets["autogen"] = [doc for doc in autogen if doc]
    else:
        doc_assets["autogen"] = []

    raw_user = doc_assets.get("user")
    if isinstance(raw_user, list):
        user_docs = [_normalize_doc_name(item) for item in raw_user]
        doc_assets["user"] = [doc for doc in user_docs if doc]
    else:
        doc_assets["user"] = []
    merged["doc_assets"] = doc_assets

    rendered = _render_config_yaml(merged)
    current = _read_text_if_exists(config_path)
    if current == rendered:
        return merged, False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(rendered, encoding="utf-8")
    return merged, True


def _apply_profile_aware_engine_defaults(
    merged: dict[str, object],
    user_config: dict[str, object],
    active_profiles: list[str],
) -> None:
    """Apply profile-aware config defaults when the user left keys unset."""
    user_engine = user_config.get("engine")
    user_engine_map = user_engine if isinstance(user_engine, dict) else {}

    engine_block = merged.get("engine")
    if not isinstance(engine_block, dict):
        engine_block = {}
        merged["engine"] = engine_block

    if "devcovrepo" in active_profiles:
        if "auto_fix_enabled" not in user_engine_map:
            engine_block["auto_fix_enabled"] = True
        if "pycache_prefix_enabled" not in user_engine_map:
            engine_block["pycache_prefix_enabled"] = True


def _materialize_policy_state_map(
    repo_root: Path, current_state: Dict[str, bool]
) -> Dict[str, bool]:
    """Return full alphabetical policy_state map from the tracked registry."""
    registry_path = policy_registry_path(repo_root)
    payload = _read_yaml(registry_path)
    raw_policies = payload.get("policies")
    if not isinstance(raw_policies, dict):
        raise ValueError(
            "Policy registry payload is invalid; expected `policies` mapping "
            f"in {registry_path}."
        )

    resolved: Dict[str, bool] = {}
    for raw_policy_id in sorted(raw_policies):
        policy_id = str(raw_policy_id or "").strip()
        if not policy_id:
            continue
        if policy_id in current_state:
            resolved[policy_id] = current_state[policy_id]
            continue
        entry = raw_policies.get(raw_policy_id)
        default_enabled = True
        if isinstance(entry, dict):
            raw_enabled = entry.get("enabled")
            if isinstance(raw_enabled, bool):
                default_enabled = raw_enabled
            elif raw_enabled is not None:
                token = str(raw_enabled).strip().lower()
                if token in {"true", "1", "yes", "y", "on"}:
                    default_enabled = True
                elif token in {"false", "0", "no", "n", "off"}:
                    default_enabled = False
        resolved[policy_id] = default_enabled
    return resolved


def _normalize_string_list(raw_value: object) -> list[str]:
    """Normalize raw config values into a clean string list."""
    if isinstance(raw_value, str):
        items = [raw_value]
    elif isinstance(raw_value, list):
        items = raw_value
    else:
        return []

    cleaned: list[str] = []
    for raw_entry in items:
        token = str(raw_entry or "").strip()
        if token:
            cleaned.append(token)
    return cleaned


def _default_core_paths(repo_root: Path) -> list[str]:
    """Load canonical devcov core paths from the config asset."""
    asset_path = (
        repo_root
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )
    payload = _read_yaml(asset_path)
    profiles = payload.get("profiles", {}) if isinstance(payload, dict) else {}
    if isinstance(profiles, dict):
        generated = profiles.get("generated", {})
    else:
        generated = {}
    if isinstance(generated, dict):
        configured = _normalize_string_list(generated.get("devcov_core_paths"))
    else:
        configured = []
    if configured:
        return configured
    return [
        "devcovenant/core",
        "devcovenant/builtin",
        "devcovenant/__init__.py",
        "devcovenant/__main__.py",
        "devcovenant/cli.py",
        "devcovenant/check.py",
        "devcovenant/clean.py",
        "devcovenant/gate.py",
        "devcovenant/test.py",
        "devcovenant/install.py",
        "devcovenant/deploy.py",
        "devcovenant/upgrade.py",
        "devcovenant/refresh.py",
        "devcovenant/uninstall.py",
        "devcovenant/undeploy.py",
        "devcovenant/update_lock.py",
        "devcovenant/registry",
    ]


def _config_autogen_metadata_overlays(
    repo_root: Path, active_profiles: list[str]
) -> Dict[str, Dict[str, object]]:
    """Build deterministic profile-derived autogen metadata overlays."""
    overlays = metadata_runtime.collect_profile_overlays(
        repo_root, active_profiles
    )
    normalized: Dict[str, Dict[str, object]] = {}
    for policy_id in sorted(overlays.keys()):
        policy_map = overlays[policy_id]
        key_map: Dict[str, object] = {}
        for key_name in sorted(policy_map.keys()):
            values, merge_values = policy_map[key_name]
            if merge_values:
                key_map[key_name] = list(values)
                continue
            if _is_scalar_path_override_key(key_name):
                key_map[key_name] = values[0] if values else ""
                continue
            key_map[key_name] = list(values)
        if key_map:
            normalized[policy_id] = key_map
    return normalized


def _config_autogen_metadata_overrides() -> Dict[str, Dict[str, object]]:
    """Return generated metadata overrides owned by refresh runtime."""
    return {}


def _is_scalar_path_override_key(key_name: str) -> bool:
    """Return True when override key represents a singular path value."""
    token = str(key_name or "").strip().lower()
    if not token:
        return False
    if token.endswith(("_files", "_paths", "_dirs", "_roots")):
        return False
    return token.endswith(("_file", "_path", "_dir", "_root"))


def _profile_registry_profiles(
    registry: dict[str, dict],
) -> dict[str, dict[str, object]]:
    """Return normalized profile map from a profile registry payload."""
    raw_profiles = registry.get("profiles")
    if not isinstance(raw_profiles, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for name, payload in raw_profiles.items():
        if not isinstance(payload, dict):
            continue
        normalized[str(name).strip().lower()] = payload
    return normalized


def _merge_mapping_fragment(
    base_payload: dict[str, object],
    fragment: dict[str, object],
) -> dict[str, object]:
    """Merge mapping fragments recursively with append-dedupe lists."""
    merged = copy.deepcopy(base_payload)
    for metadata_key, incoming_value in fragment.items():
        existing = merged.get(metadata_key)
        if isinstance(existing, dict) and isinstance(incoming_value, dict):
            merged[metadata_key] = _merge_mapping_fragment(
                existing,
                incoming_value,
            )
            continue
        if isinstance(existing, list) and isinstance(incoming_value, list):
            combined = copy.deepcopy(existing)
            for item in incoming_value:
                candidate = copy.deepcopy(item)
                if candidate not in combined:
                    combined.append(candidate)
            merged[metadata_key] = combined
            continue
        merged[metadata_key] = copy.deepcopy(incoming_value)
    return merged


def _load_global_governance_template(
    repo_root: Path,
    profiles_map: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Load governance workflow template from the global profile."""
    global_profile = profiles_map.get("global", {})
    template_name = str(global_profile.get("governance_template", "")).strip()
    if not template_name:
        raise ValueError("Global profile is missing governance_template.")

    profile_path = str(global_profile.get("path", "")).strip()
    if not profile_path:
        raise ValueError("Global profile path is unavailable.")
    profile_root = _resolve_path_under_root(
        repo_root,
        profile_path,
        field_name="global profile root",
    )

    template_path = _resolve_path_under_root(
        profile_root / "assets",
        template_name,
        field_name="global governance template",
    )
    payload = _read_yaml(template_path)
    if not isinstance(payload, dict):
        raise ValueError(
            "Global governance template must contain a YAML mapping."
        )
    return payload


def _config_governance_adjustments(
    config: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Resolve config overlays/overrides for governance workflow generation."""
    governance_block = config.get("governance_and_test")
    if not isinstance(governance_block, dict):
        return {}, {}
    overlays = governance_block.get("overlays")
    if not isinstance(overlays, dict):
        overlays = {}
    overrides = governance_block.get("overrides")
    if not isinstance(overrides, dict):
        overrides = {}
    return overlays, overrides


def _normalize_governance_trigger_key(
    payload: dict[str, object],
) -> dict[str, object]:
    """Normalize workflow trigger key to literal ``on``."""
    normalized = copy.deepcopy(payload)
    if "on" in normalized:
        normalized.pop(True, None)
    elif True in normalized:
        normalized["on"] = normalized.pop(True)

    if "on" not in normalized:
        return normalized

    ordered: dict[str, object] = {}
    if "name" in normalized:
        ordered["name"] = normalized["name"]
    ordered["on"] = normalized["on"]
    for key, value in normalized.items():
        if key in {"name", "on"}:
            continue
        ordered[key] = value
    return ordered


def _render_governance_workflow_yaml(payload: dict[str, object]) -> str:
    """Render governance workflow YAML in canonical GitHub syntax."""
    rendered = yaml.safe_dump(payload, sort_keys=False)
    lines = rendered.splitlines()
    normalized_lines: list[str] = []
    in_on_block = False
    null_event_pattern = re.compile(r"^(\s+[A-Za-z0-9_-]+): null$")

    for line in lines:
        if line in {"'on':", '"on":'}:
            normalized_lines.append("on:")
            in_on_block = True
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped and stripped != "on:":
            in_on_block = False

        if in_on_block:
            null_event_match = null_event_pattern.match(line)
            if null_event_match:
                normalized_lines.append(f"{null_event_match.group(1)}:")
                continue

        normalized_lines.append(line)

    normalized = "\n".join(normalized_lines)
    if rendered.endswith("\n"):
        normalized += "\n"
    return normalized


def _refresh_governance_and_test(
    repo_root: Path,
    config: dict[str, object],
    profile_registry: dict[str, dict],
    active_profiles: list[str],
) -> bool:
    """Regenerate governance-and-test workflow from template and fragments."""
    profiles_map = _profile_registry_profiles(profile_registry)
    payload = _load_global_governance_template(repo_root, profiles_map)

    for profile_name in active_profiles:
        normalized = str(profile_name or "").strip().lower()
        if not normalized or normalized == "global":
            continue
        profile_payload = profiles_map.get(normalized, {})
        fragment = profile_payload.get("governance_and_test")
        if isinstance(fragment, dict):
            payload = _merge_mapping_fragment(payload, fragment)

    overlays, overrides = _config_governance_adjustments(config)
    if overlays:
        payload = _merge_mapping_fragment(payload, overlays)
    if overrides:
        payload = copy.deepcopy(overrides)
    payload = _normalize_governance_trigger_key(payload)

    target_path = (
        repo_root / ".github" / "workflows" / "governance-and-test.yml"
    )
    rendered = _render_governance_workflow_yaml(payload)
    changed = True
    if target_path.exists():
        changed = target_path.read_text(encoding="utf-8") != rendered
    if changed:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered, encoding="utf-8")
    return changed


def _merge_repo_hooks(
    base_hooks: list[object], incoming_hooks: list[object]
) -> list[object]:
    """Merge pre-commit hook lists by hook id while preserving order."""
    merged = copy.deepcopy(base_hooks)
    hook_indexes: dict[str, int] = {}
    for index, hook in enumerate(merged):
        if not isinstance(hook, dict):
            continue
        hook_id = str(hook.get("id", "")).strip()
        if hook_id and hook_id not in hook_indexes:
            hook_indexes[hook_id] = index

    for hook in incoming_hooks:
        if not isinstance(hook, dict):
            merged.append(copy.deepcopy(hook))
            continue
        hook_id = str(hook.get("id", "")).strip()
        if not hook_id or hook_id not in hook_indexes:
            merged.append(copy.deepcopy(hook))
            if hook_id:
                hook_indexes[hook_id] = len(merged) - 1
            continue
        existing = merged[hook_indexes[hook_id]]
        if isinstance(existing, dict):
            updated = copy.deepcopy(existing)
            updated.update(copy.deepcopy(hook))
            merged[hook_indexes[hook_id]] = updated
            continue
        merged[hook_indexes[hook_id]] = copy.deepcopy(hook)
    return merged


def _merge_repo_entries(
    base_repos: list[object], incoming_repos: list[object]
) -> list[object]:
    """Merge pre-commit repo entries by repo identifier."""
    merged = copy.deepcopy(base_repos)
    repo_indexes: dict[str, int] = {}
    for index, repo_entry in enumerate(merged):
        if not isinstance(repo_entry, dict):
            continue
        repo_name = str(repo_entry.get("repo", "")).strip()
        if repo_name and repo_name not in repo_indexes:
            repo_indexes[repo_name] = index

    for repo_entry in incoming_repos:
        if not isinstance(repo_entry, dict):
            merged.append(copy.deepcopy(repo_entry))
            continue
        repo_name = str(repo_entry.get("repo", "")).strip()
        if not repo_name or repo_name not in repo_indexes:
            merged.append(copy.deepcopy(repo_entry))
            if repo_name:
                repo_indexes[repo_name] = len(merged) - 1
            continue

        existing = merged[repo_indexes[repo_name]]
        if not isinstance(existing, dict):
            merged[repo_indexes[repo_name]] = copy.deepcopy(repo_entry)
            continue

        updated = copy.deepcopy(existing)
        for metadata_key, incoming_value in repo_entry.items():
            if metadata_key == "hooks" and isinstance(incoming_value, list):
                current_hooks = updated.get("hooks")
                if isinstance(current_hooks, list):
                    updated["hooks"] = _merge_repo_hooks(
                        current_hooks, incoming_value
                    )
                else:
                    updated["hooks"] = copy.deepcopy(incoming_value)
                continue
            updated[metadata_key] = copy.deepcopy(incoming_value)
        merged[repo_indexes[repo_name]] = updated
    return merged


def _merge_pre_commit_fragment(
    base_payload: dict[str, object], fragment: dict[str, object]
) -> dict[str, object]:
    """Merge one pre-commit fragment into a base payload."""
    merged = copy.deepcopy(base_payload)
    for metadata_key, incoming_value in fragment.items():
        if metadata_key == "repos" and isinstance(incoming_value, list):
            current_repos = merged.get("repos")
            if isinstance(current_repos, list):
                merged["repos"] = _merge_repo_entries(
                    current_repos, incoming_value
                )
            else:
                merged["repos"] = copy.deepcopy(incoming_value)
            continue
        existing = merged.get(metadata_key)
        if isinstance(existing, dict) and isinstance(incoming_value, dict):
            updated = copy.deepcopy(existing)
            updated.update(copy.deepcopy(incoming_value))
            merged[metadata_key] = updated
            continue
        merged[metadata_key] = copy.deepcopy(incoming_value)
    return merged


def _normalize_ignore_dir(raw: object) -> str:
    """Normalize ignore directory values for pre-commit exclude generation."""
    token = str(raw or "").strip().strip("/")
    if not token:
        return ""
    return token


def _build_pre_commit_exclude(ignore_dirs: list[str]) -> str:
    """Build a shared pre-commit exclude regex from ignore directories."""
    escaped = [re.escape(entry) for entry in ignore_dirs if entry]
    if not escaped:
        return ""
    body = "\n".join(
        [
            "(?x)",
            "(^|/)",
            "(",
            "  " + "\n  | ".join(escaped),
            ")",
            "(/|$)",
        ]
    )
    return body


def _resolved_pre_commit_hooks(payload: dict[str, object]) -> list[str]:
    """Return stable list of resolved hook identifiers."""
    hooks: list[str] = []
    repos_value = payload.get("repos")
    if not isinstance(repos_value, list):
        return hooks
    for repo_entry in repos_value:
        if not isinstance(repo_entry, dict):
            continue
        repo_name = str(repo_entry.get("repo", "")).strip()
        if not repo_name:
            continue
        hooks_value = repo_entry.get("hooks")
        if not isinstance(hooks_value, list):
            continue
        for hook_entry in hooks_value:
            if not isinstance(hook_entry, dict):
                continue
            hook_id = str(hook_entry.get("id", "")).strip()
            if not hook_id:
                continue
            hooks.append(f"{repo_name}:{hook_id}")
    return hooks


_EXCLUDE_PLACEHOLDER = "__DEVCOVENANT_EXCLUDE_PLACEHOLDER__"


def _render_pre_commit_yaml(payload: dict[str, object]) -> str:
    """Render pre-commit payload while preserving readable exclude blocks."""
    exclude_value = payload.get("exclude")
    if not isinstance(exclude_value, str) or "\n" not in exclude_value:
        return yaml.safe_dump(payload, sort_keys=False)

    serialized = copy.deepcopy(payload)
    serialized["exclude"] = _EXCLUDE_PLACEHOLDER
    rendered = yaml.safe_dump(serialized, sort_keys=False)
    literal_block = "\n".join(
        f"  {line}" for line in exclude_value.splitlines()
    )
    marker = f"exclude: {_EXCLUDE_PLACEHOLDER}\n"
    replacement = "exclude: |-\n" + literal_block + "\n"
    return rendered.replace(marker, replacement, 1)


def _record_pre_commit_manifest(
    repo_root: Path,
    active_profiles: list[str],
    pre_commit_payload: dict[str, object],
) -> None:
    """Persist resolved pre-commit metadata into tracked inventory."""
    manifest = manifest_module.ensure_manifest(repo_root)
    if not isinstance(manifest, dict):
        return

    profiles_block = manifest.get("profiles")
    if not isinstance(profiles_block, dict):
        profiles_block = {}

    resolved_hooks = _resolved_pre_commit_hooks(pre_commit_payload)
    changed = False
    if profiles_block.get("active") != active_profiles:
        profiles_block["active"] = list(active_profiles)
        changed = True
    if profiles_block.get("resolved_pre_commit_hooks") != resolved_hooks:
        profiles_block["resolved_pre_commit_hooks"] = resolved_hooks
        changed = True
    if not changed:
        return

    manifest["profiles"] = profiles_block
    manifest_module.write_manifest(repo_root, manifest)


def _ensure_devcovenant_hook_last(payload: dict[str, object]) -> None:
    """Move the local devcovenant hook to the end of pre-commit repos."""
    repos_value = payload.get("repos")
    if not isinstance(repos_value, list):
        return

    target_index = -1
    for index, repo_entry in enumerate(repos_value):
        if not isinstance(repo_entry, dict):
            continue
        if str(repo_entry.get("repo", "")).strip() != "local":
            continue
        hooks_value = repo_entry.get("hooks")
        if not isinstance(hooks_value, list):
            continue
        has_devcovenant = any(
            isinstance(hook_entry, dict)
            and str(hook_entry.get("id", "")).strip() == "devcovenant"
            for hook_entry in hooks_value
        )
        if has_devcovenant:
            target_index = index

    if target_index < 0 or target_index == len(repos_value) - 1:
        return

    target_entry = repos_value.pop(target_index)
    repos_value.append(target_entry)
    payload["repos"] = repos_value


def _find_devcovenant_hook(
    payload: dict[str, object],
) -> dict[str, object] | None:
    """Return a copy of the devcovenant local hook when present."""
    repos_value = payload.get("repos")
    if not isinstance(repos_value, list):
        return None
    for repo_entry in repos_value:
        if not isinstance(repo_entry, dict):
            continue
        if str(repo_entry.get("repo", "")).strip() != "local":
            continue
        hooks_value = repo_entry.get("hooks")
        if not isinstance(hooks_value, list):
            continue
        for hook_entry in hooks_value:
            if not isinstance(hook_entry, dict):
                continue
            if str(hook_entry.get("id", "")).strip() == "devcovenant":
                return copy.deepcopy(hook_entry)
    return None


def _ensure_devcovenant_hook_present(
    payload: dict[str, object],
    fallback_hook: dict[str, object] | None,
) -> None:
    """Ensure generated pre-commit payload contains the devcovenant hook."""
    if not fallback_hook:
        return
    repos_value = payload.get("repos")
    if not isinstance(repos_value, list):
        repos_value = []

    for index, repo_entry in enumerate(repos_value):
        if not isinstance(repo_entry, dict):
            continue
        if str(repo_entry.get("repo", "")).strip() != "local":
            continue
        hooks_value = repo_entry.get("hooks")
        if not isinstance(hooks_value, list):
            hooks_value = []
            repo_entry["hooks"] = hooks_value
        has_devcovenant = any(
            isinstance(hook_entry, dict)
            and str(hook_entry.get("id", "")).strip() == "devcovenant"
            for hook_entry in hooks_value
        )
        if not has_devcovenant:
            hooks_value.append(copy.deepcopy(fallback_hook))
        payload["repos"] = repos_value
        return

    repos_value.append(
        {
            "repo": "local",
            "hooks": [copy.deepcopy(fallback_hook)],
        }
    )
    payload["repos"] = repos_value


def _refresh_pre_commit_config(
    repo_root: Path,
    config: dict[str, object],
    profile_registry: dict[str, dict],
    active_profiles: list[str],
) -> bool:
    """Regenerate .pre-commit-config.yaml from fragments and overrides."""
    profiles_map = _profile_registry_profiles(profile_registry)
    payload: dict[str, object] = {}

    global_fragment = profiles_map.get("global", {}).get("pre_commit")
    if isinstance(global_fragment, dict):
        payload = _merge_pre_commit_fragment(payload, global_fragment)

    for profile_name in active_profiles:
        normalized = str(profile_name or "").strip().lower()
        if not normalized or normalized == "global":
            continue
        fragment = profiles_map.get(normalized, {}).get("pre_commit")
        if not isinstance(fragment, dict):
            continue
        payload = _merge_pre_commit_fragment(payload, fragment)

    ignore_dirs: list[str] = []
    profile_ignores = profile_runtime.resolve_profile_ignore_dirs(
        profile_registry, active_profiles
    )
    for entry in profile_ignores:
        token = _normalize_ignore_dir(entry)
        if token and token not in ignore_dirs:
            ignore_dirs.append(token)

    engine_block = config.get("engine")
    if isinstance(engine_block, dict):
        raw_engine_ignores = engine_block.get("ignore_dirs")
        if isinstance(raw_engine_ignores, list):
            for entry in raw_engine_ignores:
                token = _normalize_ignore_dir(entry)
                if token and token not in ignore_dirs:
                    ignore_dirs.append(token)

    if ignore_dirs:
        payload["exclude"] = _build_pre_commit_exclude(ignore_dirs)

    devcovenant_hook = _find_devcovenant_hook(payload)

    pre_commit_block = config.get("pre_commit")
    if isinstance(pre_commit_block, dict):
        overlays = pre_commit_block.get("overlays")
        if isinstance(overlays, dict):
            payload = _merge_pre_commit_fragment(payload, overlays)
        overrides = pre_commit_block.get("overrides")
        if isinstance(overrides, dict) and overrides:
            payload = copy.deepcopy(overrides)

    if "repos" not in payload or not isinstance(payload.get("repos"), list):
        payload["repos"] = []

    _ensure_devcovenant_hook_present(payload, devcovenant_hook)
    _ensure_devcovenant_hook_last(payload)

    target_path = repo_root / ".pre-commit-config.yaml"
    rendered = _render_pre_commit_yaml(payload)
    changed = True
    if target_path.exists():
        changed = target_path.read_text(encoding="utf-8") != rendered
    if changed:
        target_path.write_text(rendered, encoding="utf-8")

    _record_pre_commit_manifest(repo_root, active_profiles, payload)
    return changed


def _read_text(path: Path) -> str:
    """Read UTF-8 text from a path, returning empty string when missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _normalize_gitignore_entries(raw_value: object) -> list[str]:
    """Normalize configured gitignore fragment entries."""
    if not isinstance(raw_value, list):
        return []
    entries: list[str] = []
    for raw_entry in raw_value:
        token = str(raw_entry or "").strip()
        if not token:
            continue
        if token in entries:
            continue
        entries.append(token)
    return entries


def _profile_gitignore_entries(
    profile_payload: dict[str, object],
) -> list[str]:
    """Resolve one profile's gitignore entries from manifest metadata."""
    explicit_entries = _normalize_gitignore_entries(
        profile_payload.get("gitignore_fragments")
    )
    if explicit_entries:
        return explicit_entries
    return _normalize_gitignore_entries(profile_payload.get("ignore_dirs"))


def _config_gitignore_adjustments(
    config: dict[str, object],
) -> tuple[list[str], list[str]]:
    """Resolve user-configured gitignore overlays and overrides."""
    gitignore_block = config.get("gitignore")
    if not isinstance(gitignore_block, dict):
        return [], []
    overlays = _normalize_gitignore_entries(gitignore_block.get("overlays"))
    overrides = _normalize_gitignore_entries(gitignore_block.get("overrides"))
    return overlays, overrides


def _load_global_gitignore_template(
    repo_root: Path,
    profile_registry: dict[str, dict],
) -> tuple[list[str], list[str]]:
    """Load global gitignore base/os entries from configured YAML template."""
    profiles_map = _profile_registry_profiles(profile_registry)
    global_profile = profiles_map.get("global", {})
    template_name = str(global_profile.get("gitignore_template", "")).strip()
    if not template_name:
        raise ValueError("Global profile is missing gitignore_template.")
    profile_path = str(global_profile.get("path", "")).strip()
    if not profile_path:
        raise ValueError("Global profile path is missing in registry.")
    profile_root = _resolve_path_under_root(
        repo_root,
        profile_path,
        field_name="global profile root",
    )
    template_path = _resolve_path_under_root(
        profile_root / "assets",
        template_name,
        field_name="global gitignore template",
    )
    template_payload = _read_yaml(template_path)
    base_entries = _normalize_gitignore_entries(
        template_payload.get("base_fragments")
    )
    os_entries = _normalize_gitignore_entries(
        template_payload.get("os_fragments")
    )
    return base_entries, os_entries


def _extract_user_gitignore_entries(existing_text: str) -> list[str]:
    """Extract preserved user entries from an existing .gitignore body."""
    begin_index = existing_text.find(USER_GITIGNORE_BEGIN)
    end_index = existing_text.find(USER_GITIGNORE_END)
    if begin_index < 0 or end_index < 0 or end_index < begin_index:
        return [line.rstrip() for line in existing_text.splitlines() if line]

    body_start = begin_index + len(USER_GITIGNORE_BEGIN)
    body_text = existing_text[body_start:end_index]
    user_lines = [line.rstrip() for line in body_text.splitlines()]
    while user_lines and not user_lines[0].strip():
        user_lines.pop(0)
    while user_lines and not user_lines[-1].strip():
        user_lines.pop()
    return user_lines


def _render_gitignore(
    base_entries: list[str],
    os_entries: list[str],
    profile_sections: list[tuple[str, list[str]]],
    config_overlays: list[str],
    config_overrides: list[str],
    user_entries: list[str],
) -> str:
    """Render full .gitignore with generated and preserved user sections."""
    sections: list[str] = []
    if config_overrides:
        sections.append(
            "\n".join(["# Config gitignore overrides", *config_overrides])
        )
    else:
        if base_entries:
            sections.append(
                "\n".join(["# DevCovenant base ignores", *base_entries])
            )

        for profile_name, fragment_entries in profile_sections:
            if not fragment_entries:
                continue
            section_header = f"# Profile: {profile_name}"
            section_body = "\n".join(fragment_entries)
            sections.append("\n".join([section_header, section_body]))

        if os_entries:
            sections.append(
                "\n".join(["# OS-specific ignores (DevCovenant)", *os_entries])
            )

        if config_overlays:
            sections.append(
                "\n".join(["# Config gitignore overlays", *config_overlays])
            )

    user_block_lines = [USER_GITIGNORE_BEGIN, ""]
    user_block_lines.extend(user_entries)
    user_block_lines.extend(["", USER_GITIGNORE_END])
    sections.append("\n".join(user_block_lines))

    return (
        "\n\n".join(section for section in sections if section).rstrip() + "\n"
    )


def _refresh_gitignore(
    repo_root: Path,
    config: dict[str, object],
    profile_registry: dict[str, dict],
    active_profiles: list[str],
) -> bool:
    """Regenerate .gitignore from template, profiles, and config metadata."""
    profiles_map = _profile_registry_profiles(profile_registry)
    profile_sections: list[tuple[str, list[str]]] = []
    for profile_name in active_profiles:
        normalized_name = str(profile_name or "").strip().lower()
        if not normalized_name:
            continue
        profile_payload = profiles_map.get(normalized_name, {})
        fragment_entries = _profile_gitignore_entries(profile_payload)
        profile_sections.append((normalized_name, fragment_entries))

    base_entries, os_entries = _load_global_gitignore_template(
        repo_root,
        profile_registry,
    )
    config_overlays, config_overrides = _config_gitignore_adjustments(config)
    gitignore_path = repo_root / ".gitignore"
    current_text = _read_text(gitignore_path)
    user_entries = _extract_user_gitignore_entries(current_text)
    rendered = _render_gitignore(
        base_entries,
        os_entries,
        profile_sections,
        config_overlays,
        config_overrides,
        user_entries,
    )
    if current_text == rendered:
        return False
    gitignore_path.write_text(rendered, encoding="utf-8")
    return True


def refresh_repo(repo_root: Path) -> int:
    """Run full refresh for the repository."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    try:
        config = _load_config_template(repo_root)
        user_config = _read_yaml(config_path) if config_path.exists() else {}
        _merge_user_config_values(config, user_config)
        initial_active_profiles = _active_profiles(config)
        config["autogen_metadata_overlays"] = (
            _config_autogen_metadata_overlays(
                repo_root,
                initial_active_profiles,
            )
        )
        project_governance_state = (
            project_governance_runtime_module.resolve_runtime_state(
                repo_root,
                config_payload=config,
            )
        )
        declared_project_version = _read_project_version(
            repo_root,
            config,
            required=not project_governance_state.is_unversioned,
        )
        project_version = project_governance_state.displayed_project_version(
            declared_project_version
        )
        devcovenant_version = _read_devcovenant_version(repo_root)
        _sync_doc(
            repo_root,
            "AGENTS.md",
            project_version=project_version,
            devcovenant_version=devcovenant_version,
            project_governance_state=project_governance_state,
        )
    except ValueError as error:
        print_step(f"Refresh failed: {error}", "🚫")
        return 1

    registry_result = refresh_policy_registry(repo_root)
    if registry_result != 0:
        return registry_result

    agents_path = repo_root / "AGENTS.md"
    try:
        refresh_agents_policy_block(agents_path, None, repo_root=repo_root)
    except ValueError as error:
        print_step(f"AGENTS policy refresh failed: {error}", "🚫")
        return 1

    active_profiles = _active_profiles(config)
    profile_registry = profile_runtime.refresh_profile_registry(
        repo_root, active_profiles
    )

    try:
        refreshed_assets = _refresh_profile_assets(
            repo_root,
            profile_registry,
            active_profiles,
        )
    except ValueError as error:
        print_step(f"Profile asset refresh failed: {error}", "🚫")
        return 1
    if refreshed_assets:
        print_step(
            "Materialized profile assets: " + ", ".join(refreshed_assets),
            "✅",
        )

    try:
        config, config_changed = _refresh_config_generated(
            repo_root,
            config_path,
            config,
            user_config,
            profile_registry,
            active_profiles,
        )
    except ValueError as error:
        print_step(f"Config refresh failed: {error}", "🚫")
        return 1
    if config_changed:
        print_step("Refreshed config generated profile metadata", "✅")

    try:
        governance_changed = _refresh_governance_and_test(
            repo_root,
            config,
            profile_registry,
            active_profiles,
        )
    except ValueError as error:
        print_step(f"Governance workflow refresh failed: {error}", "🚫")
        return 1
    if governance_changed:
        print_step("Regenerated governance-and-test workflow", "✅")

    try:
        pre_commit_changed = _refresh_pre_commit_config(
            repo_root,
            config,
            profile_registry,
            active_profiles,
        )
    except ValueError as error:
        print_step(f"Pre-commit config refresh failed: {error}", "🚫")
        return 1
    if pre_commit_changed:
        print_step(
            "Regenerated .pre-commit-config.yaml from profile fragments",
            "✅",
        )

    try:
        gitignore_changed = _refresh_gitignore(
            repo_root,
            config,
            profile_registry,
            active_profiles,
        )
    except ValueError as error:
        print_step(f"Gitignore refresh failed: {error}", "🚫")
        return 1
    if gitignore_changed:
        print_step("Regenerated .gitignore from profile fragments", "✅")

    try:
        docs = _managed_docs_from_config(config)
    except ValueError as error:
        print_step(f"Managed doc routing refresh failed: {error}", "🚫")
        return 1
    try:
        project_governance_state = (
            project_governance_runtime_module.resolve_runtime_state(
                repo_root,
                config_payload=config,
            )
        )
        declared_project_version = _read_project_version(
            repo_root,
            config,
            required=not project_governance_state.is_unversioned,
        )
        project_version = project_governance_state.displayed_project_version(
            declared_project_version
        )
    except ValueError as error:
        print_step(f"Project version resolution failed: {error}", "🚫")
        return 1
    devcovenant_version = _read_devcovenant_version(repo_root)
    try:
        synced = [
            doc
            for doc in docs
            if _sync_doc(
                repo_root,
                doc,
                project_version=project_version,
                devcovenant_version=devcovenant_version,
                project_governance_state=project_governance_state,
            )
        ]
    except ValueError as error:
        print_step(f"Managed doc refresh failed: {error}", "🚫")
        return 1
    if synced:
        print_step(f"Synchronized managed docs: {', '.join(synced)}", "✅")

    manifest_module.ensure_manifest(repo_root)
    return 0


# ---- AGENTS policy block refresh ----


RefreshResult = refresh_policy_block_runtime_module.RefreshResult
refresh_agents_policy_block = (
    refresh_policy_block_runtime_module.refresh_agents_policy_block
)


# ---- Local policy registry refresh ----
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


def _discover_policy_sources(repo_root: Path) -> Dict[str, Dict[str, bool]]:
    """Return policy ids and whether builtin/custom scripts exist."""

    discovered: Dict[str, Dict[str, bool]] = {}
    for source in ("builtin", "custom"):
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
                policy_id, {"builtin": False, "custom": False}
            )
            if source == "builtin":
                record["builtin"] = True
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


def _resolve_policy_sources(
    repo_root: Path, policy_id: str
) -> tuple[object | None, bool, bool]:
    """Resolve active script location and source availability flags."""
    location = resolve_script_location(repo_root, policy_id)
    available = {
        loc.kind
        for loc in iter_script_locations(repo_root, policy_id)
        if loc.path.exists()
    }
    return location, "builtin" in available, "custom" in available


def refresh_policy_registry(
    repo_root: Path | None = None,
) -> int:
    """Refresh policy hashes.

    Writes devcovenant/registry/registry.yaml.
    """

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = policy_registry_path(repo_root)

    if not agents_md_path.exists():
        runtime_print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    try:
        context = metadata_runtime.build_metadata_context(repo_root)
    except ValueError as error:
        runtime_print(f"Error: {error}", file=sys.stderr)
        return 1
    try:
        config_payload = _read_yaml(repo_root / "devcovenant" / "config.yaml")
    except ValueError as error:
        runtime_print(f"Error: {error}", file=sys.stderr)
        return 1
    config_context = CheckContext(repo_root=repo_root, config=config_payload)
    discovered = _discover_policy_sources(repo_root)

    registry = PolicyRegistry(registry_path, repo_root)

    updated = 0
    policies: List[PolicyDefinition] = []
    seen_policy_ids: set[str] = set()
    metadata_warning_targets: List[str] = []
    for policy_id in sorted(discovered):
        location, builtin_available, custom_available = (
            _resolve_policy_sources(repo_root, policy_id)
        )
        if location is None:
            runtime_print(
                f"Error: Policy script missing for {policy_id}.",
                file=sys.stderr,
            )
            return 1
        else:
            updated += 1
        try:
            descriptor = load_policy_descriptor(repo_root, policy_id)
        except ValueError as error:
            runtime_print(f"Error: {error}", file=sys.stderr)
            return 1
        if descriptor is None:
            runtime_print(
                (f"Error: Descriptor missing for {policy_id}."),
                file=sys.stderr,
            )
            return 1
        policy_text = str(descriptor.text or "").strip()
        if not policy_text:
            runtime_print(
                (f"Error: Descriptor text missing for {policy_id}."),
                file=sys.stderr,
            )
            return 1

        current_order = list(descriptor.metadata.keys())
        current_values = {
            key: _descriptor_values(descriptor.metadata.get(key))
            for key in current_order
        }
        bundle = metadata_runtime.resolve_policy_metadata_bundle(
            policy_id,
            current_order,
            current_values,
            descriptor,
            context,
            custom_policy=bool(custom_available and not builtin_available),
        )
        resolved_order = bundle.order
        resolved_metadata = bundle.string_map
        ordered_metadata = {
            key: str(resolved_metadata.get(key, "")).strip()
            for key in resolved_order
        }
        runtime_option_views = (
            runtime_actions_module.build_runtime_policy_option_views(
                bundle.decode_options(),
                config_context.get_policy_config(policy_id),
            )
        )
        severity = ordered_metadata.get("severity") or "warning"
        enabled = _as_bool(ordered_metadata.get("enabled"), default=True)
        custom = _as_bool(ordered_metadata.get("custom"), default=False)
        auto_fix = _as_bool(ordered_metadata.get("auto_fix"), default=False)
        policy_name = policy_id.replace("-", " ").title()
        policy = PolicyDefinition(
            policy_id=policy_id,
            name=policy_name,
            severity=severity,
            auto_fix=auto_fix,
            enabled=enabled,
            custom=custom,
            description=policy_text,
            raw_metadata=dict(ordered_metadata),
        )
        seen_policy_ids.add(policy_id)
        policies.append(policy)
        registry.update_policy_entry(
            policy,
            location,
            descriptor,
            resolved_metadata=ordered_metadata,
            metadata_resolution=bundle.resolution_trace,
            metadata_warnings=bundle.warnings,
            runtime_option_views=runtime_option_views,
        )
        for warning in bundle.warning_messages():
            metadata_warning_targets.append(f"{policy_id}: {warning}")
        script_name = (
            location.path.name if location is not None else "<missing>"
        )
        runtime_print(
            f"Recorded {policy_id}: {script_name}",
            verbose_only=True,
        )

    stale_ids = registry.prune_policies(seen_policy_ids)
    for stale_id in stale_ids:
        runtime_print(
            f"Removed stale policy entry: {stale_id}",
            verbose_only=True,
        )

    if updated == 0:
        runtime_print("All policy hashes are up to date.", verbose_only=True)
    else:
        runtime_print(
            "\nUpdated " f"{updated} policy hash(es) in {registry_path}",
            verbose_only=True,
        )

    if _ensure_trailing_newline(registry_path):
        runtime_print(
            f"Ensured trailing newline in {registry_path}.",
            verbose_only=True,
        )
    if metadata_warning_targets:
        runtime_print(
            "Recorded metadata replacement warnings in registry.yaml "
            f"for {len(metadata_warning_targets)} key(s).",
            verbose_only=True,
        )

    return 0
