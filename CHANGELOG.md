# Changelog
**Last Updated:** 2026-02-28
**Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Managed By:** DevCovenant

## How to Log Changes
Add one entry for each substantive change under the current version header.
Keep entries newest-first and record dates in ISO format (`YYYY-MM-DD`).
Each entry must include Change/Why/Impact summary lines with action verbs.
Example:
```
## Version 1.0.1

- 2026-01-23:
  Change: Fixed null-pointer crash in invoice import.
  Why: Production job failed when optional contact data was missing.
  Impact: Imports now complete for records with partial contact details.
  Files:
  billing/imports/parser.py
  billing/imports/test_parser.py
  docs/imports.md
  Long paths should be wrapped with a trailing \
  backslash and continued on the next indented line.
  Example:
  services/customer/contact/normalization/\
    fallback_rules.py

- 2026-01-22:
  Change: Fixed duplicate email notifications on retry.
  Why: Retry worker re-enqueued already-confirmed notification events.
  Impact: Users now receive one email per successful notification event.
  Files:
  notifications/worker.py
  notifications/retry.py
  notifications/test_retry.py

## Version 1.0.0

- 2026-01-21:
  Change: Added initial release for invoice import and notification flow.
  Why: Defined a first production-ready baseline for billing automation.
  Impact: Teams can import invoices and send notifications end-to-end.
  Files:
  billing/imports/parser.py
  notifications/worker.py
  CHANGELOG.md
```
<!-- DEVCOV:END -->

## Log changes here

## Version 1.0.0

- 2026-02-28:
  Change: Strengthened `no-raw-errors` to flag broad `except Exception`
    handlers and support explicit waiver markers/regions.
  Why: Prevented hidden broad-catch drift while preserving explicit boundary
    ownership through auditable waiver metadata.
  Impact: Improved explicit-failure enforcement consistency across runtime
    boundaries, policy/plugin isolation layers, and policy documentation.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/policies/modules_need_tests/modules_need_tests.py
  devcovenant/builtin/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/builtin/policies/last_updated_placement/autofix/global.py
  devcovenant/cli.py
  devcovenant/core/services/event.py
  devcovenant/core/services/policy_autofix.py
  devcovenant/core/services/policy_check_runner.py
  devcovenant/core/services/policy_engine.py
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  tests/devcovenant/builtin/policies/no_raw_errors/\
    test_no_raw_errors.py

- 2026-02-28:
  Change: Implemented explicit runtime error contracts and CLI normalization,
    introduced builtin `no-raw-errors` policy with profile-owned metadata
    defaults, and swept docs/doc-assets to align contracts.
  Why: Standardized explicit failure surfaces at command boundaries and
    prevented raw Python error anti-pattern drift across repositories.
  Impact: Strengthened operator-facing error determinism, policy-governed
    explicit-error enforcement, and documentation fidelity for policy/profile
    ownership and runtime behavior.
  Files:
  CHANGELOG.md
  POLICY_MAP.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/devcovuser/devcovuser.yaml
  devcovenant/cli.py
  devcovenant/core/README.md
  devcovenant/core/contracts/__init__.py
  devcovenant/core/contracts/errors.py
  devcovenant/core/runtime/errors.py
  devcovenant/core/runtime/execution.py
  devcovenant/launcher_bootstrap.py
  devcovenant/builtin/policies/no_raw_errors/__init__.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_launcher_bootstrap.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/contracts/test_errors.py
  tests/devcovenant/core/runtime/test_errors.py
  tests/devcovenant/builtin/policies/no_raw_errors/\
    test_no_raw_errors.py

- 2026-02-28:
  Change: Audited every repository Markdown doc and policy/profile doc-asset
    template, and aligned managed-environment re-exec wording across repo,
    packaged, and profile-template documentation.
  Why: Prevented documentation drift after managed-interpreter hardening so
    non-executable-path behavior and rerun fallback contracts stay explicit.
  Impact: Strengthened documentation/API clarity for operators and seeded repos
    while preserving existing command and policy behavior.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml

