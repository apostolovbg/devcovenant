"""Validate project lifecycle governance and expose runtime state helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping

import yaml

import devcovenant.core.services.metadata as metadata_runtime
from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.services.registry import load_policy_descriptor

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
_LOG_MARKER = "## Log changes here"
_MANAGED_BEGIN = "<!-- DEVCOV:BEGIN -->"
_MANAGED_END = "<!-- DEVCOV:END -->"


@dataclass(frozen=True)
class ProjectGovernanceState:
    """Resolved project-governance state for one repository runtime."""

    enabled: bool
    stage: str = ""
    development_stance: str = ""
    versioning_mode: str = "versioned"
    codename: str = ""
    build_identity: str = ""
    unversioned_label: str = _DEFAULT_UNVERSIONED_LABEL
    unreleased_heading: str = _DEFAULT_UNRELEASED_HEADING

    @property
    def is_unversioned(self) -> bool:
        """Return True when the repository is intentionally unversioned."""
        return self.enabled and self.versioning_mode == "unversioned"

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
        if not self.enabled:
            return []
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

    def agents_header_lines(self) -> list[str]:
        """Return governance header lines for compatibility callers."""
        return self.governance_header_lines()


def resolve_runtime_state(
    repo_root: Path,
    *,
    config_payload: Mapping[str, Any] | None = None,
) -> ProjectGovernanceState:
    """Return resolved project-governance state for one repo runtime."""
    repo_root = Path(repo_root).resolve()
    descriptor = load_policy_descriptor(repo_root, "project-governance")
    if descriptor is None:
        raise ValueError("Missing `project-governance` policy descriptor.")

    payload = _load_runtime_config(repo_root, config_payload)
    metadata_context = metadata_runtime.build_metadata_context_from_payload(
        repo_root,
        payload,
    )
    current_order, current_values = (
        metadata_runtime.descriptor_metadata_order_values(descriptor)
    )
    bundle = metadata_runtime.resolve_policy_metadata_bundle(
        "project-governance",
        current_order,
        current_values,
        descriptor,
        metadata_context,
    )
    checker = ProjectGovernanceCheck()
    config_context = CheckContext(repo_root=repo_root, config=payload)
    checker.set_options(
        bundle.decode_options(),
        config_context.get_policy_config("project-governance"),
    )
    return checker.runtime_state(repo_root)


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
    if state.is_unversioned:
        return [state.unreleased_heading]
    return ["## Version"]


class ProjectGovernanceCheck(PolicyCheck):
    """Validate project lifecycle metadata and unversioned changelog flow."""

    policy_id = "project-governance"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Validate project-governance metadata and changelog mode."""
        repo_root = context.repo_root
        try:
            state = self.runtime_state(repo_root)
        except ValueError as exc:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=str(exc),
                )
            ]

        if not state.enabled:
            return []

        violations: list[Violation] = []
        allowed_stages = self._normalized_list(
            self.get_option("allowed_stages", []),
            default=_DEFAULT_STAGES,
        )
        allowed_stances = self._normalized_list(
            self.get_option("allowed_development_stances", []),
            default=_DEFAULT_DEVELOPMENT_STANCES,
        )
        changelog_rel = Path(
            self.get_option("changelog_file", "CHANGELOG.md") or "CHANGELOG.md"
        )
        changelog_path = repo_root / changelog_rel

        if state.stage not in allowed_stages:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=changelog_path,
                    message=(
                        "`project-governance.stage` must be one of: "
                        + ", ".join(allowed_stages)
                        + "."
                    ),
                )
            )
        if state.development_stance not in allowed_stances:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=changelog_path,
                    message=(
                        "`project-governance.development_stance` must be "
                        "one of: " + ", ".join(allowed_stances) + "."
                    ),
                )
            )
        if state.versioning_mode not in _ALLOWED_VERSIONING_MODES:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=changelog_path,
                    message=(
                        "`project-governance.versioning_mode` must be "
                        "`versioned` or `unversioned`."
                    ),
                )
            )
        if violations:
            return violations

        if not changelog_path.exists():
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=changelog_path,
                    message=(
                        "Configured project-governance changelog file is "
                        "missing."
                    ),
                )
            ]

        if state.is_unversioned:
            top_heading = _top_visible_release_heading(changelog_path)
            if top_heading != state.unreleased_heading:
                return [
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=changelog_path,
                        message=(
                            "Unversioned project-governance requires the "
                            "top changelog heading to be "
                            f"`{state.unreleased_heading}`."
                        ),
                        suggestion=(
                            "Use the unversioned changelog flow with the "
                            "configured unreleased heading."
                        ),
                    )
                ]

        return []

    def runtime_state(self, repo_root: Path) -> ProjectGovernanceState:
        """Return validated runtime state from current policy options."""
        enabled = self._bool_option("enabled")
        if not enabled:
            return ProjectGovernanceState(enabled=False)

        stage = self._required_string("stage")
        development_stance = self._required_string("development_stance")
        versioning_mode = self._required_string("versioning_mode").lower()
        if versioning_mode not in _ALLOWED_VERSIONING_MODES:
            raise ValueError(
                "Configure `project-governance.versioning_mode` as "
                "`versioned` or `unversioned`."
            )
        return ProjectGovernanceState(
            enabled=True,
            stage=stage,
            development_stance=development_stance,
            versioning_mode=versioning_mode,
            codename=self._string_option("codename"),
            build_identity=self._string_option("build_identity"),
            unversioned_label=(
                self._string_option("unversioned_label")
                or _DEFAULT_UNVERSIONED_LABEL
            ),
            unreleased_heading=(
                self._string_option("unreleased_heading")
                or _DEFAULT_UNRELEASED_HEADING
            ),
        )

    def _bool_option(self, key: str) -> bool:
        """Return one metadata option normalized as a boolean flag."""
        raw = self.get_option(key, False)
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def _string_option(self, key: str) -> str:
        """Return one normalized string option."""
        return str(self.get_option(key, "") or "").strip()

    def _required_string(self, key: str) -> str:
        """Return one required string option or raise a clear error."""
        token = self._string_option(key)
        if token:
            return token
        raise ValueError(
            f"Configure `project-governance.{key}` explicitly before "
            "enabling project-governance."
        )

    def _normalized_list(
        self,
        raw: object,
        *,
        default: Iterable[str],
    ) -> list[str]:
        """Return a normalized non-empty string list."""
        if isinstance(raw, str):
            items = [
                entry.strip() for entry in raw.split(",") if entry.strip()
            ]
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
