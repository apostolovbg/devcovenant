# Changelog
**Last Updated:** 2026-02-13
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Managed By:** DevCovenant

## How to Log Changes
Add one entry for each substantive change under the current version header.
Keep entries newest-first and record dates in ISO format (`YYYY-MM-DD`).
Each entry must include Change/Why/Impact summary lines with action verbs.
Example entry:
- 2026-01-23:
  Change: Updated dependency manifests and license report.
  Why: Clarified dependency sources for release audits.
  Impact: Maintainers see updated dependency state in logs.
  Files:
  requirements.in
  requirements.lock
  THIRD_PARTY_LICENSES.md
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.py
  Long paths should be wrapped with a trailing \
  backslash and continued on the next indented line.
  Example:
  devcovenant/core/policies/dependency_license_sync/assets/\
    licenses/README.md
<!-- DEVCOV:END -->

## Log changes here

## Version 0.2.6

- 2026-02-13:
  Change: Added centralized translator runtime arbitration and routed
  `name-clarity` through translator resolution instead of extension maps.
  Why: Aligned API-freeze item 5 by moving language routing into one core
  runtime with deterministic no-match and ambiguous-match outcomes.
  Impact: Improved translator selection by driving it from active
  language-profile
  declarations, and translator-runtime behavior is covered by dedicated tests.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  SPEC_old.md
  devcovenant/README.md
  devcovenant/check.py
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/csharp/translator.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/go/translator.py
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/java/translator.py
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/javascript/translator.py
  devcovenant/core/profiles/python/assets/pyproject.toml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/python/translator.py
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/rust/translator.py
  devcovenant/core/profiles/typescript/translator.py
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/core/translator_runtime.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/gate.py
  pyproject.toml
  tests/devcovenant/core/policies/docstring_and_comment_coverage/\
    test_docstring_and_comment_coverage.py
  tests/devcovenant/core/policies/modules_need_tests/test_modules_need_tests.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/policies/security_scanner/test_security_scanner.py
  tests/devcovenant/core/profiles/csharp/test_translator.py
  tests/devcovenant/core/profiles/go/test_translator.py
  tests/devcovenant/core/profiles/java/test_translator.py
  tests/devcovenant/core/profiles/javascript/test_translator.py
  tests/devcovenant/core/profiles/python/test_translator.py
  tests/devcovenant/core/profiles/rust/test_translator.py
  tests/devcovenant/core/profiles/typescript/test_translator.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_gate.py

- 2026-02-13:
  Change: Updated refresh runtime to materialize `policy_state` as a full
  alphabetical map and removed profile-manifest policy activation state from
  `python.yaml` so activation stays config-only.
  Why: Aligned runtime behavior with the frozen activation contract and kept
  profile manifests focused on overlays/assets/hooks/selectors only.
  Impact: Improved config consistency, removed stale policy toggles
  automatically, and validated the contract with new refresh regression tests.
  Files:
  AGENTS.md

- 2026-02-12:
  Change: Clarified forward-only architecture rules in SPEC/PLAN and updated
  modules-need-tests policy text to define current-behavior test ownership.
  Why: Removed ambiguity around fallback handling and anti-legacy policing so
  implementation and tests stay aligned to target-state behavior only.
  Impact: Aligned future work to explicit no-fallback/no-anti-legacy intent,
  and updated test expectations to track live script/module behavior.
  Files:
  PLAN.md
  SPEC.md
  SPEC_old.md
  devcovenant/core/policies/modules_need_tests/modules_need_tests.yaml

- 2026-02-12:
  Change: Amended API-contract sections in SPEC and replaced PLAN with a
  dedicated API-freeze and runtime-consolidation backlog.
  Why: Clarified activation, translator ownership, metadata precedence, and
  contract-test expectations to remove interpretation drift.
  Impact: Defined a single implementation roadmap for contract freeze work
  while preserving additive extensibility rules.
  Files:
  PLAN.md
  SPEC.md
  SPEC_old.md

- 2026-02-12:
  Change: Corrected profile-manifest path references in SPEC/docs and
  constrained AGENTS policy parsing to the managed policy block markers.
  Why: Removed spec/documentation drift around `<name>.yaml` manifests and
  prevented runtime parsing from reading policy-like text outside
  `DEVCOV-POLICIES` markers.
  Impact: Clarified profile contract paths and hardened parser behavior to the
  canonical managed policy block surface.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/manifest.py
  devcovenant/core/parser.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/data/assets/.gitignore
  devcovenant/core/profiles/data/assets/data/README.md
  devcovenant/core/profiles/data/assets/data/manifest.json
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/assets/mkdocs.yml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/python/assets/venv.md
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/suffixes/assets/suffixes.txt
  devcovenant/core/profiles/suffixes/suffixes.yaml
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/profiles/data/__init__.py
  tests/devcovenant/core/profiles/suffixes/__init__.py
  tests/devcovenant/core/test_base.py
  tests/devcovenant/core/test_parser.py
  tests/devcovenant/core/test_profiles.py
  tests/devcovenant/core/test_repo_refresh.py

- 2026-02-12:
  Change: Normalized path-valued metadata overrides so singular path keys
  resolve as scalar strings in generated config and runtime policy options.
  Why: Fixed runtime warnings where list-shaped overrides reached
  `semantic-version-scope` and `version-sync` path parsing.
  Impact: Improved policy execution reliability while preserving list-based
  selector metadata behavior.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/repo_refresh.py
  tests/devcovenant/core/test_base.py
  tests/devcovenant/core/test_repo_refresh.py

- 2026-02-12:
  Change: Updated the 0.2.6 backlog status after a new SPEC-vs-reality
  audit and added the remaining path-normalization drift as an explicit item.
  Why: Clarified the dedrift close-loop state and kept unresolved behavior in
  one tracked backlog instead of implicit runtime warnings.
  Impact: Improved planning accuracy by marking completed audit work and
  isolating the next runtime-fix target for `semantic-version-scope` and
  `version-sync`.
  Files:
  PLAN.md

- 2026-02-12:
  Change: Removed profile-manifest `policies` activation lists and updated
  profile documentation to keep activation config-only via `policy_state`.
  Why: Clarified activation architecture so profile metadata stays overlays-
  only and no longer implies policy enablement semantics.
  Impact: Updated activation flow to reduce interpretation drift between
  manifests, docs, and runtime expectations.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/suffixes/suffixes.yaml
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_profiles.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-12:
  Change: Updated managed-block rendering to generate Doc ID/Doc Type/Managed
  By lines from descriptor metadata.
  Why: Removed descriptor drift where managed metadata was duplicated and could
  diverge between fields and hard-coded block text.
  Impact: Updated managed docs stay deterministic and enforceable by policy
  while preventing future metadata-line duplication drift.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/suffixes/suffixes.yaml
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-12:
  Change: Clarified registry-to-AGENTS policy compilation and AGENTS runtime
  parser requirements in SPEC, and updated PLAN dedrift status.
  Why: Aligned specification wording with the required flow where registry
  state compiles the AGENTS policy block that runtime parsing executes.
  Impact: Updated dedrift tracking and removed CONTRIBUTING descriptor marker
  duplication to keep managed-block generation consistent.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-12:
  Change: Updated AGENTS managed-doc synchronization to model separate managed,
  workflow, and policy blocks with generated markers.
  Why: Aligned block ownership so marker lines are renderer-generated and no
  longer copied from descriptor body text.
  Impact: Improved AGENTS refresh stability, legacy second-block migration,
  managed-block changelog filtering, and undeploy marker cleanup.
  Files:
  AGENTS.md
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-12:
  Change: Updated refresh config generation to regenerate all required
  autogen config sections on full refresh.
  Why: Fixed partial generated-config updates that left stale core paths and
  profile-derived metadata overlays in `devcovenant/config.yaml`.
  Impact: Added deterministic refresh behavior for config autogen sections
  while preserving user metadata overrides and user-managed doc asset entries.
  Files:
  MANIFEST.in
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/profiles.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-12:
  Change: Updated `update_lock` to always reconcile Python lock output and
  updated plan/spec requirements for the stale-hash edge case.
  Why: Removed cached-input short-circuit behavior that could preserve lock
  and license drift when `requirements.in` content stayed unchanged.
  Impact: Improved lock refresh correctness by forcing reconciliation each run
  and added regression coverage for no-short-circuit behavior.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Updated `update_lock` to resolve repository root before executing
  lock and license refresh routines.
  Why: Aligned command execution semantics so `update_lock` does not depend
  on process working directory.
  Impact: Added regression tests that validate subdirectory invocation and
  preserve metadata-driven lock/license behavior.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  devcovenant/update_lock.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Enforced lifecycle boundary checks for install, deploy, upgrade,
  and gate refresh flows.
  Why: Aligned registry generation semantics so install stays scaffold-only
  while deploy, upgrade, and check gates keep full-refresh behavior.
  Impact: Added deterministic install cleanup of stale local registry state
  and added unit regressions that validate install/deploy/upgrade/check
  boundaries.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Updated deploy flow to apply user-mode cleanup before full refresh.
  Why: Updated lifecycle behavior to match the `devcov_core_include: false`
  deploy contract without changing refresh/upgrade preservation rules.
  Impact: Updated deploy behavior now removes user-mode-only paths, and
  updated tests verify cleanup occurs on deploy while refresh stays
  non-destructive.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py

- 2026-02-11:
  Change: Updated install generic-config seeding to force canonical
  devcovuser defaults.
  Why: Corrected source-tree install drift where copied config could preserve
  non-generic active profiles.
  Impact: Updated install now writes deterministic generic install settings,
  and updated test coverage verifies profile and core-include reset behavior.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py

- 2026-02-11:
  Change: Updated lifecycle spec text and rewrote the dedrift plan backlog.
  Why: Aligned install/deploy/refresh contracts with current decisions and
  corrected deploy-only cleanup scope.
  Impact: Updated implementation backlog now tracks deterministic install
  config, deploy-only cleanup, repo-root lock refresh, and config autogen
  dedrift.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py

- 2026-02-11:
  Change: Updated packaging manifest rules to exclude root managed docs.
  Why: Clarified package artifact scope to match SPEC packaging requirements.
  Impact: Updated packaging checks to block root managed-doc includes.
  Files:
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py

- 2026-02-11:
  Change: Updated full `.gitignore` regeneration and undeploy fragment
  cleanup with preserved user-entry semantics.
  Why: Aligned refresh and undeploy behavior with SPEC requirements for
  profile/global/OS fragment synthesis and user-managed entry preservation.
  Impact: Updated `refresh` to regenerate `.gitignore` deterministically from
  profile assets and undeploy removes generated fragments while keeping user
  entries.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  devcovenant/undeploy.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_undeploy.py

- 2026-02-11:
  Change: Updated refresh orchestration to regenerate profile-driven
  pre-commit config and record resolved hooks in manifest metadata.
  Why: Aligned refresh behavior with SPEC merge order and manifest tracking
  requirements for active profile combinations.
  Impact: Improved deploy/upgrade/refresh consistency by rebuilding
  `.pre-commit-config.yaml` from global/profile fragments plus overrides and
  added regression coverage for merge ordering and hook recording.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/core/profiles.py
  devcovenant/core/repo_refresh.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  tests/devcovenant/core/test_repo_refresh.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py

- 2026-02-11:
  Change: Removed install mode semantics from the dedrift backlog and spec.
  Why: Clarified install behavior as a single-mode core copy plus generic
  config seeding.
  Impact: Updated plan/spec alignment so install does not imply nonexistent
  mode handling.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py

- 2026-02-11:
  Change: Updated install behavior to stop on existing DevCovenant installs
  and direct users to `devcovenant upgrade` without prompts.
  Why: Clarified install scope so install only places the core package and
  never drives interactive existing-artifact flows.
  Impact: Aligned runtime behavior, tests, and specification text around the
  non-interactive upgrade-directed install rule.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/docs/installation.md
  devcovenant/install.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_install.py

- 2026-02-11:
  Change: Aligned `check --start` and `check --end` with full-refresh
  behavior before gate execution and updated the active plan status.
  Why: Clarified gate-entry behavior so check invocations follow the SPEC
  contract consistently.
  Impact: Updated gate phases to rebuild registries and managed docs before
  pre-commit metadata recording, and added unit coverage for refresh order
  and refresh-failure short-circuiting.
  Files:
  PLAN.md
  devcovenant/check.py
  tests/devcovenant/test_check.py

- 2026-02-11:
  Change: Removed retired packaging residue and updated plan status for the
  packaging cleanup item.
  Why: Removed obsolete artifacts and manifest exclusions so packaged content
  stays aligned with current runtime expectations.
  Impact: Deleted the retired GPL template asset, dropped legacy
  `.devcov-state` manifest residue, and added regressions that keep this
  cleanup enforced.
  Files:
  AGENTS.md
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/dependency_license_sync/dependency_license_sync.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/refresh.py
  devcovenant/test.py
  devcovenant/undeploy.py
  devcovenant/uninstall.py
  devcovenant/update_lock.py
  devcovenant/upgrade.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_csharp.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_go.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_java.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_javascript.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_python.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_rust.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_typescript.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_csharp.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_go.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_java.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_javascript.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_python.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_rust.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_typescript.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_csharp.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_go.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_java.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_javascript.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_python.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_rust.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_typescript.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/core/test_manifest.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_update_lock.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Replaced placeholder adapter tests with concrete unittest coverage
  and updated plan status for item 5.
  Why: Improved adapter-level verification so policy adapters are exercised
  with real violations and allow cases.
  Impact: Added deterministic unit coverage for core adapter behavior and
  reduced false green runs from placeholder tests.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/refresh.py
  devcovenant/test.py
  devcovenant/undeploy.py
  devcovenant/uninstall.py
  devcovenant/upgrade.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_csharp.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_go.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_java.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_javascript.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_python.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_rust.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    test_typescript.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_csharp.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_go.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_java.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_javascript.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_python.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_rust.py
  tests/devcovenant/core/policies/name_clarity/adapters/test_typescript.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_csharp.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_go.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_java.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_javascript.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_python.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_rust.py
  tests/devcovenant/core/policies/security_scanner/adapters/test_typescript.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Updated managed-doc refresh behavior to replace all managed blocks
  and updated the active plan status.
  Why: Clarified multi-block document refresh semantics so AGENTS and other
  managed docs cannot keep stale managed-block content.
  Impact: Added regression coverage for multi-block managed-doc refresh and
  marked managed-doc/template drift cleanup complete.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/refresh.py
  devcovenant/test.py
  devcovenant/undeploy.py
  devcovenant/uninstall.py
  devcovenant/upgrade.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Removed stale current-path argument plumbing from lifecycle command
  entrypoints and updated the active plan status.
  Why: Clarified root-command execution so commands always resolve and operate
  on the current repository without hidden target-path internals.
  Impact: Updated root command/core helper boundaries and marked the boundary
  cleanup plan item complete.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/deploy.py
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/refresh.py
  devcovenant/test.py
  devcovenant/undeploy.py
  devcovenant/uninstall.py
  devcovenant/upgrade.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Removed legacy refresh helper naming from core runtime internals and
  updated the active plan status.
  Why: Clarified canonical refresh semantics so only `devcovenant refresh`
  remains operator-facing.
  Impact: Updated runtime internals to remove legacy refresh naming drift and
  marked the de-legacy plan item complete.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/repo_refresh.py
  devcovenant/docs/workflow.md
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Updated lifecycle status tracking in `PLAN.md` to mark completed
  simplification hardening work as done.
  Why: Clarified completed 0.2.6 scope so remaining tasks stay focused on
  unresolved items only.
  Impact: Updated plan status now keeps lifecycle cleanup completion explicit
  in active planning.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/docs/workflow.md
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_upgrade.py

- 2026-02-11:
  Change: Updated SPEC/PLAN and implemented metadata-driven
  `modules-need-tests` behavior for repo-wide full-audit coverage plus
  profile-defined mirror rules.
  Why: Updated test-enforcement scope and removed diff-only behavior so
  devcovrepo/devcovuser overlays define mirror expectations directly.
  Impact: Updated full mirror enforcement for this repo, custom-only mirror
  for user repos, and retained user-structured tests for non-DevCovenant
  modules.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/check.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/execution.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/docs/workflow.md
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/test_cli_options.py
  tests/devcovenant/core/test_engine.py
  tests/devcovenant/core/test_execution.py
  tests/devcovenant/support.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_upgrade.py

- 2026-02-10:
  Change: Updated check command flows, command surface, and spec/plan language
  for `check --start/--end`, default autofix, and single-command refresh.
  Why: Clarified gate operation and removed legacy command paths that no longer
  match the 0.2.6 lifecycle direction.
  Impact: Streamlined operator usage, aligned managed-doc templates, and added
  CLI coverage tests for the new check gate behavior.
  Files:
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/core/command_runtime.py
  devcovenant/core/gates.py
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/test_runner.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/docs/installation.md
  devcovenant/docs/refresh.md
  devcovenant/docs/troubleshooting.md