- 2026-02-28:
  Change: Hardened managed-interpreter auto-rerun by validating executable
    paths before `execve` and falling back to rerun adapters or explicit
    managed-environment errors.
  Why: Prevented raw `PermissionError` crashes when a configured managed
    interpreter path exists but is not executable.
  Impact: Improved CLI determinism for `check`/`gate`/`test` workflows with
    clear operator-facing failures and verified fallback behavior.
  Files:
  CHANGELOG.md
  devcovenant/cli.py
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_cli.py

- 2026-02-28:
  Change: Stabilized read-only check bootstrap scope, quiet-mode error routing,
    and managed-environment defaults across policy/runtime layers.
  Why: Fixed false blocking in no-session audits and clarified output behavior
    so gate/test feedback remains deterministic and operator-visible.
  Impact: Strengthened API contracts and documentation fidelity while keeping
    strict gate enforcement for lifecycle commands and non-check paths.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/builtin/policies/managed_environment/managed_environment.py
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/devcovuser/devcovuser.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/contracts/policy.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/policy_engine.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/devflow_run_gates/\
    test_devflow_run_gates.py
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/contracts/test_policy.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_policy_engine.py

- 2026-02-28:
  Change: Fixed GitHub Actions workflow validity by replacing unsupported
    job-env `runner.temp` expressions with `.gha-pycache`.
  Why: Prevented immediate workflow parse failures that produced failed runs
    with no jobs for governance, build, and publish.
  Impact: Restored valid push-trigger governance execution while keeping build
    governance-dependent and publish manual-only.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  .github/workflows/governance-and-test.yml
  .github/workflows/publish.yml
  devcovenant/builtin/profiles/global/assets/governance-and-test.yml
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md

- 2026-02-28:
  Change: Fixed GitHub Actions workflow env parsing by replacing job-level
    `${{ runner.temp }}` pycache expressions with a stable `.gha-pycache` path.
  Why: Prevented workflow-file validation failures that blocked governance,
    build, and publish runs before any jobs were created.
  Impact: Restored push-triggered governance execution, kept build dependent on
    governance success, and kept publish manual-only with valid workflow files.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  .github/workflows/governance-and-test.yml
  .github/workflows/publish.yml
  devcovenant/builtin/profiles/global/assets/governance-and-test.yml
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md

- 2026-02-28:
  Change: Fixed governance workflow trigger rendering to emit canonical
    GitHub syntax (`on:`, `push:`, `pull_request:`) and validated it in
    refresh tests.
  Why: Prevented ambiguous serialized trigger forms (`'on':`, `*: null`) that
    can obscure push-trigger behavior after refresh regeneration.
  Impact: Kept governance/test activation on push explicit, preserved build as
    governance-dependent via `workflow_run`, and improved trigger reliability.
  Files:
  CHANGELOG.md
  .github/workflows/governance-and-test.yml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_refresh.py

