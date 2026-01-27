"""
Policy: Profile/Policy Map Synchronization

Ensures `PROFILE_MAP.md` and `POLICY_MAP.md` document the shipped profiles
and policies so the short-form references stay accurate for contributors,
installers, and tooling.
"""

from pathlib import Path
from typing import Iterable, List, Set

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyParser


class ProfilePolicyMapCheck(PolicyCheck):
    """Verify that both maps cover every shipped profile and policy."""

    policy_id = "profile-policy-map"
    version = "0.1.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """
        Ensure PROFILE_MAP.md and POLICY_MAP.md reference every profile and
        policy.

        Returns a violation for each map that is missing coverage so editors
        know to refresh the short-form documentation before assets are
        regenerated.
        """

        repo_root = context.repo_root
        profile_map = repo_root / Path(
            self.get_option("profile_map_file", "PROFILE_MAP.md")
        )
        policy_map = repo_root / Path(
            self.get_option("policy_map_file", "POLICY_MAP.md")
        )
        profile_dirs = self._discover_profiles(repo_root)
        documented_profiles = self._extract_profile_names(profile_map)
        documented_policies = self._extract_policy_headers(policy_map)
        policy_ids = self._extract_policy_ids(repo_root / "AGENTS.md")

        violations: List[Violation] = []
        missing_profiles = sorted(profile_dirs - documented_profiles)
        if missing_profiles:
            profile_list = ", ".join(missing_profiles)
            profile_label = (
                "PROFILE_MAP.md is missing entries for the "
                "following profiles: "
            )
            message = profile_label + profile_list
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=message,
                    file_path=profile_map,
                )
            )

        missing_policies = sorted(policy_ids - documented_policies)
        if missing_policies:
            policy_list = ", ".join(missing_policies)
            policy_label = (
                "POLICY_MAP.md is missing entries for the following policies: "
            )
            message = policy_label + policy_list
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    message=message,
                    file_path=policy_map,
                )
            )

        return violations

    def _discover_profiles(self, repo_root: Path) -> Set[str]:
        """Return the names of every shipped profile (core + custom)."""

        def list_profiles(root: Path) -> Iterable[Path]:
            """Return each profile folder contained in the provided root."""

            if not root.is_dir():
                return []
            return [entry for entry in root.iterdir() if entry.is_dir()]

        profiles: Set[str] = set()
        profiles.update(
            entry.name.lower()
            for entry in list_profiles(repo_root / "devcovenant/core/profiles")
        )
        profiles.update(
            entry.name.lower()
            for entry in list_profiles(
                repo_root / "devcovenant/custom/profiles"
            )
        )
        return profiles

    def _extract_profile_names(self, path: Path) -> Set[str]:
        """Extract documented profile names from PROFILE_MAP.md headings."""

        if not path.exists():
            return set()

        names: Set[str] = set()
        lines = path.read_text().splitlines()
        in_scopes = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                in_scopes = False
                continue

            if stripped.startswith("### Profile:"):
                rest = stripped[len("### Profile:") :].strip()
                if "(" in rest:
                    rest = rest.split("(", 1)[0].strip()
                if rest:
                    names.add(rest.lower())
            elif stripped.startswith("### "):
                embedded = self._extract_names_from_parentheses(stripped)
                names.update(embedded)

            embedded = self._extract_names_from_parentheses(stripped)
            names.update(embedded)
            if stripped.startswith("- Scopes:"):
                in_scopes = True
                scopes_part = stripped[len("- Scopes:") :].strip()
                names.update(self._extract_names_from_list(scopes_part))
                continue
            if in_scopes and line.startswith("  "):
                names.update(self._extract_names_from_list(stripped))
                continue
            in_scopes = False

        return names

    def _extract_names_from_parentheses(self, text: str) -> Set[str]:
        """Extract comma-separated tokens from parentheses in a heading."""

        start = text.find("(")
        end = text.find(")", start)
        if start == -1 or end == -1 or end <= start + 1:
            return set()
        content = text[start + 1 : end]
        return {
            token.strip().lower()
            for token in content.split(",")
            if token.strip()
        }

    def _extract_names_from_list(self, text: str) -> Set[str]:
        """Extract comma- or plus-separated tokens from a scope list."""

        split_text = text.replace("+", ",").split(",")
        tokens = [token.strip().rstrip(".") for token in split_text]
        return {token.lower() for token in tokens if token}

    def _extract_policy_headers(self, path: Path) -> Set[str]:
        """Read policy headings documented in POLICY_MAP.md."""

        if not path.exists():
            return set()

        headers: Set[str] = set()
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith("### "):
                continue
            header_text = stripped[4:].strip()
            if "(" in header_text:
                header_text = header_text.split("(", 1)[0].strip()
            if not header_text:
                continue
            headers.add(header_text.lower())
        return headers

    def _extract_policy_ids(self, agents_path: Path) -> Set[str]:
        """Parse AGENTS.md and return every policy id that appears."""

        if not agents_path.exists():
            return set()

        parser = PolicyParser(agents_path)
        return {
            definition.policy_id
            for definition in parser.parse_agents_md()
            if definition.policy_id
        }
