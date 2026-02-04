"""
Policy: Managed Document Assets

Ensure AGENTS.md, README.md, PLAN.md, SPEC.md, CHANGELOG.md, and
CONTRIBUTING.md remain the authoritative sources of their managed-block
descriptors in `devcovenant/core/profiles/global/assets/`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from devcovenant.core.base import CheckContext, PolicyCheck, Violation


class ManagedDocAssetsCheck(PolicyCheck):
    """Verify that every managed document has a matching YAML descriptor."""

    policy_id = "managed-doc-assets"
    version = "0.1.0"

    def __init__(self) -> None:
        """Initialize the managed document descriptor list."""
        super().__init__()
        self.managed_docs = [
            {"doc": "AGENTS.md", "descriptor": "AGENTS.yaml"},
            {"doc": "README.md", "descriptor": "README.yaml"},
            {"doc": "PLAN.md", "descriptor": "PLAN.yaml"},
            {"doc": "SPEC.md", "descriptor": "SPEC.yaml"},
            {"doc": "CHANGELOG.md", "descriptor": "CHANGELOG.yaml"},
            {"doc": "CONTRIBUTING.md", "descriptor": "CONTRIBUTING.yaml"},
            {"doc": "LICENSE", "descriptor": "LICENSE.yaml"},
        ]

    def check(self, context: CheckContext) -> List[Violation]:
        """Inspect docs and descriptors to ensure they stay synchronized."""
        violations: List[Violation] = []
        repo_root = context.repo_root
        assets_dir = (
            repo_root
            / "devcovenant"
            / "core"
            / "profiles"
            / "global"
            / "assets"
        )

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

            if descriptor.get("doc_id", "") != doc_info["doc_id"]:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            "Descriptor for "
                            f"{entry['doc']} references doc_id="
                            f"{descriptor.get('doc_id', '<missing>')} "
                            f"but the document reports {doc_info['doc_id']}."
                        ),
                    )
                )

            if descriptor.get("header_lines", []) != doc_info["header_lines"]:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            "Header lines in "
                            f"{entry['doc']} diverge from its descriptor."
                        ),
                    )
                )

            if (
                descriptor.get("managed_block", "")
                != doc_info["managed_block"]
            ):
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=descriptor_path,
                        message=(
                            "Managed block for "
                            f"{entry['doc']} no longer matches "
                            f"{entry['descriptor']}."
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

    def _load_descriptor(self, path: Path) -> Dict[str, str] | None:
        """Parse the YAML descriptor for a managed document."""
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return None

    def _extract_doc_info(self, doc_path: Path) -> Dict[str, str | List[str]]:
        """Return the header metadata and managed block text for a document."""
        text = doc_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        header_lines = []
        for line in lines:
            if not line.strip():
                continue
            header_lines.append(line.rstrip())
            if len(header_lines) == 3:
                break

        managed_block_lines: List[str] = []
        metadata: Dict[str, str] = {
            "doc_id": "",
            "doc_type": "",
            "managed_by": "",
        }
        inside = False
        for line in lines:
            if "<!-- DEVCOV:BEGIN -->" in line:
                inside = True
                continue
            if "<!-- DEVCOV:END -->" in line:
                break
            if inside:
                stripped = line.rstrip()
                managed_block_lines.append(stripped)
                if stripped.startswith("**Doc ID:**"):
                    metadata["doc_id"] = stripped.split("**Doc ID:**", 1)[
                        1
                    ].strip()
                elif stripped.startswith("**Doc Type:**"):
                    metadata["doc_type"] = stripped.split("**Doc Type:**", 1)[
                        1
                    ].strip()
                elif stripped.startswith("**Managed By:**"):
                    metadata["managed_by"] = stripped.split(
                        "**Managed By:**", 1
                    )[1].strip()

        managed_block = "\n".join(managed_block_lines).rstrip()
        if not managed_block_lines:
            managed_block = text.rstrip()
        if not metadata["doc_id"]:
            metadata["doc_id"] = doc_path.stem.upper()

        return {
            "doc_id": metadata["doc_id"],
            "doc_type": metadata["doc_type"],
            "managed_by": metadata["managed_by"],
            "header_lines": header_lines,
            "managed_block": managed_block,
        }