- 2026-02-28:
  Change: Fixed baseline recovery regressions in deploy/refresh test fixtures
    after accidental undo drift changed seeded-install expectations.
  Why: Restored contract alignment so seeded installs exclude shipped custom
    payload policy scripts while custom profile fixtures remain
    descriptor-valid.
  Impact: Stabilized `devcovenant test` and gate recovery in this repository
    by removing false failures from seeded refresh/deploy expectations.
  Files:
  CHANGELOG.md
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Fixed upgrade/install preservation contract to keep all user custom
    payload directories without name-based pruning, and tightened package
    build rules so repository-owned custom payloads do not ship.
  Why: Preservation semantics must be explicit and name-agnostic, while
    package payload leakage is prevented at build/install boundaries.
  Impact: Upgrade now preserves `devcovenant/custom/policies/*` and
    `devcovenant/custom/profiles/*` payloads as-is, and install/upgrade no
    longer depend on one-time cleanup behavior for leaked custom payloads.
  Files:
  CHANGELOG.md
  MANIFEST.in
  devcovenant/custom/profiles/__init__.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  tests/devcovenant/test_install.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Fixed upgrade/refresh resilience by preserving custom policy trees
    while enforcing custom descriptor parity with core policies, and
    reconciled full shipped core files on every upgrade run.
  Why: Upgrade in user repositories could fail hard on stale custom policy
    scripts, and version-gated replacement could miss shipped
    `devcovenant/*.py` or builtin/core file updates.
  Impact: Preserved custom policy content, improved upgrade reliability, and
    ensured full shipped package files materialize on every upgrade run,
    with descriptor issues now blocking until fixed for both core and custom,
    without dropping repository `devcovenant/config.yaml`.
  Files:
  CHANGELOG.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/upgrade.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Added a new builtin `opencl` language profile with translator/test
    coverage and aligned profile inventory docs so shipped language coverage is
    explicit for `opencl` and `rust`.
  Why: Expanded general-purpose language support for mixed Rust/OpenCL
    repositories while keeping profile contracts and translator ownership
    discoverable in packaged docs.
  Impact: Enabled baseline OpenCL suffix/policy/translator behavior without
    forcing toolchain-specific hooks, and improved release clarity for shipped
    language-profile coverage.
  Files:
  CHANGELOG.md
  PROFILE_MAP.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/opencl/opencl.yaml
  devcovenant/builtin/profiles/opencl/opencl_translator.py
  devcovenant/docs/profiles.md
  devcovenant/docs/translators.md
  tests/devcovenant/builtin/profiles/opencl/test_opencl_translator.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-02-28:
  Change: Fixed managed-environment re-exec for lifecycle bootstrap commands
    and strengthened unmanaged-doc refresh sync to inject managed headers/
    blocks while preserving existing body content.
  Why: Fresh non-venv repos could fail lifecycle bootstrap before local policy
    scripts existed, `update_lock` required a tool that was not installed, and
    existing unmanaged docs did not receive managed headers/blocks on deploy.
  Impact: Improved machine-install reliability for lifecycle/update commands
    and preserved existing repo docs while standardizing managed headers/
    blocks during install/deploy/refresh.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  requirements.in
  requirements.lock
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_refresh.py

- 2026-02-27:
  Change: Updated repository documentation through a full `.md` sweep,
    standardized required `gate --mid` guidance across stale docs/templates,
    and removed the `audit_digest` runtime feature, code paths, and related
    tests from the refresh/registry surface.
  Why: Removed non-canonical drift artifacts and aligned release docs with the
    current gate/runtime contracts before the 1.0.0 baseline publish flow.
  Impact: Improved operator clarity, reduced maintenance surface, and kept one
    canonical workflow authority in AGENTS while preserving gate/test evidence
    behavior.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/audit_digest.py
  devcovenant/core/services/registry.py
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  tests/devcovenant/core/services/test_audit_digest.py
  tests/devcovenant/core/services/test_registry.py

- 2026-02-27:
  Change: Updated README banner tags to one-line absolute GitHub raw URLs,
    enabled defaults profile long-line escape toggles, and fixed policy-def
    metadata parsing so colon-containing continuation values stay intact for
    URL prefixes and long-line marker lists.
  Why: Fixed README/PyPI image rendering and removed parser drift that could
    truncate `allow_long_url_lines`, `long_lines_contain`, and
    `long_lines_between` metadata values.
  Impact: Improved release-readme reliability and strengthened line-length
    escape-hatch behavior so both long-line regimes and URL-based allowances
    apply consistently from managed policy metadata.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/config.yaml
  devcovenant/core/services/policy_parse.py
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  tests/devcovenant/core/services/test_policy_parse.py

- 2026-02-27:
  Change: Standardized the public `1.0.0` changelog surface by removing
    pre-1.0 internal history and keeping release-baseline entries only.
  Why: Clarified external release documentation and removed internal
    stabilization details from the public narrative.
  Impact: Reduced historical exposure while preserving `1.0.0` baseline
    traceability for current operators.
  Files:
  AGENTS.md
  CHANGELOG.md

- 2026-02-27:
  Change: Updated repository and package version surfaces from `0.2.6` to
    `1.0.0` across runtime metadata, docs headers, and global template assets.
  Why: Aligned stabilization state with release intent before mainline
    orchestration and cleanup decisions.
  Impact: Strengthened a consistent 1.0.0 baseline without changing runtime
    semantics or API contracts.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/VERSION
  devcovenant/__init__.py
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/LICENSE.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/README.md
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/translators.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