- 2026-02-09:
  Change: Updated policy activation flow, managed-doc sync behavior, and CLI
  command-module layout for the consolidated 0.2.6 command surface.
  Why: Removed duplicate same-name root/core command modules and finalized
  descriptor-driven managed-doc sync behavior through `doc_assets`.
  Impact: Added root-owned command implementations plus regression checks for
  command placement and managed-doc sync selection.
  Files:
  PLAN.md
  POLICY_MAP.md
  SPEC.md
  THIRD_PARTY_LICENSES.md
  devcovenant/config.yaml
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/policies/README.md
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/assets/devcovenant/run_pre_commit.py
  devcovenant/core/profiles/global/assets/devcovenant/run_tests.py
  devcovenant/core/profiles/global/assets/devcovenant/update_test_status.py
  devcovenant/core/refresh_all.py
  devcovenant/core/registry.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/update_lock.py
  devcovenant/core/update_test_status.py
  devcovenant/core/upgrade.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/docs/config.md
  devcovenant/docs/refresh.md
  devcovenant/run_pre_commit.py
  devcovenant/run_tests.py
  devcovenant/update_lock.py
  devcovenant/update_test_status.py
  licenses/pre-commit-4.5.1.txt
  licenses/pytest-9.0.2.txt
  pyproject.toml
  requirements.in
  requirements.lock
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_command_layout.py
  tests/core/tests/test_engine.py
  tests/core/tests/test_install.py
  tests/core/tests/test_policy_descriptor.py
  tests/core/tests/test_policy_inventory.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_refresh_all.py

- 2026-02-09:
  Change: Updated activation and asset ownership so stock policy assets are
  profile-owned and custom policy descriptor assets work as optional fallback.
  Why: Removed AGENTS-driven activation drift and removed direct core policy
  descriptor asset installation while keeping custom policy onboarding simple.
  Impact: Added config and tests for custom-policy fallback assets without
  custom profile wiring and blocked retired scope-key metadata reintroduction.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/config.yaml
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/policies/README.md
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/registry.py
  devcovenant/core/upgrade.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/docs/config.md
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_engine.py
  tests/core/tests/test_install.py
  tests/core/tests/test_policy_descriptor.py
  tests/core/tests/test_policy_replacements.py

- 2026-02-09:
  Change: Updated refresh flows to make policy registry the canonical resolved
  source and regenerate AGENTS policy sections from registry entries.
  Why: Removed AGENTS-first drift, removed append-missing policy-mode legacy,
  and aligned changelog coverage with managed-block-only refresh behavior.
  Impact: Streamlined refresh behavior now keeps policy rendering
  registry-first, keeps policy-mode preserve/overwrite only, and reduces
  managed-doc changelog noise.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/refresh_registry.py
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/tests/test_install.py
  tests/core/tests/test_refresh_policies.py

- 2026-02-09:
  Change: Updated managed-doc descriptor templates to generic bootstrap
  scaffolds and removed static AGENTS policy definitions from the template
  body.
  Why: Clarified bootstrap behavior so generated docs start generic while
  policy sections are generated from runtime descriptors and metadata.
  Impact: Updated new-install bootstrap output to neutral
  README/SPEC/PLAN/CHANGELOG/AGENTS
  content, and AGENTS policy sections are no longer shipped as static template
  text.
  Files:
  PLAN.md
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/install.py
  tests/core/tests/test_install.py

- 2026-02-08:
  Change: Updated `PLAN.md` to mark completed stock-text removal and
  registry-command consolidation work as done.
  Why: Clarified implementation status so immediate priorities map to
  remaining 0.2.6 work.
  Impact: Contributors continue from the correct next tasks without
  re-auditing already completed legacy cleanup.
  Files:
  PLAN.md
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml

- 2026-02-07:
  Change: Removed stock-text restore plumbing and renamed policy registry
  refresh to `refresh_registry`.
  Why: Consolidated registry workflows and retired legacy stock-text
  infrastructure in favor of descriptor `text`.
  Impact: Updated CLI/core registry flows, removed legacy files, and kept
  PLAN/SPEC in the recovered newer state.
  Files:
  README.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/engine.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devcov_integrity_guard/\
    devcov_integrity_guard.py
  devcovenant/core/policy_texts.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/refresh_registry.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/upgrade.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/registry/global/stock_policy_texts.yaml
  tests/core/tests/test_refresh_registry.py

- 2026-02-07:
  Change: Removed legacy policy override fallback behavior and legacy
  activation migration paths.
  Why: Clarified config-driven activation so `policy_state` remains the
  single authoritative enable/disable control.
  Impact: Added regression tests and clarified runtime registry state wording
  in the specification.
  Files:
  .gitignore_old
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  SPEC.md
  devcovenant/.gitignore
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.yaml
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/flutter/assets/pubspec.lock
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/refresh_policies.py
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/test_status.json
  tests/core/policies/devcov_integrity_guard/tests/\
    test_devcov_integrity_guard.py
  tests/core/policies/devflow_run_gates/tests/test_devflow_run_gates.py
  tests/core/policies/line_length_limit/tests/test_line_length_limit.py
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_base.py
  tests/core/tests/test_install.py
  tests/core/tests/test_refresh_policies.py

- 2026-02-07:
  Change: Refactored policy activation to use policy_state and removed
  profile-scope metadata keys.
  Why: Streamlined activation rules so config controls policy enablement
  uniformly for core and custom policies.
  Impact: Updated runtime, install, docs, and tests to keep activation and
  overlays consistent.
  Files:
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  .gitignore_old
  devcovenant/config.yaml
  devcovenant/.gitignore
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/devcov_integrity_guard/\
    devcov_integrity_guard.yaml
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/flutter/assets/pubspec.lock
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/refresh_policies.py
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/test_status.json
  SPEC.md
  tests/core/policies/devcov_integrity_guard/tests/\
    test_devcov_integrity_guard.py
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_refresh_policies.py

- 2026-02-07:
  Change: Updated PLAN and SPEC to keep activation migration tasks explicit.
  Why: Clarified immediate scope-removal work so implementation order stays
  aligned.
  Impact: Updated contributor guidance so config-only activation migration
  stays aligned.
  Files:
  PLAN.md
  SPEC.md
  devcovenant/registry/local/test_status.json

- 2026-02-07:
  Change: Updated changelog-coverage to require Change/Why/Impact verbs.
  Why: Clarified summary expectations to avoid vague entries.
  Impact: Users see updated change notes with explicit actions.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/deploy.py
  devcovenant/core/engine.py
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/parser.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/dependency_license_sync/assets/policy_assets.yaml
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/devcov_integrity_guard/__init__.py
  devcovenant/core/policies/devcov_integrity_guard/adapters/__init__.py
  devcovenant/core/policies/devcov_integrity_guard/assets/.gitkeep
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.yaml
  devcovenant/core/policies/devcov_integrity_guard/fixers/__init__.py
  devcovenant/core/policies/devcov_parity_guard/__init__.py
  devcovenant/core/policies/devcov_parity_guard/adapters/__init__.py
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.py
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.yaml
  devcovenant/core/policies/devcov_parity_guard/fixers/__init__.py
  devcovenant/core/policies/devcov_self_enforcement/__init__.py
  devcovenant/core/policies/devcov_self_enforcement/adapters/__init__.py
  devcovenant/core/policies/devcov_self_enforcement/assets/.gitkeep
  devcovenant/core/policies/devcov_self_enforcement/devcov_self_enforcement.py
  devcovenant/core/policies/devcov_self_enforcement/\
    devcov_self_enforcement.yaml
  devcovenant/core/policies/devcov_self_enforcement/fixers/__init__.py
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/policy_text_presence/__init__.py
  devcovenant/core/policies/policy_text_presence/adapters/__init__.py
  devcovenant/core/policies/policy_text_presence/assets/.gitkeep
  devcovenant/core/policies/policy_text_presence/fixers/__init__.py
  devcovenant/core/policies/policy_text_presence/policy_text_presence.py
  devcovenant/core/policies/policy_text_presence/policy_text_presence.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/track_test_status/__init__.py
  devcovenant/core/policies/track_test_status/adapters/__init__.py
  devcovenant/core/policies/track_test_status/assets/.gitkeep
  devcovenant/core/policies/track_test_status/fixers/__init__.py
  devcovenant/core/policies/track_test_status/track_test_status.py
  devcovenant/core/policies/track_test_status/track_test_status.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policy_schema.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/devcovuser/assets/config.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/refresh.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/registry.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/undeploy.py
  devcovenant/core/update.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/upgrade.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/README.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/registry/global/stock_policy_texts.yaml
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/test_status.json
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/policies/devcov_integrity_guard/__init__.py
  tests/core/policies/devcov_integrity_guard/tests/__init__.py
  tests/core/policies/devcov_integrity_guard/tests/\
    test_devcov_integrity_guard.py
  tests/core/policies/devcov_parity_guard/__init__.py
  tests/core/policies/devcov_parity_guard/tests/__init__.py
  tests/core/policies/devcov_parity_guard/tests/test_devcov_parity_guard.py
  tests/core/policies/devcov_self_enforcement/__init__.py
  tests/core/policies/devcov_self_enforcement/tests/__init__.py
  tests/core/policies/devcov_self_enforcement/tests/\
    test_devcov_self_enforcement.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/policies/policy_text_presence/__init__.py
  tests/core/policies/policy_text_presence/tests/__init__.py
  tests/core/policies/policy_text_presence/tests/test_policy_text_presence.py
  tests/core/policies/track_test_status/__init__.py
  tests/core/policies/track_test_status/tests/__init__.py
  tests/core/policies/track_test_status/tests/test_track_test_status.py
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_install.py
  tests/core/tests/test_parser.py
  tests/core/tests/test_policy_freeze.py
  tests/core/tests/test_policy_metadata_schema.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_policy_schema.py
  tests/core/tests/test_refresh_policies.py
  tests/custom/profiles/test_custom_profiles.py
  tests/devcovenant/__init__.py
  tests/devcovenant/core/__init__.py
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/devcov_integrity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/new_modules_need_tests/__init__.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/data/__init__.py
  tests/devcovenant/core/profiles/devcovuser/__init__.py
  tests/devcovenant/core/profiles/docker/__init__.py
  tests/devcovenant/core/profiles/docs/__init__.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/flutter/__init__.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/global/__init__.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/kubernetes/__init__.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/suffixes/__init__.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/terraform/__init__.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/custom/__init__.py
  tests/devcovenant/custom/policies/__init__.py
  tests/devcovenant/custom/policies/devcov_raw_string_escapes/__init__.py
  tests/devcovenant/custom/policies/managed_doc_assets/__init__.py
  tests/devcovenant/custom/policies/readme_sync/__init__.py
  tests/devcovenant/custom/profiles/__init__.py
  tests/devcovenant/custom/profiles/devcovrepo/__init__.py

- 2026-02-06: Consolidated registry format, policy metadata flow, and docs.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/deploy.py
  devcovenant/core/engine.py
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/parser.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/dependency_license_sync/assets/policy_assets.yaml
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.yaml
  devcovenant/core/policies/devcov_self_enforcement/\
    devcov_self_enforcement.yaml
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/policy_text_presence/policy_text_presence.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/track_test_status/track_test_status.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policy_schema.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/devcovuser/assets/config.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/refresh.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/registry.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/undeploy.py
  devcovenant/core/update.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/upgrade.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/docs/README.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/test_status.json
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/policies/devcov_parity_guard/tests/test_devcov_parity_guard.py
  tests/core/policies/devcov_self_enforcement/tests/\
    test_devcov_self_enforcement.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/policies/policy_text_presence/tests/test_policy_text_presence.py
  tests/core/profiles/test_profiles.py
  tests/core/tests/test_install.py
  tests/core/tests/test_parser.py
  tests/core/tests/test_policy_freeze.py
  tests/core/tests/test_policy_metadata_schema.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_policy_schema.py
  tests/core/tests/test_refresh_policies.py
  tests/custom/profiles/test_custom_profiles.py
  tests/devcovenant/__init__.py
  tests/devcovenant/core/__init__.py
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/devcov_parity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_self_enforcement/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/new_modules_need_tests/__init__.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/policy_text_presence/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/track_test_status/__init__.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/data/__init__.py
  tests/devcovenant/core/profiles/devcovuser/__init__.py
  tests/devcovenant/core/profiles/docker/__init__.py
  tests/devcovenant/core/profiles/docs/__init__.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/flutter/__init__.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/global/__init__.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/kubernetes/__init__.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/suffixes/__init__.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/terraform/__init__.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/custom/__init__.py
  tests/devcovenant/custom/policies/__init__.py
  tests/devcovenant/custom/policies/devcov_raw_string_escapes/__init__.py
  tests/devcovenant/custom/policies/managed_doc_assets/__init__.py
  tests/devcovenant/custom/policies/readme_sync/__init__.py
  tests/devcovenant/custom/profiles/__init__.py
  tests/devcovenant/custom/profiles/devcovrepo/__init__.py

- 2026-02-06: Switch policy assets to descriptors and drop the asset registry.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/deploy.py
  devcovenant/core/engine.py
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/parser.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/dependency_license_sync/assets/policy_assets.yaml
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.yaml
  devcovenant/core/policies/devcov_self_enforcement/\
    devcov_self_enforcement.yaml
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/policy_text_presence/policy_text_presence.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/track_test_status/track_test_status.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policy_schema.py
  devcovenant/core/profiles/devcovuser/assets/config.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/refresh.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/registry.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/undeploy.py
  devcovenant/core/update.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/upgrade.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/docs/README.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/test_status.json
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/policies/devcov_parity_guard/tests/test_devcov_parity_guard.py
  tests/core/policies/devcov_self_enforcement/tests/\
    test_devcov_self_enforcement.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/policies/policy_text_presence/tests/test_policy_text_presence.py
  tests/core/tests/test_install.py
  tests/core/tests/test_parser.py
  tests/core/tests/test_policy_freeze.py
  tests/core/tests/test_policy_metadata_schema.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_policy_schema.py
  tests/core/tests/test_refresh_policies.py
  tests/devcovenant/__init__.py
  tests/devcovenant/core/__init__.py
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/devcov_parity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_self_enforcement/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/new_modules_need_tests/__init__.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/policy_text_presence/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/track_test_status/__init__.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/data/__init__.py
  tests/devcovenant/core/profiles/devcovuser/__init__.py
  tests/devcovenant/core/profiles/docker/__init__.py
  tests/devcovenant/core/profiles/docs/__init__.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/flutter/__init__.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/global/__init__.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/kubernetes/__init__.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/suffixes/__init__.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/terraform/__init__.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/custom/__init__.py
  tests/devcovenant/custom/policies/__init__.py
  tests/devcovenant/custom/policies/devcov_raw_string_escapes/__init__.py
  tests/devcovenant/custom/policies/managed_doc_assets/__init__.py
  tests/devcovenant/custom/policies/readme_sync/__init__.py
  tests/devcovenant/custom/profiles/__init__.py
  tests/devcovenant/custom/profiles/devcovrepo/__init__.py
- 2026-02-06: Integrated pre-commit config generation with refresh and docs.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/deploy.py
  devcovenant/core/engine.py
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policy_schema.py
  devcovenant/core/profiles/devcovuser/assets/config.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/refresh.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/registry.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/undeploy.py
  devcovenant/core/update.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/upgrade.py
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/README.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_assets.yaml
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/test_status.json
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/tests/test_install.py
  tests/core/tests/test_policy_metadata_schema.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_policy_schema.py
  tests/devcovenant/__init__.py
  tests/devcovenant/core/__init__.py
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/devcov_parity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_self_enforcement/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/new_modules_need_tests/__init__.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/policy_text_presence/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/track_test_status/__init__.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/data/__init__.py
  tests/devcovenant/core/profiles/devcovuser/__init__.py
  tests/devcovenant/core/profiles/docker/__init__.py
  tests/devcovenant/core/profiles/docs/__init__.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/flutter/__init__.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/global/__init__.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/kubernetes/__init__.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/suffixes/__init__.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/terraform/__init__.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/custom/__init__.py
  tests/devcovenant/custom/policies/__init__.py
  tests/devcovenant/custom/policies/devcov_raw_string_escapes/__init__.py
  tests/devcovenant/custom/policies/managed_doc_assets/__init__.py
  tests/devcovenant/custom/policies/readme_sync/__init__.py
  tests/devcovenant/custom/profiles/__init__.py
  tests/devcovenant/custom/profiles/devcovrepo/__init__.py

