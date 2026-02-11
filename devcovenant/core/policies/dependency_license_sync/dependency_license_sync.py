"""DevCovenant policy: Keep dependency listings and license docs in sync."""

import datetime as dt
from pathlib import Path
from typing import Iterable, List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation

THIRD_PARTY = Path("THIRD_PARTY_LICENSES.md")
LICENSES_DIR = "licenses"
LICENSE_REPORT_HEADING = "## License Report"


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


def _contains_reference(section: str, needle: str) -> bool:
    """Case-insensitive search inside the license report."""
    return needle.lower() in section.lower()


def _ensure_report_heading(text: str, heading: str) -> str:
    """Ensure the target heading exists in the report body."""

    if _extract_license_report(text, heading):
        return text
    if not text.endswith("\n"):
        text += "\n"
    return text.rstrip() + f"\n\n{heading}\n"


def _append_report_entries(
    text: str,
    heading: str,
    changed_dependency_files: Iterable[str],
) -> str:
    """Append missing dependency references to the report section."""

    section = _extract_license_report(text, heading)
    today = dt.date.today().isoformat()
    additions: List[str] = []
    for dep_file in sorted({entry for entry in changed_dependency_files}):
        if section and _contains_reference(section, dep_file):
            continue
        additions.append(
            f"- {today}: Recorded dependency update for `{dep_file}`."
        )
    if not additions:
        additions.append(f"- {today}: Confirmed dependency metadata update.")
    return text.rstrip() + "\n" + "\n".join(additions) + "\n"


def refresh_license_artifacts(
    repo_root: Path,
    *,
    changed_dependency_files: Iterable[str],
    third_party_file: str = str(THIRD_PARTY),
    licenses_dir: str = LICENSES_DIR,
    report_heading: str = LICENSE_REPORT_HEADING,
) -> List[Path]:
    """Refresh THIRD_PARTY report and licenses marker files."""

    modified: List[Path] = []
    third_party_path = repo_root / third_party_file
    if third_party_path.exists():
        existing = third_party_path.read_text(encoding="utf-8")
    else:
        existing = "# Third-Party Licenses\n"

    with_heading = _ensure_report_heading(existing, report_heading)
    updated_report = _append_report_entries(
        with_heading,
        report_heading,
        changed_dependency_files,
    )
    if updated_report != existing:
        third_party_path.parent.mkdir(parents=True, exist_ok=True)
        third_party_path.write_text(updated_report, encoding="utf-8")
        modified.append(third_party_path)

    license_dir_path = repo_root / licenses_dir
    license_dir_path.mkdir(parents=True, exist_ok=True)
    sentinel = license_dir_path / "AUTO_LICENSE_SYNC.txt"
    today = dt.date.today().isoformat()
    changed = ", ".join(sorted({entry for entry in changed_dependency_files}))
    line = (
        f"{today}: DevCovenant refreshed license assets after updates to "
        f"{changed or 'dependency manifests'}.\n"
    )
    with sentinel.open("a", encoding="utf-8") as handle:
        handle.write(line)
    modified.append(sentinel)
    return modified


class DependencyLicenseSyncCheck(PolicyCheck):
    """Ensure dependency changes update licenses and the report section."""

    policy_id = "dependency-license-sync"
    version = "1.0.0"

    def check(self, context: CheckContext):
        """Verify dependency changes match the recorded license summary."""
        files = context.changed_files or []
        if not files:
            return []

        dependency_files_opt = self.get_option("dependency_files", [])
        if isinstance(dependency_files_opt, str):
            dependency_files = {dependency_files_opt.strip()}
        else:
            dependency_files = {
                str(entry).strip()
                for entry in (dependency_files_opt or [])
                if str(entry).strip()
            }
        if not dependency_files:
            return []

        third_party_rel = Path(
            self.get_option("third_party_file", str(THIRD_PARTY))
        )
        licenses_dir = self.get_option("licenses_dir", LICENSES_DIR)
        report_heading = self.get_option(
            "report_heading", LICENSE_REPORT_HEADING
        )

        changed_dependency_files = set()
        for path in files:
            if path.name not in dependency_files:
                continue
            try:
                rel_path = path.relative_to(context.repo_root)
            except ValueError:
                continue
            if rel_path.parent != Path("."):
                continue
            changed_dependency_files.add(path.name)
        if not changed_dependency_files:
            return []

        violations = []
        license_dir_path = context.repo_root / licenses_dir
        context_payload = {
            "changed_dependency_files": sorted(changed_dependency_files),
            "third_party_file": str(third_party_rel),
            "licenses_dir": str(licenses_dir),
            "report_heading": report_heading,
        }

        third_party_path = context.repo_root / third_party_rel
        if not any(path.name == third_party_rel.name for path in files):
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=third_party_path,
                    message=(
                        "Dependencies changed without updating "
                        "the license table `THIRD_PARTY_LICENSES.md`."
                    ),
                    can_auto_fix=True,
                    context={**context_payload, "issue": "third_party"},
                )
            )

        license_dir_touched = False
        for path in files:
            try:
                rel = path.relative_to(context.repo_root)
            except ValueError:
                continue
            if rel.parts and rel.parts[0] == licenses_dir:
                license_dir_touched = True
                break

        if not license_dir_touched:
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=license_dir_path,
                    message=(
                        "License files under "
                        f"{licenses_dir}/ must be refreshed."
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
                        f"`{third_party_rel}` that chronicles dependency "
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
