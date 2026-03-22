"""DevCovenant policy: Keep dependency listings and license docs in sync."""

import fnmatch
import importlib.metadata as importlib_metadata
import re
from pathlib import Path
from typing import Iterable, List

try:  # pragma: no cover - Python 3.11+ path in managed env.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback path.
    tomllib = None

from packaging.requirements import Requirement

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)

LICENSES_README_NAME = "README.md"
LICENSE_INVENTORY_HEADING = "## Dependency License Inventory"
CANONICAL_DEPENDENCY_ROLES = (
    "intent",
    "resolved",
    "package_manifest",
)
RUNTIME_ACTION_REFRESH_LOCKS = "refresh-locks-and-licenses"
_PROJECT_DEPENDENCIES_RE = re.compile(
    r"^\s*dependencies\s*=\s*\[(?P<rest>.*)$"
)
_PYTHON_LOCK_PIN_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^\s;\\]+)"
)
_DEPENDENCY_INVENTORY_RE = re.compile(
    r"^-\s+`(?P<name>[^`]+)`:\s+`(?P<path>[^`]+)`\s*$"
)
_LICENSE_NAME_RE = re.compile(
    r"^(license|licence|copying|notice)([.-]|$)",
    re.IGNORECASE,
)


def _normalize_list(value: object) -> list[str]:
    """Normalize metadata option values into non-empty string tokens."""
    if value is None:
        return []
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = [str(entry) for entry in value]
    else:
        raw = [str(value)]
    normalized = [entry.strip() for entry in raw]
    return [entry for entry in normalized if entry]


def _normalized_rel(path_text: str) -> str:
    """Normalize relative path tokens to forward-slash form."""
    return path_text.replace("\\", "/").strip()


def _validate_repo_relative_target(
    *,
    repo_root: Path,
    raw_value: str,
    label: str,
) -> Path:
    """Return validated absolute path for one repo-relative metadata target."""
    token = str(raw_value or "").strip()
    if not token:
        raise ValueError(
            f"dependency-license-sync metadata is missing `{label}`."
        )
    relative = Path(token)
    if relative.is_absolute():
        raise ValueError(
            f"dependency-license-sync `{label}` must be repo-relative."
        )
    repo_root_resolved = repo_root.resolve()
    absolute = (repo_root / relative).resolve()
    try:
        absolute.relative_to(repo_root_resolved)
    except ValueError as error:
        raise ValueError(
            "dependency-license-sync metadata path must stay inside the "
            f"repository: `{label}` = `{token}`."
        ) from error
    return absolute


def _resolve_artifact_targets(
    *,
    repo_root: Path,
    third_party_file: str,
    licenses_dir: str,
) -> tuple[Path, Path]:
    """Resolve and validate report and license-directory metadata targets."""
    report_path = _validate_repo_relative_target(
        repo_root=repo_root,
        raw_value=third_party_file,
        label="third_party_file",
    )
    licenses_path = _validate_repo_relative_target(
        repo_root=repo_root,
        raw_value=licenses_dir,
        label="licenses_dir",
    )
    return report_path, licenses_path