- 2026-02-06: Seeded config, added lifecycle tests, aligned docs/plan.
  Files:
    AGENTS.md
    CONTRIBUTING.md
    PLAN.md
    README.md
    SPEC.md
    devcovenant/README.md
    devcovenant/cli.py
    devcovenant/config.yaml
    devcovenant/core/cli_options.py
    devcovenant/core/deploy.py
    devcovenant/core/engine.py
    devcovenant/core/generate_policy_metadata_schema.py
    devcovenant/core/install.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    devcovenant/core/policies/changelog_coverage/fixers/global.py
    devcovenant/core/policies/last_updated_placement/fixers/global.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.yaml
    devcovenant/core/policy_schema.py
    devcovenant/core/profiles/devcovuser/assets/config.yaml
    devcovenant/core/profiles/devcovuser/devcovuser.yaml
    devcovenant/core/profiles/global/assets/AGENTS.yaml
    devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    devcovenant/core/profiles/global/assets/PLAN.yaml
    devcovenant/core/profiles/global/assets/README.yaml
    devcovenant/core/profiles/global/assets/SPEC.yaml
    devcovenant/core/profiles/global/assets/devcovenant/README.yaml
    devcovenant/core/refresh.py
    devcovenant/core/refresh_all.py
    devcovenant/core/refresh_policies.py
    devcovenant/core/registry.py
    devcovenant/core/run_pre_commit.py
    devcovenant/core/run_tests.py
    devcovenant/core/undeploy.py
    devcovenant/core/update.py
    devcovenant/core/update_policy_registry.py
    devcovenant/core/upgrade.py
    devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
    devcovenant/docs/README.md
    devcovenant/docs/config.md
    devcovenant/docs/installation.md
    devcovenant/docs/policies.md
    devcovenant/docs/refresh.md
    devcovenant/docs/registry.md
    tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
    tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    tests/core/tests/test_install.py
    tests/core/tests/test_policy_metadata_schema.py
    tests/core/tests/test_policy_replacements.py
    tests/core/tests/test_policy_schema.py

- 2026-02-06: Refined install/deploy lifecycle, config gating, and docs/tests.
  Files:
    AGENTS.md
    CONTRIBUTING.md
    PLAN.md
    README.md
    SPEC.md
    devcovenant/README.md
    devcovenant/cli.py
    devcovenant/config.yaml
    devcovenant/core/cli_options.py
    devcovenant/core/deploy.py
    devcovenant/core/engine.py
    devcovenant/core/generate_policy_metadata_schema.py
    devcovenant/core/install.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    devcovenant/core/policies/changelog_coverage/fixers/global.py
    devcovenant/core/policies/last_updated_placement/fixers/global.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.yaml
    devcovenant/core/policy_schema.py
    devcovenant/core/profiles/devcovuser/devcovuser.yaml
    devcovenant/core/profiles/global/assets/AGENTS.yaml
    devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    devcovenant/core/profiles/global/assets/PLAN.yaml
    devcovenant/core/profiles/global/assets/README.yaml
    devcovenant/core/profiles/global/assets/SPEC.yaml
    devcovenant/core/profiles/global/assets/devcovenant/README.yaml
    devcovenant/core/refresh.py
    devcovenant/core/refresh_all.py
    devcovenant/core/refresh_policies.py
    devcovenant/core/registry.py
    devcovenant/core/run_pre_commit.py
    devcovenant/core/run_tests.py
    devcovenant/core/undeploy.py
    devcovenant/core/update.py
    devcovenant/core/update_policy_registry.py
    devcovenant/core/upgrade.py
    devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
    devcovenant/docs/README.md
    devcovenant/docs/config.md
    devcovenant/docs/installation.md
    devcovenant/docs/policies.md
    devcovenant/docs/refresh.md
    devcovenant/docs/registry.md
    tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
    tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    tests/core/tests/test_install.py
    tests/core/tests/test_policy_metadata_schema.py
    tests/core/tests/test_policy_replacements.py
    tests/core/tests/test_policy_schema.py

- 2026-02-06: Adjusted lifecycle flow and hook wiring; reduced noise scope.
  Files:
    AGENTS.md
    CONTRIBUTING.md
    PLAN.md
    README.md
    SPEC.md
    devcovenant/README.md
    devcovenant/cli.py
    devcovenant/core/cli_options.py
    devcovenant/core/deploy.py
    devcovenant/core/engine.py
    devcovenant/core/generate_policy_metadata_schema.py
    devcovenant/core/install.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    devcovenant/core/policies/changelog_coverage/fixers/global.py
    devcovenant/core/policies/last_updated_placement/fixers/global.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.yaml
    devcovenant/core/policy_schema.py
    devcovenant/core/profiles/global/assets/AGENTS.yaml
    devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    devcovenant/core/profiles/global/assets/PLAN.yaml
    devcovenant/core/profiles/global/assets/README.yaml
    devcovenant/core/profiles/global/assets/SPEC.yaml
    devcovenant/core/profiles/global/assets/devcovenant/README.yaml
    devcovenant/core/refresh_all.py
    devcovenant/core/refresh.py
    devcovenant/core/refresh_policies.py
    devcovenant/core/registry.py
    devcovenant/core/run_pre_commit.py
    devcovenant/core/run_tests.py
    devcovenant/core/undeploy.py
    devcovenant/core/update.py
    devcovenant/core/update_policy_registry.py
    devcovenant/core/upgrade.py
    devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
    devcovenant/core/profiles/devcovuser/devcovuser.yaml
    devcovenant/docs/config.md
    devcovenant/docs/policies.md
    devcovenant/docs/registry.md
    tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
    tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    tests/core/tests/test_install.py
    tests/core/tests/test_policy_replacements.py
    tests/core/tests/test_policy_metadata_schema.py
    tests/core/tests/test_policy_schema.py

- 2026-02-06: Aligned metadata refresh with plan tracking and registry/docs.
  Files:
    AGENTS.md
    PLAN.md
    SPEC.md
    devcovenant/cli.py
    devcovenant/core/engine.py
    devcovenant/core/generate_policy_metadata_schema.py
    devcovenant/core/install.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    devcovenant/core/policies/changelog_coverage/fixers/global.py
    devcovenant/core/policies/last_updated_placement/last_updated_placement.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.yaml
    devcovenant/core/policies/last_updated_placement/fixers/global.py
    devcovenant/core/policy_schema.py
    devcovenant/core/profiles/global/assets/AGENTS.yaml
    devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    devcovenant/core/profiles/global/assets/PLAN.yaml
    devcovenant/core/profiles/global/assets/README.yaml
    devcovenant/core/profiles/global/assets/SPEC.yaml
    devcovenant/core/profiles/global/assets/devcovenant/README.yaml
    devcovenant/core/refresh_all.py
    devcovenant/core/refresh_policies.py
    devcovenant/core/registry.py
    devcovenant/core/run_pre_commit.py
    devcovenant/core/run_tests.py
    devcovenant/core/update.py
    devcovenant/core/update_policy_registry.py
    devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
    devcovenant/docs/config.md
    devcovenant/docs/policies.md
    devcovenant/docs/registry.md
    tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
    tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    tests/core/tests/test_policy_metadata_schema.py
    tests/core/tests/test_policy_schema.py

- 2026-02-06: Removed schema reg plumbing and made policy metadata flow lean.
  Files:
    AGENTS.md
    PLAN.md
    SPEC.md
    devcovenant/cli.py
    devcovenant/core/engine.py
    devcovenant/core/generate_policy_metadata_schema.py
    devcovenant/core/install.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    devcovenant/core/policies/changelog_coverage/fixers/global.py
    devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.py
    devcovenant/core/policy_schema.py
    devcovenant/core/profiles/global/assets/AGENTS.yaml
    devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    devcovenant/core/profiles/global/assets/PLAN.yaml
    devcovenant/core/profiles/global/assets/README.yaml
    devcovenant/core/profiles/global/assets/SPEC.yaml
    devcovenant/core/profiles/global/assets/devcovenant/README.yaml
    devcovenant/core/refresh_all.py
    devcovenant/core/refresh_policies.py
    devcovenant/core/registry.py
    devcovenant/core/run_pre_commit.py
    devcovenant/core/run_tests.py
    devcovenant/core/update.py
    devcovenant/core/update_policy_registry.py
    devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
    devcovenant/docs/config.md
    devcovenant/docs/policies.md
    devcovenant/docs/registry.md
    tests/core/policies/changelog_coverage/tests/\
      test_changelog_coverage.py
    tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    tests/core/tests/test_policy_metadata_schema.py
    tests/core/tests/test_policy_schema.py

- 2026-02-05: Documented metadata-flow refactor plus plan/spec and docs.
  Files:
    - AGENTS.md
    - devcovenant/core/install.py
    - devcovenant/core/policies/changelog_coverage/changelog_coverage.py
    - devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
    - devcovenant/core/policies/changelog_coverage/fixers/__init__.py
    - devcovenant/core/policies/changelog_coverage/fixers/global.py
    - devcovenant/core/policies/last_updated_placement/\
      last_updated_placement.py
    - devcovenant/core/run_pre_commit.py
    - devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
    - devcovenant/docs/config.md
    - tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
    - tests/core/policies/last_updated_placement/tests/\
      test_last_updated_placement.py
    - SPEC.md
    - PLAN.md
    - devcovenant/docs/registry.md
    - devcovenant/docs/policies.md
    - devcovenant/core/profiles/global/assets/AGENTS.yaml
    - devcovenant/core/profiles/global/assets/CHANGELOG.yaml
    - devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
    - devcovenant/core/profiles/global/assets/PLAN.yaml
    - devcovenant/core/profiles/global/assets/README.yaml
    - devcovenant/core/profiles/global/assets/SPEC.yaml
    - devcovenant/core/profiles/global/assets/devcovenant/README.yaml

- 2026-02-05: Switched managed docs to YAML assets and updated install flow.
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/last_updated_placement/\
    last_updated_placement.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/devcovenant/\
    README.yaml
  devcovenant/core/run_pre_commit.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/docs/config.md
  tests/core/policies/changelog_coverage/tests/\
    test_changelog_coverage.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py

- 2026-02-05: Aligned plan with spec, refined changelog tooling, and doc stamp.
  Files:
  AGENTS.md
  PLAN.md
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/changelog_coverage/fixers/__init__.py
  devcovenant/core/policies/changelog_coverage/fixers/global.py
  devcovenant/core/policies/last_updated_placement/\
    last_updated_placement.py
  devcovenant/core/run_pre_commit.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/docs/config.md
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py

- 2026-02-05: Generalized dependency-license-sync metadata, shifted manifest
  lists into profiles, and updated docs/spec/plan guidance.
  Files:
  AGENTS.md
  PLAN.md
  POLICY_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.py
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/stock_policy_texts.json
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/registry/global/stock_policy_texts.yaml
  tests/core/policies/dependency_license_sync/tests/\
    test_dependency_license_sync.py

- 2026-02-04: Expanded DevCovenant docs and linked the detailed guide set
  from the main README while wiring the devcovrepo profile to track the
  full docs catalog.
  Files:
  README.md
  devcovenant/README.md
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    adapters.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/\
    workflow.md
  devcovenant/docs/README.md
  devcovenant/docs/adapters.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md

- 2026-02-04: Moved VERSION into devcovenant/, updated packaging scope,
  removed .devcov-state usage, and refreshed version policy paths.
  Files:
  AGENTS.md
  CITATION.cff
  MANIFEST.in
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/VERSION
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/profiles.py
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/CITATION.yaml
  devcovenant/core/profiles/global/assets/VERSION
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/update.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/registry/global/stock_policy_texts.yaml
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/tests/test_engine.py
  tests/core/tests/test_install.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_refresh_policies.py

- 2026-02-04: Accelerated install tests, tightened changelog coverage, and
  added CLI stage output.
  Files:
  AGENTS.md
  CITATION.cff
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/profiles.py
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/CITATION.yaml
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/update.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/tests/test_engine.py
  tests/core/tests/test_install.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_refresh_policies.py

- 2026-02-04: Relocated test_status.json into the local registry, refreshed
  devflow/track-test-status wiring, repaired gitignore templates/refresh, and
  removed legacy registry/config files.
  Files:
  .gitignore
  AGENTS.md
  CHANGELOG.md
  CITATION.cff
  MANIFEST.in
  PLAN.md
  POLICY_MAP.md
  README.md
  SPEC.md
  devcovenant/config.yaml
  devcovenant/config_old.yaml
  devcovenant/registry.json
  devcovenant/registry/local/policy_metadata_schema.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/cli.py
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/track_test_status/track_test_status.py
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/global/assets/.gitignore
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CITATION.yaml
  devcovenant/core/profiles/global/assets/gitignore_base.txt
  devcovenant/core/profiles/global/assets/gitignore_os.txt
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles.py
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/update.py
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  tests/core/tests/test_engine.py
  tests/core/tests/test_refresh_policies.py
  tests/core/policies/devflow_run_gates/tests/test_devflow_run_gates.py

- 2026-02-03: Enforced daily, file-complete changelog coverage; simplified
  check modes to audit/fix; regenerated managed docs and synced README
  descriptors.
  Files:
  PLAN.md
  SPEC.md
  AGENTS.md
  CONTRIBUTING.md
  README.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/engine.py
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/install.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  PROFILE_MAP.md
  devcovenant/core/profiles/php/assets/phpunit.xml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/docs/README.md
  devcovenant/core/update_policy_registry.py
  devcovenant/core/refresh_all.py
  tests/core/policies/changelog_coverage/tests/changelog_coverage_impl.py
  tests/core/policies/changelog_coverage/tests/test_changelog_coverage.py
  MANIFEST.in
- 2026-02-02: Aligned docs/data profiles with doc-quality policies and added
  dependency-license-sync coverage for Objective-C (Podfile/lock manifests).
  Files:
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
- 2026-02-02: Updated POLICY_MAP/PROFILE_MAP to reflect the doc/data/
  objective-c policy expectations and manifest overlays.
  Files:
  POLICY_MAP.md
  PROFILE_MAP.md
- 2026-02-02: Added documentation-growth-tracking overlays for docs/global
  profiles to enumerate user-facing suffixes explicitly.
  Files:
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/global/global.yaml
- 2026-02-02: Generated canonical policy metadata schema from descriptors and
  added regression test to keep it in sync.
  Files:
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/registry/local/policy_metadata_schema.yaml
  tests/core/tests/test_policy_metadata_schema.py
  PLAN.md
- 2026-02-02: refresh_policies now regenerates the canonical metadata schema
  before rebuilding AGENTS policy blocks to keep descriptors and schema
  aligned.
  Files:
  devcovenant/core/refresh_policies.py
- 2026-02-02: Moved policy_metadata_schema.yaml to registry/local,
  auto-generated on every run (engine startup/refresh) so CI/users never rely
  on a packaged schema copy.
  Files:
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/engine.py
  devcovenant/registry/local/policy_metadata_schema.yaml
  devcovenant/registry/global/policy_metadata_schema.yaml
- 2026-02-02: `devcovenant test` now delegates to the full test runner
  (pytest + unittest discover) to match devflow gates.
  Files:
  devcovenant/cli.py
- 2026-02-02: Regenerated managed docs from YAML assets, removed duplicated
  managed blocks, and refreshed Last Updated headers.
  Files:
  AGENTS.md
  CONTRIBUTING.md
  SPEC.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
- 2026-02-02: Marked PLAN tasks for map materialization and profile descriptor
  completion as done after aligning profiles/policies with reference maps.
  Files:
  PLAN.md
- 2026-02-02: Clarified dependency-license-sync as profile-scoped (not global)
  and removed it from the global profile; map now documents per-profile
  activation only.
  Files:
  POLICY_MAP.md
  devcovenant/core/profiles/global/global.yaml
