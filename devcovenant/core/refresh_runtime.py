"""Full refresh orchestration for DevCovenant repositories."""

from __future__ import annotations

import copy
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from devcovenant.core import metadata_runtime, profile_runtime
from devcovenant.core import registry_runtime as manifest_module
from devcovenant.core.execution_runtime import print_step
from devcovenant.core.policy_runtime import PolicyDefinition
from devcovenant.core.registry_runtime import (
    POLICY_BLOCK_RE,
    PolicyDescriptor,
    PolicyRegistry,
    iter_script_locations,
    load_policy_descriptor,
    parse_metadata_block,
    policy_registry_path,
    resolve_script_location,
)

BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
WORKFLOW_BEGIN = "<!-- DEVCOV-WORKFLOW:BEGIN -->"
WORKFLOW_END = "<!-- DEVCOV-WORKFLOW:END -->"
_POLICIES_BEGIN = "<!-- DEVCOV-POLICIES:BEGIN -->"
_POLICIES_END = "<!-- DEVCOV-POLICIES:END -->"
_DOC_ID_LABEL = "**Doc ID:**"
_DOC_TYPE_LABEL = "**Doc Type:**"
_MANAGED_BY_LABEL = "**Managed By:**"
USER_GITIGNORE_BEGIN = "# --- User entries (preserved) ---"
USER_GITIGNORE_END = "# --- End user entries ---"
GITIGNORE_BASE_PATH = (
    "devcovenant/core/profiles/global/assets/gitignore_base.txt"
)
GITIGNORE_OS_PATH = "devcovenant/core/profiles/global/assets/gitignore_os.txt"

DEFAULT_MANAGED_DOCS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "devcovenant/README.md",
]


def _utc_today() -> str:
    """Return current UTC date."""
    return datetime.now(timezone.utc).date().isoformat()


def _read_version(repo_root: Path) -> str:
    """Read the target DevCovenant version."""
    version_path = repo_root / "devcovenant" / "VERSION"
    if not version_path.exists():
        return "0.0.0"
    version_text = version_path.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0"


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


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
        return list(DEFAULT_MANAGED_DOCS)

    raw_autogen = doc_assets.get("autogen")
    raw_user = doc_assets.get("user")

    autogen = []
    if isinstance(raw_autogen, list):
        autogen = [_normalize_doc_name(item) for item in raw_autogen]

    user_docs = set()
    if isinstance(raw_user, list):
        user_docs = {_normalize_doc_name(item) for item in raw_user if item}

    selected = [doc for doc in autogen if doc and doc not in user_docs]
    if not selected:
        selected = list(DEFAULT_MANAGED_DOCS)
    if "AGENTS.md" not in selected:
        selected.insert(0, "AGENTS.md")

    ordered: list[str] = []
    for doc in selected:
        if doc not in ordered:
            ordered.append(doc)
    return ordered


def _descriptor_path(repo_root: Path, doc_name: str) -> Path:
    """Resolve YAML descriptor path for a managed doc."""
    assets_root = (
        repo_root / "devcovenant" / "core" / "profiles" / "global" / "assets"
    )
    doc_path = Path(doc_name)
    if doc_path.parent != Path("."):
        return assets_root / doc_path.with_suffix(".yaml")
    return assets_root / f"{doc_path.stem}.yaml"