def _relative_posix(path: Path, repo_root: Path) -> str | None:
    """Return repository-relative POSIX path for a changed file."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return None


def _matches_dependency(
    rel_path: str,
    *,
    dependency_files: list[str],
    dependency_globs: list[str],
    dependency_dirs: list[str],
) -> bool:
    """Return True when a path matches dependency selector metadata."""
    rel_name = Path(rel_path).name
    for token in dependency_files:
        normalized = _normalized_rel(token)
        if not normalized:
            continue
        if "/" in normalized:
            if rel_path == normalized:
                return True
            continue
        if rel_name == normalized:
            return True

    for token in dependency_globs:
        normalized = _normalized_rel(token)
        if normalized and fnmatch.fnmatch(rel_path, normalized):
            return True

    for token in dependency_dirs:
        normalized = _normalized_rel(token).strip("/")
        if not normalized:
            continue
        if rel_path == normalized or rel_path.startswith(f"{normalized}/"):
            return True

    return False


def _normalize_dependency_roles(raw: object) -> list[str]:
    """Normalize configured dependency roles."""
    tokens = _normalize_list(raw)
    if not tokens:
        return list(CANONICAL_DEPENDENCY_ROLES)
    normalized = [token.lower() for token in tokens]
    if len(set(normalized)) != len(normalized):
        raise ValueError(
            "dependency-license-sync `dependency_roles` contains duplicates."
        )
    unknown = [
        token
        for token in normalized
        if token not in CANONICAL_DEPENDENCY_ROLES
    ]
    if unknown:
        listed = ", ".join(sorted(unknown))
        raise ValueError(
            "dependency-license-sync `dependency_roles` contains unsupported "
            f"roles: {listed}."
        )
    return normalized


def resolve_dependency_roles(raw: object) -> list[str]:
    """Public helper for validating dependency role metadata."""
    return _normalize_dependency_roles(raw)


def parse_role_selector_entries(
    *,
    entries: list[str],
    allowed_roles: list[str],
    metadata_key: str,
) -> list[tuple[str, str]]:
    """
    Parse `role=>selector` entries and validate declared roles.
    """
    pairs: list[tuple[str, str]] = []
    for entry in entries:
        if "=>" not in entry:
            raise ValueError(
                "dependency-license-sync role selector entries must use "
                f"`role=>selector` format in `{metadata_key}`."
            )
        role, selector = entry.split("=>", 1)
        role_token = role.strip().lower()
        selector_token = selector.strip()
        if not role_token or not selector_token:
            raise ValueError(
                "dependency-license-sync role selector entries must include "
                f"both role and selector in `{metadata_key}`."
            )
        if role_token not in allowed_roles:
            raise ValueError(
                "dependency-license-sync role selector uses role "
                f"`{role_token}` outside configured `dependency_roles`."
            )
        pairs.append((role_token, selector_token))
    return pairs


def _expand_role_selectors(
    *,
    entries: list[str],
    allowed_roles: list[str],
    metadata_key: str,
) -> list[str]:
    """Expand `role=>selector` entries into selector tokens."""
    return [
        selector
        for _, selector in parse_role_selector_entries(
            entries=entries,
            allowed_roles=allowed_roles,
            metadata_key=metadata_key,
        )
    ]


def _resolve_dependency_selectors(
    policy: PolicyCheck,
) -> tuple[list[str], list[str], list[str]]:
    """
    Resolve flat selectors plus role-based selectors into one selector set.
    """
    files = _normalize_list(policy.get_option("dependency_files", []))
    globs = _normalize_list(policy.get_option("dependency_globs", []))
    dirs = _normalize_list(policy.get_option("dependency_dirs", []))
    roles = _normalize_dependency_roles(
        policy.get_option("dependency_roles", list(CANONICAL_DEPENDENCY_ROLES))
    )

    role_files = _expand_role_selectors(
        entries=_normalize_list(
            policy.get_option("dependency_role_files", [])
        ),
        allowed_roles=roles,
        metadata_key="dependency_role_files",
    )
    role_globs = _expand_role_selectors(
        entries=_normalize_list(
            policy.get_option("dependency_role_globs", [])
        ),
        allowed_roles=roles,
        metadata_key="dependency_role_globs",
    )
    role_dirs = _expand_role_selectors(
        entries=_normalize_list(policy.get_option("dependency_role_dirs", [])),
        allowed_roles=roles,
        metadata_key="dependency_role_dirs",
    )

    return files + role_files, globs + role_globs, dirs + role_dirs


def _render_licenses_readme(third_party_file: str) -> str:
    """Build generic README text for the licenses directory."""
    lines = [
        "# License Assets",
        "",
        "## Table of Contents",
        "- [Overview](#overview)",
        "- [Workflow](#workflow)",
        "- [Update Checklist](#update-checklist)",
        "",
        "## Overview",
        "This directory stores generated third-party license texts and",
        "generated compliance notes for direct repository dependencies.",
        "Keep these files synchronized whenever dependency declarations or",
        "resolved lock versions change. The goal is to preserve a clear audit",
        "trail that maps declared direct dependencies to local license",
        "artifacts without requiring manual reconstruction during release",
        "reviews or legal checks.",
        "",
        "## Workflow",
        f"- Keep `{third_party_file}` synchronized with dependency",
        "  manifest updates.",
        "- Add, remove, or refresh generated license files in this directory",
        "  when dependency versions change.",
        "- Record each changed dependency manifest in the report section so",
        "  coverage checks can verify synchronization.",
        "- Keep the dependency inventory aligned with the actual generated",
        "  license files.",
        "",
        "## Update Checklist",
        "- Verify each direct dependency entry points to a current license",
        "  file.",
        "- Verify generated license files reflect the currently installed",
        "  upstream distribution notices.",
        "- Re-run DevCovenant checks and commit both report and license",
        "  artifact updates together.",
        "",
    ]
    return "\n".join(lines)


def _extract_license_report(text: str, heading: str) -> str:
    """Extract the text inside the License Report section."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start = index
            break

    if start is None:
        return ""

    # Collect lines until the next section header
    section_lines: List[str] = [lines[start]]
    remaining = iter(lines)
    for _ in range(start + 1):
        next(remaining, None)
    for line in remaining:
        stripped = line.strip()
        header_prefix = stripped.startswith("## ")
        header_not_report = not stripped.lower().startswith(heading.lower())
        if header_prefix and header_not_report:
            break
        section_lines.append(line)

    return "\n".join(section_lines)