- 2026-02-02: Added version-sync activation to all retained profiles per
  POLICY_MAP coverage.
  Files:
  devcovenant/core/profiles/*/*.yaml
- 2026-02-02: Ensured update/refresh notifications always persist by creating
  manifest.json on demand and added a regression test.
  Files:
  devcovenant/core/manifest.py
  tests/core/tests/test_manifest.py
  devcovenant/core/profiles/flutter/assets/pubspec.lock
  devcovenant/core/profiles/csharp/assets/packages.lock.json
- 2026-02-02: Added starter assets for flutter (.gitignore) and objective-c
  (Podfile) to improve profile completeness.
  Files:
  devcovenant/core/profiles/flutter/assets/.gitignore
  devcovenant/core/profiles/objective-c/assets/Podfile
- 2026-02-02: Filled remaining profile assets (devcovuser .gitignore, suffixes
  suffixes.txt) and made profile asset checks dynamic.
  Files:
  devcovenant/core/profiles/devcovuser/assets/.gitignore
  devcovenant/core/profiles/suffixes/assets/suffixes.txt
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/suffixes/suffixes.yaml
  devcovenant/core/profiles.py
  tests/core/profiles/test_profiles.py
- 2026-02-02: Switched all profile .gitignore assets to merge mode, fixed
  objective-c/flutter asset manifests, and expanded POLICY_MAP/PROFILE_MAP
  into full reference guides.
  Files:
  POLICY_MAP.md
  PROFILE_MAP.md
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/devcovuser/assets/.gitignore
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
- 2026-02-02: Wove the expanded policy/profile maps into SPEC and PLAN (maps
  declared authoritative references; new PLAN task to materialize them).
  Files:
  SPEC.md
  PLAN.md
- 2026-02-01: Made all policies explicitly profile-activated (global now lists
  every global policy), expanded POLICY_MAP/PROFILE_MAP details, and updated
  SPEC/PLAN plus config defaults.
  Files:
  POLICY_MAP.md
  PROFILE_MAP.md
  SPEC.md
  PLAN.md
  devcovenant/core/profiles/global/global.yaml (custom policies remain in
  devcovrepo/config, not global)
  devcovenant/config.yaml
- 2026-02-01: Trimmed stock profiles to a core set and refreshed maps/README.
  Adjusted scopes for new-modules-need-tests and security-scanner.
  Files:
  POLICY_MAP.md
  PROFILE_MAP.md
  devcovenant/core/profiles/README.md
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/profiles/*
- 2026-02-01: Retired the profile-policy-map custom policy and clarified that
  core profile YAMLs are static descriptors (PROFILE/POLICY maps are references
  only); aligned SPEC/PLAN/AGENTS and registries accordingly.
  Files:
  AGENTS.md
  PLAN.md
  POLICY_MAP.md
  SPEC.md
  devcovenant/registry/local/policy_metadata_schema.yaml
- 2026-02-01: Implemented name-clarity adapters for JS/TS/Go/Rust/Java/C#,
  expanded default suffix coverage, and added adapter tests.
  Files:
  devcovenant/core/policies/name_clarity/name_clarity.py
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/name_clarity/adapters/javascript.py
  devcovenant/core/policies/name_clarity/adapters/typescript.py
  devcovenant/core/policies/name_clarity/adapters/go.py
  devcovenant/core/policies/name_clarity/adapters/rust.py
  devcovenant/core/policies/name_clarity/adapters/java.py
  devcovenant/core/policies/name_clarity/adapters/csharp.py
  tests/core/policies/name_clarity/tests/test_name_clarity.py
  POLICY_MAP.md
- 2026-02-01: Enabled name-clarity policy across JS/TS/Go/Rust/Java/C#
  profiles with overlays keyed to their suffixes.
  Files:
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/csharp/csharp.yaml
- 2026-02-01: Added doc/comment coverage adapters for JS/TS/Go/Rust/Java/C#
  and enabled the policy across corresponding profiles.
  Files:
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.py
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    javascript.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    typescript.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/go.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/rust.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/java.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/\
    csharp.py
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/csharp/csharp.yaml
  tests/core/policies/docstring_and_comment_coverage/tests/\
    test_docstring_and_comment_coverage.py
  POLICY_MAP.md
- 2026-02-01: Extended new-modules-need-tests and security-scanner to JS/TS/\
  Go/Rust/Java/C# with adapters, profile overlays, and tests.
  Files:
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.py
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/new_modules_need_tests/adapters/javascript.py
  devcovenant/core/policies/new_modules_need_tests/adapters/typescript.py
  devcovenant/core/policies/new_modules_need_tests/adapters/go.py
  devcovenant/core/policies/new_modules_need_tests/adapters/rust.py
  devcovenant/core/policies/new_modules_need_tests/adapters/java.py
  devcovenant/core/policies/new_modules_need_tests/adapters/csharp.py
  devcovenant/core/policies/security_scanner/security_scanner.py
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/security_scanner/adapters/javascript.py
  devcovenant/core/policies/security_scanner/adapters/typescript.py
  devcovenant/core/policies/security_scanner/adapters/go.py
  devcovenant/core/policies/security_scanner/adapters/rust.py
  devcovenant/core/policies/security_scanner/adapters/java.py
  devcovenant/core/policies/security_scanner/adapters/csharp.py
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/csharp/csharp.yaml
  tests/core/policies/new_modules_need_tests/tests/\
    test_new_modules_need_tests.py
  tests/core/policies/security_scanner/tests/test_security_scanner.py
  POLICY_MAP.md
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/custom/policies/profile_policy_map/profile_policy_map.py
  devcovenant/custom/policies/profile_policy_map/profile_policy_map.yaml
  tests/custom/policies/test_profile_policy_map.py

- 2026-02-01: Filled key profile descriptors from stubs (data exclusions, Rails
  manifest/policies, Angular/JVM build gates, Quarkus assets) to match the
  reference guidance.
  Files:
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/rails/rails.yaml
  devcovenant/core/profiles/angular/angular.yaml
  devcovenant/core/profiles/quarkus/quarkus.yaml
  devcovenant/core/profiles/express/express.yaml
  devcovenant/core/profiles/nestjs/nestjs.yaml
  devcovenant/core/profiles/react/react.yaml
  devcovenant/core/profiles/nextjs/nextjs.yaml
  devcovenant/core/profiles/vue/vue.yaml
  devcovenant/core/profiles/nuxt/nuxt.yaml
  devcovenant/core/profiles/svelte/svelte.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/kotlin/kotlin.yaml
  devcovenant/core/profiles/scala/scala.yaml
  devcovenant/core/profiles/groovy/groovy.yaml
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/fsharp/fsharp.yaml
  devcovenant/core/profiles/laravel/laravel.yaml
  devcovenant/core/profiles/symfony/symfony.yaml
  devcovenant/core/profiles/spring/spring.yaml
  devcovenant/core/profiles/micronaut/micronaut.yaml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/ansible/ansible.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/zig/zig.yaml
  devcovenant/core/profiles/ocaml/ocaml.yaml
  devcovenant/core/profiles/nim/nim.yaml
  devcovenant/core/profiles/lua/lua.yaml
  devcovenant/core/profiles/perl/perl.yaml
  devcovenant/core/profiles/r/r.yaml
  devcovenant/core/profiles/lisp/lisp.yaml
  devcovenant/core/run_tests.py
  SPEC.md
  PLAN.md
  devcovenant/core/policies/docstring_and_comment_coverage/\
docstring_and_comment_coverage.py
  devcovenant/core/policies/docstring_and_comment_coverage/adapters/python.py
  devcovenant/core/policies/name_clarity/name_clarity.py
  devcovenant/core/policies/name_clarity/adapters/python.py
  devcovenant/core/policies/security_scanner/security_scanner.py
  devcovenant/core/policies/security_scanner/adapters/python.py
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.py
  devcovenant/core/policies/new_modules_need_tests/adapters/python.py
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.yaml
  devcovenant/core/policies/name_clarity/adapters/javascript.py
  devcovenant/core/policies/name_clarity/adapters/typescript.py
  devcovenant/core/policies/name_clarity/adapters/go.py
  devcovenant/core/policies/name_clarity/adapters/rust.py
  devcovenant/core/policies/name_clarity/adapters/java.py
  devcovenant/core/policies/name_clarity/adapters/csharp.py
  tests/core/policies/docstring_and_comment_coverage/tests/\
test_docstring_and_comment_coverage.py
  tests/core/policies/name_clarity/tests/test_name_clarity.py
  tests/core/policies/security_scanner/tests/test_security_scanner.py

- 2026-02-01: Tracked the new per-profile descriptors and managed doc assets to
  align metadata with PROFILE_MAP/POLICY_MAP.
  Files:
  devcovenant/core/profiles/global/assets/CITATION.yaml
  devcovenant/core/profiles/global/assets/LICENSE.yaml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/angular/angular.yaml
  devcovenant/core/profiles/ansible/ansible.yaml
  devcovenant/core/profiles/bash/bash.yaml
  devcovenant/core/profiles/c/c.yaml
  devcovenant/core/profiles/clojure/clojure.yaml
  devcovenant/core/profiles/cobol/cobol.yaml
  devcovenant/core/profiles/cpp/cpp.yaml
  devcovenant/core/profiles/crystal/crystal.yaml
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/data/data.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/django/django.yaml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/dotnet/dotnet.yaml
  devcovenant/core/profiles/elixir/elixir.yaml
  devcovenant/core/profiles/erlang/erlang.yaml
  devcovenant/core/profiles/express/express.yaml
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flask/flask.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/fortran/fortran.yaml
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/fsharp/fsharp.yaml
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/groovy/groovy.yaml
  devcovenant/core/profiles/haskell/haskell.yaml
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/julia/julia.yaml
  devcovenant/core/profiles/kotlin/kotlin.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/laravel/laravel.yaml
  devcovenant/core/profiles/lisp/lisp.yaml
  devcovenant/core/profiles/lua/lua.yaml
  devcovenant/core/profiles/matlab/matlab.yaml
  devcovenant/core/profiles/micronaut/micronaut.yaml
  devcovenant/core/profiles/nestjs/nestjs.yaml
  devcovenant/core/profiles/nextjs/nextjs.yaml
  devcovenant/core/profiles/nim/nim.yaml
  devcovenant/core/profiles/nuxt/nuxt.yaml
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/ocaml/ocaml.yaml
  devcovenant/core/profiles/pascal/pascal.yaml
  devcovenant/core/profiles/perl/perl.yaml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/powershell/powershell.yaml
  devcovenant/core/profiles/prolog/prolog.yaml
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/quarkus/quarkus.yaml
  devcovenant/core/profiles/r/r.yaml
  devcovenant/core/profiles/rails/rails.yaml
  devcovenant/core/profiles/react/react.yaml
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/scala/scala.yaml
  devcovenant/core/profiles/scheme/scheme.yaml
  devcovenant/core/profiles/spring/spring.yaml
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/suffixes/suffixes.yaml
  devcovenant/core/profiles/svelte/svelte.yaml
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/symfony/symfony.yaml
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/profiles/vue/vue.yaml
  devcovenant/core/profiles/zig/zig.yaml
- 2026-02-01: Synced dependency license records and metadata classifiers; added
  AUTO_LICENSE_SYNC marker to license assets and declared Python 3.13/3.14
  support in PyPI classifiers.
  Files:
  THIRD_PARTY_LICENSES.md
  licenses/AUTO_LICENSE_SYNC.txt
  pyproject.toml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
- 2026-02-01: Added per-profile descriptors (`<profile>.yaml`) for all core
  and custom profiles, refreshed the profile registry, and wired loaders to
  prefer the new filenames while keeping the old `profile.yaml` fallback.
  Files:
  PROFILE_MAP.md
  devcovenant/core/profiles.py
  devcovenant/core/install.py
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/core/profiles/*/*.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovuser/devcovuser.yaml
  tests/core/profiles/test_profiles.py
  tests/custom/profiles/test_custom_profiles.py
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/profiles/react/react.yaml
  devcovenant/core/profiles/data/data.yaml
- 2026-02-01: Removed the temporary helper script
  `devcovenant/core/generate_policy_metadata_schema.py`; schema generation now
  runs inside the refresh pipeline.
  Files:
  devcovenant/core/generate_policy_metadata_schema.py
- 2026-01-31: Switched DevCovenant to MIT (assets, docs, PyPI metadata) and
  refreshed citation authors/license/version.
  Files:
  LICENSE
  devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt
  README.md
  devcovenant/README.md
  pyproject.toml
  CITATION.cff
- 2026-01-31: Cleaned raw-string-escapes test fixtures to avoid policy/flake8
  noise while preserving coverage of bare-backslash detection.
  Files:
  tests/core/policies/raw_string_escapes/tests/test_raw_string_escapes.py
- 2026-01-30: Removed dogfood-only policies, added the repo-only
  `devcov-raw-string-escapes` policy, and implemented the
  `autogen_do_not_apply`/`manual_force_apply` config flow with python
  profile defaults for `raw-string-escapes`.
  Files:
  CHANGELOG.md
  AGENTS.md
  PLAN.md
  SPEC.md
  POLICY_MAP.md
  devcovenant/config.yaml
  devcovenant/core/refresh_policies.py
  devcovenant/core/install.py
  devcovenant/core/policy_freeze.py
  devcovenant/core/policies/raw_string_escapes/\
    raw_string_escapes.yaml
  devcovenant/core/profiles/python/profile.yaml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/registry/local/policy_metadata_schema.yaml
  tests/core/policies/devcov_parity_guard/tests/\
    test_devcov_parity_guard.py
  devcovenant/custom/policies/managed_doc_assets/\
    managed_doc_assets.yaml
  devcovenant/custom/policies/profile_policy_map/\
    profile_policy_map.yaml
  devcovenant/custom/policies/devcov_raw_string_escapes/__init__.py
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.py
  devcovenant/custom/policies/devcov_raw_string_escapes/\
    devcov_raw_string_escapes.yaml
  devcovenant/core/policies/gcv_script_naming/\
    gcv_script_naming.py
  devcovenant/core/policies/gcv_script_naming/__init__.py
  devcovenant/core/policies/gcv_script_naming/adapters/__init__.py
  devcovenant/core/policies/gcv_script_naming/fixers/__init__.py
  devcovenant/core/policies/gcv_script_naming/assets/.gitkeep
  devcovenant/core/policies/gcv_script_naming/\
    gcv_script_naming.yaml
  devcovenant/core/policies/security_compliance_notes/\
    security_compliance_notes.py
  devcovenant/core/policies/security_compliance_notes/__init__.py
  devcovenant/core/policies/security_compliance_notes/adapters/__init__.py
  devcovenant/core/policies/security_compliance_notes/fixers/__init__.py
  devcovenant/core/policies/security_compliance_notes/assets/.gitkeep
  devcovenant/core/policies/security_compliance_notes/\
    security_compliance_notes.yaml
  tests/core/policies/gcv_script_naming/tests/\
    test_gcv_script_naming.py
  tests/core/policies/gcv_script_naming/__init__.py
  tests/core/policies/gcv_script_naming/tests/__init__.py
  tests/core/policies/security_compliance_notes/tests/\
    test_security_compliance_notes.py
  tests/core/policies/security_compliance_notes/__init__.py
  tests/core/policies/security_compliance_notes/tests/__init__.py
  devcovenant/registry/local/policy_registry.yaml
- 2026-01-30: Updated PLAN/SPEC to reflect completed devcovrepo/devcovuser
  documentation and to scope raw-string-escapes follow-up work.
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
- 2026-01-30: Clarified managed doc/header refresh, config autogen behavior,
  runtime-required registry artifacts, and tests/devcovenant mirror rules in
  PLAN/SPEC.
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
- 2026-01-30: Removed the dogfood-only `patches-txt-sync` policy, rebuilt
  metadata schema generation to prefer descriptor YAMLs, and refreshed
  policy registry outputs plus devcov scaffolding refresh logic.
  Files:
  CHANGELOG.md
  AGENTS.md
  POLICY_MAP.md
  devcovenant/core/refresh_policies.py
  devcovenant/core/refresh_all.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/gcv_script_naming/gcv_script_naming.yaml
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/security_compliance_notes/\
    security_compliance_notes.yaml
  devcovenant/core/policies/track_test_status/track_test_status.yaml
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/profile_policy_map/profile_policy_map.yaml
  devcovenant/core/policies/patches_txt_sync/patches_txt_sync.py
  devcovenant/core/policies/patches_txt_sync/__init__.py
  devcovenant/core/policies/patches_txt_sync/adapters/__init__.py
  devcovenant/core/policies/patches_txt_sync/fixers/__init__.py
  devcovenant/core/policies/patches_txt_sync/assets/.gitkeep
  tests/core/policies/patches_txt_sync/__init__.py
  tests/core/policies/patches_txt_sync/tests/test_patches_txt_sync.py
  tests/core/policies/patches_txt_sync/tests/__init__.py
  devcovenant/registry/local/policy_metadata_schema.yaml
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/core/parser.py
- 2026-01-30: Renamed `stock-policy-text-sync` to `devcov-parity-guard`,
  updated the policy to compare AGENTS text against descriptor metadata, and
  refreshed the registry/metadata references to match the new policy id.
  Files:
  CHANGELOG.md
  AGENTS.md
  POLICY_MAP.md
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.py
  devcovenant/core/policies/devcov_parity_guard/devcov_parity_guard.yaml
  devcovenant/core/policies/devcov_parity_guard/__init__.py
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/registry/local/policy_metadata_schema.yaml
  devcovenant/registry/global/stock_policy_texts.yaml
  devcovenant/core/stock_policy_texts.json
  tests/core/policies/devcov_parity_guard/tests/test_devcov_parity_guard.py
  tests/core/policies/devcov_parity_guard/tests/__init__.py
  devcovenant/core/policies/stock_policy_text_sync/adapters/__init__.py
  devcovenant/core/policies/stock_policy_text_sync/assets/.gitkeep
  devcovenant/core/policies/stock_policy_text_sync/fixers/__init__.py
  devcovenant/core/policies/stock_policy_text_sync/stock_policy_text_sync.yaml
  tests/core/policies/stock_policy_text_sync/__init__.py
  tests/core/policies/stock_policy_text_sync/tests/__init__.py