def _apply_header_overrides(
    header_lines: list[str],
    *,
    version: str,
    title: str | None = None,
) -> list[str]:
    """Inject standard header fields into descriptor header lines."""
    updated = []
    saw_title = False
    saw_date = False
    saw_version = False

    for line in header_lines:
        stripped = line.strip().lower()
        if title and line.lstrip().startswith("#") and not saw_title:
            updated.append(f"# {title}")
            saw_title = True
            continue
        if stripped.startswith("**last updated:**"):
            updated.append(f"**Last Updated:** {_utc_today()}")
            saw_date = True
            continue
        if stripped.startswith("**version:**"):
            updated.append(f"**Version:** {version}")
            saw_version = True
            continue
        updated.append(line.rstrip())

    if title and not saw_title:
        updated.insert(0, f"# {title}")

    insert_index = 1 if updated and updated[0].startswith("#") else 0
    if not saw_date:
        updated.insert(insert_index, f"**Last Updated:** {_utc_today()}")
        insert_index += 1
    if not saw_version:
        updated.insert(insert_index, f"**Version:** {version}")
    return updated


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
    return "\n".join([begin_marker, body.strip("\n"), end_marker])


def _managed_metadata_lines(descriptor: dict[str, object]) -> list[str]:
    """Return managed-block metadata lines from descriptor fields."""
    doc_id = str(descriptor.get("doc_id", "")).strip()
    doc_type = str(descriptor.get("doc_type", "")).strip()
    managed_by = str(descriptor.get("managed_by", "")).strip()
    lines: list[str] = []
    if doc_id:
        lines.append(f"{_DOC_ID_LABEL} {doc_id}")
    if doc_type:
        lines.append(f"{_DOC_TYPE_LABEL} {doc_type}")
    if managed_by:
        lines.append(f"{_MANAGED_BY_LABEL} {managed_by}")
    return lines


def _normalize_managed_block_body(body: str) -> str:
    """Strip legacy marker/header lines from descriptor-managed block body."""
    cleaned: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped in {BLOCK_BEGIN, BLOCK_END}:
            continue
        if stripped.startswith(_DOC_ID_LABEL):
            continue
        if stripped.startswith(_DOC_TYPE_LABEL):
            continue
        if stripped.startswith(_MANAGED_BY_LABEL):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip("\n")


def _compose_managed_block_body(descriptor: dict[str, object]) -> str:
    """Compose managed block body from descriptor metadata and body text."""
    metadata_lines = _managed_metadata_lines(descriptor)
    block_extra = _normalize_managed_block_body(
        str(descriptor.get("managed_block", ""))
    )
    if metadata_lines and block_extra:
        return "\n".join(metadata_lines + ["", block_extra])
    if metadata_lines:
        return "\n".join(metadata_lines)
    return block_extra


def _render_doc(repo_root: Path, doc_name: str, version: str) -> str | None:
    """Render managed doc text from YAML descriptor."""
    descriptor = _read_yaml(_descriptor_path(repo_root, doc_name))
    if not descriptor:
        return None

    headers_raw = descriptor.get("header_lines")
    if isinstance(headers_raw, list):
        header_lines = [str(item).rstrip() for item in headers_raw]
    else:
        header_lines = []

    title_override = repo_root.name if doc_name == "README.md" else None
    header_lines = _apply_header_overrides(
        header_lines,
        version=version,
        title=title_override,
    )

    block_body = _compose_managed_block_body(descriptor)
    managed_block = ""
    if block_body:
        managed_block = _render_block(BLOCK_BEGIN, BLOCK_END, block_body)

    body_value = descriptor.get("body")
    body_lines = []
    if isinstance(body_value, str):
        body_lines = [line.rstrip() for line in body_value.splitlines()]

    workflow_body = str(descriptor.get("workflow_block", "")).strip("\n")
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
        return None
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
    if not current_blocks or not template_blocks:
        return current, False

    replacement_count = min(len(current_blocks), len(template_blocks))
    updated = current
    changed = False
    for index in range(replacement_count - 1, -1, -1):
        start, end, _ = current_blocks[index]
        replacement = template_blocks[index][2]
        if updated[start:end] == replacement:
            continue
        updated = updated[:start] + replacement + updated[end:]
        changed = True
    return updated, changed


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
    """Return start of next workflow/policy/legacy block after offset."""
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
    editable_section = current[editable_start:editable_end]

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

    return updated, updated != current


