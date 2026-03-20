"""Core runtime service for project-governance state and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

_DEFAULT_STAGES = (
    "prototype",
    "alpha",
    "beta",
    "stable",
    "mature",
    "deprecated",
    "archived",
)
_DEFAULT_DEVELOPMENT_STANCES = (
    "experimental",
    "active-development",
    "maintenance",
    "release-managed",
    "frozen",
    "sunset",
)
_ALLOWED_VERSIONING_MODES = {"versioned", "unversioned"}
_DEFAULT_UNVERSIONED_LABEL = "Unversioned"
_DEFAULT_UNRELEASED_HEADING = "## Unreleased"
_DEFAULT_CHANGELOG_FILE = "CHANGELOG.md"
_LOG_MARKER = "## Log changes here"
_MANAGED_BEGIN = "<!-- DEVCOV:BEGIN -->"
_MANAGED_END = "<!-- DEVCOV:END -->"


@dataclass(frozen=True)
class ProjectGovernanceState:
    """Resolved project-governance state for one repository runtime."""

    enabled: bool = True
    stage: str = ""
    development_stance: str = ""
    versioning_mode: str = "versioned"
    codename: str = ""
    build_identity: str = ""
    unversioned_label: str = _DEFAULT_UNVERSIONED_LABEL
    unreleased_heading: str = _DEFAULT_UNRELEASED_HEADING
    changelog_file: str = _DEFAULT_CHANGELOG_FILE
    allowed_stages: tuple[str, ...] = _DEFAULT_STAGES
    allowed_development_stances: tuple[str, ...] = _DEFAULT_DEVELOPMENT_STANCES

    @property
    def is_unversioned(self) -> bool:
        """Return True when the repository is intentionally unversioned."""
        return self.versioning_mode == "unversioned"

    def displayed_project_version(self, declared_version: str) -> str:
        """Return the rendered Project Version header value."""
        if self.is_unversioned:
            return self.unversioned_label
        token = str(declared_version or "").strip()
        if token:
            return token
        raise ValueError(
            "Versioned repository is missing a declared project version."
        )

    def governance_header_lines(self) -> list[str]:
        """Return managed-doc governance header lines for opted-in docs."""
        lines = [
            f"**Project Stage:** {self.stage}",
            f"**Development Stance:** {self.development_stance}",
            f"**Versioning Mode:** {self.versioning_mode}",
        ]
        if self.codename:
            lines.append(f"**Project Codename:** {self.codename}")
        if self.build_identity:
            lines.append(f"**Build Identity:** {self.build_identity}")
        return lines

    def section_lines(self, declared_version: str) -> list[str]:
        """Return the AGENTS project-governance section lines."""
        lines = [
            "## Project Governance",
            (
                "This block reflects the repository's active "
                "project-governance state."
            ),
            (
                "- Project Version: "
                f"{self.displayed_project_version(declared_version)}"
            ),
            f"- Project Stage: {self.stage}",
            f"- Development Stance: {self.development_stance}",
            f"- Versioning Mode: {self.versioning_mode}",
        ]
        if self.codename:
            lines.append(f"- Project Codename: {self.codename}")
        if self.build_identity:
            lines.append(f"- Build Identity: {self.build_identity}")
        return lines

    def registry_payload(self, declared_version: str) -> dict[str, object]:
        """Return a deterministic registry mapping for project governance."""
        payload: dict[str, object] = {
            "project_version": self.displayed_project_version(
                declared_version
            ),
            "stage": self.stage,
            "development_stance": self.development_stance,
            "versioning_mode": self.versioning_mode,
            "unversioned_label": self.unversioned_label,
            "unreleased_heading": self.unreleased_heading,
            "changelog_file": self.changelog_file,
            "release_headings": release_headings_for_state(self),
            "allowed_stages": list(self.allowed_stages),
            "allowed_development_stances": list(
                self.allowed_development_stances
            ),
        }
        if self.codename:
            payload["codename"] = self.codename
        if self.build_identity:
            payload["build_identity"] = self.build_identity
        return payload


def resolve_runtime_state(
    repo_root: Path,
    *,
    config_payload: Mapping[str, Any] | None = None,
) -> ProjectGovernanceState:
    """Return validated project-governance state for one repo runtime."""
    repo_root = Path(repo_root).resolve()
    payload = _load_runtime_config(repo_root, config_payload)
    raw_block = payload.get("project-governance")
    if not isinstance(raw_block, dict):
        raise ValueError(
            "Configure `project-governance` as a mapping in "
            "`devcovenant/config.yaml`."
        )

    stage = _required_string(raw_block, "stage")
    development_stance = _required_string(raw_block, "development_stance")
    versioning_mode = _required_string(raw_block, "versioning_mode").lower()
    if versioning_mode not in _ALLOWED_VERSIONING_MODES:
        raise ValueError(
            "`project-governance.versioning_mode` must be `versioned` "
            "or `unversioned`."
        )

    allowed_stages = tuple(
        _normalized_list(
            raw_block.get("allowed_stages"),
            default=_DEFAULT_STAGES,
        )
    )
    if stage not in allowed_stages:
        raise ValueError(
            "`project-governance.stage` must be one of: "
            + ", ".join(allowed_stages)
            + "."
        )

    allowed_development_stances = tuple(
        _normalized_list(
            raw_block.get("allowed_development_stances"),
            default=_DEFAULT_DEVELOPMENT_STANCES,
        )
    )
    if development_stance not in allowed_development_stances:
        raise ValueError(
            "`project-governance.development_stance` must be one of: "
            + ", ".join(allowed_development_stances)
            + "."
        )

    changelog_file = (
        _string_option(raw_block, "changelog_file") or _DEFAULT_CHANGELOG_FILE
    )
    return ProjectGovernanceState(
        stage=stage,
        development_stance=development_stance,
        versioning_mode=versioning_mode,
        codename=_string_option(raw_block, "codename"),
        build_identity=_string_option(raw_block, "build_identity"),
        unversioned_label=(
            _string_option(raw_block, "unversioned_label")
            or _DEFAULT_UNVERSIONED_LABEL
        ),
        unreleased_heading=(
            _string_option(raw_block, "unreleased_heading")
            or _DEFAULT_UNRELEASED_HEADING
        ),
        changelog_file=changelog_file,
        allowed_stages=allowed_stages,
        allowed_development_stances=allowed_development_stances,
    )


def resolve_release_headings(
    repo_root: Path,
    *,
    config_payload: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return active changelog release headings for one repo runtime."""
    state = resolve_runtime_state(
        repo_root,
        config_payload=config_payload,
    )
    validate_changelog_contract(
        repo_root,
        config_payload=config_payload,
        state=state,
    )
    return release_headings_for_state(state)