- 2026-01-30: Fixed policy metadata override handling, expanded update
  replacements to copy full policy descriptors into custom overrides, and
  ensured install/update rebuild devcovenant custom/test scaffolding while
  pruning devcovrepo-only overrides when core inclusion is disabled.
  Files:
  CHANGELOG.md
  devcovenant/core/refresh_policies.py
  devcovenant/core/update.py
  devcovenant/core/install.py
  devcovenant/custom/profiles/devcovrepo/profile.yaml
- 2026-01-30: Renamed the repo-specific profile to `devcovrepo` and
  introduced the `devcovuser` profile so repo and user installs can keep
  DevCovenant artifacts separated while maintaining the config overrides.
  Files:
  CHANGELOG.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  PLAN.md
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/profile.yaml
  devcovenant/custom/profiles/devcovrepo/assets/.gitignore
  devcovenant/custom/profiles/devcovuser/profile.yaml
  devcovenant/custom/profiles/devcovenant/assets/.gitignore
  devcovenant/README.md
- 2026-01-29: Made `SPEC.md` and `PLAN.md` part of the normal profile-driven
  doc assets, removed the `--include-spec/--include-plan` flags and the
  deprecated `config_old.yaml`, and extended the install tests to cover the
  new behavior.
  Files:
  AGENTS.md
  README.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/config.yaml
  devcovenant/config_old.yaml
  tests/core/tests/test_install.py

- 2026-01-29: Reformatted `devcovenant/core/stock_policy_texts.json` with
  inline indentation to keep line lengths short and JSON parsing intact.
  Files:
  devcovenant/core/stock_policy_texts.json

- 2026-01-29: Removed the legacy `devcovenant/registry.json` and
  `devcovenant/core/update_hashes.py`. Added the helper
  `devcovenant/core/generate_policy_metadata_schema.py` so the schema is
  always derived from the descriptor YAMLs.
  Files:
  devcovenant/core/generate_policy_metadata_schema.py
  devcovenant/core/update_hashes.py
  devcovenant/registry.json
  devcovenant/registry/local/policy_metadata_schema.yaml

- 2026-01-29: Refreshed policy metadata handling, canonicalized the schema,
  and recorded the new descriptor imports plus a python3-based pre-commit
  command so DevFlow gates see `python3 -m pre_commit`. Entries now flow
  through `refresh_policies`, `update-policy-registry`, `install`, `update`,
  and `cli` helpers so the same schema and start command propagate everywhere.
  Files:
  devcovenant/core/refresh_policies.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/registry.py
  devcovenant/core/policy_descriptor.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/install.py
  devcovenant/core/update.py
  devcovenant/cli.py
  devcovenant/core/refresh_all.py

- 2026-01-28: Moved user-facing helper scripts to `devcovenant/` root, removed
  `devcovenant/core/tools/`, and aligned manifests, assets, policies, and
  docs to the new command surface and python3 usage.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/config_old.yaml
  devcovenant/core/base.py
  devcovenant/core/cli_options.py
  devcovenant/core/install.py

- 2026-01-28: Documented the global profile’s helper packaging so the
  installer keeps bundling `devcovenant/run_pre_commit.py` and
  `devcovenant/run_tests.py` in its doc assets.
  Files:
  devcovenant/core/profiles/global/assets/devcovenant/run_pre_commit.py
  devcovenant/core/profiles/global/assets/devcovenant/run_tests.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/track_test_status/track_test_status.py
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.md
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/python/assets/venv.md
  devcovenant/core/profiles/python/profile.yaml
  devcovenant/core/refresh_all.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/tools/run_pre_commit.py
  devcovenant/core/tools/run_tests.py
  devcovenant/core/tools/update_lock.py
  devcovenant/core/tools/update_test_status.py
  devcovenant/core/uninstall.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/update_test_status.py
  devcovenant/custom/policies/readme_sync/readme_sync.py
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/run_pre_commit.py
  devcovenant/run_tests.py
  devcovenant/update_lock.py
  devcovenant/update_test_status.py
  DEVCOVENANT.md
  tests/core/policies/devflow_run_gates/tests/test_devflow_run_gates.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/policies/stock_policy_text_sync/tests/\
    test_stock_policy_text_sync.py
  tests/core/policies/track_test_status/tests/test_track_test_status.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_refresh_policies.py
  tests/custom/policies/test_readme_sync.py

- 2026-01-28: Restored the `readme-sync` script and fixer so README mirroring
  remains enforced with the managed README asset.
  Files:
  devcovenant/custom/policies/readme_sync/readme_sync.py
  devcovenant/custom/policies/readme_sync/fixers/global.py

- 2026-01-28: Added policy freeze automation, canonical schema metadata, and
  retired the legacy registry storage so policy hashes live solely inside the
  local registry directory.
  Files:
  devcovenant/core/policy_freeze.py
  devcovenant/core/policy_schema.py
  devcovenant/core/parser.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/manifest.py
  devcovenant/registry/local/policy_metadata_schema.yaml
  tests/core/tests/test_policy_freeze.py
  tests/core/tests/test_policy_schema.py
  devcovenant/core/update_hashes.py
  devcovenant/registry.json
  tests/core/policies/devflow_run_gates/tests/test_devflow_run_gates.py
  tests/core/policies/last_updated_placement/tests/\
    test_last_updated_placement.py
  tests/core/policies/stock_policy_text_sync/tests/\
    test_stock_policy_text_sync.py
  tests/core/policies/track_test_status/tests/test_track_test_status.py
  tests/core/tests/test_policy_replacements.py
  tests/core/tests/test_refresh_policies.py
  tests/custom/policies/test_readme_sync.py

- 2026-01-28: Moved the workflow helpers (`run_pre_commit`, `run_tests`,
  `update_lock`, `update_test_status`) out of `devcovenant/core/tools` into
  `devcovenant/core/` and synchronized every doc/manifest/asset that
  referenced the old path. Rebuilt the profile-managed copies so the global
  profile still packages the helpers under
  `devcovenant/core/profiles/global/assets/devcovenant/core/`.
  Renamed the selector helpers module to `selector_helpers` and refreshed the
  selector tests accordingly.
  Files:
  devcovenant/core/run_pre_commit.py
  devcovenant/core/run_tests.py
  devcovenant/core/update_lock.py
  devcovenant/core/update_test_status.py
  devcovenant/core/selector_helpers.py
  tests/core/tests/test_selectors.py
  devcovenant/core/profiles/global/assets/devcovenant/core/run_pre_commit.py
  devcovenant/core/profiles/global/assets/devcovenant/core/run_tests.py
  devcovenant/core/profiles/global/assets/devcovenant/core/update_lock.py
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    update_test_status.py
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/engine.py
  devcovenant/core/install.py

- 2026-01-27: Added a repo-only `devcovenant` profile so the published
  `devcovenant/**` sources stay covered by `new-modules-need-tests`.
  The mirrored `tests/devcovenant/**` suites now receive the same coverage.
  Documented the profile in `README.md` and `PROFILE_MAP.md`.
  Files:
  devcovenant/custom/profiles/devcovenant/profile.yaml
  devcovenant/config.yaml
  README.md
  PROFILE_MAP.md

- 2026-01-27: Removed policy-level test helpers from
  `devcovenant/core/policies/*/tests` and moved them under
  `tests/devcovenant/`. Files:
  devcovenant/core/policies/new_modules_need_tests/tests/\
    new_modules_need_tests_impl.py
  devcovenant/core/policies/changelog_coverage/tests/\
    changelog_coverage_impl.py
  tests/devcovenant/core/policies/changelog_coverage/tests/\
    changelog_coverage_impl.py

- 2026-01-27: Added live policy map automation so `refresh-policies`/
  `update-policy-registry` keep every policy’s metadata, profile coverage,
  enabled state, core/custom origin, and script hash clustered in
  `devcovenant/registry/local/policy_registry.yaml`.
  The registry pulls data from `AGENTS.md` and drives the engine.
  Files:
  AGENTS.md
  README.md
  devcovenant/README.md
  SPEC.md
  PLAN.md
  POLICY_MAP.md
  devcovenant/README.md

  devcovenant/core/manifest.py
  devcovenant/core/refresh_policies.py
  devcovenant/core/update_policy_registry.py
  devcovenant/core/registry.py
  devcovenant/core/policies/devcov_self_enforcement/devcov_self_enforcement.py
  devcovenant/core/update.py
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_registry.yaml
  tests/devcovenant/core/tests/test_refresh_policies.py
  tests/devcovenant/core/policies/devcov_self_enforcement/tests/\
    test_devcov_self_enforcement.py

- 2026-01-27: Split the registry into tracked `devcovenant/registry/global/`
-  (curated assets) and gitignored `devcovenant/registry/local/` (generated
  artifacts: policy registry, manifest, profile registry, policy assets, and
  test status). Updated the install/update/engine stack, policy scripts,
  tools, and docs to read/write the new paths and documented the new layout.
  Files:
  .gitignore
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/config.yaml
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policy_replacements.py
  devcovenant/core/policy_texts.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/track_test_status/track_test_status.py
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    devcovenant/core/run_pre_commit.py
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    devcovenant/core/update_test_status.py
  devcovenant/core/profiles/python/assets/pyproject.toml
  devcovenant/core/profiles/python/assets/venv.md
  devcovenant/core/profiles/python/profile.yaml
  devcovenant/core/devcovenant/core/run_pre_commit.py
  devcovenant/core/devcovenant/core/update_test_status.py
  devcovenant/registry/global/stock_policy_texts.yaml
  devcovenant/registry/global/policy_replacements.yaml
  POLICY_MAP.md
  PLAN.md

- 2026-01-27: Removed the legacy `metadata_normalizer` artifacts and the
  outdated managed_doc_assets coverage in favor of the new refresh/registry
  flow, keeping policy metadata parity and regression tests in sync.
  Files:
  devcovenant/core/metadata_normalizer.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  tests/devcovenant/core/tests/test_metadata_normalizer.py
  tests/devcovenant/custom/policies/test_managed_doc_assets.py

- 2026-01-26: Relocated the changelog-coverage suite beneath the policy folder
  so policy tests stay with their implementation.
  Files:
  tests/devcovenant/core/policies/changelog_coverage/tests/\
    changelog_coverage_impl.py
  tests/devcovenant/core/policies/changelog_coverage/tests/\
    test_changelog_coverage.py

- 2026-01-26: Relocated DevCovenant's core test modules outside the package so
  they now live under `tests/devcovenant/core/tests/`. Files:
  devcovenant/core/tests/__init__.py
  devcovenant/core/tests/test_base.py
  devcovenant/core/tests/test_main_entrypoint.py
  tests/devcovenant/core/tests/test_refresh_policies.py
  devcovenant/core/tests/test_parser.py
  devcovenant/core/tests/test_selectors.py

- 2026-01-26: Added a regression test ensuring `new-modules-need-tests` ignores
  support directories such as `adapters/`.
  Files:
  tests/devcovenant/core/policies/new_modules_need_tests/tests/\
    test_new_modules_need_tests.py