def _sync_doc(repo_root: Path, doc_name: str, version: str) -> bool:
    """Synchronize one managed doc from descriptor content."""
    rendered = _render_doc(repo_root, doc_name, version)
    if rendered is None:
        return False

    target = repo_root / doc_name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        return True

    current = target.read_text(encoding="utf-8")
    if _doc_is_placeholder(current):
        target.write_text(rendered, encoding="utf-8")
        return True

    if doc_name == "AGENTS.md":
        updated, changed = _sync_agents_content(current, rendered)
    else:
        updated, changed = _replace_managed_block(current, rendered)
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
    return repo_root / raw_path


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
    return repo_root / profile_path / "assets" / raw_template


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
            rel_path = target.relative_to(repo_root).as_posix()
            changed.append(rel_path)
    return changed


_CONFIG_AUTOGEN_PATHS: tuple[tuple[str, ...], ...] = (
    ("devcov_core_paths",),
    ("autogen_metadata_overrides",),
    ("profiles", "generated"),
    ("doc_assets", "autogen"),
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
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )


def _load_config_template(repo_root: Path) -> dict[str, object]:
    """Load global config template payload."""
    template_payload = _read_yaml(_config_template_path(repo_root))
    if isinstance(template_payload, dict) and template_payload:
        return template_payload
    return {
        "devcov_core_include": False,
        "devcov_core_paths": _default_core_paths(repo_root),
        "profiles": {
            "active": [
                "global",
                "devcovuser",
                "python",
                "docs",
            ],
            "generated": {"file_suffixes": ["__none__"]},
        },
        "paths": {
            "policy_definitions": "AGENTS.md",
            "registry_file": (
                "devcovenant/registry/local/policy_registry.yaml"
            ),
        },
        "version": {"override": None},
        "docs": {
            "managed_blocks": {
                "begin": BLOCK_BEGIN,
                "end": BLOCK_END,
            }
        },
        "doc_assets": {"autogen": list(DEFAULT_MANAGED_DOCS), "user": []},
        "install": {"generic_config": True},
        "engine": {
            "fail_threshold": "error",
            "auto_fix_enabled": True,
            "file_suffixes": [".md", ".rst", ".txt", ".yml", ".yaml"],
            "ignore_dirs": [".git", ".venv", "build", "dist"],
        },
        "pre_commit": {"overrides": {}},
        "policy_state": {},
        "ignore": {"patterns": []},
        "autogen_metadata_overrides": {},
        "user_metadata_overrides": {},
    }


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
        "devcov_core_paths",
        "profiles",
        "paths",
        "version",
        "docs",
        "doc_assets",
        "install",
        "engine",
        "pre_commit",
        "policy_state",
        "ignore",
        "autogen_metadata_overrides",
        "user_metadata_overrides",
    ]
    comments = {
        "scope": _config_section_header("Scope control"),
        "profiles": _config_section_header("Profile activation"),
        "paths": _config_section_header("Canonical paths"),
        "version": _config_section_header("Version controls"),
        "docs": _config_section_header("Managed document controls"),
        "install": _config_section_header("Install/deploy safety"),
        "engine": _config_section_header("Engine behavior"),
        "pre_commit": _config_section_header("Pre-commit generation"),
        "policy": _config_section_header(
            "Policy activation and customization"
        ),
        "ignore": _config_section_header("Global ignore patterns"),
        "metadata": _config_section_header(
            "Metadata overrides (resolution order matters)"
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
        "\n".join(
            [
                (
                    "# Paths excluded from checks when "
                    "`devcov_core_include` is false."
                ),
                "# Keep this list aligned with command and core internals.",
            ]
        ),
        _yaml_block(
            {
                "devcov_core_paths": _normalize_string_list(
                    payload.get("devcov_core_paths")
                ),
            }
        ),
        comments["profiles"],
        "# Ordered profile list. `global` should stay first.",
        ("# Profiles contribute suffixes, assets, and metadata overlays."),
        (
            "# Profiles do not activate policies. "
            "Policy activation is `policy_state`."
        ),
        _yaml_block({"profiles": payload.get("profiles", {})}),
        comments["paths"],
        "# Runtime policy source parsed by the engine.",
        "# Generated local policy registry (hashes + diagnostics).",
        _yaml_block({"paths": payload.get("paths", {})}),
        comments["version"],
        "# Optional forced version value for version-aware logic.",
        _yaml_block({"version": payload.get("version", {})}),
        comments["docs"],
        "# Marker pair used by managed-block refresh logic.",
        _yaml_block({"docs": payload.get("docs", {})}),
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
        "# auto_fix_enabled controls policy auto-fix pass behavior.",
        "# file_suffixes and ignore_dirs define broad scan boundaries.",
        _yaml_block({"engine": payload.get("engine", {})}),
        comments["pre_commit"],
        "# Structured overrides merged into generated pre-commit config.",
        _yaml_block({"pre_commit": payload.get("pre_commit", {})}),
        comments["policy"],
        "# Canonical policy on/off map: {policy-id: true|false}.",
        _yaml_block({"policy_state": payload.get("policy_state", {})}),
        comments["ignore"],
        "# Extra glob patterns excluded from CheckContext file collections.",
        _yaml_block({"ignore": payload.get("ignore", {})}),
        comments["metadata"],
        "# Auto-generated profile overlays written by refresh.",
        "# Do not hand-edit unless you intentionally own this layer.",
        _yaml_block(
            {
                "autogen_metadata_overrides": payload.get(
                    "autogen_metadata_overrides", {}
                )
            }
        ),
        "# User-owned overrides applied last (highest precedence).",
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
    registry: dict[str, dict],
    active_profiles: list[str],
) -> tuple[dict[str, object], bool]:
    """Refresh config with autogen values while preserving user-owned keys."""
    template = _load_config_template(repo_root)
    merged = copy.deepcopy(template)
    _merge_user_config_values(merged, config)

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
    profiles_block["generated"] = generated
    merged["profiles"] = profiles_block

    merged["devcov_core_paths"] = _default_core_paths(repo_root)
    merged["autogen_metadata_overrides"] = _config_autogen_metadata_overrides(
        repo_root, active_profiles
    )
    merged["policy_state"] = _materialize_policy_state_map(
        repo_root,
        metadata_runtime.normalize_policy_state(merged.get("policy_state")),
    )

    doc_assets = merged.get("doc_assets")
    if not isinstance(doc_assets, dict):
        doc_assets = {}
    doc_assets["autogen"] = list(DEFAULT_MANAGED_DOCS)
    user_docs = doc_assets.get("user")
    if not isinstance(user_docs, list):
        doc_assets["user"] = []
    merged["doc_assets"] = doc_assets

    rendered = _render_config_yaml(merged)
    current = _read_text_if_exists(config_path)
    if current == rendered:
        return merged, False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(rendered, encoding="utf-8")
    return merged, True


def _materialize_policy_state_map(
    repo_root: Path, current_state: Dict[str, bool]
) -> Dict[str, bool]:
    """Return full alphabetical policy_state map from local registry."""
    registry_path = policy_registry_path(repo_root)
    payload = _read_yaml(registry_path)
    raw_policies = payload.get("policies")
    if not isinstance(raw_policies, dict):
        return {}

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
        if token and token != "__none__":
            cleaned.append(token)
    return cleaned


def _default_core_paths(repo_root: Path) -> list[str]:
    """Load canonical devcov core paths from the config asset."""
    asset_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )
    payload = _read_yaml(asset_path)
    configured = _normalize_string_list(payload.get("devcov_core_paths"))
    if configured:
        return configured
    return [
        "devcovenant/core",
        "devcovenant/__init__.py",
        "devcovenant/__main__.py",
        "devcovenant/cli.py",
        "devcovenant/check.py",
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


def _config_autogen_metadata_overrides(
    repo_root: Path, active_profiles: list[str]
) -> Dict[str, Dict[str, object]]:
    """Build deterministic profile-derived autogen metadata overrides."""
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
                key_map[key_name] = values[0] if values else "__none__"
                continue
            key_map[key_name] = list(values)
        if key_map:
            normalized[policy_id] = key_map
    return normalized


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
    if not token or token == "__none__":
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
    """Persist resolved pre-commit metadata into manifest.json."""
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
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
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

    pre_commit_block = config.get("pre_commit")
    if isinstance(pre_commit_block, dict):
        overrides = pre_commit_block.get("overrides")
        if isinstance(overrides, dict):
            payload = _merge_pre_commit_fragment(payload, overrides)

    if "repos" not in payload or not isinstance(payload.get("repos"), list):
        payload["repos"] = []

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


def _profile_gitignore_fragment(
    repo_root: Path,
    profile_name: str,
    profile_payload: dict[str, object],
) -> str:
    """Resolve a profile .gitignore fragment or synthesize from ignore_dirs."""
    path_value = str(profile_payload.get("path", "")).strip()
    if path_value:
        fragment_path = repo_root / path_value / "assets" / ".gitignore"
        fragment_text = _read_text(fragment_path).strip()
        if fragment_text:
            return fragment_text

    ignore_dirs_value = profile_payload.get("ignore_dirs")
    if not isinstance(ignore_dirs_value, list):
        return "# DevCovenant profile ignores"

    ignore_dirs: list[str] = []
    for entry in ignore_dirs_value:
        token = str(entry or "").strip()
        if not token or token == "__none__":
            continue
        ignore_dirs.append(token)
    if not ignore_dirs:
        return "# DevCovenant profile ignores"

    lines = ["# DevCovenant profile ignores", *ignore_dirs]
    return "\n".join(lines)


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
    base_fragment: str,
    os_fragment: str,
    profile_sections: list[tuple[str, str]],
    user_entries: list[str],
) -> str:
    """Render full .gitignore with generated and preserved user sections."""
    sections: list[str] = []
    base_text = base_fragment.strip()
    if base_text:
        sections.append(base_text)

    for profile_name, fragment_text in profile_sections:
        section_header = f"# Profile: {profile_name}"
        section_body = fragment_text.strip() or "# DevCovenant profile ignores"
        sections.append("\n".join([section_header, section_body]))

    os_text = os_fragment.strip()
    if os_text:
        sections.append(os_text)

    user_block_lines = [USER_GITIGNORE_BEGIN, ""]
    user_block_lines.extend(user_entries)
    user_block_lines.extend(["", USER_GITIGNORE_END])
    sections.append("\n".join(user_block_lines))

    return (
        "\n\n".join(section for section in sections if section).rstrip() + "\n"
    )