def release_headings_for_state(
    state: ProjectGovernanceState,
) -> list[str]:
    """Return active changelog headings from one resolved state."""
    if state.is_unversioned:
        return [state.unreleased_heading]
    return ["## Version"]


def validate_changelog_contract(
    repo_root: Path,
    *,
    config_payload: Mapping[str, Any] | None = None,
    state: ProjectGovernanceState | None = None,
) -> None:
    """Validate the changelog contract implied by project-governance."""
    repo_root = Path(repo_root).resolve()
    runtime_state = state or resolve_runtime_state(
        repo_root,
        config_payload=config_payload,
    )
    if not runtime_state.is_unversioned:
        return
    changelog_path = repo_root / runtime_state.changelog_file
    if not changelog_path.exists():
        raise ValueError(
            "Configured project-governance changelog file is missing."
        )
    top_heading = _top_visible_release_heading(changelog_path)
    if top_heading != runtime_state.unreleased_heading:
        raise ValueError(
            "Unversioned project-governance requires the top changelog "
            f"heading to be `{runtime_state.unreleased_heading}`."
        )


def _load_runtime_config(
    repo_root: Path,
    config_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return runtime config payload, defaulting to repo config.yaml."""
    if config_payload:
        return dict(config_payload)
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Unable to load runtime config: {exc}") from exc
    if isinstance(payload, dict):
        return payload
    raise ValueError("Runtime config must be a YAML mapping.")


def _string_option(raw_block: Mapping[str, Any], key: str) -> str:
    """Return one normalized string option from the config block."""
    return str(raw_block.get(key, "") or "").strip()


def _required_string(raw_block: Mapping[str, Any], key: str) -> str:
    """Return one required string config option or raise a clear error."""
    token = _string_option(raw_block, key)
    if token:
        return token
    raise ValueError(
        f"Configure `project-governance.{key}` explicitly in "
        "`devcovenant/config.yaml`."
    )


def _normalized_list(
    raw: object,
    *,
    default: Iterable[str],
) -> list[str]:
    """Return a normalized non-empty string list."""
    if isinstance(raw, str):
        items = [entry.strip() for entry in raw.split(",") if entry.strip()]
    elif isinstance(raw, list):
        items = [str(entry).strip() for entry in raw if str(entry).strip()]
    else:
        items = []
    return items or [
        str(entry).strip() for entry in default if str(entry).strip()
    ]


def _visible_changelog_lines(changelog_text: str) -> list[str]:
    """Return changelog lines outside managed blocks and fenced examples."""
    start = changelog_text.find(_LOG_MARKER)
    content = changelog_text[start:] if start >= 0 else changelog_text
    visible: list[str] = []
    in_managed = False
    in_fence = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == _LOG_MARKER:
            continue
        if stripped == _MANAGED_BEGIN:
            in_managed = True
            continue
        if stripped == _MANAGED_END:
            in_managed = False
            continue
        if in_managed:
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped:
            visible.append(stripped)
    return visible


def _top_visible_release_heading(changelog_path: Path) -> str:
    """Return the top visible release heading from a changelog."""
    content = changelog_path.read_text(encoding="utf-8")
    for line in _visible_changelog_lines(content):
        if line.startswith("## "):
            return line
    return ""