- 2026-01-24: Populated profile manifests and assets for
  language/framework templates. (AI assistant)
  Files:
  CHANGELOG.md
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/profiles/angular/assets/.gitignore
  devcovenant/core/profiles/angular/assets/angular.json
  devcovenant/core/profiles/angular/assets/tsconfig.json
  devcovenant/core/profiles/angular/profile.yaml
  devcovenant/core/profiles/ansible/assets/.gitignore
  devcovenant/core/profiles/ansible/assets/ansible.cfg
  devcovenant/core/profiles/ansible/assets/inventory.ini
  devcovenant/core/profiles/ansible/profile.yaml
  devcovenant/core/profiles/bash/assets/.gitignore
  devcovenant/core/profiles/bash/profile.yaml
  devcovenant/core/profiles/c/assets/.gitignore
  devcovenant/core/profiles/c/assets/CMakeLists.txt
  devcovenant/core/profiles/c/assets/Makefile
  devcovenant/core/profiles/c/profile.yaml
  devcovenant/core/profiles/clojure/assets/.gitignore
  devcovenant/core/profiles/clojure/assets/deps.edn
  devcovenant/core/profiles/clojure/assets/project.clj
  devcovenant/core/profiles/clojure/profile.yaml
  devcovenant/core/profiles/cobol/assets/.gitignore
  devcovenant/core/profiles/cobol/profile.yaml
  devcovenant/core/profiles/cpp/assets/.gitignore
  devcovenant/core/profiles/cpp/assets/CMakeLists.txt
  devcovenant/core/profiles/cpp/profile.yaml
  devcovenant/core/profiles/crystal/assets/.gitignore
  devcovenant/core/profiles/crystal/assets/shard.lock
  devcovenant/core/profiles/crystal/assets/shard.yml
  devcovenant/core/profiles/crystal/profile.yaml
  devcovenant/core/profiles/csharp/assets/.gitignore
  devcovenant/core/profiles/csharp/assets/Project.csproj
  devcovenant/core/profiles/csharp/profile.yaml
  devcovenant/core/profiles/dart/assets/.gitignore
  devcovenant/core/profiles/dart/assets/pubspec.lock
  devcovenant/core/profiles/dart/assets/pubspec.yaml
  devcovenant/core/profiles/dart/profile.yaml
  devcovenant/core/profiles/data/assets/.gitignore
  devcovenant/core/profiles/data/assets/data/README.md
  devcovenant/core/profiles/data/assets/data/manifest.json
  devcovenant/core/profiles/data/profile.yaml
  devcovenant/core/profiles/django/assets/.gitignore
  devcovenant/core/profiles/django/assets/asgi.py
  devcovenant/core/profiles/django/assets/manage.py
  devcovenant/core/profiles/django/assets/settings.py
  devcovenant/core/profiles/django/assets/urls.py
  devcovenant/core/profiles/django/assets/wsgi.py
  devcovenant/core/profiles/django/profile.yaml
  devcovenant/core/profiles/docker/assets/.dockerignore
  devcovenant/core/profiles/docker/assets/.gitignore
  devcovenant/core/profiles/docker/assets/Dockerfile
  devcovenant/core/profiles/docker/assets/docker-compose.yml
  devcovenant/core/profiles/docker/profile.yaml
  devcovenant/core/profiles/docs/assets/.gitignore
  devcovenant/core/profiles/docs/assets/mkdocs.yml
  devcovenant/core/profiles/docs/profile.yaml
  devcovenant/core/profiles/dotnet/assets/.gitignore
  devcovenant/core/profiles/dotnet/assets/packages.lock.json
  devcovenant/core/profiles/dotnet/profile.yaml
  devcovenant/core/profiles/elixir/assets/.gitignore
  devcovenant/core/profiles/elixir/assets/mix.exs
  devcovenant/core/profiles/elixir/assets/mix.lock
  devcovenant/core/profiles/elixir/profile.yaml
  devcovenant/core/profiles/erlang/assets/.gitignore
  devcovenant/core/profiles/erlang/assets/rebar.config
  devcovenant/core/profiles/erlang/assets/rebar.lock
  devcovenant/core/profiles/erlang/profile.yaml
  devcovenant/core/profiles/express/assets/.gitignore
  devcovenant/core/profiles/express/assets/app.js
  devcovenant/core/profiles/express/assets/package.json
  devcovenant/core/profiles/express/assets/server.js
  devcovenant/core/profiles/express/profile.yaml
  devcovenant/core/profiles/fastapi/assets/.gitignore
  devcovenant/core/profiles/fastapi/assets/main.py
  devcovenant/core/profiles/fastapi/assets/openapi.json
  devcovenant/core/profiles/fastapi/profile.yaml
  devcovenant/core/profiles/flask/assets/.gitignore
  devcovenant/core/profiles/flask/assets/app.py
  devcovenant/core/profiles/flask/profile.yaml
  devcovenant/core/profiles/flutter/assets/.gitignore
  devcovenant/core/profiles/flutter/assets/pubspec.yaml
  devcovenant/core/profiles/flutter/profile.yaml
  devcovenant/core/profiles/fortran/assets/.gitignore
  devcovenant/core/profiles/fortran/profile.yaml
  devcovenant/core/profiles/frappe/assets/.gitignore
  devcovenant/core/profiles/frappe/assets/hooks.py
  devcovenant/core/profiles/frappe/assets/modules.txt
  devcovenant/core/profiles/frappe/profile.yaml
  devcovenant/core/profiles/fsharp/assets/.gitignore
  devcovenant/core/profiles/fsharp/assets/Project.fsproj
  devcovenant/core/profiles/fsharp/profile.yaml
  devcovenant/core/profiles/global/assets/.gitignore
  devcovenant/core/profiles/global/profile.yaml
  devcovenant/core/profiles/go/assets/.gitignore
  devcovenant/core/profiles/go/assets/go.sum
  devcovenant/core/profiles/go/profile.yaml
  devcovenant/core/profiles/groovy/assets/.gitignore
  devcovenant/core/profiles/groovy/assets/build.gradle
  devcovenant/core/profiles/groovy/profile.yaml
  devcovenant/core/profiles/haskell/assets/.gitignore
  devcovenant/core/profiles/haskell/assets/project.cabal
  devcovenant/core/profiles/haskell/assets/stack.yaml
  devcovenant/core/profiles/haskell/profile.yaml
  devcovenant/core/profiles/java/assets/.gitignore
  devcovenant/core/profiles/java/profile.yaml
  devcovenant/core/profiles/javascript/assets/.gitignore
  devcovenant/core/profiles/javascript/profile.yaml
  devcovenant/core/profiles/julia/assets/.gitignore
  devcovenant/core/profiles/julia/assets/Manifest.toml
  devcovenant/core/profiles/julia/assets/Project.toml
  devcovenant/core/profiles/julia/profile.yaml
  devcovenant/core/profiles/kotlin/assets/.gitignore
  devcovenant/core/profiles/kotlin/profile.yaml
  devcovenant/core/profiles/kubernetes/assets/.gitignore
  devcovenant/core/profiles/kubernetes/assets/Chart.yaml
  devcovenant/core/profiles/kubernetes/assets/values.yaml
  devcovenant/core/profiles/kubernetes/profile.yaml
  devcovenant/core/profiles/laravel/assets/.gitignore
  devcovenant/core/profiles/laravel/assets/artisan
  devcovenant/core/profiles/laravel/assets/composer.json
  devcovenant/core/profiles/laravel/profile.yaml
  devcovenant/core/profiles/lisp/assets/.gitignore
  devcovenant/core/profiles/lisp/profile.yaml
  devcovenant/core/profiles/lua/assets/.gitignore
  devcovenant/core/profiles/lua/assets/project.rockspec
  devcovenant/core/profiles/lua/profile.yaml
  devcovenant/core/profiles/matlab/assets/.gitignore
  devcovenant/core/profiles/matlab/profile.yaml
  devcovenant/core/profiles/micronaut/assets/.gitignore
  devcovenant/core/profiles/micronaut/assets/application.yml
  devcovenant/core/profiles/micronaut/profile.yaml
  devcovenant/core/profiles/nestjs/assets/.gitignore
  devcovenant/core/profiles/nestjs/assets/nest-cli.json
  devcovenant/core/profiles/nestjs/assets/tsconfig.json
  devcovenant/core/profiles/nestjs/profile.yaml
  devcovenant/core/profiles/nextjs/assets/.gitignore
  devcovenant/core/profiles/nextjs/assets/next.config.js
  devcovenant/core/profiles/nextjs/assets/tsconfig.json
  devcovenant/core/profiles/nextjs/profile.yaml
  devcovenant/core/profiles/nim/assets/.gitignore
  devcovenant/core/profiles/nim/assets/project.nimble
  devcovenant/core/profiles/nim/profile.yaml
  devcovenant/core/profiles/nuxt/assets/.gitignore
  devcovenant/core/profiles/nuxt/assets/nuxt.config.ts
  devcovenant/core/profiles/nuxt/profile.yaml
  devcovenant/core/profiles/objective-c/assets/.gitignore
  devcovenant/core/profiles/objective-c/profile.yaml
  devcovenant/core/profiles/ocaml/assets/.gitignore
  devcovenant/core/profiles/ocaml/assets/dune
  devcovenant/core/profiles/ocaml/assets/opam
  devcovenant/core/profiles/ocaml/profile.yaml
  devcovenant/core/profiles/pascal/assets/.gitignore
  devcovenant/core/profiles/pascal/profile.yaml
  devcovenant/core/profiles/perl/assets/.gitignore
  devcovenant/core/profiles/perl/assets/cpanfile
  devcovenant/core/profiles/perl/profile.yaml
  devcovenant/core/profiles/php/assets/.gitignore
  devcovenant/core/profiles/php/assets/composer.lock
  devcovenant/core/profiles/php/profile.yaml
  devcovenant/core/profiles/powershell/assets/.gitignore
  devcovenant/core/profiles/powershell/profile.yaml
  devcovenant/core/profiles/prolog/assets/.gitignore
  devcovenant/core/profiles/prolog/profile.yaml
  devcovenant/core/profiles/python/assets/.gitignore
  devcovenant/core/profiles/python/assets/.python-version
  devcovenant/core/profiles/python/profile.yaml
  devcovenant/core/profiles/quarkus/assets/.gitignore
  devcovenant/core/profiles/quarkus/assets/application.properties
  devcovenant/core/profiles/quarkus/profile.yaml
  devcovenant/core/profiles/r/assets/.gitignore
  devcovenant/core/profiles/r/assets/DESCRIPTION
  devcovenant/core/profiles/r/assets/NAMESPACE
  devcovenant/core/profiles/r/profile.yaml
  devcovenant/core/profiles/rails/assets/.gitignore
  devcovenant/core/profiles/rails/assets/Gemfile
  devcovenant/core/profiles/rails/profile.yaml
  devcovenant/core/profiles/react/assets/.gitignore
  devcovenant/core/profiles/react/assets/package.json
  devcovenant/core/profiles/react/profile.yaml
  devcovenant/core/profiles/ruby/assets/.gitignore
  devcovenant/core/profiles/ruby/assets/Gemfile.lock
  devcovenant/core/profiles/ruby/profile.yaml
  devcovenant/core/profiles/rust/assets/.gitignore
  devcovenant/core/profiles/rust/assets/Cargo.lock
  devcovenant/core/profiles/rust/profile.yaml
  devcovenant/core/profiles/scala/assets/.gitignore
  devcovenant/core/profiles/scala/assets/build.sbt
  devcovenant/core/profiles/scala/profile.yaml
  devcovenant/core/profiles/scheme/assets/.gitignore
  devcovenant/core/profiles/scheme/profile.yaml
  devcovenant/core/profiles/spring/assets/.gitignore
  devcovenant/core/profiles/spring/assets/application.yml
  devcovenant/core/profiles/spring/profile.yaml
  devcovenant/core/profiles/sql/assets/.gitignore
  devcovenant/core/profiles/sql/assets/schema.sql
  devcovenant/core/profiles/sql/profile.yaml
  devcovenant/core/profiles/suffixes/assets/.gitignore
  devcovenant/core/profiles/svelte/assets/.gitignore
  devcovenant/core/profiles/svelte/assets/svelte.config.js
  devcovenant/core/profiles/svelte/profile.yaml
  devcovenant/core/profiles/swift/assets/.gitignore
  devcovenant/core/profiles/swift/assets/Package.swift
  devcovenant/core/profiles/swift/profile.yaml
  devcovenant/core/profiles/symfony/assets/.gitignore
  devcovenant/core/profiles/symfony/assets/composer.json
  devcovenant/core/profiles/symfony/profile.yaml
  devcovenant/core/profiles/terraform/assets/.gitignore
  devcovenant/core/profiles/terraform/assets/main.tf
  devcovenant/core/profiles/terraform/assets/variables.tf
  devcovenant/core/profiles/terraform/profile.yaml
  devcovenant/core/profiles/typescript/assets/.gitignore
  devcovenant/core/profiles/typescript/profile.yaml
  devcovenant/core/profiles/vue/assets/.gitignore
  devcovenant/core/profiles/vue/assets/package.json
  devcovenant/core/profiles/vue/assets/vue.config.js
  devcovenant/core/profiles/vue/profile.yaml
  devcovenant/core/profiles/zig/assets/.gitignore
  devcovenant/core/profiles/zig/assets/build.zig
  devcovenant/core/profiles/zig/profile.yaml
  devcovenant/core/tests/test_install.py
  devcovenant/custom/fixers/__init__.py
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/test_status.json

- 2026-01-24: Removed legacy policy script/fixer folders and
  updated install cleanup/test coverage. (AI assistant)
  Files:
  CHANGELOG.md
  devcovenant/core/install.py
  devcovenant/core/cli_options.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/policy_scripts/
  devcovenant/core/fixers/
  devcovenant/custom/policy_scripts/
  devcovenant/custom/fixers/__init__.py
  devcovenant/custom/fixers/
  devcovenant/common_policy_patches/