def _refresh_gitignore(
    repo_root: Path,
    profile_registry: dict[str, dict],
    active_profiles: list[str],
) -> bool:
    """Regenerate .gitignore from global/profile/os fragments."""
    profiles_map = _profile_registry_profiles(profile_registry)
    profile_sections: list[tuple[str, str]] = []
    for profile_name in active_profiles:
        normalized_name = str(profile_name or "").strip().lower()
        if not normalized_name:
            continue
        profile_payload = profiles_map.get(normalized_name, {})
        fragment_text = _profile_gitignore_fragment(
            repo_root, normalized_name, profile_payload
        )
        profile_sections.append((normalized_name, fragment_text))

    base_fragment = _read_text(repo_root / GITIGNORE_BASE_PATH)
    os_fragment = _read_text(repo_root / GITIGNORE_OS_PATH)
    gitignore_path = repo_root / ".gitignore"
    current_text = _read_text(gitignore_path)
    user_entries = _extract_user_gitignore_entries(current_text)
    rendered = _render_gitignore(
        base_fragment, os_fragment, profile_sections, user_entries
    )
    if current_text == rendered:
        return False
    gitignore_path.write_text(rendered, encoding="utf-8")
    return True


def refresh_repo(repo_root: Path) -> int:
    """Run full refresh for the repository."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config = _load_config_template(repo_root)
    _merge_user_config_values(config, _read_yaml(config_path))
    version = _read_version(repo_root)

    _sync_doc(repo_root, "AGENTS.md", version)

    registry_result = refresh_policy_registry(repo_root)
    if registry_result != 0:
        return registry_result

    agents_path = repo_root / "AGENTS.md"
    refresh_agents_policy_block(agents_path, None, repo_root=repo_root)

    active_profiles = _active_profiles(config)
    profile_registry = profile_runtime.refresh_profile_registry(
        repo_root, active_profiles
    )

    refreshed_assets = _refresh_profile_assets(
        repo_root,
        profile_registry,
        active_profiles,
    )
    if refreshed_assets:
        print_step(
            "Materialized profile assets: " + ", ".join(refreshed_assets),
            "✅",
        )

    config, config_changed = _refresh_config_generated(
        repo_root, config_path, config, profile_registry, active_profiles
    )
    if config_changed:
        print_step("Refreshed config generated profile metadata", "✅")

    if _refresh_pre_commit_config(
        repo_root, config, profile_registry, active_profiles
    ):
        print_step(
            "Regenerated .pre-commit-config.yaml from profile fragments",
            "✅",
        )

    if _refresh_gitignore(repo_root, profile_registry, active_profiles):
        print_step("Regenerated .gitignore from profile fragments", "✅")

    docs = _managed_docs_from_config(config)
    synced = [doc for doc in docs if _sync_doc(repo_root, doc, version)]
    if synced:
        print_step(f"Synchronized managed docs: {', '.join(synced)}", "✅")

    manifest_module.ensure_manifest(repo_root)
    return 0


# ---- AGENTS policy block refresh ----


@dataclass(frozen=True)
class RefreshResult:
    """Summary of refresh work."""

    changed_policies: Tuple[str, ...]
    skipped_policies: Tuple[str, ...]
    updated: bool


@dataclass
class _PolicyEntry:
    """Track a policy block's key attributes during refresh."""

    policy_id: str
    text: str
    group: int
    changed: bool
    custom: bool


