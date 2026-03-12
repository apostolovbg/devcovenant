"""
Policy: Managed Document Assets

Ensure managed-document descriptors in global assets remain the authoritative
source for generated header fields and managed block payloads.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import yaml

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)


class ManagedDocAssetsCheck(PolicyCheck):
    """Verify managed docs and their descriptors remain synchronized."""

    policy_id = "managed-doc-assets"
    version = "0.2.0"

    _DOC_ID_LABEL = "**Doc ID:**"
    _DOC_TYPE_LABEL = "**Doc Type:**"
    _PROJECT_VERSION_LABEL = "**Project Version:**"
    _LAST_UPDATED_LABEL = "**Last Updated:**"
    _DEVCOV_VERSION_LABEL = "**DevCovenant Version:**"
    _PRESERVE_BEGIN = "<!-- DEVCOV-USER-PRESERVE:BEGIN -->"
    _PRESERVE_END = "<!-- DEVCOV-USER-PRESERVE:END -->"

    _DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

    def __init__(self) -> None:
        """Initialize descriptor-doc pairs covered by this policy."""
        super().__init__()
        self.managed_docs = [
            {"doc": "AGENTS.md", "descriptor": "AGENTS.yaml"},
            {"doc": "README.md", "descriptor": "README.yaml"},
            {"doc": "PLAN.md", "descriptor": "PLAN.yaml"},
            {"doc": "SPEC.md", "descriptor": "SPEC.yaml"},
            {"doc": "CHANGELOG.md", "descriptor": "CHANGELOG.yaml"},
            {"doc": "CONTRIBUTING.md", "descriptor": "CONTRIBUTING.yaml"},
        ]

    def check(self, context: CheckContext) -> List[Violation]:
        """Inspect docs and descriptors to ensure authoritative sync."""
        violations: List[Violation] = []
        repo_root = context.repo_root
        assets_dir = self._assets_dir(repo_root)

        for entry in self.managed_docs:
            doc_path = repo_root / entry["doc"]
            descriptor_path = assets_dir / entry["descriptor"]

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

            descriptor = self._load_descriptor(descriptor_path)
            if descriptor is None:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            "Descriptor "
                            f"{descriptor_path} is not a valid YAML document."
                        ),
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
                )
            )

        return violations

    def _assets_dir(self, repo_root: Path) -> Path:
        """Resolve active global assets directory location."""
        builtin_assets_dir = (
            repo_root
            / "devcovenant"
            / "builtin"
            / "profiles"
            / "global"
            / "assets"
        )
        core_assets_dir = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "global"
            / "assets"
        )
        return (
            builtin_assets_dir
            if builtin_assets_dir.exists()
            else core_assets_dir
        )

    def _check_descriptor_sync(
        self,
        *,
        descriptor: Dict[str, object],
        descriptor_path: Path,
        doc_info: Dict[str, object],
        doc_name: str,
    ) -> List[Violation]:
        """Build violations for one descriptor-doc pair."""
        violations: List[Violation] = []

        doc_id = str(descriptor.get("doc_id", "")).strip()
        doc_type = str(descriptor.get("doc_type", "")).strip()
        title = str(descriptor.get("title", "")).strip()

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

    def _load_descriptor(self, path: Path) -> Dict[str, object] | None:
        """Parse one descriptor document."""
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _extract_doc_info(self, doc_path: Path) -> Dict[str, object]:
        """Return generated header fields and managed block text."""
        text = doc_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        header_map: Dict[str, str] = {}
        title = ""
        doc_id = ""
        doc_type = ""

        for line in lines:
            stripped = line.strip()
            if stripped == "<!-- DEVCOV:BEGIN -->":
                break
            if not stripped:
                continue
            if not title and stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
            if stripped.startswith(self._DOC_ID_LABEL):
                doc_id = stripped.split(self._DOC_ID_LABEL, 1)[1].strip()
                continue
            if stripped.startswith(self._DOC_TYPE_LABEL):
                doc_type = stripped.split(self._DOC_TYPE_LABEL, 1)[1].strip()
                continue
            for label in (
                self._PROJECT_VERSION_LABEL,
                self._LAST_UPDATED_LABEL,
                self._DEVCOV_VERSION_LABEL,
            ):
                if stripped.startswith(label):
                    header_map[label] = stripped.split(label, 1)[1].strip()

        managed_block_lines: List[str] = []
        inside = False
        has_managed_block = False
        for line in lines:
            if "<!-- DEVCOV:BEGIN -->" in line:
                inside = True
                has_managed_block = True
                continue
            if "<!-- DEVCOV:END -->" in line:
                break
            if inside:
                managed_block_lines.append(line.rstrip())

        managed_block = self._strip_preserve_blocks(
            "\n".join(managed_block_lines)
        ).strip("\n")

        return {
            "title": title,
            "doc_id": doc_id,
            "doc_type": doc_type,
            "header_map": header_map,
            "managed_block": managed_block,
            "has_managed_block": has_managed_block,
        }

    def _strip_preserve_blocks(self, text: str) -> str:
        """Remove user-preserve blocks from text before comparison."""
        cleaned: list[str] = []
        inside = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == self._PRESERVE_BEGIN:
                inside = True
                continue
            if stripped == self._PRESERVE_END:
                inside = False
                continue
            if not inside:
                cleaned.append(line)
        return "\n".join(cleaned)

    def _expected_managed_block(self, descriptor: Dict[str, object]) -> str:
        """Build managed block payload expected in rendered docs."""
        body = str(descriptor.get("managed_block", ""))
        lines: list[str] = []
        for raw_line in body.splitlines():
            stripped = raw_line.strip()
            if stripped in {"<!-- DEVCOV:BEGIN -->", "<!-- DEVCOV:END -->"}:
                continue
            lines.append(raw_line.rstrip())
        return "\n".join(lines).strip("\n")

    def _descriptor_contains_generated_headers(
        self,
        descriptor: Dict[str, object],
    ) -> bool:
        """Return True when managed_block duplicates header labels."""
        body = str(descriptor.get("managed_block", ""))
        for line in body.splitlines():
            stripped = line.strip()
            for label in (
                self._DOC_ID_LABEL,
                self._DOC_TYPE_LABEL,
                self._PROJECT_VERSION_LABEL,
                self._LAST_UPDATED_LABEL,
                self._DEVCOV_VERSION_LABEL,
            ):
                if stripped.startswith(label):
                    return True
        return False