- 2026-01-24: Reorganized policy/profile layout and refreshed docs,
  registry entries, and tests. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/engine.py
  devcovenant/core/fixers/__init__.py
  devcovenant/core/fixers/dependency_license_sync.py
  devcovenant/core/fixers/last_updated_placement.py
  devcovenant/core/fixers/no_future_dates.py
  devcovenant/core/fixers/raw_string_escapes.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/__init__.py
  devcovenant/core/policies/changelog_coverage/__init__.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/tests/__init__.py
  devcovenant/core/policies/changelog_coverage/tests\
  /test_changelog_coverage.py
  devcovenant/core/policies/dependency_license_sync/__init__.py
  devcovenant/core/policies/dependency_license_sync/assets\
  /THIRD_PARTY_LICENSES.md
  devcovenant/core/policies/dependency_license_sync/assets/licenses/README.md
  devcovenant/core/policies/dependency_license_sync/assets/policy_assets.yaml
  devcovenant/core/policies/dependency_license_sync/dependency_license_sync.py
  devcovenant/core/policies/dependency_license_sync/fixers/__init__.py
  devcovenant/core/policies/dependency_license_sync/fixers/global.py
  devcovenant/core/policies/dependency_license_sync/tests/__init__.py
  devcovenant/core/policies/dependency_license_sync/tests\
  /test_dependency_license_sync.py
  devcovenant/core/policies/devcov_self_enforcement/__init__.py
  devcovenant/core/policies/devcov_self_enforcement/devcov_self_enforcement.py
  devcovenant/core/policies/devcov_self_enforcement/tests/__init__.py
  devcovenant/core/policies/devcov_self_enforcement/tests\
  /test_devcov_self_enforcement.py
  devcovenant/core/policies/devcov_structure_guard/__init__.py
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.py
  devcovenant/core/policies/devcov_structure_guard/tests/__init__.py
  devcovenant/core/policies/devcov_structure_guard/tests\
  /test_devcov_structure_guard.py
  devcovenant/core/policies/devflow_run_gates/__init__.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/tests/__init__.py
  devcovenant/core/policies/devflow_run_gates/tests/test_devflow_run_gates.py
  devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage\
  /docstring_and_comment_coverage.py
  devcovenant/core/policies/docstring_and_comment_coverage/tests/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage/tests\
  /test_docstring_and_comment_coverage.py
  devcovenant/core/policies/documentation_growth_tracking/__init__.py
  devcovenant/core/policies/documentation_growth_tracking\
  /documentation_growth_tracking.py
  devcovenant/core/policies/documentation_growth_tracking/tests/__init__.py
  devcovenant/core/policies/documentation_growth_tracking/tests\
  /test_documentation_growth_tracking.py
  devcovenant/core/policies/gcv_script_naming/__init__.py
  devcovenant/core/policies/gcv_script_naming/gcv_script_naming.py
  devcovenant/core/policies/gcv_script_naming/tests/__init__.py
  devcovenant/core/policies/gcv_script_naming/tests/test_gcv_script_naming.py
  devcovenant/core/policies/last_updated_placement/__init__.py
  devcovenant/core/policies/last_updated_placement/fixers/__init__.py
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/tests/__init__.py
  devcovenant/core/policies/last_updated_placement/tests\
  /test_last_updated_placement.py
  devcovenant/core/policies/line_length_limit/__init__.py
  devcovenant/core/policies/line_length_limit/line_length_limit.py
  devcovenant/core/policies/line_length_limit/tests/__init__.py
  devcovenant/core/policies/line_length_limit/tests/test_line_length_limit.py
  devcovenant/core/policies/managed_environment/__init__.py
  devcovenant/core/policies/managed_environment/managed_environment.py
  devcovenant/core/policies/managed_environment/tests/__init__.py
  devcovenant/core/policies/managed_environment/tests\
  /test_managed_environment.py
  devcovenant/core/policies/name_clarity/__init__.py
  devcovenant/core/policies/name_clarity/name_clarity.py
  devcovenant/core/policies/name_clarity/tests/__init__.py
  devcovenant/core/policies/name_clarity/tests/test_name_clarity.py
  devcovenant/core/policies/new_modules_need_tests/__init__.py
  devcovenant/core/policies/new_modules_need_tests/new_modules_need_tests.py
  devcovenant/core/policies/new_modules_need_tests/tests/__init__.py
  devcovenant/core/policies/new_modules_need_tests/tests\
  /test_new_modules_need_tests.py
  devcovenant/core/policies/no_future_dates/__init__.py
  devcovenant/core/policies/no_future_dates/fixers/__init__.py
  devcovenant/core/policies/no_future_dates/fixers/global.py
  devcovenant/core/policies/no_future_dates/no_future_dates.py
  devcovenant/core/policies/no_future_dates/tests/__init__.py
  devcovenant/core/policies/no_future_dates/tests/test_no_future_dates.py
  devcovenant/core/policies/patches_txt_sync/__init__.py
  devcovenant/core/policies/patches_txt_sync/patches_txt_sync.py
  devcovenant/core/policies/patches_txt_sync/tests/__init__.py
  devcovenant/core/policies/patches_txt_sync/tests/test_patches_txt_sync.py
  devcovenant/core/policies/policy_text_presence/__init__.py
  devcovenant/core/policies/policy_text_presence/policy_text_presence.py
  devcovenant/core/policies/policy_text_presence/tests/__init__.py
  devcovenant/core/policies/policy_text_presence/tests\
  /test_policy_text_presence.py
  devcovenant/core/policies/raw_string_escapes/__init__.py
  devcovenant/core/policies/raw_string_escapes/fixers/__init__.py
  devcovenant/core/policies/raw_string_escapes/fixers/global.py
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/core/policies/raw_string_escapes/tests/__init__.py
  devcovenant/core/policies/raw_string_escapes/tests\
  /test_raw_string_escapes.py
  devcovenant/core/policies/read_only_directories/__init__.py
  devcovenant/core/policies/read_only_directories/read_only_directories.py
  devcovenant/core/policies/read_only_directories/tests/__init__.py
  devcovenant/core/policies/read_only_directories/tests\
  /test_read_only_directories.py
  devcovenant/core/policies/security_compliance_notes/__init__.py
  devcovenant/core/policies/security_compliance_notes\
  /security_compliance_notes.py
  devcovenant/core/policies/security_compliance_notes/tests/__init__.py
  devcovenant/core/policies/security_compliance_notes/tests\
  /test_security_compliance_notes.py
  devcovenant/core/policies/security_scanner/__init__.py
  devcovenant/core/policies/security_scanner/security_scanner.py
  devcovenant/core/policies/security_scanner/tests/__init__.py
  devcovenant/core/policies/security_scanner/tests/test_security_scanner.py
  devcovenant/core/policies/semantic_version_scope/__init__.py
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.py
  devcovenant/core/policies/semantic_version_scope/tests/__init__.py
  devcovenant/core/policies/semantic_version_scope/tests\
  /test_semantic_version_scope.py
  devcovenant/core/policies/stock_policy_text_sync/__init__.py
  devcovenant/core/policies/stock_policy_text_sync/stock_policy_text_sync.py
  devcovenant/core/policies/stock_policy_text_sync/tests/__init__.py
  devcovenant/core/policies/stock_policy_text_sync/tests\
  /test_stock_policy_text_sync.py
  devcovenant/core/policies/track_test_status/__init__.py
  devcovenant/core/policies/track_test_status/tests/__init__.py
  devcovenant/core/policies/track_test_status/tests/test_track_test_status.py
  devcovenant/core/policies/track_test_status/track_test_status.py
  devcovenant/core/policies/version_sync/__init__.py
  devcovenant/core/policies/version_sync/tests/__init__.py
  devcovenant/core/policies/version_sync/tests/test_version_sync.py
  devcovenant/core/policies/version_sync/version_sync.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/__init__.py
  devcovenant/core/policy_scripts/changelog_coverage.py
  devcovenant/core/policy_scripts/dependency_license_sync.py
  devcovenant/core/policy_scripts/devcov_self_enforcement.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/core/policy_scripts/documentation_growth_tracking.py
  devcovenant/core/policy_scripts/gcv_script_naming.py
  devcovenant/core/policy_scripts/last_updated_placement.py
  devcovenant/core/policy_scripts/line_length_limit.py
  devcovenant/core/policy_scripts/managed_environment.py
  devcovenant/core/policy_scripts/name_clarity.py
  devcovenant/core/policy_scripts/new_modules_need_tests.py
  devcovenant/core/policy_scripts/no_future_dates.py
  devcovenant/core/policy_scripts/patches_txt_sync.py
  devcovenant/core/policy_scripts/policy_text_presence.py
  devcovenant/core/policy_scripts/raw_string_escapes.py
  devcovenant/core/policy_scripts/read_only_directories.py
  devcovenant/core/policy_scripts/security_compliance_notes.py
  devcovenant/core/policy_scripts/security_scanner.py
  devcovenant/core/policy_scripts/semantic_version_scope.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/profiles.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/angular/profile.yaml
  devcovenant/core/profiles/ansible/profile.yaml
  devcovenant/core/profiles/bash/profile.yaml
  devcovenant/core/profiles/c/profile.yaml
  devcovenant/core/profiles/clojure/profile.yaml
  devcovenant/core/profiles/cobol/profile.yaml
  devcovenant/core/profiles/cpp/profile.yaml
  devcovenant/core/profiles/crystal/profile.yaml
  devcovenant/core/profiles/csharp/profile.yaml
  devcovenant/core/profiles/dart/profile.yaml
  devcovenant/core/profiles/data/profile.yaml
  devcovenant/core/profiles/django/profile.yaml
  devcovenant/core/profiles/docker/profile.yaml
  devcovenant/core/profiles/docs/profile.yaml
  devcovenant/core/profiles/dotnet/assets/.gitignore
  devcovenant/core/profiles/dotnet/assets/global.json
  devcovenant/core/profiles/dotnet/profile.yaml
  devcovenant/core/profiles/elixir/profile.yaml
  devcovenant/core/profiles/erlang/profile.yaml
  devcovenant/core/profiles/express/profile.yaml
  devcovenant/core/profiles/fastapi/profile.yaml
  devcovenant/core/profiles/flask/profile.yaml
  devcovenant/core/profiles/flutter/profile.yaml
  devcovenant/core/profiles/fortran/profile.yaml
  devcovenant/core/profiles/frappe/profile.yaml
  devcovenant/core/profiles/fsharp/profile.yaml
  devcovenant/core/profiles/global/assets/.github/workflows/ci.yml
  devcovenant/core/profiles/global/assets/.pre-commit-config.yaml
  devcovenant/core/profiles/global/assets/AGENTS.md
  devcovenant/core/profiles/global/assets/CONTRIBUTING.md
  devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt
  devcovenant/core/profiles/global/assets/VERSION
  devcovenant/core/profiles/global/assets/gitignore_base.txt
  devcovenant/core/profiles/global/assets/gitignore_os.txt
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    devcovenant/core/run_pre_commit.py
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    devcovenant/core/run_tests.py
  devcovenant/core/profiles/global/assets/devcovenant/core/\
    devcovenant/core/update_test_status.py
  devcovenant/core/profiles/global/profile.yaml
  devcovenant/core/profiles/go/assets/.gitignore
  devcovenant/core/profiles/go/assets/go.mod
  devcovenant/core/profiles/go/profile.yaml
  devcovenant/core/profiles/groovy/profile.yaml
  devcovenant/core/profiles/haskell/profile.yaml
  devcovenant/core/profiles/java/assets/.gitignore
  devcovenant/core/profiles/java/assets/build.gradle
  devcovenant/core/profiles/java/profile.yaml
  devcovenant/core/profiles/javascript/assets/.gitignore
  devcovenant/core/profiles/javascript/assets/package.json
  devcovenant/core/profiles/javascript/profile.yaml
  devcovenant/core/profiles/julia/profile.yaml
  devcovenant/core/profiles/kotlin/assets/.gitignore
  devcovenant/core/profiles/kotlin/assets/build.gradle.kts
  devcovenant/core/profiles/kotlin/profile.yaml
  devcovenant/core/profiles/kubernetes/profile.yaml
  devcovenant/core/profiles/laravel/profile.yaml
  devcovenant/core/profiles/lisp/profile.yaml
  devcovenant/core/profiles/lua/profile.yaml
  devcovenant/core/profiles/matlab/profile.yaml
  devcovenant/core/profiles/micronaut/profile.yaml
  devcovenant/core/profiles/nestjs/profile.yaml
  devcovenant/core/profiles/nextjs/profile.yaml
  devcovenant/core/profiles/nim/profile.yaml
  devcovenant/core/profiles/nuxt/profile.yaml
  devcovenant/core/profiles/objective-c/profile.yaml
  devcovenant/core/profiles/ocaml/profile.yaml
  devcovenant/core/profiles/pascal/profile.yaml
  devcovenant/core/profiles/perl/profile.yaml
  devcovenant/core/profiles/php/assets/.gitignore
  devcovenant/core/profiles/php/assets/composer.json
  devcovenant/core/profiles/php/profile.yaml
  devcovenant/core/profiles/powershell/profile.yaml
  devcovenant/core/profiles/prolog/profile.yaml
  devcovenant/core/profiles/python/assets/.gitignore
  devcovenant/core/profiles/python/assets/requirements.in
  devcovenant/core/profiles/python/assets/requirements.lock
  devcovenant/core/profiles/python/profile.yaml
  devcovenant/core/profiles/quarkus/profile.yaml
  devcovenant/core/profiles/r/profile.yaml
  devcovenant/core/profiles/rails/profile.yaml
  devcovenant/core/profiles/react/profile.yaml
  devcovenant/core/profiles/ruby/assets/.gitignore
  devcovenant/core/profiles/ruby/assets/Gemfile
  devcovenant/core/profiles/ruby/profile.yaml
  devcovenant/core/profiles/rust/assets/.gitignore
  devcovenant/core/profiles/rust/assets/Cargo.toml
  devcovenant/core/profiles/rust/profile.yaml
  devcovenant/core/profiles/scala/profile.yaml
  devcovenant/core/profiles/scheme/profile.yaml
  devcovenant/core/profiles/spring/profile.yaml
  devcovenant/core/profiles/sql/profile.yaml
  devcovenant/core/profiles/suffixes/profile.yaml
  devcovenant/core/profiles/svelte/profile.yaml
  devcovenant/core/profiles/swift/profile.yaml
  devcovenant/core/profiles/symfony/profile.yaml
  devcovenant/core/profiles/terraform/profile.yaml
  devcovenant/core/profiles/typescript/assets/.gitignore
  devcovenant/core/profiles/typescript/assets/package.json
  devcovenant/core/profiles/typescript/assets/tsconfig.json
  devcovenant/core/profiles/typescript/profile.yaml
  devcovenant/core/profiles/vue/profile.yaml
  devcovenant/core/profiles/zig/profile.yaml
  devcovenant/core/registry.py
  devcovenant/core/templates/README.md
  devcovenant/core/templates/global/.github/workflows/ci.yml
  devcovenant/core/templates/global/.pre-commit-config.yaml
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/templates/global/CONTRIBUTING.md
  devcovenant/core/templates/global/LICENSE_GPL-3.0.txt
  devcovenant/core/templates/global/VERSION
  devcovenant/core/templates/global/gitignore_base.txt
  devcovenant/core/templates/global/gitignore_os.txt
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_pre_commit.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_tests.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    update_test_status.py
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/policies/dependency-license-sync\
  /THIRD_PARTY_LICENSES.md
  devcovenant/core/templates/policies/dependency-license-sync/licenses\
  /README.md
  devcovenant/core/templates/policies/dependency-license-sync\
  /policy_assets.yaml
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/profile.yaml
  devcovenant/core/templates/profiles/ansible/profile.yaml
  devcovenant/core/templates/profiles/bash/profile.yaml
  devcovenant/core/templates/profiles/c/profile.yaml
  devcovenant/core/templates/profiles/clojure/profile.yaml
  devcovenant/core/templates/profiles/cobol/profile.yaml
  devcovenant/core/templates/profiles/cpp/profile.yaml
  devcovenant/core/templates/profiles/crystal/profile.yaml
  devcovenant/core/templates/profiles/csharp/profile.yaml
  devcovenant/core/templates/profiles/dart/profile.yaml
  devcovenant/core/templates/profiles/data/profile.yaml
  devcovenant/core/templates/profiles/django/profile.yaml
  devcovenant/core/templates/profiles/docker/profile.yaml
  devcovenant/core/templates/profiles/docs/profile.yaml
  devcovenant/core/templates/profiles/dotnet/.gitignore
  devcovenant/core/templates/profiles/dotnet/global.json
  devcovenant/core/templates/profiles/dotnet/profile.yaml
  devcovenant/core/templates/profiles/elixir/profile.yaml
  devcovenant/core/templates/profiles/erlang/profile.yaml
  devcovenant/core/templates/profiles/express/profile.yaml
  devcovenant/core/templates/profiles/fastapi/profile.yaml
  devcovenant/core/templates/profiles/flask/profile.yaml
  devcovenant/core/templates/profiles/flutter/profile.yaml
  devcovenant/core/templates/profiles/fortran/profile.yaml
  devcovenant/core/templates/profiles/frappe/profile.yaml
  devcovenant/core/templates/profiles/fsharp/profile.yaml
  devcovenant/core/templates/profiles/go/.gitignore
  devcovenant/core/templates/profiles/go/go.mod
  devcovenant/core/templates/profiles/go/profile.yaml
  devcovenant/core/templates/profiles/groovy/profile.yaml
  devcovenant/core/templates/profiles/haskell/profile.yaml
  devcovenant/core/templates/profiles/java/.gitignore
  devcovenant/core/templates/profiles/java/build.gradle
  devcovenant/core/templates/profiles/java/profile.yaml
  devcovenant/core/templates/profiles/javascript/.gitignore
  devcovenant/core/templates/profiles/javascript/package.json
  devcovenant/core/templates/profiles/javascript/profile.yaml
  devcovenant/core/templates/profiles/julia/profile.yaml
  devcovenant/core/templates/profiles/kotlin/.gitignore
  devcovenant/core/templates/profiles/kotlin/build.gradle.kts
  devcovenant/core/templates/profiles/kotlin/profile.yaml
  devcovenant/core/templates/profiles/kubernetes/profile.yaml
  devcovenant/core/templates/profiles/laravel/profile.yaml
  devcovenant/core/templates/profiles/lisp/profile.yaml
  devcovenant/core/templates/profiles/lua/profile.yaml
  devcovenant/core/templates/profiles/matlab/profile.yaml
  devcovenant/core/templates/profiles/micronaut/profile.yaml
  devcovenant/core/templates/profiles/nestjs/profile.yaml
  devcovenant/core/templates/profiles/nextjs/profile.yaml
  devcovenant/core/templates/profiles/nim/profile.yaml
  devcovenant/core/templates/profiles/nuxt/profile.yaml
  devcovenant/core/templates/profiles/objective-c/profile.yaml
  devcovenant/core/templates/profiles/ocaml/profile.yaml
  devcovenant/core/templates/profiles/pascal/profile.yaml
  devcovenant/core/templates/profiles/perl/profile.yaml
  devcovenant/core/templates/profiles/php/.gitignore
  devcovenant/core/templates/profiles/php/composer.json
  devcovenant/core/templates/profiles/php/profile.yaml
  devcovenant/core/templates/profiles/powershell/profile.yaml
  devcovenant/core/templates/profiles/prolog/profile.yaml
  devcovenant/core/templates/profiles/python/.gitignore
  devcovenant/core/templates/profiles/python/profile.yaml
  devcovenant/core/templates/profiles/python/requirements.in
  devcovenant/core/templates/profiles/python/requirements.lock
  devcovenant/core/templates/profiles/quarkus/profile.yaml
  devcovenant/core/templates/profiles/r/profile.yaml
  devcovenant/core/templates/profiles/rails/profile.yaml
  devcovenant/core/templates/profiles/react/profile.yaml
  devcovenant/core/templates/profiles/ruby/.gitignore
  devcovenant/core/templates/profiles/ruby/Gemfile
  devcovenant/core/templates/profiles/ruby/profile.yaml
  devcovenant/core/templates/profiles/rust/.gitignore
  devcovenant/core/templates/profiles/rust/Cargo.toml
  devcovenant/core/templates/profiles/rust/profile.yaml
  devcovenant/core/templates/profiles/scala/profile.yaml
  devcovenant/core/templates/profiles/scheme/profile.yaml
  devcovenant/core/templates/profiles/spring/profile.yaml
  devcovenant/core/templates/profiles/sql/profile.yaml
  devcovenant/core/templates/profiles/suffixes/profile.yaml
  devcovenant/core/templates/profiles/svelte/profile.yaml
  devcovenant/core/templates/profiles/swift/profile.yaml
  devcovenant/core/templates/profiles/symfony/profile.yaml
  devcovenant/core/templates/profiles/terraform/profile.yaml
  devcovenant/core/templates/profiles/typescript/.gitignore
  devcovenant/core/templates/profiles/typescript/package.json
  devcovenant/core/templates/profiles/typescript/profile.yaml
  devcovenant/core/templates/profiles/typescript/tsconfig.json
  devcovenant/core/templates/profiles/vue/profile.yaml
  devcovenant/core/templates/profiles/zig/profile.yaml
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_policies/test_changelog_coverage.py
  devcovenant/core/tests/test_policies/test_dependency_license_sync.py
  devcovenant/core/tests/test_policies/test_devcov_self_enforcement.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/core/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/core/tests/test_policies/test_gcv_script_naming.py
  devcovenant/core/tests/test_policies/test_last_updated_placement.py
  devcovenant/core/tests/test_policies/test_line_length_limit.py
  devcovenant/core/tests/test_policies/test_managed_environment.py
  devcovenant/core/tests/test_policies/test_name_clarity.py
  devcovenant/core/tests/test_policies/test_new_modules_need_tests.py
  devcovenant/core/tests/test_policies/test_no_future_dates.py
  devcovenant/core/tests/test_policies/test_patches_txt_sync.py
  devcovenant/core/tests/test_policies/test_policy_text_presence.py
  devcovenant/core/tests/test_policies/test_raw_string_escapes.py
  devcovenant/core/tests/test_policies/test_read_only_directories.py
  devcovenant/core/tests/test_policies/test_security_compliance_notes.py
  devcovenant/core/tests/test_policies/test_security_scanner.py
  devcovenant/core/tests/test_policies/test_semantic_version_scope.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policies/test_track_test_status.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/core/tests/test_profiles.py
  devcovenant/core/update.py
  devcovenant/custom/policies/README.md
  devcovenant/custom/policies/__init__.py
  devcovenant/custom/policy_scripts/__init__.py
  devcovenant/custom/profiles/README.md
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/local/test_status.json
- 2026-01-24: Documented language-aware fixers and fixer
  expectations in plan/spec. (AI assistant)
  Files:
  PLAN.md
  SPEC.md
- 2026-01-24: Applied profile scope metadata and populated profile
  manifests with suffix/ignore data. (AI assistant)
  Files:
  AGENTS.md
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/templates/profiles/angular/profile.yaml
  devcovenant/core/templates/profiles/ansible/profile.yaml
  devcovenant/core/templates/profiles/bash/profile.yaml
  devcovenant/core/templates/profiles/c/profile.yaml
  devcovenant/core/templates/profiles/clojure/profile.yaml
  devcovenant/core/templates/profiles/cobol/profile.yaml
  devcovenant/core/templates/profiles/cpp/profile.yaml
  devcovenant/core/templates/profiles/crystal/profile.yaml
  devcovenant/core/templates/profiles/csharp/profile.yaml
  devcovenant/core/templates/profiles/dart/profile.yaml
  devcovenant/core/templates/profiles/data/profile.yaml
  devcovenant/core/templates/profiles/django/profile.yaml
  devcovenant/core/templates/profiles/docker/profile.yaml
  devcovenant/core/templates/profiles/docs/profile.yaml
  devcovenant/core/templates/profiles/dotnet/profile.yaml
  devcovenant/core/templates/profiles/elixir/profile.yaml
  devcovenant/core/templates/profiles/erlang/profile.yaml
  devcovenant/core/templates/profiles/express/profile.yaml
  devcovenant/core/templates/profiles/fastapi/profile.yaml
  devcovenant/core/templates/profiles/flask/profile.yaml
  devcovenant/core/templates/profiles/flutter/profile.yaml
  devcovenant/core/templates/profiles/fortran/profile.yaml
  devcovenant/core/templates/profiles/frappe/profile.yaml
  devcovenant/core/templates/profiles/fsharp/profile.yaml
  devcovenant/core/templates/profiles/go/profile.yaml
  devcovenant/core/templates/profiles/groovy/profile.yaml
  devcovenant/core/templates/profiles/haskell/profile.yaml
  devcovenant/core/templates/profiles/java/profile.yaml
  devcovenant/core/templates/profiles/javascript/profile.yaml
  devcovenant/core/templates/profiles/julia/profile.yaml
  devcovenant/core/templates/profiles/kotlin/profile.yaml
  devcovenant/core/templates/profiles/kubernetes/profile.yaml
  devcovenant/core/templates/profiles/laravel/profile.yaml
  devcovenant/core/templates/profiles/lisp/profile.yaml
  devcovenant/core/templates/profiles/lua/profile.yaml
  devcovenant/core/templates/profiles/matlab/profile.yaml
  devcovenant/core/templates/profiles/micronaut/profile.yaml
  devcovenant/core/templates/profiles/nestjs/profile.yaml
  devcovenant/core/templates/profiles/nextjs/profile.yaml
  devcovenant/core/templates/profiles/nim/profile.yaml
  devcovenant/core/templates/profiles/nuxt/profile.yaml
  devcovenant/core/templates/profiles/objective-c/profile.yaml
  devcovenant/core/templates/profiles/ocaml/profile.yaml
  devcovenant/core/templates/profiles/pascal/profile.yaml
  devcovenant/core/templates/profiles/perl/profile.yaml
  devcovenant/core/templates/profiles/php/profile.yaml
  devcovenant/core/templates/profiles/powershell/profile.yaml
  devcovenant/core/templates/profiles/prolog/profile.yaml
  devcovenant/core/templates/profiles/python/profile.yaml
  devcovenant/core/templates/profiles/quarkus/profile.yaml
  devcovenant/core/templates/profiles/r/profile.yaml
  devcovenant/core/templates/profiles/rails/profile.yaml
  devcovenant/core/templates/profiles/react/profile.yaml
  devcovenant/core/templates/profiles/ruby/profile.yaml
  devcovenant/core/templates/profiles/rust/profile.yaml
  devcovenant/core/templates/profiles/scala/profile.yaml
  devcovenant/core/templates/profiles/scheme/profile.yaml
  devcovenant/core/templates/profiles/spring/profile.yaml
  devcovenant/core/templates/profiles/sql/profile.yaml
  devcovenant/core/templates/profiles/suffixes/profile.yaml
  devcovenant/core/templates/profiles/svelte/profile.yaml
  devcovenant/core/templates/profiles/swift/profile.yaml
  devcovenant/core/templates/profiles/symfony/profile.yaml
  devcovenant/core/templates/profiles/terraform/profile.yaml
  devcovenant/core/templates/profiles/typescript/profile.yaml
  devcovenant/core/templates/profiles/vue/profile.yaml
  devcovenant/core/templates/profiles/zig/profile.yaml
