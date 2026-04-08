"""Check that blueprint descriptors stay synchronized with mirrored tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import devcovenant.core.test_blueprints as test_blueprint_service
from devcovenant.core.policy_contract import (
    CheckContext,
    PolicyCheck,
    Violation,
)


@dataclass(frozen=True)
class _BlueprintTarget:
    """One blueprint tree and its materialized test mirror."""

    label: str
    blueprint_path: Path
    test_root: Path


def _normalize_mirror_roots(raw_value: object) -> list[tuple[str, str]]:
    """Parse mirror-root metadata into source and test-root pairs."""
    if raw_value is None:
        return []
    entries: list[str]
    if isinstance(raw_value, str):
        entries = [raw_value]
    elif isinstance(raw_value, list):
        entries = [str(entry).strip() for entry in raw_value]
    else:
        entries = [str(raw_value).strip()]

    rules: list[tuple[str, str]] = []
    for raw_entry in entries:
        token = raw_entry.strip()
        if not token:
            continue
        if "=>" in token:
            source, target = token.split("=>", 1)
        elif ":" in token:
            source, target = token.split(":", 1)
        else:
            continue
        source_prefix = source.strip().replace("\\", "/").strip("/")
        target_prefix = target.strip().replace("\\", "/").strip("/")
        if not source_prefix or not target_prefix:
            continue
        rules.append((source_prefix, target_prefix))
    return rules


def _normalize_blueprint_directories(raw_value: object) -> list[str]:
    """Parse blueprint-directory metadata into relative path strings."""
    if raw_value is None:
        return []
    entries: list[str]
    if isinstance(raw_value, str):
        entries = [raw_value]
    elif isinstance(raw_value, list):
        entries = [str(entry).strip() for entry in raw_value]
    else:
        entries = [str(raw_value).strip()]

    directories: list[str] = []
    for raw_entry in entries:
        token = raw_entry.strip().replace("\\", "/").strip("/")
        if token:
            directories.append(token)
    return directories


def _normalize_blueprint_name(raw_value: object) -> str:
    """Return one canonical test-blueprint filename from metadata."""
    token = str(raw_value or "").strip().replace("\\", "/").strip("/")
    if not token:
        raise ValueError(
            "Policy metadata must define `blueprint_name` for blueprint "
            "sync."
        )
    return token


class BuiltinTestBlueprintSyncCheck(PolicyCheck):
    """Policy that keeps blueprint metadata and mirrored tests in sync."""

    def _targets(self, repo_root: Path) -> list[_BlueprintTarget]:
        """Return metadata-driven blueprint and mirror targets."""
        mirror_roots = _normalize_mirror_roots(
            self.get_option("mirror_roots", [])
        )
        blueprint_directories = _normalize_blueprint_directories(
            self.get_option("blueprint_directories", [])
        )
        if not mirror_roots:
            raise ValueError(
                "Policy metadata must define `mirror_roots` for blueprint "
                "sync."
            )
        if not blueprint_directories:
            raise ValueError(
                "Policy metadata must define `blueprint_directories` for "
                "blueprint sync."
            )
        blueprint_name = _normalize_blueprint_name(
            self.get_option("blueprint_name", "")
        )
        targets: list[_BlueprintTarget] = []
        for source_prefix, tests_prefix in mirror_roots:
            for relative_dir in blueprint_directories:
                source_root = repo_root / source_prefix / relative_dir
                if not source_root.exists():
                    continue
                targets.append(
                    _BlueprintTarget(
                        label=f"{source_prefix}/{relative_dir}",
                        blueprint_path=source_root / blueprint_name,
                        test_root=repo_root / tests_prefix / relative_dir,
                    )
                )
        return targets

    def check(self, context: CheckContext):
        """Return one violation per blueprint/test-tree mismatch."""
        violations: list[Violation] = []
        repo_root = context.repo_root
        for target in self._targets(repo_root):
            if not target.blueprint_path.exists():
                violations.append(
                    Violation(
                        policy_id="builtin-test-blueprint-sync",
                        severity="error",
                        file_path=target.blueprint_path,
                        message=(
                            "Missing test blueprint descriptor for "
                            f"`{target.label}`."
                        ),
                        suggestion=(
                            "Generate `test_blueprints.yaml` from the checked-"
                            "in test tree and refresh."
                        ),
                        can_auto_fix=False,
                    )
                )
                continue

            blueprints = test_blueprint_service.load_test_blueprints_yaml(
                target.blueprint_path
            )
            issues = test_blueprint_service.compare_test_tree_to_blueprints(
                target.test_root,
                blueprints,
            )

            for issue in issues:
                if issue.issue_type == "missing_file":
                    message = (
                        f"Blueprint sync for `{target.label}` is missing "
                        f"`{issue.path}`."
                    )
                elif issue.issue_type == "extra_file":
                    message = (
                        f"Blueprint sync for `{target.label}` does not "
                        f"describe `{issue.path}`."
                    )
                else:
                    message = (
                        f"Blueprint sync for `{target.label}` is out of "
                        f"sync at `{issue.path}`."
                    )
                violations.append(
                    Violation(
                        policy_id="builtin-test-blueprint-sync",
                        severity="error",
                        file_path=target.blueprint_path,
                        message=message,
                        suggestion=(
                            "Regenerate the descriptor blueprint from the "
                            "checked-in test tree, then materialize the "
                            "mirrored tests again with `devcovenant custom "
                            "--do` if this is a shadow copy."
                        ),
                        can_auto_fix=False,
                    )
                )
        return violations
