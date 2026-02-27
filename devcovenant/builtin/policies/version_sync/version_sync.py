"""Ensure role-targeted version surfaces stay synchronized."""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path
from typing import Iterable, List, Optional

import yaml

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[assignment]


_VERSION_PATTERN = re.compile(r"(?P<version>\d+\.\d+\.\d+)")
_STRICT_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_DOC_VERSION_PATTERN = re.compile(
    r"^\s*\*\*Version:\*\*\s*(?P<version>\d+\.\d+\.\d+)",
    flags=re.MULTILINE,
)
_EXTRACTOR_NAMES = {
    "doc_header_version",
    "changelog_header_version",
    "manifest_project_version",
    "semver_token",
}


class VersionSyncCheck(PolicyCheck):
    """Ensure every configured target role reports the same SemVer string."""

    policy_id = "version-sync"
    version = "2.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check for version synchronization across role targets."""
        violations: List[Violation] = []

        version_file = context.repo_root / Path(
            self.get_option("version_file", "VERSION")
        )
        changelog_rel = Path(self.get_option("changelog_file", "CHANGELOG.md"))
        changelog_prefix = str(
            self.get_option("changelog_header_prefix", "## Version")
        )
        changelog_file = context.repo_root / changelog_rel

        try:
            target_roles = self._normalize_roles(
                self._normalize_list(self.get_option("target_roles", []))
            )
            role_extractors = self._resolve_role_extractors(
                roles=target_roles,
                raw_extractors=self._normalize_list(
                    self.get_option("role_extractors", [])
                ),
            )
            targets_by_role = self._resolve_targets_by_role(
                context=context,
                roles=target_roles,
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

        required_targets: set[Path] = {version_file, changelog_file}
        for targets in targets_by_role.values():
            required_targets.update(targets)

        for target in sorted(required_targets):
            if not target.exists():
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=target,
                        message="Required metadata file missing",
                    )
                )
        if violations:
            return violations

        try:
            tracked_version = version_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=version_file,
                    message=f"Cannot read version file: {exc}",
                )
            ]

        if not _STRICT_SEMVER_PATTERN.fullmatch(tracked_version):
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=version_file,
                    message=(
                        f"Tracked VERSION '{tracked_version}' is not valid "
                        "SemVer; use MAJOR.MINOR.PATCH notation."
                    ),
                )
            ]

        changelog_targeted = False
        for role in target_roles:
            extractor_name = role_extractors[role]
            targets = sorted(targets_by_role.get(role, set()))
            if extractor_name == "changelog_header_version":
                if changelog_file in targets:
                    changelog_targeted = True

            for target in targets:
                try:
                    target_version = self._extract_target_version(
                        extractor_name=extractor_name,
                        target=target,
                        changelog_prefix=changelog_prefix,
                    )
                except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=target,
                            message=(
                                "Cannot extract version for role "
                                f"`{role}` using `{extractor_name}`: {exc}"
                            ),
                        )
                    )
                    continue

                if not target_version:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=target,
                            message=(
                                f"Role `{role}` target lacks version via "
                                f"`{extractor_name}`"
                            ),
                        )
                    )
                    continue

                if target_version != tracked_version:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=target,
                            message=(
                                f"Role `{role}` target version "
                                f"{target_version} does not match "
                                f"{version_file.name} ({tracked_version})"
                            ),
                        )
                    )

        try:
            changelog_text = changelog_file.read_text(encoding="utf-8")
        except OSError as exc:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=changelog_file,
                    message=f"Cannot read {changelog_rel.as_posix()}: {exc}",
                )
            )
        else:
            latest = self._latest_changelog_version(
                changelog_text,
                changelog_prefix,
            )
            if not changelog_targeted:
                if not latest:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=changelog_file,
                            message=(
                                f"Missing {changelog_prefix} header in "
                                f"{changelog_rel.as_posix()}"
                            ),
                        )
                    )
                elif latest != tracked_version:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=changelog_file,
                            message=(
                                f"Changelog version {latest} does not match "
                                f"{version_file.name} ({tracked_version})"
                            ),
                        )
                    )
        return violations

    @staticmethod
    def _normalize_list(raw: Iterable[str] | str | None) -> List[str]:
        """Return a list of non-empty strings."""
        if raw is None:
            return []
        if isinstance(raw, str):
            candidates = [entry.strip() for entry in raw.split(",")]
        else:
            candidates = [str(entry).strip() for entry in raw]
        return [entry for entry in candidates if entry]

    def _normalize_roles(self, roles: List[str]) -> List[str]:
        """Validate and normalize configured target roles."""
        normalized = [role.lower() for role in roles if role.strip()]
        if not normalized:
            raise ValueError(
                "version-sync metadata is missing non-empty `target_roles`."
            )
        if len(set(normalized)) != len(normalized):
            raise ValueError(
                "version-sync `target_roles` contains duplicates."
            )
        return normalized

    def _parse_role_selector_entries(
        self,
        *,
        entries: List[str],
        roles: List[str],
        metadata_key: str,
    ) -> List[tuple[str, str]]:
        """Parse `role=>selector` metadata entries."""
        pairs: List[tuple[str, str]] = []
        for entry in entries:
            if "=>" not in entry:
                raise ValueError(
                    "version-sync role selector entries must use "
                    f"`role=>selector` format in `{metadata_key}`."
                )
            role, selector = entry.split("=>", 1)
            role_token = role.strip().lower()
            selector_token = selector.strip()
            if not role_token or not selector_token:
                raise ValueError(
                    "version-sync role selector entries must include both "
                    f"role and selector in `{metadata_key}`."
                )
            if role_token not in roles:
                raise ValueError(
                    "version-sync role selector uses role "
                    f"`{role_token}` outside configured `target_roles`."
                )
            pairs.append((role_token, selector_token))
        return pairs

    def _resolve_role_extractors(
        self,
        *,
        roles: List[str],
        raw_extractors: List[str],
    ) -> dict[str, str]:
        """Resolve role-to-extractor mappings."""
        extractor_pairs = self._parse_role_selector_entries(
            entries=raw_extractors,
            roles=roles,
            metadata_key="role_extractors",
        )
        role_extractors: dict[str, str] = {}
        for role, extractor in extractor_pairs:
            if extractor not in _EXTRACTOR_NAMES:
                raise ValueError(
                    "version-sync `role_extractors` uses unknown extractor "
                    f"`{extractor}`."
                )
            if role in role_extractors:
                raise ValueError(
                    "version-sync `role_extractors` defines duplicate role "
                    f"`{role}`."
                )
            role_extractors[role] = extractor

        missing = [role for role in roles if role not in role_extractors]
        if missing:
            listed = ", ".join(sorted(missing))
            raise ValueError(
                "version-sync `role_extractors` is missing mappings for: "
                f"{listed}."
            )
        return role_extractors

    def _resolve_targets_by_role(
        self,
        *,
        context: CheckContext,
        roles: List[str],
    ) -> dict[str, set[Path]]:
        """Resolve role-target file paths from files/globs/dirs selectors."""
        file_pairs = self._parse_role_selector_entries(
            entries=self._normalize_list(
                self.get_option("target_role_files", [])
            ),
            roles=roles,
            metadata_key="target_role_files",
        )
        glob_pairs = self._parse_role_selector_entries(
            entries=self._normalize_list(
                self.get_option("target_role_globs", [])
            ),
            roles=roles,
            metadata_key="target_role_globs",
        )
        dir_pairs = self._parse_role_selector_entries(
            entries=self._normalize_list(
                self.get_option("target_role_dirs", [])
            ),
            roles=roles,
            metadata_key="target_role_dirs",
        )

        if not (file_pairs or glob_pairs or dir_pairs):
            raise ValueError(
                "version-sync requires role selectors in `target_role_files`, "
                "`target_role_globs`, or `target_role_dirs`."
            )

        role_targets: dict[str, set[Path]] = {role: set() for role in roles}

        for role, selector in file_pairs:
            role_targets[role].add(
                self._resolve_repo_relative_path(
                    repo_root=context.repo_root,
                    raw_value=selector,
                    metadata_key="target_role_files",
                )
            )

        candidate_files = self._candidate_files(context)
        candidate_rows: List[tuple[Path, str]] = []
        for candidate in candidate_files:
            try:
                rel_text = candidate.relative_to(context.repo_root).as_posix()
            except ValueError:
                continue
            candidate_rows.append((candidate, rel_text))

        for role, pattern in glob_pairs:
            for candidate, rel_text in candidate_rows:
                matches = fnmatch.fnmatch(rel_text, pattern)
                nested_matches = pattern.startswith("**/") and fnmatch.fnmatch(
                    rel_text, pattern[3:]
                )
                if matches or nested_matches:
                    role_targets[role].add(candidate)

        for role, prefix in dir_pairs:
            normalized_prefix = prefix.strip().strip("/")
            if not normalized_prefix:
                raise ValueError(
                    "version-sync `target_role_dirs` cannot include empty "
                    "selectors."
                )
            for candidate, rel_text in candidate_rows:
                if rel_text == normalized_prefix or rel_text.startswith(
                    f"{normalized_prefix}/"
                ):
                    role_targets[role].add(candidate)

        for role, targets in role_targets.items():
            if not targets:
                raise ValueError(
                    "version-sync resolved no targets for role "
                    f"`{role}`; adjust role selectors."
                )

        return role_targets

    @staticmethod
    def _candidate_files(context: CheckContext) -> List[Path]:
        """Return candidate files for selector expansion."""
        if context.all_files:
            return sorted(context.all_files)
        return sorted(
            path for path in context.repo_root.rglob("*") if path.is_file()
        )

    @staticmethod
    def _resolve_repo_relative_path(
        *,
        repo_root: Path,
        raw_value: str,
        metadata_key: str,
    ) -> Path:
        """Resolve and validate one repo-relative selector path."""
        token = str(raw_value).strip()
        if not token:
            raise ValueError(
                f"version-sync `{metadata_key}` contains an empty path token."
            )
        selector = Path(token)
        if selector.is_absolute():
            raise ValueError(
                f"version-sync `{metadata_key}` paths must be repo-relative."
            )
        absolute = (repo_root / selector).resolve()
        try:
            absolute.relative_to(repo_root.resolve())
        except ValueError as error:
            raise ValueError(
                "version-sync role selectors must stay inside repository: "
                f"`{metadata_key}` = `{token}`."
            ) from error
        return absolute

    def _extract_target_version(
        self,
        *,
        extractor_name: str,
        target: Path,
        changelog_prefix: str,
    ) -> Optional[str]:
        """Extract one version value using the configured extractor."""
        if extractor_name == "doc_header_version":
            return self._extract_doc_header_version(target)
        if extractor_name == "changelog_header_version":
            return self._extract_changelog_header_version(
                target,
                changelog_prefix,
            )
        if extractor_name == "manifest_project_version":
            return self._extract_manifest_project_version(target)
        if extractor_name == "semver_token":
            return self._extract_semver_token(target)
        raise ValueError(
            f"Unsupported version extractor `{extractor_name}` configured."
        )

    @staticmethod
    def _extract_doc_header_version(path: Path) -> Optional[str]:
        """Extract `**Version:**` header from a document."""
        text = path.read_text(encoding="utf-8")
        match = _DOC_VERSION_PATTERN.search(text)
        if not match:
            return None
        return match.group("version")

    @staticmethod
    def _extract_changelog_header_version(
        path: Path,
        changelog_prefix: str,
    ) -> Optional[str]:
        """Extract latest changelog version after the log marker."""
        text = path.read_text(encoding="utf-8")
        return VersionSyncCheck._latest_changelog_version(
            text,
            changelog_prefix,
        )

    @staticmethod
    def _extract_manifest_project_version(path: Path) -> Optional[str]:
        """Extract manifest version from TOML/JSON/YAML project manifests."""
        suffix = path.suffix.lower()
        if suffix == ".toml":
            return VersionSyncCheck._extract_manifest_version_toml(path)
        if suffix == ".json":
            return VersionSyncCheck._extract_manifest_version_json(path)
        if suffix in {".yaml", ".yml"}:
            return VersionSyncCheck._extract_manifest_version_yaml(path)
        raise ValueError(
            "manifest_project_version supports only TOML/JSON/YAML files; "
            f"got `{path.name}`."
        )

    @staticmethod
    def _extract_manifest_version_toml(path: Path) -> Optional[str]:
        """Extract project version from TOML manifest structures."""
        raw = path.read_text(encoding="utf-8")
        toml_payload = tomllib.loads(raw)

        project = toml_payload.get("project")
        if isinstance(project, dict):
            project_version = project.get("version")
            if isinstance(project_version, str):
                return project_version.strip() or None

        tool = toml_payload.get("tool")
        if isinstance(tool, dict):
            poetry = tool.get("poetry")
            if isinstance(poetry, dict):
                poetry_version = poetry.get("version")
                if isinstance(poetry_version, str):
                    return poetry_version.strip() or None
        return None

    @staticmethod
    def _extract_manifest_version_json(path: Path) -> Optional[str]:
        """Extract version from JSON manifest structures."""
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None

        direct = payload.get("version")
        if isinstance(direct, str):
            return direct.strip() or None

        project = payload.get("project")
        if isinstance(project, dict):
            project_version = project.get("version")
            if isinstance(project_version, str):
                return project_version.strip() or None
        return None

    @staticmethod
    def _extract_manifest_version_yaml(path: Path) -> Optional[str]:
        """Extract version from YAML manifest structures."""
        raw = path.read_text(encoding="utf-8")
        payload = yaml.safe_load(raw)
        if not isinstance(payload, dict):
            return None

        direct = payload.get("version")
        if isinstance(direct, str):
            return direct.strip() or None

        project = payload.get("project")
        if isinstance(project, dict):
            project_version = project.get("version")
            if isinstance(project_version, str):
                return project_version.strip() or None
        return None

    @staticmethod
    def _extract_semver_token(path: Path) -> Optional[str]:
        """Extract first SemVer token from generic text file."""
        text = path.read_text(encoding="utf-8")
        match = _VERSION_PATTERN.search(text)
        if not match:
            return None
        return match.group("version")

    @staticmethod
    def _latest_changelog_version(
        content: str,
        prefix: str,
    ) -> Optional[str]:
        """Return the newest changelog version after the log marker."""
        marker = "## Log changes here"
        lines = content.splitlines()
        start_idx = 0
        for idx, line in enumerate(lines):
            if line.strip() == marker:
                start_idx = idx
                break
        search_space = lines[start_idx:]
        prefix_text = prefix.strip()
        for line in search_space:
            stripped = line.strip()
            if stripped.startswith(prefix_text):
                return stripped[len(prefix_text) :].strip() or None
        return None
