"""Ensure every metadata file listed in the policy options shares one
version."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from devcovenant.base import CheckContext, PolicyCheck, Violation

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[assignment]

try:
    from semver import VersionInfo
except ImportError:  # pragma: no cover - dependency misconfigured
    VersionInfo = None  # type: ignore[assignment]


_VERSION_PATTERN = re.compile(r"(?P<version>\d+\.\d+\.\d+)")
_README_PATTERN = re.compile(
    r"^\s*\*\*Version:\*\*\s*(?P<version>\d+\.\d+\.\d+)",
    flags=re.MULTILINE,
)


class VersionSyncCheck(PolicyCheck):
    """Ensure every configured surface reports the same SemVer string."""

    policy_id = "version-sync"
    version = "1.3.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check for version synchronization across metadata files."""
        violations: List[Violation] = []

        version_file = context.repo_root / Path(
            self.get_option("version_file", "VERSION")
        )
        changelog_rel = Path(self.get_option("changelog_file", "CHANGELOG.md"))
        changelog_prefix = self.get_option(
            "changelog_header_prefix",
            "## Version",
        )
        changelog_file = context.repo_root / changelog_rel

        raw_readme_paths = self._path_list(
            self.get_option("readme_files", None)
            or self.get_option("readme_file", None)
        )
        raw_pyproject_paths = self._path_list(
            self.get_option("pyproject_files", None)
            or self.get_option("pyproject_file", None)
        )
        raw_license_paths = self._path_list(
            self.get_option("license_files", None)
        )

        readme_paths = [
            self._resolve_path(context.repo_root, path)
            for path in raw_readme_paths
        ]
        pyproject_paths = [
            self._resolve_path(context.repo_root, path)
            for path in raw_pyproject_paths
        ]
        license_paths = [
            self._resolve_path(context.repo_root, path)
            for path in raw_license_paths
        ]
        citation_option = self.get_option("citation_file", "CITATION.cff")
        citation_file = None
        if citation_option and str(citation_option).strip() != "__none__":
            citation_file = self._resolve_path(
                context.repo_root,
                Path(str(citation_option)),
            )

        required_targets = [version_file, changelog_file]
        if citation_file is not None:
            required_targets.append(citation_file)
        required_targets.extend(readme_paths)
        required_targets.extend(pyproject_paths)
        required_targets.extend(license_paths)
        for target in required_targets:
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

        if VersionInfo is None:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=version_file,
                    message=(
                        "SemVer runtime dependency missing; install `semver` "
                        "so version sync can validate the tracked string."
                    ),
                )
            ]

        version = version_file.read_text(encoding="utf-8").strip()
        try:
            current_semver = VersionInfo.parse(version)
        except ValueError:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=version_file,
                    message=(
                        f"Tracked VERSION '{version}' is not valid SemVer; "
                        "use MAJOR.MINOR.PATCH notation."
                    ),
                )
            ]

        # READMEs
        for path in readme_paths:
            readme_version = self._extract_readme_version(path)
            if not readme_version:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message="Missing Version header",
                    )
                )
            elif readme_version != version:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message=(
                            f"Version {readme_version} does not match "
                            f"{version_file.name} ({version})"
                        ),
                    )
                )

        # pyproject.toml files
        for path in pyproject_paths:
            try:
                py_version = self._read_pyproject_version(path)
            except (OSError, tomllib.TOMLDecodeError) as exc:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message=f"Cannot read pyproject.toml: {exc}",
                    )
                )
                continue

            if not py_version:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message="pyproject.toml lacks project.version",
                    )
                )
            elif py_version != version:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message=(
                            f"pyproject.toml version {py_version} does not "
                            f"match {version_file.name} ({version})"
                        ),
                    )
                )

        # CITATION.cff
        if citation_file is not None:
            try:
                citation_text = citation_file.read_text(encoding="utf-8")
            except OSError as exc:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=citation_file,
                        message=f"Cannot read CITATION.cff: {exc}",
                    )
                )
            else:
                citation_regex = r"version:\s*\"(?P<version>\d+\.\d+\.\d+)\""
                citation_pattern = re.compile(citation_regex)
                citation_matches = citation_pattern.findall(citation_text)
                if len(citation_matches) < 2:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=citation_file,
                            message=(
                                "Must declare project and preferred-citation "
                                "versions"
                            ),
                        )
                    )
                else:
                    unique_versions = set(citation_matches)
                    if len(unique_versions) != 1 or (
                        version not in unique_versions
                    ):
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity="error",
                                file_path=citation_file,
                                message=(
                                    f"Versions {unique_versions} out of sync "
                                    f"with {version_file.name} ({version})"
                                ),
                            )
                        )

        # License files
        for path in license_paths:
            try:
                contents = path.read_text(encoding="utf-8")
            except OSError as exc:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message=f"Cannot read license file: {exc}",
                    )
                )
                continue
            match = _VERSION_PATTERN.search(contents)
            if not match:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message="License file missing project version",
                    )
                )
            elif match.group("version") != version:
                found = match.group("version")
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=path,
                        message=(
                            f"License file version {found} does not match "
                            f"{version_file.name} ({version})"
                        ),
                    )
                )

        # Changelog header
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
                str(changelog_prefix),
            )
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
            elif latest != version:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=changelog_file,
                        message=(
                            f"Changelog version {latest} does not match "
                            f"{version_file.name} ({version})"
                        ),
                    )
                )

        # Prevent runtime code from hard-coding the suite version.
        runtime_hits: List[Path] = []
        runtime_entrypoints = self._normalize_list(
            self.get_option("runtime_entrypoints", [])
        )
        runtime_roots = self._normalize_list(
            self.get_option("runtime_roots", [])
        )

        runtime_files = self._runtime_python_files(
            context.repo_root,
            runtime_entrypoints,
            runtime_roots,
        )
        for runtime_file in runtime_files:
            try:
                contents = runtime_file.read_text(encoding="utf-8")
            except OSError as exc:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=runtime_file,
                        message=f"Cannot read runtime file: {exc}",
                    )
                )
                continue

            if version in contents:
                runtime_hits.append(runtime_file)

        for runtime_file in runtime_hits:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=runtime_file,
                    message=(
                        f"Hard-coded suite version {version}; import the "
                        "shared version helper instead of embedding literals."
                    ),
                )
            )

        previous_version = self._previous_version(
            context.repo_root,
            str(version_file.relative_to(context.repo_root)),
        )
        if previous_version and previous_version != version:
            try:
                previous_semver = VersionInfo.parse(previous_version)
            except ValueError:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=version_file,
                        message=(
                            "Previous version recorded in Git is not valid "
                            f"SemVer; update {version_file.name} before "
                            "bumping again."
                        ),
                    )
                )
            else:
                if current_semver <= previous_semver:
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=version_file,
                            message=(
                                "Version must advance beyond "
                                f"{previous_version}; {version} is not a "
                                "forward-moving SemVer bump."
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
        return [entry for entry in candidates if entry and entry != "__none__"]

    def _resolve_path(self, repo_root: Path, path: Path) -> Path:
        """Return an absolute path anchored to the repository root."""
        if path.is_absolute():
            return path
        return repo_root / path

    def _path_list(self, raw_option: Iterable[str] | str | None) -> List[Path]:
        """Return a list of repository-relative Path objects."""
        paths: List[Path] = []
        for entry in self._normalize_list(raw_option):
            paths.append(Path(entry))
        return paths

    def _extract_readme_version(self, path: Path) -> Optional[str]:
        """Return the version declared in a README file."""
        text = path.read_text(encoding="utf-8")
        match = _README_PATTERN.search(text)
        if match:
            return match.group("version")
        return None

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
                return stripped[len(prefix_text) :].strip()
        return None

    @staticmethod
    def _read_pyproject_version(pyproject_path: Path) -> Optional[str]:
        """Return the project.version from pyproject.toml."""
        raw = pyproject_path.read_text(encoding="utf-8")
        pyproject_data = tomllib.loads(raw)
        project = pyproject_data.get("project")
        if not isinstance(project, dict):
            return None
        return project.get("version")

    def _runtime_python_files(
        self,
        repo_root: Path,
        entrypoints: List[str],
        runtime_roots: List[str],
    ) -> List[Path]:
        """Return Python files that represent runtime entrypoints."""
        runtime_files: List[Path] = []

        for entry in entrypoints:
            entry_path = repo_root / entry
            if entry_path.is_file():
                runtime_files.append(entry_path)

        for folder_name in runtime_roots:
            root = repo_root / folder_name
            if not root.exists():
                continue
            runtime_files.extend(root.rglob("*.py"))

        return runtime_files

    def _previous_version(
        self,
        repo_root: Path,
        version_rel: str,
    ) -> Optional[str]:
        """Return the version string from the previous commit if available."""

        try:
            completed = subprocess.run(
                ["git", "show", f"HEAD:{version_rel}"],
                cwd=repo_root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None
        output = completed.stdout.strip()
        return output or None
