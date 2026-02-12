"""
Main DevCovenant engine - orchestrates policy checking and enforcement.
"""

import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from . import manifest as manifest_module
from .base import CheckContext, PolicyCheck, PolicyFixer, Violation
from .manifest import ensure_manifest
from .parser import PolicyDefinition, PolicyParser
from .policy_descriptor import resolve_script_location
from .profiles import (
    load_profile_registry,
    resolve_profile_ignore_dirs,
    resolve_profile_suffixes,
)
from .registry import PolicyRegistry, PolicySyncIssue


class DevCovenantEngine:
    """
    Main engine for devcovenant policy enforcement.
    """

    _RESERVED_METADATA_KEYS = {
        "id",
        "status",
        "severity",
        "auto_fix",
        "updated",
        "enabled",
        "custom",
        "hash",
        "enforcement",
    }

    # Directories we never traverse for policy checks
    _BASE_IGNORED_DIRS = frozenset(
        {
            ".git",
            ".venv",
            ".python",
            "output",
            "logs",
            "build",
            "dist",
            "node_modules",
            "__pycache__",
            ".cache",
            ".venv.lock",
        }
    )

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize the engine.

        Args:
            repo_root: Root directory of the repository (default: current dir)
        """
        if repo_root is None:
            repo_root = Path.cwd()

        self.repo_root = Path(repo_root).resolve()
        self.devcovenant_dir = self.repo_root / "devcovenant"
        self.agents_md_path = self.repo_root / "AGENTS.md"
        self.config_path = self.devcovenant_dir / "config.yaml"
        self.registry_path = manifest_module.policy_registry_path(
            self.repo_root
        )

        # Load configuration and apply overrides
        self.config = self._load_config()
        self._apply_config_paths()
        self._ignored_dirs = set(self._BASE_IGNORED_DIRS)
        self._ignored_paths: list[Path] = []
        self._merge_configured_ignored_dirs()
        self._apply_core_exclusions()

        self._profile_registry = load_profile_registry(self.repo_root)
        self._active_profiles = self._resolve_active_profiles()
        self._merge_profile_ignored_dirs()

        ensure_manifest(self.repo_root)

        # Initialize parser and registry
        self.parser = PolicyParser(self.agents_md_path)
        self.registry = PolicyRegistry(self.registry_path, self.repo_root)

        # Statistics
        self.passed_count = 0
        self.failed_count = 0
        self._custom_policy_overrides = (
            self._discover_custom_policy_overrides()
        )
        self.fixers: List[PolicyFixer] = self._load_fixers()

    def _load_config(self) -> Dict:
        """Load configuration from config.yaml."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_policies_from_agents(self) -> List[PolicyDefinition]:
        """Load policy definitions directly from AGENTS policy blocks."""
        if not self.agents_md_path.exists():
            return []
        try:
            parsed = self.parser.parse_agents_md()
        except Exception as exc:
            print(f"⚠️  Warning: Failed to parse AGENTS policies: {exc}")
            return []
        policies: List[PolicyDefinition] = []
        for policy in parsed:
            if policy.policy_id:
                policies.append(policy)
        return sorted(policies, key=lambda policy: policy.policy_id)

    def _apply_config_paths(self) -> None:
        """Apply configurable path overrides after the config loads."""
        paths_cfg = self.config.get("paths", {})
        policy_doc = paths_cfg.get("policy_definitions")
        if policy_doc:
            self.agents_md_path = self.repo_root / Path(policy_doc)
        registry_file = paths_cfg.get("registry_file")
        if registry_file:
            self.registry_path = self.repo_root / Path(registry_file)

    def _merge_configured_ignored_dirs(self) -> None:
        """Extend the default ignored directory set via configuration."""
        engine_cfg = self.config.get("engine", {}) if self.config else {}
        extra_dirs = engine_cfg.get("ignore_dirs", [])
        if isinstance(extra_dirs, str):
            candidates = [extra_dirs]
        elif isinstance(extra_dirs, list):
            candidates = extra_dirs
        else:
            candidates = [extra_dirs] if extra_dirs else []
        for entry in candidates:
            name = str(entry).strip()
            if name:
                self._ignored_dirs.add(name)

    def _apply_core_exclusions(self) -> None:
        """Apply devcovenant core exclusion rules from configuration."""
        include_core = bool(self.config.get("devcov_core_include", False))
        core_paths = self.config.get("devcov_core_paths", ["devcovenant/core"])
        if include_core:
            return
        if isinstance(core_paths, str):
            core_entries = [core_paths]
        else:
            core_entries = list(core_paths or [])
        for entry in core_entries:
            rel = str(entry).strip()
            if not rel:
                continue
            self._ignored_paths.append(self.repo_root / rel)

    def _resolve_active_profiles(self) -> list[str]:
        """Return the normalized list of active profiles."""
        profiles_cfg = self.config.get("profiles", {}) if self.config else {}
        active = profiles_cfg.get("active", [])
        if isinstance(active, str):
            candidates = [active]
        elif isinstance(active, list):
            candidates = active
        else:
            candidates = [active] if active else []
        normalized: list[str] = []
        for entry in candidates:
            normalized_value = str(entry or "").strip().lower()
            if not normalized_value or normalized_value == "__none__":
                continue
            normalized.append(normalized_value)
        return sorted(set(normalized))

    def _discover_custom_policy_overrides(self) -> set[str]:
        """Return policy ids overridden by custom policy scripts."""
        overrides: set[str] = set()
        custom_dir = self.repo_root / "devcovenant" / "custom" / "policies"
        if not custom_dir.exists():
            return overrides
        for policy_dir in custom_dir.iterdir():
            if not policy_dir.is_dir():
                continue
            script_path = policy_dir / f"{policy_dir.name}.py"
            if not script_path.exists():
                continue
            overrides.add(policy_dir.name.replace("_", "-"))
        return overrides

    def _is_ignored_path(self, candidate: Path) -> bool:
        """Return True when candidate is within an ignored path prefix."""
        for part in candidate.parts:
            if part in self._ignored_dirs:
                return True
        for root in self._ignored_paths:
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            return True
        return False

    def _merge_profile_ignored_dirs(self) -> None:
        """Extend ignored directories with active profile declarations."""
        ignored = resolve_profile_ignore_dirs(
            self._profile_registry, self._active_profiles
        )
        for entry in ignored:
            name = str(entry).strip()
            if name:
                self._ignored_dirs.add(name)

    def _load_fixers(self) -> List[PolicyFixer]:
        """Dynamically import policy fixers bundled with DevCovenant."""
        fixers: List[PolicyFixer] = []
        roots = [
            ("custom", self.repo_root / "devcovenant" / "custom" / "policies"),
            ("core", self.repo_root / "devcovenant" / "core" / "policies"),
        ]
        for origin, root in roots:
            if not root.exists():
                continue
            for policy_dir in root.iterdir():
                if not policy_dir.is_dir() or policy_dir.name.startswith("_"):
                    continue
                policy_id = policy_dir.name.replace("_", "-")
                if (
                    origin == "core"
                    and policy_id in self._custom_policy_overrides
                ):
                    continue
                fixers_dir = policy_dir / "fixers"
                if not fixers_dir.exists():
                    continue
                for module_file in fixers_dir.glob("*.py"):
                    if (
                        module_file.name.startswith("_")
                        or module_file.name == "__init__.py"
                    ):
                        continue
                    module_name = (
                        f"devcovenant.{origin}.policies."
                        f"{policy_dir.name}.fixers.{module_file.stem}"
                    )
                    try:
                        module = importlib.import_module(module_name)
                    except Exception:
                        continue
                    for member in module.__dict__.values():
                        if (
                            inspect.isclass(member)
                            and issubclass(member, PolicyFixer)
                            and member is not PolicyFixer
                        ):
                            try:
                                instance = member()
                                setattr(instance, "repo_root", self.repo_root)
                                setattr(instance, "_origin", origin)
                                fixers.append(instance)
                            except Exception:
                                continue
        return fixers

    def check(
        self, mode: str = "normal", apply_fixes: bool = False
    ) -> "CheckResult":
        """
        Main entry point for policy checking.

        Args:
            mode: Check mode label recorded in CheckContext.

        Returns:
            CheckResult object
        """
        # Runtime policy input is the compiled AGENTS policy block.
        policies = self._load_policies_from_agents()
        if not policies:
            violation = Violation(
                policy_id="agents-parse",
                severity="error",
                file_path=self.agents_md_path,
                message=(
                    "AGENTS policy blocks are empty or invalid. "
                    "Checks cannot run without resolved policy metadata."
                ),
                suggestion=(
                    "Run `python3 -m devcovenant refresh` to regenerate "
                    "AGENTS.md policy blocks from descriptors."
                ),
            )
            self.report_violations([violation], mode)
            return CheckResult([violation], should_block=True, sync_issues=[])

        # Registry remains hash/diagnostic state only.
        self.registry.load()
        sync_issues = self.registry.check_policy_sync(policies)

        if sync_issues:
            self.report_sync_issues(sync_issues)

        # Load and run policy checks
        context = self._build_check_context(mode)
        self.passed_count = 0
        self.failed_count = 0
        violations = self.run_policy_checks(policies, mode, context)

        auto_fix_enabled = self.config.get("engine", {}).get(
            "auto_fix_enabled", True
        )
        if apply_fixes and auto_fix_enabled:
            fixes_applied = self.apply_auto_fixes(violations)
            if fixes_applied:
                context = self._build_check_context(mode)
                self.passed_count = 0
                self.failed_count = 0
                violations = self.run_policy_checks(policies, mode, context)

        # Report violations
        self.report_violations(violations, mode)

        # Determine if should block
        should_block = self.should_block(violations)

        return CheckResult(violations, should_block, sync_issues=[])

    def report_sync_issues(self, issues: List[PolicySyncIssue]):
        """
        Report policy sync issues in AI-friendly format.

        Args:
            issues: List of PolicySyncIssue objects
        """
        print("\n" + "=" * 70)
        print("🔄 POLICY SYNC REQUIRED")
        print("=" * 70)
        print()

        for issue in issues:
            print(f"Policy '{issue.policy_id}' requires attention.")
            print(f"Issue: {issue.issue_type.replace('_', ' ').title()}")
            print()

            print("📋 Current Policy (from AGENTS.md):")
            print("━" * 70)
            # Print first 500 chars of policy text
            policy_preview = issue.policy_text[:500]
            if len(issue.policy_text) > 500:
                policy_preview += "..."
            print(policy_preview)
            print("━" * 70)
            print()

            print("🎯 Action Required:")
            is_new = (
                issue.issue_type == "script_missing"
                or issue.issue_type == "new_policy"
            )
            if is_new:
                print(f"1. Create: {issue.script_path}")
                print("2. Implement the policy described above")
                print(
                    "3. Use the PolicyCheck base class from "
                    "devcovenant.core.base"
                )
                policy_slug = issue.policy_id.replace("-", "_")
                test_file = (
                    f"tests/devcovenant/core/policies/{policy_slug}/"
                    f"test_{policy_slug}.py"
                )
                print(f"4. Add tests in {test_file}")
                print(f"5. Run tests: pytest {test_file} -v")
            else:
                print(f"1. Update: {issue.script_path}")
                print("2. Modify the script to implement the updated policy")
                policy_slug = issue.policy_id.replace("-", "_")
                test_file = (
                    f"tests/devcovenant/core/policies/{policy_slug}/"
                    f"test_{policy_slug}.py"
                )
                print(f"3. Update tests in {test_file}")
                print(f"4. Run tests: pytest {test_file} -v")

            print("6. Re-run `devcovenant refresh` " "to sync policy hashes")
            print()
            print("⚠️  Complete this BEFORE working on user's request.")
            print()
            print("=" * 70)
            print()

    def run_policy_checks(
        self,
        policies: List[PolicyDefinition],
        mode: str,
        context: Optional[CheckContext] = None,
    ) -> List[Violation]:
        """
        Load and run all policy check scripts.

        Args:
            policies: List of policy definitions
            mode: Check mode

        Returns:
            List of all violations found
        """
        violations = []

        # Build check context when not provided
        if context is None:
            context = self._build_check_context(mode)

        for policy in policies:
            if not policy.enabled:
                continue
            if policy.status == "fiducial":
                violations.append(
                    Violation(
                        policy_id=policy.policy_id,
                        severity="info",
                        file_path=self.agents_md_path,
                        message=(
                            "Fiducial policy reminder:\n"
                            f"{policy.description}"
                        ),
                    )
                )
            # Skip inactive policies
            if policy.status not in ["active", "new", "fiducial"]:
                continue

            # Try to load and run the policy script
            try:
                checker = self._load_policy_script(policy.policy_id)
                if checker:
                    options = self._extract_policy_options(policy)
                    config_overrides = context.get_policy_config(
                        policy.policy_id
                    )
                    checker.set_options(options, config_overrides)
                    policy_violations = checker.check(context)
                    violations.extend(policy_violations)
                    if not policy_violations:
                        self.passed_count += 1
                    else:
                        self.failed_count += 1
            except Exception as e:
                # If script fails, report but don't block
                print(
                    f"⚠️  Warning: Policy '{policy.policy_id}' "
                    f"check failed: {e}"
                )

        return violations

    def _build_check_context(self, mode: str) -> CheckContext:
        """
        Build the CheckContext for policy checks.

        Args:
            mode: Check mode

        Returns:
            CheckContext object
        """
        changed_files = []
        all_files = []

        suffixes = set(self._resolve_file_suffixes())
        all_files = [
            path
            for path in self._collect_all_files(suffixes)
            if not self._is_ignored_path(path)
        ]

        return CheckContext(
            repo_root=self.repo_root,
            changed_files=changed_files,
            all_files=all_files,
            mode=mode,
            config=self.config,
        )

    def _collect_all_files(self, suffixes: Set[str]) -> List[Path]:
        """
        Walk the repository tree and collect files matching the given suffixes,
        skipping large or third-party directories.
        """
        matched: List[Path] = []

        for root, dirs, files in os.walk(self.repo_root):
            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs if self._should_descend_dir(Path(root) / d)
            ]

            for name in files:
                file_path = Path(root) / name
                if self._is_ignored_path(file_path):
                    continue
                if file_path.suffix.lower() in suffixes:
                    matched.append(file_path)

        return matched

    def apply_auto_fixes(self, violations: List[Violation]) -> bool:
        """
        Attempt to auto-fix any violations that advertise a fixer.

        Returns:
            True when at least one file was modified.
        """
        if not violations or not self.fixers:
            return False

        applied = False
        print("\n🔧 Running auto-fixers...\n")
        for violation in violations:
            if not violation.can_auto_fix:
                continue
            for fixer in self.fixers:
                if not fixer.can_fix(violation):
                    continue
                result = fixer.fix(violation)
                message = result.message or ""
                if result.success:
                    if message:
                        print(f"  • {message}")
                    if result.files_modified:
                        applied = True
                else:
                    print(
                        f"  • Auto-fix failed for {violation.policy_id}: "
                        f"{message or 'unknown error'}"
                    )
                break

        if applied:
            print("\n🔁 Re-running policy checks after auto-fix.\n")
        else:
            print("⚪ No auto-fixable violations were modified.\n")

        return applied

    def _should_descend_dir(self, candidate: Path) -> bool:
        """
        Decide whether to continue walking into a directory.
        """
        name = candidate.name

        if name in self._ignored_dirs:
            return False

        if self._is_ignored_path(candidate):
            return False

        # Always skip __pycache__ variants
        if name.startswith("__pycache__"):
            return False

        return True

    def _resolve_file_suffixes(self) -> list[str]:
        """Resolve file suffixes using profiles and overrides."""
        engine_cfg = self.config.get("engine", {}) if self.config else {}
        suffixes = list(
            engine_cfg.get(
                "file_suffixes",
                [".py", ".md", ".yml", ".yaml"],
            )
        )
        profile_suffixes = resolve_profile_suffixes(
            self._profile_registry, self._active_profiles
        )
        suffixes.extend(profile_suffixes)
        cleaned: list[str] = []
        for entry in suffixes:
            text = str(entry).strip()
            if text:
                cleaned.append(text)
        return cleaned

    def _load_policy_script(self, policy_id: str) -> Optional[PolicyCheck]:
        """
        Dynamically load a policy script.

        Args:
            policy_id: ID of the policy

        Returns:
            PolicyCheck instance or None if not found
        """
        location = resolve_script_location(self.repo_root, policy_id)
        if location is None:
            return None

        # Load the module
        spec = importlib.util.spec_from_file_location(
            location.module, location.path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find the PolicyCheck subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PolicyCheck)
                    and attr is not PolicyCheck
                ):
                    return attr()

        return None

    def _extract_policy_options(
        self, policy: PolicyDefinition
    ) -> Dict[str, Any]:
        """Pull custom metadata options from a policy definition."""

        options: Dict[str, Any] = {}
        for key, raw_value in policy.raw_metadata.items():
            if key.lower() in self._RESERVED_METADATA_KEYS:
                continue
            options[key] = self._parse_metadata_value(raw_value)
        return options

    @staticmethod
    def _parse_metadata_value(raw_value: str) -> Any:
        """Decode scalar/list metadata from the policy-def block."""

        text = (raw_value or "").strip()
        if not text:
            return ""

        lowered = text.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"

        if "," in text:
            return [item.strip() for item in text.split(",") if item.strip()]

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            pass

        return text

    def report_violations(self, violations: List[Violation], mode: str):
        """
        Report violations in AI-friendly, actionable format.

        Args:
            violations: List of violations
            mode: Check mode
        """
        if not violations:
            print("\n✅ All policy checks passed!")
            return

        print("\n" + "=" * 70)
        print("📊 DEVCOVENANT CHECK RESULTS")
        print("=" * 70)
        print()
        print(f"✅ Passed: {self.passed_count} policies")
        print(f"⚠️  Violations: {len(violations)} issues found")
        print()

        # Group by severity
        by_severity = {}
        for violation_entry in violations:
            if violation_entry.severity not in by_severity:
                by_severity[violation_entry.severity] = []
            by_severity[violation_entry.severity].append(violation_entry)

        # Report in order: critical, error, warning, info
        for severity in ["critical", "error", "warning", "info"]:
            if severity not in by_severity:
                continue

            for violation in by_severity[severity]:
                self._report_single_violation(violation)

        # Summary
        print("=" * 70)
        self._report_summary(by_severity)

    def _report_single_violation(self, violation: Violation):
        """Report a single violation with full context."""
        # Icon based on severity
        icons = {
            "critical": "❌",
            "error": "🚫",
            "warning": "⚠️",
            "info": "💡",
        }
        icon = icons.get(violation.severity, "•")

        print(f"{icon} {violation.severity.upper()}: {violation.policy_id}")

        if violation.file_path:
            location = str(violation.file_path)
            if violation.line_number:
                location += f":{violation.line_number}"
            print(f"📍 {location}")

        print()
        print(f"Issue: {violation.message}")

        if violation.suggestion:
            print()
            print("Fix:")
            print(violation.suggestion)

        if violation.can_auto_fix:
            print()
            print("Auto-fix: Enabled by default (use --nofix to disable)")

        print()
        print(f"Policy: AGENTS.md#{violation.policy_id}")
        print("━" * 70)
        print()

    def _report_summary(self, by_severity: Dict[str, List[Violation]]):
        """Report summary of violations."""
        critical = len(by_severity.get("critical", []))
        errors = len(by_severity.get("error", []))
        warnings = len(by_severity.get("warning", []))
        info = len(by_severity.get("info", []))

        print(
            f"Summary: {critical} critical, {errors} errors, "
            f"{warnings} warnings, {info} info"
        )
        print()

        # Determine status
        if critical > 0:
            print("Status: 🚫 BLOCKED (critical violations must be fixed)")
        elif errors > 0:
            fail_threshold = self.config.get("engine", {}).get(
                "fail_threshold", "error"
            )
            if fail_threshold in ["error", "warning", "info"]:
                print("Status: 🚫 BLOCKED (violations >= error threshold)")
        else:
            print("Status: ✅ PASSED")

        print()
        if self.config.get("engine", {}).get("auto_fix_enabled", True):
            print(
                "💡 Auto-fix is enabled by default; run "
                "'devcovenant check --nofix' for audit-only checks"
            )

        print("=" * 70)

    def should_block(self, violations: List[Violation]) -> bool:
        """
        Determine if violations should block the commit/operation.

        Args:
            violations: List of violations

        Returns:
            True if should block
        """
        if not violations:
            return False

        fail_threshold = self.config.get("engine", {}).get(
            "fail_threshold", "error"
        )

        # Map severity to numeric level
        severity_levels = {
            "critical": 4,
            "error": 3,
            "warning": 2,
            "info": 1,
        }

        threshold_level = severity_levels.get(fail_threshold, 3)

        # Check if any violation meets or exceeds threshold
        for violation in violations:
            violation_level = severity_levels.get(violation.severity, 1)
            if violation_level >= threshold_level:
                return True

        return False


class CheckResult:
    """Result of a devcovenant check operation."""

    def __init__(
        self,
        violations: List[Violation],
        should_block: bool,
        sync_issues: List[PolicySyncIssue],
    ):
        """Store the check result metadata for later inspection."""
        self.violations = violations
        self.should_block = should_block
        self.sync_issues = sync_issues

    def has_sync_issues(self) -> bool:
        """Check if there are policy sync issues."""
        return len(self.sync_issues) > 0

    def has_violations(self) -> bool:
        """Check if there are any violations."""
        return len(self.violations) > 0