def _assemble_sections(entries: List[_PolicyEntry]) -> str:
    """Build a policy block ordered alphabetically."""
    if not entries:
        return ""

    sorted_entries = sorted(entries, key=lambda item: item.policy_id)
    sections_text: List[str] = []
    for idx, entry in enumerate(sorted_entries):
        if idx > 0:
            sections_text.append("\n\n---\n\n")
        sections_text.append(entry.text)
    final = "".join(sections_text)
    if not final.endswith("\n"):
        final += "\n"
    return final


def _locate_policy_block(text: str) -> Tuple[int, int, str]:
    """Return the start/end spans and content of the policy block."""
    try:
        start = text.index(_POLICIES_BEGIN)
        end = text.index(_POLICIES_END, start + len(_POLICIES_BEGIN))
    except ValueError:
        raise ValueError("Policy block markers not found in AGENTS.md")
    block_start = start + len(_POLICIES_BEGIN)
    block_text = text[block_start:end]
    return block_start, end, block_text


def _ensure_policy_block_scaffold(
    agents_path: Path, content: str
) -> Tuple[str, bool]:
    """Ensure AGENTS has exactly one policy marker block scaffold."""
    has_begin = _POLICIES_BEGIN in content
    has_end = _POLICIES_END in content
    if has_begin and has_end:
        return content, False

    stripped = (
        content.replace(_POLICIES_BEGIN, "")
        .replace(_POLICIES_END, "")
        .rstrip()
    )
    scaffold = f"{_POLICIES_BEGIN}\n{_POLICIES_END}\n"
    rebuilt = f"{stripped}\n\n{scaffold}"
    agents_path.write_text(rebuilt, encoding="utf-8")
    return rebuilt, True