- 2026-01-24: Reordered the plan with remaining and completed
  work. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-24: Documented adapter locations in plan/spec. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
- 2026-01-24: Clarified policy/profile asset hierarchy in the profile
  draft. (AI assistant)
  Files:
  CHANGELOG.md
  PROFILE_POLICY_DRAFT.md
- 2026-01-24: Aligned plan/spec with the policy folder layout. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
- 2026-01-24: Clarified always-on profiles in the policy draft. (AI assistant)
  Files:
  CHANGELOG.md
  PROFILE_POLICY_DRAFT.md
- 2026-01-24: Marked docs as always-on and clarified the global
  baseline profile. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  PROFILE_POLICY_DRAFT.md
- 2026-01-24: Marked always-on profiles and updated install
  guidance. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  PROFILE_POLICY_DRAFT.md
- 2026-01-24: Updated SemVer scope policy and release guidance,
  plus profile-scoped planning updates. (AI assistant)
  Files:
  CHANGELOG.md
  AGENTS.md
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policy_assets.yaml
  devcovenant/core/policy_replacements.py
  devcovenant/core/policy_replacements.yaml
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_texts.py
  devcovenant/core/profile_registry.yaml
  devcovenant/core/profiles.py
  devcovenant/core/stock_policy_texts.yaml
  devcovenant/core/templates/README.md
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_pre_commit.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_tests.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    update_test_status.py
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/policies/dependency-license-sync/\
    policy_assets.yaml
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_profiles.py
  devcovenant/core/update_hashes.py
  devcovenant/custom/policy_assets.yaml
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
  devcovenant/manifest.json
  devcovenant/policy_registry.yaml
  devcovenant/registry/local/manifest.json
  devcovenant/registry/local/policy_assets.yaml
  devcovenant/registry/global/policy_replacements.yaml
  devcovenant/registry/local/profile_registry.yaml
  devcovenant/registry/local/policy_registry.yaml
  devcovenant/registry/global/stock_policy_texts.yaml
  devcovenant/registry/local/test_status.json
  devcovenant/core/devcovenant/core/run_pre_commit.py
  devcovenant/core/devcovenant/core/run_tests.py
  devcovenant/core/devcovenant/core/update_test_status.py
- 2026-01-24: Planned dynamic profile/policy catalogs and registry
  layout updates. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/manifest.py
  devcovenant/core/templates/README.md
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/custom/policy_assets.yaml
  devcovenant/custom/profile_registry.yaml
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
- 2026-01-24: Expanded template documentation and removed per-profile
  README stubs. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/manifest.py
  devcovenant/core/templates/README.md
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/custom/policy_assets.yaml
  devcovenant/custom/profile_registry.yaml
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
- 2026-01-24: Consolidated template docs and added custom template
  indexes plus profile registrys. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/manifest.py
  devcovenant/core/templates/README.md
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/custom/policy_assets.yaml
  devcovenant/custom/profile_registry.yaml
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
- 2026-01-24: Consolidated template docs, added custom catalogs,
  and clarified global override behavior. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/manifest.py
  devcovenant/core/templates/README.md
  devcovenant/core/templates/policies/README.md
  devcovenant/core/templates/profiles/README.md
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/custom/policy_assets.yaml
  devcovenant/custom/profile_registry.yaml
  devcovenant/custom/templates/policies/README.md
  devcovenant/custom/templates/profiles/README.md
- 2026-01-23: Added profile manifests, gitignore fragments, and
  profile overlays, plus managed-environment guidance and template
  refreshes. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/registry/local/policy_assets.yaml
  devcovenant/core/policy_scripts/managed_environment.py
  devcovenant/core/profiles.py
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/templates/global/gitignore_base.txt
  devcovenant/core/templates/global/gitignore_os.txt
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/angular/profile.yaml
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/ansible/profile.yaml
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/bash/profile.yaml
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/c/profile.yaml
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/clojure/profile.yaml
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cobol/profile.yaml
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/cpp/profile.yaml
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/crystal/profile.yaml
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/csharp/profile.yaml
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/dart/profile.yaml
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/data/profile.yaml
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/django/profile.yaml
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docker/profile.yaml
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/docs/profile.yaml
  devcovenant/core/templates/profiles/dotnet/.gitignore
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/dotnet/profile.yaml
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/elixir/profile.yaml
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/erlang/profile.yaml
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/express/profile.yaml
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/fastapi/profile.yaml
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flask/profile.yaml
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/flutter/profile.yaml
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/fortran/profile.yaml
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/frappe/profile.yaml
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/fsharp/profile.yaml
  devcovenant/core/templates/profiles/go/.gitignore
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/go/profile.yaml
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/groovy/profile.yaml
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/haskell/profile.yaml
  devcovenant/core/templates/profiles/java/.gitignore
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/java/profile.yaml
  devcovenant/core/templates/profiles/javascript/.gitignore
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/javascript/profile.yaml
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/julia/profile.yaml
  devcovenant/core/templates/profiles/kotlin/.gitignore
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kotlin/profile.yaml
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/kubernetes/profile.yaml
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/laravel/profile.yaml
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lisp/profile.yaml
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/lua/profile.yaml
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/matlab/profile.yaml
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/micronaut/profile.yaml
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nestjs/profile.yaml
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nextjs/profile.yaml
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nim/profile.yaml
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/nuxt/profile.yaml
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/objective-c/profile.yaml
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/ocaml/profile.yaml
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/pascal/profile.yaml
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/perl/profile.yaml
  devcovenant/core/templates/profiles/php/.gitignore
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/php/profile.yaml
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/powershell/profile.yaml
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/prolog/profile.yaml
  devcovenant/core/templates/profiles/python/.gitignore
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/python/profile.yaml
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/quarkus/profile.yaml
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/r/profile.yaml
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/rails/profile.yaml
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/react/profile.yaml
  devcovenant/core/templates/profiles/ruby/.gitignore
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/ruby/profile.yaml
  devcovenant/core/templates/profiles/rust/.gitignore
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/rust/profile.yaml
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scala/profile.yaml
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/scheme/profile.yaml
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/spring/profile.yaml
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/sql/profile.yaml
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/suffixes/profile.yaml
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/svelte/profile.yaml
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/swift/profile.yaml
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/symfony/profile.yaml
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/terraform/profile.yaml
  devcovenant/core/templates/profiles/typescript/.gitignore
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/typescript/profile.yaml
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/vue/profile.yaml
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/core/templates/profiles/zig/profile.yaml
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_managed_environment.py
  devcovenant/core/tests/test_profiles.py
  devcovenant/custom/policy_assets.yaml
  devcovenant/registry/local/policy_registry.yaml
- 2026-01-23: Embedded the policy scope map and language scanner tasks
  into the Phase L planning checklist.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded the policy scope map to a per-policy checklist
  with overlays and asset precedence rules.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded the policy scope map and profile overlay
  guidance for stock templates.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded Phase L planning and added a policy scope map.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Replaced managed-bench with managed-environment and
  refreshed policy docs and templates. (AI assistant)
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/core/policy_scripts/managed_environment.py
  devcovenant/core/tests/test_policies/test_managed_environment.py
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/registry/global/stock_policy_texts.yaml
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/tests/test_policies/test_managed_bench.py
  CHANGELOG.md
- 2026-01-23: Made config profile-generated and expanded
  config schema documentation. (AI assistant)
  Files:
  devcovenant/core/install.py
  devcovenant/config.yaml
  devcovenant/README.md
  SPEC.md
  CHANGELOG.md
- 2026-01-23: Planned profile-driven config, custom catalogs, and
  gitignore assets. (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Documented custom profiles, policies, and asset
  overrides. (AI assistant)
  Files:
  devcovenant/README.md
  SPEC.md
  CHANGELOG.md
- 2026-01-23: Fixed install template resolution for profile assets.
  (AI assistant)
  Files:
  devcovenant/core/install.py
  CHANGELOG.md
- 2026-01-23: Added Phase G tests for profile assets and manifests.
  (AI assistant)
  Files:
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_manifest.py
  CHANGELOG.md
- 2026-01-23: Removed real-repo validation from Phase G.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Completed Phase K asset gating and tests. (AI assistant)
- 2026-01-23: Added profile-aware templates,
  install/update logic, and profile registry tests. (AI assistant)
  Files:
AGENTS.md
CHANGELOG.md
MANIFEST.in
PLAN.md
README.md
SPEC.md
devcovenant/README.md
devcovenant/__init__.py
devcovenant/cli.py
devcovenant/config.yaml
devcovenant/core/engine.py
devcovenant/core/install.py
devcovenant/core/manifest.py
devcovenant/core/refresh_policies.py
devcovenant/registry/local/policy_assets.yaml
devcovenant/core/policy_scripts/changelog_coverage.py
devcovenant/registry/local/profile_registry.yaml
devcovenant/core/profiles.py
devcovenant/core/templates/global/.github/workflows/ci.yml
devcovenant/core/templates/global/.pre-commit-config.yaml
devcovenant/core/templates/global/AGENTS.md
devcovenant/core/templates/global/CONTRIBUTING.md
devcovenant/core/templates/global/LICENSE_GPL-3.0.txt
devcovenant/core/templates/global/VERSION
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_pre_commit.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    run_tests.py
  devcovenant/core/templates/global/devcovenant/core/devcovenant/core/\
    update_test_status.py
devcovenant/core/templates/policies/dependency-license-sync/\
  THIRD_PARTY_LICENSES.md
devcovenant/core/templates/policies/dependency-license-sync/licenses/README.md
devcovenant/core/templates/profiles/angular/README.md
devcovenant/core/templates/profiles/ansible/README.md
devcovenant/core/templates/profiles/bash/README.md
devcovenant/core/templates/profiles/c/README.md
devcovenant/core/templates/profiles/clojure/README.md
devcovenant/core/templates/profiles/cobol/README.md
devcovenant/core/templates/profiles/cpp/README.md
devcovenant/core/templates/profiles/crystal/README.md
devcovenant/core/templates/profiles/csharp/README.md
devcovenant/core/templates/profiles/dart/README.md
devcovenant/core/templates/profiles/data/README.md
devcovenant/core/templates/profiles/django/README.md
devcovenant/core/templates/profiles/docker/README.md
devcovenant/core/templates/profiles/docs/README.md
devcovenant/core/templates/profiles/dotnet/README.md
devcovenant/core/templates/profiles/dotnet/global.json
devcovenant/core/templates/profiles/elixir/README.md
devcovenant/core/templates/profiles/erlang/README.md
devcovenant/core/templates/profiles/express/README.md
devcovenant/core/templates/profiles/fastapi/README.md
devcovenant/core/templates/profiles/flask/README.md
devcovenant/core/templates/profiles/flutter/README.md
devcovenant/core/templates/profiles/fortran/README.md
devcovenant/core/templates/profiles/frappe/README.md
devcovenant/core/templates/profiles/fsharp/README.md
devcovenant/core/templates/profiles/go/README.md
devcovenant/core/templates/profiles/go/go.mod
devcovenant/core/templates/profiles/groovy/README.md
devcovenant/core/templates/profiles/haskell/README.md
devcovenant/core/templates/profiles/java/README.md
devcovenant/core/templates/profiles/java/build.gradle
devcovenant/core/templates/profiles/javascript/README.md
devcovenant/core/templates/profiles/javascript/package.json
devcovenant/core/templates/profiles/julia/README.md
devcovenant/core/templates/profiles/kotlin/README.md
devcovenant/core/templates/profiles/kotlin/build.gradle.kts
devcovenant/core/templates/profiles/kubernetes/README.md
devcovenant/core/templates/profiles/laravel/README.md
devcovenant/core/templates/profiles/lisp/README.md
devcovenant/core/templates/profiles/lua/README.md
devcovenant/core/templates/profiles/matlab/README.md
devcovenant/core/templates/profiles/micronaut/README.md
devcovenant/core/templates/profiles/nestjs/README.md
devcovenant/core/templates/profiles/nextjs/README.md
devcovenant/core/templates/profiles/nim/README.md
devcovenant/core/templates/profiles/nuxt/README.md
devcovenant/core/templates/profiles/objective-c/README.md
devcovenant/core/templates/profiles/ocaml/README.md
devcovenant/core/templates/profiles/pascal/README.md
devcovenant/core/templates/profiles/perl/README.md
devcovenant/core/templates/profiles/php/README.md
devcovenant/core/templates/profiles/php/composer.json
devcovenant/core/templates/profiles/powershell/README.md
devcovenant/core/templates/profiles/prolog/README.md
devcovenant/core/templates/profiles/python/README.md
devcovenant/core/templates/profiles/python/requirements.in
devcovenant/core/templates/profiles/python/requirements.lock
devcovenant/core/templates/profiles/quarkus/README.md
devcovenant/core/templates/profiles/r/README.md
devcovenant/core/templates/profiles/rails/README.md
devcovenant/core/templates/profiles/react/README.md
devcovenant/core/templates/profiles/ruby/Gemfile
devcovenant/core/templates/profiles/ruby/README.md
devcovenant/core/templates/profiles/rust/Cargo.toml
devcovenant/core/templates/profiles/rust/README.md
devcovenant/core/templates/profiles/scala/README.md
devcovenant/core/templates/profiles/scheme/README.md
devcovenant/core/templates/profiles/spring/README.md
devcovenant/core/templates/profiles/sql/README.md
devcovenant/core/templates/profiles/suffixes/README.md
devcovenant/core/templates/profiles/svelte/README.md
devcovenant/core/templates/profiles/swift/README.md
devcovenant/core/templates/profiles/symfony/README.md
devcovenant/core/templates/profiles/terraform/README.md
devcovenant/core/templates/profiles/typescript/README.md
devcovenant/core/templates/profiles/typescript/package.json
devcovenant/core/templates/profiles/typescript/tsconfig.json
devcovenant/core/templates/profiles/vue/README.md
devcovenant/core/templates/profiles/zig/README.md
devcovenant/core/tests/test_policies/test_changelog_coverage.py
devcovenant/core/tests/test_profiles.py
devcovenant/core/update.py
devcovenant/registry/local/manifest.json
devcovenant/registry/local/policy_registry.yaml
devcovenant/templates/.github/workflows/ci.yml
devcovenant/templates/.pre-commit-config.yaml
devcovenant/templates/AGENTS.md
devcovenant/templates/CONTRIBUTING.md
devcovenant/templates/LICENSE_GPL-3.0.txt
devcovenant/templates/VERSION
devcovenant/templates/devcovenant/core/devcovenant/core/run_pre_commit.py
devcovenant/templates/devcovenant/core/devcovenant/core/run_tests.py
devcovenant/templates/devcovenant/core/devcovenant/core/update_test_status.py
devcovenant/core/tests/test_install.py
- 2026-01-23: Implemented Phase F install/update convergence with
  auto-uninstall prompts, disable-policy support, version discovery
  order, and backup logging, plus docs/tests updates. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/registry/local/manifest.json
- 2026-01-23: Added manifest support for profiles and policy assets,
  updated schema docs, and aligned tests/spec. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/manifest.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/registry/local/manifest.json
- 2026-01-23: Reordered the plan phases to separate completed and
  remaining work without revisit markers. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/tests/test_policy_replacements.py
- 2026-01-23: Revised profile scope semantics and template layout to
  use core/custom templates with explicit global scopes. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/tests/test_policy_replacements.py