def _extract_section(text: str, heading: str) -> str:
    """Extract the text inside one markdown section by heading label."""
    return _extract_license_report(text, heading)


def _contains_reference(section: str, needle: str) -> bool:
    """Case-insensitive search inside the license report."""
    return needle.lower() in section.lower()


def _normalize_report_entries(
    changed_dependency_files: Iterable[str],
) -> list[str]:
    """Normalize dependency entries for deterministic report rendering."""
    entries: set[str] = set()
    for entry in changed_dependency_files:
        normalized = _normalized_rel(entry)
        if normalized:
            entries.add(normalized)
    return sorted(entries)


def _render_report_section(
    heading: str,
    changed_dependency_files: Iterable[str],
) -> str:
    """Render deterministic `License Report` section content."""
    lines: List[str] = [heading]
    for dep_file in _normalize_report_entries(changed_dependency_files):
        lines.append(f"- `{dep_file}`")
    return "\n".join(lines)


def _normalize_distribution_name(name: str) -> str:
    """Return the PEP 503-normalized form of a distribution name."""
    return re.sub(r"[-_.]+", "-", str(name or "").strip()).lower()


def _parse_requirement_strings(requirement_lines: Iterable[str]) -> list[str]:
    """Extract dependency names from requirement-style strings."""
    names: list[str] = []
    for raw_line in requirement_lines:
        stripped = str(raw_line).split("#", 1)[0].strip()
        if not stripped or stripped.startswith("-"):
            continue
        requirement = Requirement(stripped)
        names.append(requirement.name)
    return names


def _parse_requirements_in(path: Path) -> list[str]:
    """Return direct dependency names declared in requirements.in."""
    if not path.exists():
        return []
    return _parse_requirement_strings(
        path.read_text(encoding="utf-8").splitlines()
    )


