"""
Policy: Managed Document Assets

Ensure managed documents and their global-asset descriptors stay
synchronized.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.services import managed_docs as managed_docs_service
from devcovenant.core.services import (
    project_governance as project_governance_service,
)

ProjectGovernanceState = project_governance_service.ProjectGovernanceState


class ManagedDocAssetsCheck(PolicyCheck):
    """Verify managed docs and their descriptors remain synchronized."""

    policy_id = "managed-doc-assets"
    version = "0.2.0"

    _DOC_ID_LABEL = managed_docs_service.DOC_ID_LABEL
    _DOC_TYPE_LABEL = managed_docs_service.DOC_TYPE_LABEL
    _PROJECT_VERSION_LABEL = managed_docs_service.PROJECT_VERSION_LABEL
    _PROJECT_STAGE_LABEL = managed_docs_service.PROJECT_STAGE_LABEL
    _MAINTENANCE_STANCE_LABEL = managed_docs_service.MAINTENANCE_STANCE_LABEL
    _COMPATIBILITY_POLICY_LABEL = (
        managed_docs_service.COMPATIBILITY_POLICY_LABEL
    )
    _VERSIONING_MODE_LABEL = managed_docs_service.VERSIONING_MODE_LABEL
    _PROJECT_CODENAME_LABEL = managed_docs_service.PROJECT_CODENAME_LABEL
    _BUILD_IDENTITY_LABEL = managed_docs_service.BUILD_IDENTITY_LABEL
    _LAST_UPDATED_LABEL = managed_docs_service.LAST_UPDATED_LABEL
    _DEVCOV_VERSION_LABEL = managed_docs_service.DEVCOV_VERSION_LABEL
    _PRESERVE_BEGIN = managed_docs_service.USER_PRESERVE_BEGIN
    _PRESERVE_END = managed_docs_service.USER_PRESERVE_END

    _DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

    def __init__(self) -> None:
        """Initialize descriptor-doc pairs covered by this policy."""
        super().__init__()

    def check(self, context: CheckContext) -> List[Violation]:
        """Inspect docs and descriptors to ensure synchronization."""
        violations: List[Violation] = []
        repo_root = context.repo_root
        try:
            project_governance_state = (
                project_governance_service.resolve_runtime_state(
                    repo_root,
                    config_payload=context.config,
                )
            )
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=str(error),
                )
            ]

        for entry in managed_docs_service.authoritative_managed_doc_entries(
            repo_root,
            config_payload=context.config,
        ):
            doc_path = repo_root / entry["doc"]
            descriptor_path = Path(str(entry["descriptor_path"]))

            if not doc_path.is_file():
                violations.append(self._missing_doc_violation(doc_path))
                continue
            if not descriptor_path.is_file():
                violations.append(
                    self._missing_descriptor_violation(
                        entry["doc"],
                        descriptor_path,
                    )
                )
                continue

            try:
                descriptor = self._load_descriptor(
                    descriptor_path,
                    doc_name=entry["doc"],
                )
            except ValueError as error:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=str(error),
                    )
                )
                continue

            doc_info = self._extract_doc_info(doc_path)
            violations.extend(
                self._check_descriptor_sync(
                    descriptor=descriptor,
                    descriptor_path=descriptor_path,
                    doc_info=doc_info,
                    doc_name=entry["doc"],
                    project_governance_state=project_governance_state,
                )
            )

        return violations

    def _load_descriptor(
        self,
        path: Path,
        *,
        doc_name: str,
    ) -> Dict[str, object]:
        """Parse one descriptor document."""
        return managed_docs_service.load_managed_doc_descriptor(
            path,
            doc_name=doc_name,
        )

    def _check_descriptor_sync(
        self,
        *,
        descriptor: Dict[str, object],
        descriptor_path: Path,
        doc_info: Dict[str, object],
        doc_name: str,
        project_governance_state: ProjectGovernanceState,
    ) -> List[Violation]:
        """Build violations for one descriptor-doc pair."""
        violations: List[Violation] = []

        doc_id = str(descriptor.get("doc_id", "")).strip()
        doc_type = str(descriptor.get("doc_type", "")).strip()
        title = project_governance_service.render_identity_placeholders(
            str(descriptor.get("title", "")),
            project_governance_state,
        ).strip()

        if title and title != str(doc_info["title"]):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"Descriptor title for {doc_name} is `{title}` but "
                        f"document header reports `{doc_info['title']}`."
                    ),
                )
            )
        if doc_id and doc_id != str(doc_info["doc_id"]):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"Descriptor doc_id for {doc_name} is `{doc_id}` but "
                        f"document reports `{doc_info['doc_id']}`."
                    ),
                )
            )
        if doc_type and doc_type != str(doc_info["doc_type"]):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"Descriptor doc_type for {doc_name} is `{doc_type}` "
                        f"but document reports `{doc_info['doc_type']}`."
                    ),
                )
            )

        header_map = doc_info["header_map"]
        for descriptor_key, label in (
            ("project_version", self._PROJECT_VERSION_LABEL),
            ("last_updated", self._LAST_UPDATED_LABEL),
            ("devcovenant_version", self._DEVCOV_VERSION_LABEL),
        ):
            required = bool(descriptor.get(descriptor_key, False))
            present = label in header_map
            if required and not present:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            f"{doc_name} is missing required header "
                            f"`{label}` from descriptor key "
                            f"`{descriptor_key}`."
                        ),
                    )
                )
            if not required and present:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            f"{doc_name} contains header `{label}` but "
                            f"descriptor key `{descriptor_key}` is false."
                        ),
                    )
                )

        governance_headers_required = (
            bool(descriptor.get("project_governance_headers", False))
            and project_governance_state.enabled
        )
        for label in self._project_governance_labels(project_governance_state):
            present = label in header_map
            if governance_headers_required and not present:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            f"{doc_name} is missing required header "
                            f"`{label}` from descriptor key "
                            "`project_governance_headers`."
                        ),
                    )
                )
            if not governance_headers_required and present:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            f"{doc_name} contains header `{label}` but "
                            "`project_governance_headers` is inactive."
                        ),
                    )
                )

        last_updated_value = str(header_map.get(self._LAST_UPDATED_LABEL, ""))
        if last_updated_value and not self._DATE_RE.search(last_updated_value):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"{doc_name} Last Updated header is missing an "
                        "ISO date (YYYY-MM-DD)."
                    ),
                )
            )

        if self._descriptor_contains_generated_headers(descriptor):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        "Descriptor managed_block must not duplicate "
                        "generated header labels."
                    ),
                )
            )

        expected_managed = self._expected_managed_block(descriptor)
        actual_managed = (
            str(doc_info["managed_block"])
            if doc_info["has_managed_block"]
            else ""
        )
        if expected_managed != actual_managed:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"Managed block for {doc_name} no longer matches its "
                        "descriptor."
                    ),
                )
            )

        governance_section_required = doc_name == "AGENTS.md"
        actual_governance_section = ""
        managed_blocks = doc_info.get("managed_blocks", [])
        if isinstance(managed_blocks, list) and len(managed_blocks) > 1:
            actual_governance_section = str(managed_blocks[1]).strip("\n")
        expected_governance_section = ""
        if governance_section_required:
            expected_governance_section = (
                self._expected_project_governance_section(
                    project_governance_state,
                    str(header_map.get(self._PROJECT_VERSION_LABEL, "")),
                )
            )
        if expected_governance_section != actual_governance_section:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=descriptor_path,
                    message=(
                        f"Project-governance section for {doc_name} no "
                        "longer matches its rendered contract."
                    ),
                )
            )

        return violations

    def _missing_doc_violation(self, doc_path: Path) -> Violation:
        """Report when a managed document disappears."""
        return Violation(
            policy_id=self.policy_id,
            severity="error",
            file_path=doc_path,
            message=f"Managed document {doc_path.name} is missing.",
        )

    def _missing_descriptor_violation(
        self,
        doc_name: str,
        descriptor_path: Path,
    ) -> Violation:
        """Report when a descriptor is absent."""
        descriptor_rel = descriptor_path.relative_to(
            descriptor_path.parent.parent
        )
        return Violation(
            policy_id=self.policy_id,
            severity="error",
            file_path=descriptor_path,
            message=(
                "Descriptor for "
                f"{doc_name} is missing; expected at {descriptor_rel}."
            ),
        )

    def _extract_doc_info(self, doc_path: Path) -> Dict[str, object]:
        """Return generated header fields and managed block text."""
        return managed_docs_service.extract_doc_info(doc_path)

    def _strip_preserve_blocks(self, text: str) -> str:
        """Remove user-preserve blocks from text before comparison."""
        return managed_docs_service.strip_preserve_blocks(text)

    def _expected_managed_block(self, descriptor: Dict[str, object]) -> str:
        """Build managed block payload expected in rendered docs."""
        return managed_docs_service.expected_managed_block(descriptor)

    def _descriptor_contains_generated_headers(
        self,
        descriptor: Dict[str, object],
    ) -> bool:
        """Return True when managed_block duplicates header labels."""
        return managed_docs_service.descriptor_contains_generated_headers(
            descriptor
        )

    def _project_governance_labels(
        self,
        state: ProjectGovernanceState,
    ) -> list[str]:
        """Return expected header labels for project-governance."""
        return managed_docs_service.project_governance_labels(state)

    def _expected_project_governance_section(
        self,
        state: ProjectGovernanceState,
        project_version: str,
    ) -> str:
        """Return expected rendered project-governance section text."""
        try:
            lines = state.section_lines(project_version)
        except ValueError:
            return ""
        return "\n".join(lines).strip("\n")
