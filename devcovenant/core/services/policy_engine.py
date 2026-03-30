"""
Main DevCovenant engine - orchestrates policy checking and enforcement.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

import devcovenant.core.flow.policy_check_context as policy_check_context
import devcovenant.core.flow.workflow_validation as workflow_validation
import devcovenant.core.runtime.policy_reporting as policy_reporting
import devcovenant.core.runtime.policy_runtime_actions as runtime_actions
import devcovenant.core.services.policy_autofix as policy_autofix
import devcovenant.core.services.policy_check_runner as policy_check_runner
import devcovenant.core.services.policy_file_scope as policy_file_scope
from devcovenant.core.contracts.policy import (
    ChangeState,
    CheckContext,
    PolicyCheck,
    PolicyFixer,
    Violation,
)
from devcovenant.core.runtime.execution import get_output_mode, runtime_print
from devcovenant.core.services import integrity_validation
from devcovenant.core.services import metadata as metadata_runtime
from devcovenant.core.services import structure_validation
from devcovenant.core.services import yaml_cache as yaml_cache_service
from devcovenant.core.services.manifest_inventory import ensure_manifest
from devcovenant.core.services.policy_parse import (
    PolicyDefinition,
    PolicyParser,
)
from devcovenant.core.services.policy_registry import (
    PolicyRegistry,
    PolicySyncIssue,
    load_policy_descriptor,
)
from devcovenant.core.services.profile_registry import (
    load_profile_registry,
    parse_active_profiles,
)
from devcovenant.core.services.tracked_registry import policy_registry_path
from devcovenant.core.services.translator_engine import TranslatorRuntime


def load_policy_check_instance(
    repo_root: Path, policy_id: str
) -> Optional[PolicyCheck]:
    """Load one policy script and return its PolicyCheck instance."""
    return runtime_actions.load_policy_check_instance(repo_root, policy_id)


def run_policy_runtime_action(
    repo_root: Path,
    *,
    policy_id: str,
    action: str,
    payload: Dict[str, Any] | None = None,
) -> Any:
    """Run one policy-owned runtime action through the policy contract."""
    return runtime_actions.run_policy_runtime_action(
        repo_root,
        policy_id=policy_id,
        action=action,
        payload=payload,
        checker_loader=load_policy_check_instance,
        metadata_loader=_runtime_policy_metadata_options,
        config_loader=_runtime_policy_config_overrides,
    )


def _runtime_policy_config_overrides(
    repo_root: Path, policy_id: str
) -> dict[str, Any]:
    """Return merged config overrides for one policy runtime action."""
    return runtime_actions.runtime_policy_config_overrides(
        repo_root, policy_id
    )


def _runtime_policy_metadata_options(
    repo_root: Path, policy_id: str
) -> dict[str, Any]:
    """Return runtime metadata options for a policy action."""
    return runtime_actions.runtime_policy_metadata_options(
        repo_root,
        policy_id,
        descriptor_loader=load_policy_descriptor,
        registry_path_resolver=policy_registry_path,
    )


class DevCovenantEngine:
    """
    Main engine for devcovenant policy enforcement.
    """

    _RESERVED_METADATA_KEYS = {
        "id",
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
    _DEFAULT_GATE_STATUS_PATH = (
        Path("devcovenant") / "registry" / "runtime" / "gate_status.json"
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
        self.registry_path = policy_registry_path(self.repo_root)

        # Load configuration and apply overrides
        self.config = self._load_config()
        self._normalized_policy_state = (
            metadata_runtime.normalize_policy_state(
                self.config.get("policy_state")
            )
        )
        self._apply_config_paths()
        self._ignored_dirs = set(self._BASE_IGNORED_DIRS)
        self._ignored_paths: list[Path] = []
        self._config_ignore_patterns = self._load_config_ignore_patterns()
        self._merge_configured_ignored_dirs()
        self._apply_core_exclusions()

        try:
            self._profile_registry = load_profile_registry(self.repo_root)
        except ValueError as error:
            raise SystemExit(f"Invalid profile metadata: {error}") from error
        self._active_profiles = parse_active_profiles(
            self.config, include_global=True
        )
        self.translator_runtime = TranslatorRuntime(
            self.repo_root,
            self._profile_registry,
            self._active_profiles,
        )
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
        if not self.config_path.exists():
            raise SystemExit(
                f"Missing config file: {self.config_path}. "
                "Run `devcovenant install` or restore config."
            )
        try:
            payload = yaml_cache_service.load_yaml(self.config_path)
        except yaml.YAMLError as exc:
            raise SystemExit(
                f"Invalid YAML in config file {self.config_path}: {exc}"
            ) from exc
        except OSError as exc:
            raise SystemExit(
                f"Unable to read config file {self.config_path}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise SystemExit(
                f"Config file must be a YAML mapping: {self.config_path}"
            )
        return payload

    def _load_policies_from_agents(self) -> List[PolicyDefinition]:
        """Load policy definitions directly from AGENTS policy blocks."""
        if not self.agents_md_path.exists():
            raise ValueError(
                f"Missing policy definitions file: {self.agents_md_path}."
            )
        try:
            parsed = self.parser.parse_agents_md()
        # DEVCOV_ALLOW_BROAD_ONCE AGENTS parser boundary.
        except Exception as exc:
            raise ValueError(
                f"Failed to parse AGENTS policies: {exc}"
            ) from exc
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
        for name in policy_file_scope.configured_ignore_dir_names(self.config):
            self._ignored_dirs.add(name)

    def _load_config_ignore_patterns(self) -> list[str]:
        """Return normalized ignore patterns from config.ignore.patterns."""
        return policy_file_scope.config_ignore_patterns(self.config)

    def _matches_config_ignore_pattern(self, candidate: Path) -> bool:
        """Return True when candidate matches config ignore glob patterns."""
        return policy_file_scope.matches_config_ignore_pattern(
            self.repo_root,
            candidate,
            self._config_ignore_patterns,
        )

    def _apply_core_exclusions(self) -> None:
        """Apply devcovenant core exclusion rules from configuration."""
        self._ignored_paths.extend(
            policy_file_scope.core_exclusion_paths(self.repo_root, self.config)
        )

    def _discover_custom_policy_overrides(self) -> set[str]:
        """Return policy ids overridden by custom policy scripts."""
        return policy_file_scope.discover_custom_policy_overrides(
            self.repo_root
        )

    def _is_ignored_path(self, candidate: Path) -> bool:
        """Return True when candidate is within an ignored path prefix."""
        return policy_file_scope.is_ignored_path(
            candidate,
            repo_root=self.repo_root,
            ignored_dirs=self._ignored_dirs,
            ignored_paths=self._ignored_paths,
            config_ignore_patterns=self._config_ignore_patterns,
        )

    def _merge_profile_ignored_dirs(self) -> None:
        """Extend ignored directories with active profile declarations."""
        for name in policy_file_scope.profile_ignored_dir_names(
            self._profile_registry,
            self._active_profiles,
        ):
            self._ignored_dirs.add(name)

    def _load_fixers(self) -> List[PolicyFixer]:
        """Dynamically import policy fixers bundled with DevCovenant."""
        return policy_autofix.load_fixers(
            self.repo_root,
            custom_policy_overrides=self._custom_policy_overrides,
        )

    def check(self, apply_fixes: bool = False) -> "CheckResult":
        """
        Main entry point for policy checking.

        Returns:
            CheckResult object
        """
        # Runtime policy input is the compiled AGENTS policy block.
        try:
            policies = self._load_policies_from_agents()
        except ValueError as exc:
            return self._agents_parse_failure_result(str(exc))
        if not policies:
            return self._agents_parse_failure_result(
                "AGENTS policy blocks are empty or invalid. "
                "Checks cannot run without resolved policy metadata."
            )

        # Registry remains hash/diagnostic state only.
        self.registry.load()
        sync_issues = self.registry.check_policy_sync(policies)

        if sync_issues:
            self.report_sync_issues(sync_issues)

        auto_fix_enabled = self.config.get("engine", {}).get(
            "auto_fix_enabled", False
        )
        violations = self._run_check_cycle(
            policies,
            apply_fixes=bool(apply_fixes),
            auto_fix_enabled=bool(auto_fix_enabled),
        )

        # Report violations
        self.report_violations(violations)

        # Determine if should block
        should_block = self.should_block(violations)

        return CheckResult(
            violations,
            should_block,
            sync_issues=sync_issues,
        )

    def _agents_parse_failure_result(self, message: str) -> "CheckResult":
        """Build and report one deterministic AGENTS parse failure result."""
        violation = Violation(
            policy_id="agents-parse",
            severity="error",
            file_path=self.agents_md_path,
            message=message,
            suggestion=(
                "Run `python3 -m devcovenant refresh` to regenerate "
                "AGENTS.md policy blocks from descriptors."
            ),
        )
        self.report_violations([violation])
        return CheckResult([violation], should_block=True, sync_issues=[])

    def _reset_check_counts(self) -> None:
        """Reset aggregate pass/fail counters before one full check pass."""
        self.passed_count = 0
        self.failed_count = 0

    def _run_checks_for_context(
        self,
        policies: List[PolicyDefinition],
        *,
        context: CheckContext,
    ) -> List[Violation]:
        """Run built-in checks and policy checks for one resolved context."""
        self._reset_check_counts()
        built_in_violations: List[Violation] = []
        for check_fn in (
            integrity_validation.check_integrity,
            structure_validation.check_structure,
            workflow_validation.check_workflow_contract,
        ):
            current = list(check_fn(context))
            built_in_violations.extend(current)
            if current:
                self.failed_count += 1
            else:
                self.passed_count += 1
        violations = list(built_in_violations)
        violations.extend(self.run_policy_checks(policies, context))
        return violations

    def _run_check_cycle(
        self,
        policies: List[PolicyDefinition],
        *,
        apply_fixes: bool,
        auto_fix_enabled: bool,
    ) -> List[Violation]:
        """Run one full check cycle with one optional autofix rerun."""
        context = self._build_check_context(
            apply_fixes=apply_fixes,
            auto_fix_enabled=auto_fix_enabled,
        )
        violations = self._run_checks_for_context(policies, context=context)
        if not (apply_fixes and auto_fix_enabled):
            return violations
        if not self.apply_auto_fixes(violations):
            return violations
        context = self._build_check_context(
            apply_fixes=apply_fixes,
            auto_fix_enabled=auto_fix_enabled,
        )
        return self._run_checks_for_context(policies, context=context)

    def report_sync_issues(self, issues: List[PolicySyncIssue]):
        """
        Report policy sync issues in AI-friendly format.

        Args:
            issues: List of PolicySyncIssue objects
        """
        policy_reporting.report_sync_issues(
            issues,
            print_fn=self._report_print_fn(error_channel=bool(issues)),
        )

    def run_policy_checks(
        self,
        policies: List[PolicyDefinition],
        context: Optional[CheckContext] = None,
    ) -> List[Violation]:
        """
        Load and run all policy check scripts.

        Args:
            policies: List of policy definitions

        Returns:
            List of all violations found
        """
        violations = []

        # Build check context when not provided
        if context is None:
            context = self._build_check_context()
        result = policy_check_runner.run_policy_checks(
            policies,
            context=context,
            load_policy_script=self._load_policy_script,
            extract_policy_options_fn=self._extract_policy_options,
            critical_disable_attempted_fn=self._critical_disable_attempted,
            critical_disable_attempt_violation_fn=(
                self._critical_disable_attempt_violation
            ),
        )
        self.passed_count += result.passed_count
        self.failed_count += result.failed_count
        violations.extend(result.violations)
        return violations

    def _critical_disable_attempted(self, policy: PolicyDefinition) -> bool:
        """Return True when config attempts to disable a critical policy."""
        return policy_check_runner.critical_disable_attempted(
            policy,
            normalized_policy_state=getattr(
                self, "_normalized_policy_state", None
            ),
            config=self.config,
        )

    def _critical_disable_attempt_violation(
        self, policy: PolicyDefinition
    ) -> Violation:
        """Build a deterministic violation for critical disable attempts."""
        return policy_check_runner.critical_disable_attempt_violation(
            policy,
            config_path=getattr(self, "config_path", None),
        )

    def _build_check_context(
        self,
        *,
        apply_fixes: bool = False,
        auto_fix_enabled: bool = False,
    ) -> CheckContext:
        """
        Build the CheckContext for policy checks.

        Returns:
            CheckContext object
        """
        return policy_check_context.build_check_context(
            self.repo_root,
            config=self.config,
            translator_runtime=self.translator_runtime,
            gate_status_path=self._DEFAULT_GATE_STATUS_PATH,
            autofix_enabled=bool(auto_fix_enabled),
            autofix_requested=bool(apply_fixes and auto_fix_enabled),
            is_ignored_path=self._is_ignored_path,
            resolve_file_suffixes=self._resolve_file_suffixes,
            collect_all_files=self._collect_all_files,
        )

    def _build_change_state(self) -> ChangeState:
        """Build current-snapshot and session scopes for policy checks."""
        return policy_check_context.build_change_state(
            self.repo_root,
            gate_status_path=self._DEFAULT_GATE_STATUS_PATH,
            is_ignored_path=self._is_ignored_path,
        )

    def _collect_all_files(self, suffixes: Set[str]) -> List[Path]:
        """
        Walk the repository tree and collect files matching the given suffixes,
        skipping large or third-party directories.
        """
        return policy_file_scope.collect_all_files(
            self.repo_root,
            set(suffixes),
            ignored_dirs=self._ignored_dirs,
            ignored_paths=self._ignored_paths,
            config_ignore_patterns=self._config_ignore_patterns,
        )

    def apply_auto_fixes(self, violations: List[Violation]) -> bool:
        """
        Attempt to auto-fix any violations that advertise a fixer.

        Returns:
            True when at least one file was modified.
        """
        return policy_autofix.apply_auto_fixes(
            violations,
            self.fixers,
            print_fn=runtime_print,
        )

    def _should_descend_dir(self, candidate: Path) -> bool:
        """
        Decide whether to continue walking into a directory.
        """
        return policy_file_scope.should_descend_dir(
            candidate,
            repo_root=self.repo_root,
            ignored_dirs=self._ignored_dirs,
            ignored_paths=self._ignored_paths,
            config_ignore_patterns=self._config_ignore_patterns,
        )

    def _resolve_file_suffixes(self) -> list[str]:
        """Resolve file suffixes using profiles and overrides."""
        return policy_file_scope.resolve_engine_file_suffixes(
            self.config,
            self._profile_registry,
            self._active_profiles,
        )

    def _load_policy_script(self, policy_id: str) -> Optional[PolicyCheck]:
        """
        Dynamically load a policy script.

        Args:
            policy_id: ID of the policy

        Returns:
            PolicyCheck instance or None if not found
        """
        return load_policy_check_instance(self.repo_root, policy_id)

    def _extract_policy_options(
        self, policy: PolicyDefinition
    ) -> Dict[str, Any]:
        """Pull custom metadata options from a policy definition."""
        return policy_check_runner.extract_policy_options(
            policy,
            reserved_metadata_keys=set(self._RESERVED_METADATA_KEYS),
        )

    @staticmethod
    def _parse_metadata_value(raw_value: str) -> Any:
        """Decode scalar/list metadata from the policy-def block."""
        return metadata_runtime.decode_metadata_option_value(raw_value)

    def report_violations(self, violations: List[Violation]):
        """
        Report violations in AI-friendly, actionable format.

        Args:
            violations: List of violations
        """
        if not violations and get_output_mode() == "quiet":
            return
        policy_reporting.report_violations(
            violations,
            passed_count=self.passed_count,
            failed_count=self.failed_count,
            print_fn=self._report_print_fn(error_channel=bool(violations)),
            fail_threshold=policy_reporting.config_fail_threshold(self.config),
            auto_fix_enabled=policy_reporting.config_auto_fix_enabled(
                self.config
            ),
        )

    def _report_single_violation(self, violation: Violation):
        """Report a single violation with full context."""
        policy_reporting.report_single_violation(
            violation, print_fn=runtime_print
        )

    def _report_summary(self, by_severity: Dict[str, List[Violation]]):
        """Report summary of violations."""
        policy_reporting.report_summary(
            by_severity,
            print_fn=self._report_print_fn(
                error_channel=any(by_severity.values())
            ),
            fail_threshold=policy_reporting.config_fail_threshold(self.config),
            auto_fix_enabled=policy_reporting.config_auto_fix_enabled(
                self.config
            ),
        )

    @staticmethod
    def _report_print_fn(*, error_channel: bool):
        """Return report printer routed for the active output mode."""
        if not (error_channel and get_output_mode() == "quiet"):
            return runtime_print

        def _stderr_print(message: str = "", **kwargs: Any) -> None:
            """Route quiet-mode violation output to stderr."""
            runtime_print(str(message), file=sys.stderr, **kwargs)

        return _stderr_print

    def should_block(self, violations: List[Violation]) -> bool:
        """
        Determine if violations should block the commit/operation.

        Args:
            violations: List of violations

        Returns:
            True if should block
        """
        return policy_reporting.should_block(
            violations,
            fail_threshold=policy_reporting.config_fail_threshold(self.config),
        )


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