def _fallback_project_dependency_strings(path: Path) -> list[str]:
    """Best-effort fallback for `[project].dependencies` on Python 3.10."""
    strings: list[str] = []
    in_project = False
    collecting = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            if not in_project:
                collecting = False
            continue
        if not in_project:
            continue
        line_to_scan = ""
        if not collecting:
            match = _PROJECT_DEPENDENCIES_RE.match(stripped)
            if match is None:
                continue
            collecting = True
            line_to_scan = str(match.group("rest") or "")
        else:
            line_to_scan = stripped
        for quote in ('"', "'"):
            needle = re.compile(rf"{quote}([^\"']+){quote}")
            for match in needle.finditer(line_to_scan):
                strings.append(str(match.group(1)))
        if "]" in line_to_scan:
            collecting = False
    return strings


def _parse_pyproject_dependencies(path: Path) -> list[str]:
    """Return direct dependency names declared in pyproject metadata."""
    if not path.exists():
        return []
    dependency_strings: list[str] = []
    if tomllib is not None:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        project_block = payload.get("project", {})
        raw_dependencies = project_block.get("dependencies", [])
        if isinstance(raw_dependencies, list):
            dependency_strings = [str(entry) for entry in raw_dependencies]
    if not dependency_strings:
        dependency_strings = _fallback_project_dependency_strings(path)
    return _parse_requirement_strings(dependency_strings)


def _direct_dependency_display_names(repo_root: Path) -> dict[str, str]:
    """Return normalized direct dependency names mapped to display casing."""
    display_names: dict[str, str] = {}
    candidates = []
    candidates.extend(_parse_requirements_in(repo_root / "requirements.in"))
    candidates.extend(
        _parse_pyproject_dependencies(repo_root / "pyproject.toml")
    )
    for name in candidates:
        normalized = _normalize_distribution_name(name)
        if normalized and normalized not in display_names:
            display_names[normalized] = name
    return display_names


def _resolved_python_lock_versions(
    repo_root: Path,
) -> dict[str, tuple[str, str]]:
    """Return normalized lockfile names mapped to display name/version."""
    lock_path = repo_root / "requirements.lock"
    if not lock_path.exists():
        return {}
    resolved: dict[str, tuple[str, str]] = {}
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or raw_line[:1].isspace() or stripped.startswith("#"):
            continue
        match = _PYTHON_LOCK_PIN_RE.match(stripped)
        if match is None:
            continue
        display_name = str(match.group("name"))
        version = str(match.group("version"))
        normalized = _normalize_distribution_name(display_name)
        resolved[normalized] = (display_name, version)
    return resolved


def _find_distribution(name: str):
    """Load installed distribution metadata for one dependency name."""
    candidates = [name]
    normalized = _normalize_distribution_name(name)
    if normalized not in candidates:
        candidates.append(normalized)
    for candidate in candidates:
        try:
            return importlib_metadata.distribution(candidate)
        except importlib_metadata.PackageNotFoundError:
            continue
    raise importlib_metadata.PackageNotFoundError(name)


def _distribution_license_sources(dist) -> list[tuple[str, str]]:
    """Return bundled upstream license texts for one installed distribution."""
    files = dist.files or []
    collected: list[tuple[str, str]] = []
    for entry in sorted(files, key=lambda item: str(item).lower()):
        entry_text = str(entry)
        if (
            ".dist-info/" not in entry_text
            and ".dist-info\\" not in entry_text
        ):
            continue
        name = Path(entry_text).name
        if not _LICENSE_NAME_RE.match(name):
            continue
        located = Path(dist.locate_file(entry))
        if not located.exists() or not located.is_file():
            continue
        collected.append((name, located.read_text(encoding="utf-8")))
    if not collected:
        package_name = dist.metadata.get(
            "Name", dist.metadata.get("Summary", "")
        )
        raise RuntimeError(
            "No upstream license files were found in the installed "
            f"distribution metadata for `{package_name or dist}`."
        )
    return collected