def _metadata_from_registry(
    policy_id: str,
    metadata_map: object,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return ordered metadata keys/values sourced from registry entries."""
    if not isinstance(metadata_map, dict):
        return ["id"], {"id": [policy_id]}

    order: List[str] = []
    values: Dict[str, List[str]] = {}
    for key, raw_value in metadata_map.items():
        key_name = str(key).strip()
        if not key_name:
            continue
        order.append(key_name)
        if isinstance(raw_value, list):
            normalized = [
                str(item).strip() for item in raw_value if str(item).strip()
            ]
        else:
            normalized = metadata_runtime.split_metadata_values(
                [str(raw_value)]
            )
        values[key_name] = normalized
    if "id" not in values:
        values["id"] = [policy_id]
    else:
        values["id"] = [policy_id]
    if "id" not in order:
        order.insert(0, "id")
    return order, values


def _section_map(block_text: str) -> Dict[str, str]:
    """Return a map of policy id -> rendered section from a policy block."""
    sections: Dict[str, str] = {}
    for match in POLICY_BLOCK_RE.finditer(block_text):
        heading = match.group(1)
        metadata_block = match.group(2).strip()
        order, values = parse_metadata_block(metadata_block)
        policy_id = values.get("id", [""])[0] if values.get("id") else ""
        if not policy_id:
            continue
        description = match.group(3).strip()
        rendered = metadata_runtime.render_metadata_block(order, values)
        section = f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        sections[policy_id] = section
    return sections


def _descriptor_text_or_error(
    descriptor: PolicyDescriptor | None,
    policy_id: str,
) -> str:
    """Return canonical descriptor text or raise when missing."""
    if descriptor is None:
        raise ValueError(
            f"Missing policy descriptor for `{policy_id}`."
            " Add a <policy>.yaml file with a non-empty `text` field."
        )
    text = str(descriptor.text or "").strip()
    if text:
        return text
    raise ValueError(
        f"Missing descriptor text for `{policy_id}`."
        " Set the `text` field in the policy descriptor YAML."
    )


def refresh_agents_policy_block(
    agents_path: Path,
    schema_path: Path | None,
    *,
    repo_root: Path | None = None,
) -> RefreshResult:
    """Refresh the AGENTS policy block from registry policy entries."""
    if not agents_path.exists():
        return RefreshResult((), (), False)

    repo_root = repo_root or agents_path.parent
    del schema_path
    content = agents_path.read_text(encoding="utf-8")
    scaffolded = False
    try:
        block_start, block_end, block_text = _locate_policy_block(content)
    except ValueError:
        content, scaffolded = _ensure_policy_block_scaffold(
            agents_path, content
        )
        try:
            block_start, block_end, block_text = _locate_policy_block(content)
        except ValueError:
            return RefreshResult((), (), scaffolded)

    registry_path = policy_registry_path(repo_root)
    if not registry_path.exists():
        return RefreshResult((), (), scaffolded)
    try:
        payload = (
            yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        )
    except Exception:
        return RefreshResult((), (), scaffolded)
    policies = payload.get("policies", {})
    if not isinstance(policies, dict) or not policies:
        return RefreshResult((), (), scaffolded)

    previous_sections = _section_map(block_text)
    generated_sections: Dict[str, str] = {}
    skipped: List[str] = []
    entries: List[_PolicyEntry] = []
    for policy_id in sorted(policies):
        payload_entry = policies.get(policy_id, {})
        if not isinstance(payload_entry, dict):
            skipped.append(policy_id)
            continue
        order, values = _metadata_from_registry(
            policy_id, payload_entry.get("metadata")
        )
        rendered = metadata_runtime.render_metadata_block(order, values)
        heading_name = (
            str(payload_entry.get("description", "")).strip()
            or policy_id.replace("-", " ").title()
        )
        heading = f"## Policy: {heading_name}\n\n"
        description = str(payload_entry.get("policy_text", "")).strip()
        if not description:
            descriptor = load_policy_descriptor(repo_root, policy_id)
            try:
                description = _descriptor_text_or_error(descriptor, policy_id)
            except ValueError:
                skipped.append(policy_id)
                continue
        final_text = (
            f"{heading}```policy-def\n{rendered}\n```\n\n{description}\n"
        )
        generated_sections[policy_id] = final_text
        custom_flag = (
            str(payload_entry.get("custom", False)).strip().lower() == "true"
        )
        entries.append(
            _PolicyEntry(
                policy_id=policy_id,
                text=final_text,
                group=0,
                changed=False,
                custom=custom_flag,
            )
        )

    if not entries:
        return RefreshResult((), tuple(skipped), scaffolded)

    new_block = _assemble_sections(entries)
    block_clean = block_text.strip()
    new_block_clean = new_block.strip()
    updated = new_block_clean != block_clean
    changed_file = scaffolded or updated
    if updated:
        prefix = content[:block_start]
        suffix = content[block_end:]
        rebuilt = (
            f"{prefix}\n{new_block.rstrip()}\n{suffix}"
            if not prefix.endswith("\n")
            else f"{prefix}{new_block.rstrip()}\n{suffix}"
        )
        agents_path.write_text(rebuilt, encoding="utf-8")
    changed = sorted(
        {
            *previous_sections.keys(),
            *generated_sections.keys(),
        }
        - {
            policy_id
            for policy_id in previous_sections.keys()
            & generated_sections.keys()
            if previous_sections.get(policy_id, "").strip()
            == generated_sections.get(policy_id, "").strip()
        }
    )
    return RefreshResult(tuple(changed), tuple(skipped), changed_file)


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
    return location, "core" in available, "custom" in available


def refresh_policy_registry(
    repo_root: Path | None = None,
) -> int:
    """Refresh policy hashes.

    Writes devcovenant/registry/local/policy_registry.yaml.
    """

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    agents_md_path = repo_root / "AGENTS.md"
    registry_path = policy_registry_path(repo_root)

    if not agents_md_path.exists():
        print(
            f"Error: AGENTS.md not found at {agents_md_path}",
            file=sys.stderr,
        )
        return 1

    context = metadata_runtime.build_metadata_context(repo_root)
    discovered = _discover_policy_sources(repo_root)

    registry = PolicyRegistry(registry_path, repo_root)

    updated = 0
    policies: List[PolicyDefinition] = []
    seen_policy_ids: set[str] = set()
    for policy_id in sorted(discovered):
        location, core_available, custom_available = _resolve_policy_sources(
            repo_root, policy_id
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
        resolved_order, resolved_metadata = (
            metadata_runtime.resolve_policy_metadata_map(
                policy_id,
                current_order,
                current_values,
                descriptor,
                context,
                custom_policy=bool(custom_available and not core_available),
            )
        )
        ordered_metadata = {
            key: str(resolved_metadata.get(key, "")).strip()
            for key in resolved_order
        }
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
        )
        script_name = (
            location.path.name if location is not None else "<missing>"
        )
        print(f"Recorded {policy_id}: {script_name}")

    stale_ids = registry.prune_policies(seen_policy_ids)
    for stale_id in stale_ids:
        print(f"Removed stale policy entry: {stale_id}")

    if updated == 0:
        print("All policy hashes are up to date.")
    else:
        print("\nUpdated " f"{updated} policy hash(es) in {registry_path}")

    if _ensure_trailing_newline(registry_path):
        print(f"Ensured trailing newline in {registry_path}.")

    return 0
