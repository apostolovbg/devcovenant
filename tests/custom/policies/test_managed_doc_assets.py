"""Tests for the managed-doc-assets policy."""

from pathlib import Path

import yaml

from devcovenant.core.base import CheckContext
from devcovenant.custom.policies.managed_doc_assets.managed_doc_assets import (
    ManagedDocAssetsCheck,
)


def _write_doc(tmp_path: Path, name: str) -> Path:
    """Create a minimal managed document for tests."""
    doc_path = tmp_path / name
    doc_path.write_text(
        "\n".join(
            [
                "# Title",
                "**Last Updated:** 2026-01-23",
                "**Version:** 0.2.6",
                "",
                "<!-- DEVCOV:BEGIN -->",
                "**Doc ID:** doc",
                "**Doc Type:** custom",
                "**Managed By:** DevCovenant",
                "",
                "Note line",
                "<!-- DEVCOV:END -->",
            ]
        )
    )
    return doc_path


def _write_descriptor(
    assets_dir: Path, name: str, descriptor_data: dict[str, object]
) -> Path:
    """Record YAML descriptors for the managed docs."""

    assets_dir.mkdir(parents=True, exist_ok=True)
    path = assets_dir / f"{name}.yaml"
    path.write_text(yaml.safe_dump(descriptor_data, sort_keys=False))
    return path


def test_managed_doc_assets_passes_when_descriptors_match(
    tmp_path: Path,
) -> None:
    """Pass when descriptors mirror the managed documents."""

    repo_root = tmp_path
    doc_path = _write_doc(repo_root, "AGENTS.md")
    policy = ManagedDocAssetsCheck()
    policy.managed_docs = [{"doc": "AGENTS.md", "descriptor": "AGENTS.yaml"}]
    context = CheckContext(repo_root=repo_root)

    doc_info = policy._extract_doc_info(doc_path)
    assets_dir = (
        repo_root / "devcovenant" / "core" / "profiles" / "global" / "assets"
    )
    _write_descriptor(
        assets_dir,
        "AGENTS",
        {
            "doc_id": doc_info["doc_id"],
            "doc_type": doc_info["doc_type"],
            "managed_by": doc_info["managed_by"],
            "header_lines": doc_info["header_lines"],
            "managed_block": doc_info["managed_block"],
        },
    )

    violations = policy.check(context)
    assert not violations


def test_managed_doc_assets_detects_descriptor_drift(tmp_path: Path) -> None:
    """Detect and surface descriptor drift."""

    repo_root = tmp_path
    _write_doc(repo_root, "AGENTS.md")
    policy = ManagedDocAssetsCheck()
    policy.managed_docs = [{"doc": "AGENTS.md", "descriptor": "AGENTS.yaml"}]
    context = CheckContext(repo_root=repo_root)

    assets_dir = (
        repo_root / "devcovenant" / "core" / "profiles" / "global" / "assets"
    )
    _write_descriptor(
        assets_dir,
        "AGENTS",
        {
            "doc_id": "wrong",
            "doc_type": "manual",
            "managed_by": "someone else",
            "header_lines": [
                "# Wrong",
                "**Last Updated:** 1900-01-01",
                "**Version:** 0.0.1",
            ],
            "managed_block": "broken",
        },
    )

    violations = policy.check(context)
    assert len(violations) == 3