def _render_dependency_license_text(
    *,
    package_name: str,
    version: str,
    sources: list[tuple[str, str]],
) -> str:
    """Render one local aggregate license text for a direct dependency."""
    lines = [
        f"# {package_name} {version}",
        "",
        "This file aggregates the upstream license texts bundled with the",
        f"installed distribution for `{package_name}=={version}`.",
        "",
        "Included upstream files:",
    ]
    for source_name, _ in sources:
        lines.append(f"- {source_name}")
    for source_name, source_text in sources:
        lines.extend(
            [
                "",
                f"===== {source_name} =====",
                "",
                source_text.rstrip(),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _inventory_entry_path(
    licenses_dir_path: Path,
    *,
    package_name: str,
    version: str,
) -> Path:
    """Return the managed local license-text path for one dependency."""
    return licenses_dir_path / f"{package_name}-{version}.txt"


def _build_dependency_inventory(
    repo_root: Path,
    *,
    licenses_dir_path: Path,
) -> list[dict[str, str]]:
    """Resolve direct dependency inventory with generated license targets."""
    direct_display_names = _direct_dependency_display_names(repo_root)
    if not direct_display_names:
        return []
    resolved_versions = _resolved_python_lock_versions(repo_root)
    inventory: list[dict[str, str]] = []
    for normalized_name in sorted(direct_display_names):
        if normalized_name not in resolved_versions:
            continue
        _, version = resolved_versions[normalized_name]
        display_name = direct_display_names[normalized_name]
        try:
            _find_distribution(display_name)
        except importlib_metadata.PackageNotFoundError:
            continue
        inventory.append(
            {
                "normalized_name": normalized_name,
                "package_name": display_name,
                "version": version,
                "relative_path": _inventory_entry_path(
                    licenses_dir_path,
                    package_name=display_name,
                    version=version,
                ).name,
            }
        )
    return inventory


def _render_inventory_section(
    *,
    licenses_dir: str,
    inventory: list[dict[str, str]],
) -> str:
    """Render deterministic dependency inventory section content."""
    lines = [LICENSE_INVENTORY_HEADING]
    for entry in inventory:
        relative_path = _normalized_rel(
            str(Path(licenses_dir) / str(entry["relative_path"]))
        )
        lines.append(
            f"- `{entry['package_name']}=={entry['version']}`: "
            f"`{relative_path}`"
        )
    return "\n".join(lines)


def _inventory_paths_from_report(text: str) -> set[str]:
    """Return repo-relative license artifact paths listed in the inventory."""
    section = _extract_section(text, LICENSE_INVENTORY_HEADING)
    paths: set[str] = set()
    for line in section.splitlines():
        match = _DEPENDENCY_INVENTORY_RE.match(line.strip())
        if match is None:
            continue
        paths.add(_normalized_rel(str(match.group("path"))))
    return paths


def _replace_report_section(
    text: str,
    *,
    heading: str,
    replacement: str,
) -> str:
    """Replace one report section or append it when missing."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start = index
            break

    if start is None:
        if not text.strip():
            return replacement + "\n"
        return text.rstrip() + "\n\n" + replacement + "\n"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## ") and stripped.lower() != heading.lower():
            end = index
            break

    replacement_lines = replacement.splitlines()
    if end < len(lines) and replacement_lines:
        if replacement_lines[-1].strip():
            replacement_lines.append("")
    updated_lines = lines[:start] + replacement_lines + lines[end:]
    return "\n".join(updated_lines).rstrip() + "\n"


def _sync_dependency_license_files(
    *,
    repo_root: Path,
    licenses_dir_path: Path,
    licenses_dir: str,
    inventory: list[dict[str, str]],
    existing_inventory_paths: set[str],
) -> list[Path]:
    """Materialize current dependency license texts and prune stale ones."""
    modified: list[Path] = []
    desired_inventory_paths = {
        _normalized_rel(str(Path(licenses_dir) / entry["relative_path"]))
        for entry in inventory
    }
    for entry in inventory:
        package_name = str(entry["package_name"])
        version = str(entry["version"])
        target_path = licenses_dir_path / str(entry["relative_path"])
        dist = _find_distribution(package_name)
        sources = _distribution_license_sources(dist)
        rendered = _render_dependency_license_text(
            package_name=package_name,
            version=version,
            sources=sources,
        )
        if not target_path.exists() or (
            target_path.read_text(encoding="utf-8") != rendered
        ):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(rendered, encoding="utf-8")
            modified.append(target_path)

    stale_inventory_paths = sorted(
        existing_inventory_paths - desired_inventory_paths
    )
    for relative_path in stale_inventory_paths:
        stale_path = repo_root / relative_path
        if stale_path.exists() and stale_path.is_file():
            stale_path.unlink()
            modified.append(stale_path)
    return modified


def _ensure_licenses_readme(
    *,
    licenses_dir_path: Path,
    third_party_file: str,
) -> Path | None:
    """Ensure licenses/README.md exists with generic, metadata-driven text."""
    readme_path = licenses_dir_path / LICENSES_README_NAME
    desired = _render_licenses_readme(third_party_file)
    if readme_path.exists():
        existing = readme_path.read_text(encoding="utf-8")
        if existing == desired:
            return None
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(desired, encoding="utf-8")
    return readme_path


def refresh_license_artifacts(
    repo_root: Path,
    *,
    changed_dependency_files: Iterable[str],
    third_party_file: str,
    licenses_dir: str,
    report_heading: str,
) -> List[Path]:
    """Refresh configured report file and licenses marker files."""

    modified: List[Path] = []
    third_party_path, licenses_dir_path = _resolve_artifact_targets(
        repo_root=repo_root,
        third_party_file=third_party_file,
        licenses_dir=licenses_dir,
    )
    third_party_rel = third_party_path.relative_to(
        repo_root.resolve()
    ).as_posix()
    if third_party_path.exists():
        existing = third_party_path.read_text(encoding="utf-8")
    else:
        existing = "# Third-Party Licenses\n"

    inventory = _build_dependency_inventory(
        repo_root,
        licenses_dir_path=licenses_dir_path,
    )
    updated_report = existing
    if _normalize_report_entries(changed_dependency_files):
        report_section = _render_report_section(
            report_heading, changed_dependency_files
        )
        updated_report = _replace_report_section(
            updated_report,
            heading=report_heading,
            replacement=report_section,
        )
    existing_inventory_paths = _inventory_paths_from_report(updated_report)
    inventory_section = _render_inventory_section(
        licenses_dir=licenses_dir,
        inventory=inventory,
    )
    updated_report = _replace_report_section(
        updated_report,
        heading=LICENSE_INVENTORY_HEADING,
        replacement=inventory_section,
    )
    if updated_report != existing:
        third_party_path.parent.mkdir(parents=True, exist_ok=True)
        third_party_path.write_text(updated_report, encoding="utf-8")
        modified.append(third_party_path)

    modified.extend(
        _sync_dependency_license_files(
            repo_root=repo_root,
            licenses_dir_path=licenses_dir_path,
            licenses_dir=licenses_dir,
            inventory=inventory,
            existing_inventory_paths=existing_inventory_paths,
        )
    )

    readme_path = _ensure_licenses_readme(
        licenses_dir_path=licenses_dir_path,
        third_party_file=third_party_rel,
    )
    if readme_path is not None:
        modified.append(readme_path)
    return modified


class DependencyLicenseSyncCheck(PolicyCheck):
    """Ensure dependency changes update licenses and the report section."""

    policy_id = "dependency-license-sync"
    version = "1.0.0"

    def run_runtime_action(
        self,
        action: str,
        *,
        repo_root: Path,
        payload: dict[str, object] | None = None,
    ) -> tuple[list[object], list[Path]]:
        """Run policy-owned runtime actions used by command entrypoints."""
        del payload
        if action != RUNTIME_ACTION_REFRESH_LOCKS:
            raise ValueError(
                "Unsupported dependency-license-sync runtime action: "
                f"`{action}`."
            )
        from devcovenant.builtin.policies.dependency_license_sync import (
            dependency_lock_runtime,
        )

        return dependency_lock_runtime.refresh_locks_and_licenses(repo_root)

    def check(self, context: CheckContext):
        """Verify dependency changes match the recorded license summary."""
        files = context.changed_files or []
        if not files:
            return []

        try:
            dependency_files, dependency_globs, dependency_dirs = (
                _resolve_dependency_selectors(self)
            )
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=str(error),
                    can_auto_fix=False,
                )
            ]
        if not (dependency_files or dependency_globs or dependency_dirs):
            return []

        third_party_text = str(self.get_option("third_party_file", "")).strip()
        licenses_dir = str(self.get_option("licenses_dir", "")).strip()
        report_heading = str(self.get_option("report_heading", "")).strip()
        try:
            third_party_path, license_dir_path = _resolve_artifact_targets(
                repo_root=context.repo_root,
                third_party_file=third_party_text,
                licenses_dir=licenses_dir,
            )
        except ValueError as error:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=str(error),
                    can_auto_fix=False,
                )
            ]
        if not report_heading:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=(
                        "dependency-license-sync metadata is missing "
                        "`report_heading`."
                    ),
                    can_auto_fix=False,
                )
            ]
        third_party_rel_text = third_party_path.relative_to(
            context.repo_root.resolve()
        ).as_posix()
        licenses_rel_text = license_dir_path.relative_to(
            context.repo_root.resolve()
        ).as_posix()

        changed_rel_paths: set[str] = set()
        changed_dependency_files = set()
        for path in files:
            rel_path = _relative_posix(path, context.repo_root)
            if rel_path is None:
                continue
            changed_rel_paths.add(rel_path)
            if _matches_dependency(
                rel_path,
                dependency_files=dependency_files,
                dependency_globs=dependency_globs,
                dependency_dirs=dependency_dirs,
            ):
                changed_dependency_files.add(rel_path)
        if not changed_dependency_files:
            return []

        violations = []
        context_payload = {
            "changed_dependency_files": sorted(changed_dependency_files),
            "third_party_file": third_party_rel_text,
            "licenses_dir": licenses_rel_text,
            "report_heading": report_heading,
        }

        if third_party_rel_text not in changed_rel_paths:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=third_party_path,
                    message=(
                        "Dependencies changed without updating "
                        "the license table "
                        f"`{third_party_rel_text}`."
                    ),
                    can_auto_fix=True,
                    context={**context_payload, "issue": "third_party"},
                )
            )

        normalized_licenses_dir = _normalized_rel(licenses_rel_text).strip("/")
        license_dir_touched = any(
            rel == normalized_licenses_dir
            or rel.startswith(f"{normalized_licenses_dir}/")
            for rel in changed_rel_paths
        )

        if not license_dir_touched:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=license_dir_path,
                    message=(
                        "License files under "
                        f"{licenses_rel_text}/ must be refreshed."
                    ),
                    can_auto_fix=True,
                    context={**context_payload, "issue": "licenses_dir"},
                )
            )

        if third_party_path.is_file():
            raw_report = third_party_path.read_text(encoding="utf-8")
            report = _extract_license_report(raw_report, report_heading)
        else:
            report = ""

        if not report:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=third_party_path,
                    message=(
                        f"Add a '{report_heading}' section to "
                        f"`{third_party_rel_text}` that chronicles dependency "
                        "updates."
                    ),
                    can_auto_fix=True,
                    context={**context_payload, "issue": "missing_report"},
                )
            )
        else:
            missing_references = [
                dep_file
                for dep_file in sorted(changed_dependency_files)
                if not _contains_reference(report, dep_file)
            ]
            if missing_references:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=third_party_path,
                        message=(
                            "The license report must mention each changed "
                            "dependency manifest."
                        ),
                        can_auto_fix=True,
                        context={
                            **context_payload,
                            "issue": "missing_reference",
                            "missing_references": missing_references,
                        },
                    )
                )

        return violations
