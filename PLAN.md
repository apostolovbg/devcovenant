# DevCovenant Deep Audit Remediation Plan
**Last Updated:** 2026-02-27
**Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan replaces the completed `1.0.0` pre-release handoff roadmap with a
new, audit-seeded remediation roadmap for the next DevCovenant hardening
cycle.

The purpose is not to re-litigate already-closed work. The purpose is to turn
a full-repo deep audit (debug, de-BS semantics, modularity, standardization,
compliance, security, documentation, metadata, profiles, and runtime systems)
into a small number of high-leverage, dependency-ordered work items.

## Table of Contents
1. [Overview](#overview)
2. [Audit Scope and Method](#audit-scope-and-method)
3. [Findings in Scope (Issue Register)](#findings-in-scope-issue-register)
4. [Non-Negotiable Constraints](#non-negotiable-constraints)
5. [Workflow](#workflow)
6. [Execution Order](#execution-order)
7. [Ordered Backlog](#ordered-backlog)
8. [Cross-Cut Validation Matrix](#cross-cut-validation-matrix)
9. [Documentation Deliverables](#documentation-deliverables)
10. [Completion Criteria](#completion-criteria)
11. [Risk Controls](#risk-controls)
12. [Deferred Appendix (Non-Blocking)](#deferred-appendix-non-blocking)

## Overview
### Status Vocabulary
- `complete`: implemented, tested, documented (when needed), gated, and
  staged.
- `pending`: in scope and not yet closed.
- `deferred`: intentionally postponed and tracked only in the deferred
  appendix; deferred items do not block plan completion.

### Baseline Assumptions
- The pre-release `PLAN.md` cycle (`Items 1-5`) is complete and treated as
  baseline.
- Runtime logging, summaries, `gate --status`, token-economy workflow rules,
  and `check` audit-only semantics are already in place.
- Builtin critical-policy enforcement semantics are implemented and the
  current critical set is: `devflow-run-gates`, `devcov-integrity-guard`, and
  `devcov-structure-guard`.
- `semantic-version-scope` remains intentionally disabled unless a future
  explicit slice changes that posture.

### Plan Purpose
- Record a full-repo deep audit issue register in one place.
- Prioritize the issues by dependency and architectural leverage.
- Preserve current strengths while reducing drift, duplication, and hidden
  maintenance risk.
- End with a final evidence-backed closure audit for the new hardening cycle.

### Strengths Preserved (Audit Baseline)
- Governance workflow and evidence model are coherent and operationally
  usable.
- `check` / `gate` semantics are explicit and stable.
- Critical-policy disable-immunity works for the current builtin set.
- Packaging/install evidence discipline is present and release-grade.
- Normal-mode operator UX is substantially improved (live progress, heartbeat,
  log pointers, artifact-first debugging).

## Audit Scope and Method
### Scope
- Root CLI entrypoints and command behavior.
- Core subsystems (`flow`, `runtime`, `services`, `contracts`, `lib`).
- Builtin and custom policies, policy metadata, and resolved registry state.
- Builtin and custom profiles, overlays, assets, and manifest consistency.
- Documentation set (`README`, package README, `devcovenant/docs/*`, AGENTS,
  PLAN, SPEC, CONTRIBUTING).
- Runtime registries/logs conventions and packaging/install behavior.
- Test infrastructure and operator-efficiency behavior.

### Method (This Audit Seed)
- Automated inventory and consistency checks across policies/profiles/docs.
- Resolved-metadata inspection through `devcovenant/registry/local` outputs.
- Targeted code review of high-risk / high-size modules and recent changes.
- Cross-check of workflow, docs, and runtime behavior for contract drift.
- Manual issue triage into blocker/high/medium/low and dependency mapping.

## Findings in Scope (Issue Register)
This register captures the issues to be solved by the backlog below.
Issue IDs are stable within this plan and are mapped into the ordered items.

### Blocker / High
- `F1` (`high`): Fallback launcher source-checkout runs (`python3 -m
  devcovenant ...`) can still write repo-local `devcovenant/__pycache__`
  before DevCovenant runtime code takes control. The current pycache-prefix
  config/runtime work fixes managed child Python processes and CI job env, but
  not all local fallback-launcher invocations.
- `F2` (`high`): Pre-import pycache-prefix bootstrap logic is duplicated in
  `devcovenant/cli.py` and `devcovenant/__main__.py`, increasing drift risk
  for launcher behavior and future bootstrap features.
- `F3` (`high`): Managed/header exemption fingerprint logic is duplicated in
  `devcovenant/core/runtime/session_snapshot.py` and
  `changelog_coverage.py`, creating a recurring drift vector for gate-session
  coverage behavior.

### Medium
- `F4` (`medium`): Core orchestration and policy modules are large and carry
  multiple responsibilities (`refresh.py`, `execution.py`, `gate.py`,
  `policy_engine.py`, `changelog_coverage.py`). Maintenance and feature work
  now regularly crosses many concerns per file.
- `F5` (`medium`): Registry metadata remains stringly/flattened in
  `policy_registry.yaml`, so tooling and policies repeatedly normalize values
  (`bool`, list, selectors, globs) from string form. This increases parsing
  complexity and audit friction.
- `F6` (`medium`): Profile asset manifest integrity is not fully enforced;
  audit found a concrete missing template reference in the builtin `flutter`
  profile (`pubspec.lock`).
- `F7` (`medium`): Full test runtime remains high (intentional dual-runner
  fidelity), and optimization work lacks a committed profiling/reporting loop
  for targeted further improvements.
- `F8` (`medium`): Security/compliance posture is strong operationally but
  still lacks a single explicit threat-model / due-diligence artifact for CLI,
  local mutation boundaries, packaging, and CI supply-chain considerations.
- `F9` (`medium`): AGENTS is correctly canonical but large; startup token cost
  and operator/tooling context hydration remain expensive without a generated,
  low-token audit digest (while preserving the requirement to read AGENTS).

### Low
- `F10` (`low`): Some CI/runtime env hardening behavior is currently split
  between generated workflow assets and repo-maintained workflows, which is
  workable but drift-prone without an explicit consistency review step.
- `F11` (`low`): Documentation and architecture notes now describe many recent
  runtime/workflow changes correctly, but continued rapid evolution makes
  cross-doc consistency regressions likely without a dedicated sweep item.

### Findings Outside Scope (Informational)
- Historical changelog references to removed files (for example the retired
  `devcovenant/docs/README.md`) are expected evidence and not remediation
  targets.
- Descriptor-minimal policy metadata (missing `enabled`/`custom` in some
  shipped YAML descriptors) is an intentional design choice, not a defect, as
  long as resolved metadata remains correct and auditable.

## Non-Negotiable Constraints
- No edits inside managed `<!-- DEVCOV* -->` blocks.
- No silent contract flips.
- `check` remains the read-only audit command.
- `gate` commands own lifecycle writes and never run tests internally.
- No deletion of historical changelog entries.
- Logging remains enabled by design; retention is configurable, disablement is
  not the default path.
- Packaging/build/install verification is required before final closure.
- Fix root causes where feasible; if a workaround is used, document the
  limitation and the intended root fix path in the same slice.

## Workflow
This plan follows the repository workflow contract in `AGENTS.md`.
Each work slice uses the same closure pattern:

1. Use the managed environment when configured.
2. Run `devcovenant gate --start` before edits.
3. Clear start-gate complaints before feature work.
4. Implement the requested slice.
5. Run focused tests first.
6. Run `devcovenant test`.
7. Run `devcovenant gate --end`.
8. If end gate introduces changes/complaints, loop explicitly (`test` then
   `gate --end` when needed) until clean.
9. Stage all changes for the completed slice.

Notes:
- Keep operator updates concise (`what changed`, `what passed/failed`, `next`).
- Normal-mode live streaming is acceptable when concise.
- Prefer official run artifacts for failure details and deep inspection.

## Execution Order
The order below is dependency-driven and keeps architectural risk visible:

1. Record the deep-audit baseline and issue register.
2. Fix launcher/bootstrap and repo-bytecode-drift root-cause boundaries.
3. Consolidate shared changelog/session exemption logic before more policy
   behavior changes pile on.
4. Standardize metadata/registry typing and profile/asset integrity checks so
   later refactors operate on stronger contracts.
5. Split high-risk mega-modules with behavior-preserving decomposition.
6. Run docs/contract/operator-efficiency standardization as a dedicated sweep.
7. Improve test-performance observability and security/compliance artifacts
   without reducing fidelity.
8. Execute a final deep-system closure audit and record disposition.

## Ordered Backlog
### Item 1 [complete]: Deep Audit Baseline and Issue Register Seeding
**Objective:** Execute a full-repo deep audit and replace the completed
pre-release roadmap with a new remediation plan seeded by real findings.

**Depends on:** completion of the pre-release `PLAN.md` cycle.

**Scope:** whole-repo audit pass, issue triage, and plan rewrite.

**Implementation Tasks**
1. Re-read `AGENTS.md`, workflow contract, and active policies.
2. Audit repository systems and subsystems using inventory checks,
   metadata/registry inspection, and targeted code/doc review.
3. Produce a severity-ranked issue register with concrete, fixable items.
4. Rewrite `PLAN.md` into a new dependency-ordered remediation roadmap.

**Tests and Validation**
1. `PLAN.md` remains policy-clean and internally consistent.
2. Audit-derived issues are mapped into concrete backlog items.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`

**Acceptance Criteria**
1. A new active plan exists and is based on evidence, not generic cleanup.
2. Findings are explicit, scoped, and actionable.
3. The plan preserves current strengths while targeting real debt.

**Closure Notes (2026-02-26)**
- Replaced the completed pre-release roadmap with an audit-seeded remediation
  plan.
- Recorded a severity-ranked issue register spanning runtime, policies,
  profiles, metadata, docs, tests, security/compliance, and operator UX.
- Mapped issues into a dependency-ordered backlog for the next hardening
  cycle.

### Item 2 [complete]: Launcher Bootstrap and Repo Bytecode-Drift Root Fix
**Objective:** Eliminate fallback-launcher bytecode drift friction at the
right boundary and remove duplicated bootstrap logic.

**Depends on:** Item 1.

**Addresses:** `F1`, `F2`.

**Scope:** fallback launcher behavior, pre-import bootstrap wiring,
`PYTHONPYCACHEPREFIX` launcher strategy, and runtime/bootstrap module
ownership.

**Implementation Tasks**
1. Extract duplicated pre-import pycache-prefix/bootstrap parsing logic from
   `devcovenant/cli.py` and `devcovenant/__main__.py` into a shared bootstrap
   module with no heavy imports.
2. Preserve current behavior while centralizing:
   repo-root discovery, lightweight config read, pycache-prefix env setup.
3. Design and implement a launcher-level mitigation path for local fallback
   runs that preserves fidelity (for example shell helper/snippet or wrapper
   guidance that sets `PYTHONPYCACHEPREFIX` before Python starts).
4. Keep CI job-level `PYTHONPYCACHEPREFIX` behavior aligned with the shared
   bootstrap model and docs.
5. Re-validate that managed child Python subprocesses still inherit the
   configured pycache-prefix env.
6. Document the boundary truth explicitly:
   what runtime config fixes, what launcher env must fix.

**Tests and Validation**
1. Focused tests for shared bootstrap logic (`cli` + `__main__`).
2. Regression tests for pycache-prefix config parsing and env propagation.
3. Manual/source-checkout validation that fallback launcher guidance prevents
   repo-local `devcovenant/__pycache__` drift when used.

**Documentation**
1. `devcovenant/docs/workflow.md`
2. `devcovenant/docs/installation.md`
3. `devcovenant/docs/troubleshooting.md`
4. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. No duplicated pre-import pycache bootstrap logic remains in root CLI
   entrypoints.
2. Launcher-level mitigation for fallback runs is explicit and usable.
3. Runtime and CI pycache-prefix behavior remains fidelity-preserving.

**Closure Notes (2026-02-26)**
- Extracted a stdlib-only shared launcher bootstrap module
  (`devcovenant/launcher_bootstrap.py`) and removed duplicated pre-import
  pycache-prefix parsing/setup logic from `devcovenant/cli.py` and
  `devcovenant/__main__.py`.
- Added focused launcher-bootstrap regressions for config parsing/apply
  behavior plus source checks that both root entrypoints use the shared
  helper, and re-validated runtime pycache-prefix env propagation tests.
- Documented the launcher/runtime boundary truth and a concrete shell-wrapper
  mitigation path that exports `PYTHONPYCACHEPREFIX` before fallback
  `python3 -m devcovenant ...` launches; verified CI governance workflow
  alignment remains job-level `PYTHONPYCACHEPREFIX`.

### Item 3 [complete]: Changelog/Session Exemption Engine Consolidation
**Objective:** Remove duplication between gate-session exemption baseline logic
and changelog-coverage consumer logic, preserving current behavior.

**Depends on:** Item 2.

**Addresses:** `F3`, supports `F11`.

**Scope:** managed/header exemption fingerprinting, baseline capture,
consumer-side comparison, and shared helpers/contracts.

**Implementation Tasks**
1. Extract shared managed-marker/header exemption fingerprint logic into one
   reusable module (runtime/lib/contracts, not policy-local duplication).
2. Migrate `session_snapshot` baseline capture and `changelog-coverage`
   exemption checks to the shared implementation.
3. Preserve current gate-session behavior for:
   managed-only block changes, header-only doc changes, and combined changes.
4. Keep policy semantics unchanged while reducing drift risk.
5. Add targeted regression coverage for:
   `.md` docs, AGENTS managed blocks, `.yaml/.yml` asset regenerations, and
   mixed managed/non-managed edits.
6. Document the shared exemption model in architecture/workflow docs.

**Tests and Validation**
1. Focused `session_snapshot` and `changelog_coverage` regressions.
2. Full `devcovenant test`.
3. Gate workflow verification with managed-doc/asset regeneration in scope.

**Documentation**
1. `devcovenant/docs/architecture.md`
2. `devcovenant/docs/workflow.md`
3. `CHANGELOG.md`

**Acceptance Criteria**
1. Shared exemption logic has one canonical implementation.
2. Existing exemption behavior remains correct and regression-covered.
3. Future exemption changes can be made in one place.

**Closure Notes (2026-02-26)**
- Extracted shared managed/header exemption fingerprint helpers into
  `devcovenant/core/lib/document_exemptions.py` and rewired both
  `devcovenant/core/runtime/session_snapshot.py` and the
  `changelog-coverage` policy to use the same implementation.
- Preserved gate-session exemption behavior while removing duplicated marker/
  header-range fingerprint code from the policy and runtime baseline paths.
- Added focused regressions covering `.md` docs, AGENTS managed-block/header
  combinations, `.yml` and `.yaml` managed asset regenerations, and mixed
  managed/non-managed workflow edits.
- Updated workflow/architecture/policies docs to record the shared exemption
  model and canonical helper ownership.

### Item 4 [complete]: Metadata and Registry Typing Standardization
**Objective:** Reduce stringly metadata parsing debt while preserving current
policy/profile flexibility and backward compatibility.

**Depends on:** Item 3.

**Addresses:** `F5`, supports `F11`.

**Scope:** metadata normalization APIs, registry serialization contracts,
typed access helpers, and tooling/audit ergonomics.

**Implementation Tasks**
1. Audit the highest-friction metadata normalization call paths across
   runtime/services/policies.
2. Introduce a typed metadata access layer (or typed companion export) for
   common scalar/list/bool patterns without breaking existing consumers.
3. Preserve the current string-map registry contract if needed, but provide a
   canonical typed view for internal code and audits.
4. Consolidate repeated selector/list/bool normalization helpers where
   practical.
5. Add schema/shape validation tests for resolved metadata of active policies.
6. Document the typed-vs-string metadata contract and migration posture.

**Tests and Validation**
1. Metadata normalization/accessor unit tests.
2. Registry serialization/deserialization regression tests.
3. Full `devcovenant test`.

**Documentation**
1. `devcovenant/docs/architecture.md`
2. `devcovenant/docs/policies.md`
3. `devcovenant/docs/profiles.md`
4. `CHANGELOG.md`

**Acceptance Criteria**
1. Common metadata reads no longer require ad-hoc string parsing everywhere.
2. Existing runtime behavior remains unchanged.
3. Registry/metadata contracts are clearer and easier to audit.

**Closure Notes (2026-02-26)**
- Added a typed companion resolved-metadata export in
  `devcovenant/core/services/metadata.py` (`ResolvedPolicyMetadata` +
  `resolve_policy_metadata_bundle`) while preserving
  `resolve_policy_metadata_map` string-map compatibility.
- Consolidated common metadata scalar/list/bool/number decoding into shared
  metadata helpers and rewired policy-engine AGENTS parsing plus runtime
  registry metadata option loading to use the same decoder.
- Preserved the registry persistence contract as string metadata while adding
  a typed registry accessor (`PolicyRegistry.get_policy_metadata_typed`) for
  internal runtime/audit ergonomics and regression coverage.
- Added metadata/registry/policy-engine tests covering typed decoding,
  string-vs-typed registry behavior, and resolved metadata shape validation
  across enabled policies; updated architecture/policies/profiles docs with
  the typed-vs-string contract posture.

### Item 5 [complete]: Profile and Asset Integrity Hardening
**Objective:** Tighten profile manifest/asset integrity checks and fix known
cross-profile drift (including the builtin `flutter` asset template issue).

**Depends on:** Item 4.

**Addresses:** `F6`, `F10`, supports `F11`.

**Scope:** profile manifests, asset template existence checks, route/asset
consistency, and profile-registry validation coverage.

**Implementation Tasks**
1. Fix the builtin `flutter` profile asset inconsistency (`pubspec.lock`
   template reference) by either adding the missing template or correcting the
   asset declaration contract.
2. Add a profile-manifest integrity validator/test that checks asset template
   existence across all builtin/custom profiles.
3. Add explicit checks for workflow-asset consistency where generated and
   repo-maintained CI workflows must stay aligned on critical env/contract
   behavior.
4. Review profile asset examples and templates for typed empty-value style
   consistency (`''`, `[]`, `{}`) and correct obvious drift.
5. Document profile asset/CI ownership boundaries and validation rules.

**Tests and Validation**
1. New profile-asset integrity regression tests (all profiles).
2. Focused refresh/profile-registry tests.
3. Full `devcovenant test`.

**Documentation**
1. `devcovenant/docs/profiles.md`
2. `devcovenant/docs/installation.md` (CI workflow notes if affected)
3. `CHANGELOG.md`

**Acceptance Criteria**
1. No profile manifest references missing asset templates.
2. Asset/template integrity is regression-tested across the profile set.
3. Workflow-asset consistency risks are explicitly covered.

**Closure Notes (2026-02-26)**
- Fixed the builtin `flutter` profile asset-template drift by adding the
  missing `assets/pubspec.lock` template (`packages: {}`), keeping the
  existing manifest contract unchanged.
- Added profile manifest integrity validation in
  `devcovenant/core/services/profile_registry.py` so
  `assets[*].template`, `gitignore_template`, and `governance_template`
  references must resolve to files under the profile `assets/` root.
- Expanded `test_profile_registry` with regressions for missing-template
  failures, builtin `flutter` template presence, and root-vs-global-asset
  governance workflow alignment on critical CI contract behavior.
- Reviewed profile manifests/assets for typed empty placeholder drift; no
  additional obvious corrections were needed beyond the new `pubspec.lock`
  template using a typed empty map (`{}`).
- Updated profiles/installation docs to record template-validation ownership
  and DevCovenant-repo governance workflow alignment expectations.

### Item 6 [complete]: Core Modularity Decomposition of High-Risk Modules
**Objective:** Split oversized, multi-responsibility modules into clearer
units without changing public semantics or weakening API contracts.

**Depends on:** Items 3-5.

**Addresses:** `F4`, supports `F2`, `F3`, `F5`.

**Scope:** decomposition planning and phased extraction for large modules,
with behavior-preserving refactors and regression safety.

**API-Strength Guardrails (remaining Item 6 slices)**
1. Preserve current command/runtime contracts and the existing
   `DevCovenantEngine` callable surface used by CLI/runtime/tests.
2. Keep extracted helpers as internal implementation modules; do not introduce
   accidental public API surfaces through convenience exports.
3. Keep compatibility wrappers behavior-equivalent and add delegation coverage
   in the same slice when wrappers are retained at prior boundaries.
4. Any intentional API-surface change requires explicit plan authorization,
   migration/docs updates, and dedicated acceptance evidence in the same slice.

**Retroactive API Remediation (completed Item 6 slices)**
1. Tighten package-level service exports so extracted helper modules remain
   internal by default unless explicitly promoted as stable API.
2. Preserve compatibility at the stable boundaries (`DevCovenantEngine`,
   command modules, runtime call sites) rather than by expanding package-level
   convenience exports.
3. Re-scope helper module tests so symbol-contract assertions enforce stable
   boundaries and behavior, not accidental helper-module publicness.
4. Add one explicit package-export inventory guard so future modularization
   slices cannot silently grow the package API surface.

**Target Modules (initial set)**
1. `devcovenant/core/flow/refresh.py`
2. `devcovenant/core/runtime/execution.py`
3. `devcovenant/core/flow/gate.py`
4. `devcovenant/core/services/policy_engine.py`
5. `devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py`

**Implementation Tasks**
1. Define sub-responsibility boundaries per target module before extraction.
2. Extract cohesive helpers/modules incrementally (one target at a time).
3. Keep runtime behavior and public command semantics unchanged.
4. Expand focused tests around extracted seams before/with each split.
5. Add short architecture notes where new module boundaries matter.
6. Track line-count and responsibility reduction in closure notes.
7. Record an explicit API-surface delta (`none` or exact contract) per slice.
8. Execute retroactive API-boundary remediation for completed slices when
   decomposition work widened package-level exports or helper symbol contracts.
9. Keep any unavoidable transitional export in a documented compatibility list
   with explicit removal or promotion criteria.
10. Keep `gate --start`, `gate --mid`, and `gate --end` on one shared
   pre-commit target-derivation path so hook coverage is phase-consistent.

**Tests and Validation**
1. Focused tests for each extracted module/slice.
2. Full `devcovenant test` after each completed decomposition slice.
3. Clean `gate --end` after each slice.
4. Wrapper-delegation regressions verify extracted seams keep prior callers
   on stable engine/command surfaces.
5. Package-export inventory regression fails when unapproved service exports
   are introduced.
6. Helper-module tests validate behavior and seam fidelity without turning
   internal helper symbols into de-facto public API commitments.
7. Gate-flow regressions verify shared pre-commit target derivation across
   `gate --start`, `gate --mid`, and `gate --end`.

**Documentation**
1. `devcovenant/docs/architecture.md`
2. `devcovenant/docs/workflow.md` (only if runtime/output/gate internals affect
   operator-visible contracts)
3. `CHANGELOG.md`

**Acceptance Criteria**
1. Target modules are reduced in size/responsibility without semantic drift.
2. New boundaries are explicit and test-covered.
3. Future feature work no longer requires crossing as many concerns per file.
4. API surface remains stable unless a slice explicitly authorizes and
   documents a contract change.
5. Completed Item 6 slices no longer rely on accidental package-level export
   growth to preserve compatibility.
6. Internal helper modules are explicitly treated as implementation details
   unless promoted by an authorized contract-change slice.

**Progress Notes (2026-02-26, Slice 1: `policy_engine` runtime actions)**
- Defined the first extraction seam inside
  `devcovenant/core/services/policy_engine.py` as top-level policy loading and
  runtime-action dispatch helpers (separate from `DevCovenantEngine` stateful
  orchestration responsibilities).
- Extracted that seam into
  `devcovenant/core/services/policy_runtime_actions.py` and kept
  compatibility wrappers in `policy_engine.py` so existing imports and test
  monkeypatching remain valid during the decomposition phase.
- Added mirrored tests for the new helper module (symbol contract, config/
  metadata decoding, runtime-action dispatch) while preserving existing
  `policy_engine` regressions.
- `policy_engine.py` line count reduced from 1275 to 1216 lines (`-59`) in
  this slice; further Item 6 slices remain pending for additional target
  modules and deeper extractions.

**Progress Notes (2026-02-26, Slice 2: `policy_engine` reporting helpers)**
- Defined the second extraction seam inside
  `devcovenant/core/services/policy_engine.py` as reporting/blocking logic
  (`report_sync_issues`, `report_violations`, `_report_single_violation`,
  `_report_summary`, `should_block`) separate from engine state orchestration.
- Extracted that seam into
  `devcovenant/core/services/policy_reporting.py` and kept
  `DevCovenantEngine` methods as compatibility wrappers that pass through the
  current output boundary (`runtime_print`) and config-derived thresholds.
- Added mirrored tests for the new reporting helper module, including symbol
  contract assertions, fail-threshold blocking logic, summary status output,
  sync-issue guidance paths, and grouped violation reporting behavior.
- `policy_engine.py` line count reduced from 1216 to 1028 lines (`-188`) in
  this slice after formatter stabilization; cumulative Item 6
  `policy_engine` reduction is `-247` lines from the pre-Item-6 baseline
  (`1275 -> 1028`).

**Progress Notes (2026-02-26, Slice 3: `policy_engine` file-scope helpers)**
- Defined the third extraction seam inside
  `devcovenant/core/services/policy_engine.py` as repository file-scope
  helper logic (config ignore patterns, core exclusions, custom-policy
  override discovery, profile suffix/ignore merges, and file collection)
  separate from stateful check orchestration.
- Extracted that seam into
  `devcovenant/core/services/policy_file_scope.py` and kept
  `DevCovenantEngine` methods as compatibility wrappers so existing callers
  and tests continue using the same engine surface during decomposition.
- Added mirrored tests for the new file-scope helper module, including symbol
  contract assertions, ignore-pattern normalization/matching, core exclusion
  path resolution, custom override discovery, profile suffix/ignore merges,
  directory walk decisions, and repository file collection behavior.
- `policy_engine.py` line count reduced from 1028 to 907 lines (`-121`) in
  this slice after final formatter output; cumulative Item 6 `policy_engine`
  reduction is `-368` lines from the pre-Item-6 baseline (`1275 -> 907`).

**Progress Notes (2026-02-26, Slice 4: `policy_engine` autofix helpers)**
- Defined the fourth extraction seam inside
  `devcovenant/core/services/policy_engine.py` as autofixer discovery and
  execution behavior (`_load_fixers`, `apply_auto_fixes`) separate from
  policy-check orchestration and engine state initialization.
- Extracted that seam into
  `devcovenant/core/services/policy_autofix.py` and kept
  `DevCovenantEngine` wrapper methods as compatibility pass-throughs so
  command flows and existing callers continue using the engine surface.
- Added focused helper regressions for fixer loading (custom-override
  precedence, module import path filtering, origin/repo-root stamping) and
  auto-fix run-loop reporting outcomes (success, no-op, failure), plus a
  `policy_engine` wrapper-delegation regression for the extracted seam.
- `policy_engine.py` line count reduced from 907 to 818 lines (`-89`) in
  this slice; cumulative Item 6 `policy_engine` reduction is `-457` lines
  from the pre-Item-6 baseline (`1275 -> 818`).

**Progress Notes (2026-02-26, Slice 5: `policy_engine` context builders)**
- Defined the fifth extraction seam inside
  `devcovenant/core/services/policy_engine.py` as change-state/check-context
  assembly (`_build_change_state`, `_build_check_context`) separate from
  policy execution, reporting, file-scope helpers, and autofix orchestration.
- Extracted that seam into
  `devcovenant/core/services/policy_check_context.py` and kept
  `DevCovenantEngine` wrapper methods as compatibility pass-throughs so
  command flows and test monkeypatching can continue using the engine
  surface during decomposition.
- Added focused helper regressions covering start/open/closed gate-session
  state handling, ignored-path filtering, and `CheckContext` assembly, plus
  a `policy_engine` wrapper-delegation regression for the extracted seam.
- `policy_engine.py` line count reduced from 818 to 658 lines (`-160`) in
  this slice; cumulative Item 6 `policy_engine` reduction is `-617` lines
  from the pre-Item-6 baseline (`1275 -> 658`).

**Progress Notes (2026-02-26, Slice 6: `policy_engine` policy runner)**
- Defined the sixth extraction seam inside
  `devcovenant/core/services/policy_engine.py` as policy execution-loop
  helpers (`run_policy_checks`, critical-disable enforcement helpers, and
  policy option extraction) separate from engine orchestration/state setup.
- Extracted that seam into
  `devcovenant/core/services/policy_check_runner.py` and kept
  `DevCovenantEngine` wrapper methods so existing callers/tests retain the
  same engine surface and pass/fail counter mutation semantics.
- Added focused helper regressions covering critical-disable detection/
  remediation messaging, metadata option extraction, forced-critical + pass
  count behavior, and exception-to-violation conversion, plus
  `policy_engine` wrapper-delegation assertions for the extracted seam.
- `policy_engine.py` line count reduced from 656 to 598 lines (`-58`) in
  this slice before final gate formatting; cumulative Item 6
  `policy_engine` reduction is `-677` lines from the pre-Item-6 baseline
  (`1275 -> 598` measured at write time).

**Progress Notes (2026-02-27, Slice 7: Item 6 API-boundary hardening)**
- Executed the first retroactive Item 6 API remediation slice by tightening
  `devcovenant/core/services/__init__.py` exports so extracted helper seams
  are no longer part of the package-level compatibility surface by default.
- Rewired `policy_engine.py` to import extracted helper seams through explicit
  submodule imports (`devcovenant.core.services.policy_*`) so runtime
  compatibility remains anchored at engine wrappers instead of convenience
  package exports.
- Added a package-export inventory regression guard in
  `tests/devcovenant/core/services/test_registry.py` that locks the intended
  stable `devcovenant.core.services` export set and fails on unapproved
  surface growth.
- Re-scoped extracted-helper tests to remove generic "public symbol" checks
  and keep seam assertions focused on behavior and wrapper/delegation
  contracts rather than accidental helper-module publicness.
- API-surface delta for this slice: `none` at command/runtime/engine contract
  boundaries; package-level helper convenience exports intentionally reduced as
  internalization hardening per Item 6 retroactive remediation rules.

**Progress Notes (2026-02-27, Slice 8: `gate.py` helper extraction)**
- Defined the next Item 6 seam inside `devcovenant/core/flow/gate.py` as
  read-only gate-status rendering/pointer lookup plus changelog-baseline
  metadata helpers, separate from `run_pre_commit_gate` lifecycle
  orchestration.
- Extracted that seam into internal helper modules
  `devcovenant/core/flow/gate_status_helpers.py` and
  `devcovenant/core/flow/gate_changelog_helpers.py` while keeping
  `run_pre_commit_gate` semantics unchanged and retaining a compatibility
  wrapper for `_resolve_latest_relevant_run_pointer` in `gate.py`.
- Added focused mirrored regressions for the new helper modules in
  `tests/devcovenant/core/flow/test_gate_status_helpers.py` and
  `tests/devcovenant/core/flow/test_gate_changelog_helpers.py`, while keeping
  existing gate-flow tests on stable command/runtime behavior.
- `gate.py` line count reduced from `1097` to `687` lines (`-410`) in this
  slice; helper logic now resides in dedicated internal modules without
  expanding package-level exports.
- API-surface delta for this slice: `none` at CLI/runtime gate contracts;
  extracted helper modules remain internal implementation details.

**Progress Notes (2026-02-27, Slice 9: gate-phase pre-commit parity)**
- Hardened gate-phase consistency by routing `gate --start`, `gate --mid`, and
  `gate --end` through one shared pre-commit target resolver that converts
  `--all-files` into explicit snapshot-backed `--files` arguments.
- Preserved lifecycle semantics (`start`/`end` status writes, `mid`
  non-lifecycle behavior) while eliminating cross-session drift where newly
  created files could escape a prior phase and mutate unexpectedly on the next
  phase.
- Added explicit gate-flow regressions for start/mid/end command targeting so
  phase coverage stays synchronized and untracked/new files are enforced by all
  gate phases before lifecycle decisions.
- API-surface delta for this slice: `none`; behavior change is internal
  gate-hook targeting consistency only.

**Progress Notes (2026-02-27, Slice 10: compatibility wrapper inventory)**
- Performed a code-and-test verification pass that confirms Slice 8 helper
  extraction and Slice 9 gate-phase pre-commit parity are implemented in
  runtime code paths and covered by focused gate-flow/helper regressions.
- Added an explicit Item 6 compatibility-wrapper inventory and
  promotion/removal criteria in `devcovenant/docs/architecture.md` so
  transitional seams remain auditable instead of implicit.
- Added a dedicated gate-wrapper delegation regression
  (`test_latest_pointer_wrapper_delegates_to_status_helper`) so the
  `gate.py` compatibility wrapper cannot silently diverge from
  `gate_status_helpers` during future modularization slices.
- API-surface delta for this slice: `none`; contracts remain stable while
  compatibility governance is made explicit and test-enforced.

**Reconciliation Addendum (2026-02-27, post-Slice-10 out-of-plan hardening)**
- Recorded out-of-plan stability hardening delivered between Slice 10 and the
  next planned slice:
  1. PTY-backed subprocess streaming path plus pipe fallback to remove
     source-level child-output buffering drift.
  2. Centralized output-policy runtime module wiring for gate/test/managed
     child command channels.
  3. Added `quiet` output mode and simplified normal-mode test messaging,
     while keeping gate hook output visible and suppressing managed/test flood
     output in normal mode.
  4. Package-doc neutrality/readability corrections in
     `devcovenant/docs/config.md` (`engine.auto_fix_enabled` one-line
     contract bullet and spaced Top-Level section list).
- Mandatory reconciliation check before resuming planned slices:
  1. Verify docs/templates/tests/policies consistently reflect
     `normal|quiet|verbose` output contract behavior and run-log-first
     debugging guidance.
  2. Verify package docs avoid repo-specific contract wording for config keys.
- API-surface delta for this out-of-plan hardening set: `none`; command and
  engine contracts remain stable while internal runtime boundaries were
  strengthened.

### Item 7 [complete]: Documentation, Contract, and Operator-Efficiency Sweep
**Objective:** Run a deliberate phase-2 standardization sweep across docs/help/
workflow guidance and add a low-token audit digest strategy without weakening
AGENTS canon.

**Depends on:** Items 2-6.

**Addresses:** `F9`, `F10`, `F11`.

**Scope:** docs/help/AGENTS alignment, glossary/contract consistency,
operator-efficiency guidance, and generated digest support for tooling.

**Implementation Tasks**
1. Perform a cross-doc contract sweep (`README`, package README,
   `devcovenant/docs/*`, AGENTS editable notes/workflow text) for current
   runtime semantics and wording consistency.
2. Standardize terminology on technical surfaces using the canonical glossary
   nouns and remove newly accumulated parallel labels.
3. Add a generated low-token policy/workflow audit digest (machine-readable and
   optionally short human-readable) for tooling/operator inspection while
   preserving the requirement to read canonical `AGENTS.md`.
4. Document how the digest is informational (not canonical law) and how it is
   refreshed/validated.
5. Reconcile CI/workflow docs with the current generated-vs-repo-maintained
   workflow split and env hardening expectations.
6. Consume the post-Slice-10 out-of-plan hardening ledger and close the
   mandatory docs/templates/tests/policies output-contract consistency check.

**Tests and Validation**
1. Refresh-generated docs/assets remain synchronized.
2. Docs-route and managed-doc policies pass cleanly.
3. Full `devcovenant test`.

**Documentation**
1. `AGENTS.md` (via managed assets/refresh)
2. `README.md`
3. `devcovenant/README.md`
4. `devcovenant/docs/*` as needed
5. `CHANGELOG.md`

**Acceptance Criteria**
1. Docs/help/runtime contracts read as one coherent system.
2. A low-token audit digest exists and is clearly non-canonical.
3. Operator-efficiency guidance remains correct and up to date.

**Progress Notes (2026-02-27, Slice 1: output-contract reconciliation)**
- Completed the mandatory post-Slice-10 reconciliation check by aligning
  package docs/template wording and runtime regressions to the
  `normal|quiet|verbose` output contract.
- Standardized README/package README test-runtime wording so test-console
  behavior is explicitly keyed to `engine.tests_output_mode`.
- Removed repo-specific `devcovrepo` profile wording from package docs
  contract sections and replaced it with profile/config-neutral wording.
- Added focused output/doc-contract regression checks in
  `tests/devcovenant/core/runtime/test_execution.py` for:
  README wording anchor, package-doc neutrality guard, template quiet-mode
  selector comment coverage, and normal-mode test-message contract stability.
- API-surface delta for this slice: `none`; changes are documentation/runtime
  contract clarification and test guardrails only.

**Progress Notes (2026-02-27, Slice 2: unified child-output pipeline)**
- Standardized child-command execution routing by adding
  `resolve_child_output_plan_for_channel` and
  `run_child_command_with_output_policy` in
  `devcovenant/core/runtime/execution.py` as the shared output-policy gateway.
- Consolidated gate and managed-environment command wrappers to delegate
  through that single runtime helper instead of duplicating mode/channel
  resolution logic.
- Added mirrored regression coverage for the new helper and updated gate/
  managed tests to assert delegation and suppressed-failure-tail behavior.
- Clarified architecture/workflow docs so operator guidance and implementation
  both describe one shared child-output pipeline across gate/test/managed
  command families.
- API-surface delta for this slice: additive runtime helper exports only;
  existing command contracts remain unchanged.

**Progress Notes (2026-02-27, Side-task: line-length escape hatch metadata)**
- Added additive `line-length-limit` metadata controls for targeted long-line
  exceptions: `allow_long_url_lines`, `url_prefixes`, `allow_long_lines`,
  `long_lines_contain`, and `long_lines_between` (`left=>right` pairs).
- Implemented policy runtime handling so URL-prefix and marker-based escape
  hatches apply generically to any selected file type, not documentation only.
- Added focused policy regressions for default/custom URL-prefix behavior,
  contain markers, and between-pair matching semantics.
- Updated policy/architecture docs to reflect the new metadata contract.
- API-surface delta for this side-task: none; change is additive policy
  metadata behavior only.

**Progress Notes (2026-02-27, Slice 3: low-token audit digest artifacts)**
- Added refresh-generated local audit digest artifacts under
  `devcovenant/registry/local/`:
  `audit_digest.json` (machine-readable) and `audit_digest.txt`
  (short human-readable).
- Implemented digest generation in `devcovenant/core/services/audit_digest.py`
  and wired refresh-policy-registry orchestration to regenerate digest
  artifacts deterministically from AGENTS workflow/policy blocks and local
  policy registry metadata.
- Extended registry generated-artifact contracts so manifest defaults include
  both audit digest files, and added path helpers for digest artifact lookup.
- Documented the digest as informational/non-canonical and clarified refresh
  lifecycle behavior in workflow/registry/architecture docs.
- Added focused mirrored regressions for audit-digest generation/idempotence,
  registry generated-artifact contracts, and refresh symbol-surface checks.
- API-surface delta for this slice: additive helper seams only
  (`audit_digest_json_path`, `audit_digest_txt_path`,
  `build_audit_digest_payload`, `render_audit_digest_text`,
  `refresh_audit_digest_artifacts`); existing command contracts unchanged.

**Progress Notes (2026-02-27, Slice 4: CI/workflow ownership reconciliation)**
- Reconciled docs wording for workflow ownership so
  `.github/workflows/governance-and-test.yml` is documented as tracked
  refresh-generated output, while `build.yml` and `publish.yml` are documented
  as repository-maintained workflows.
- Updated installation/workflow/profile guidance to describe one consistent
  generated-vs-repo-maintained CI contract and clarify that refresh does not
  regenerate repository-maintained workflows.
- Added a focused documentation-consistency regression in
  `tests/devcovenant/core/runtime/test_execution.py` that guards against
  ownership wording drift and stale "repo-maintained copy" language.
- API-surface delta for this slice: `none`; changes are docs-contract
  reconciliation plus guard-test coverage.

**Progress Notes (2026-02-27, Slice 5: output-contract wording closure)**
- Completed a closure audit pass for the post-Slice-10 output-contract
  reconciliation and fixed remaining wording drift in
  `devcovenant/docs/workflow.md`.
- Standardized the canonical workflow command block so `gate --mid` is
  explicitly required (rerun-until-clean) rather than described as optional.
- Added a focused docs-contract regression in
  `tests/devcovenant/core/runtime/test_execution.py` to enforce mandatory
  `gate --mid` wording and prevent future optional-language regression.
- API-surface delta for this slice: `none`; this is contract wording hardening
  plus guard-test coverage.

### Item 8 [complete]: Fidelity-Preserving Test Performance and
Security/Compliance Hardening
**Objective:** Improve observability and efficiency of the high-fidelity test
pipeline while formalizing security/compliance due diligence artifacts.

**Depends on:** Items 4-7.

**Addresses:** `F7`, `F8`.

**Scope:** test-performance instrumentation and optimization, plus explicit
security/compliance review artifacts and supply-chain/runtime boundary
hardening.

**Implementation Tasks**
1. Add a repeatable profiling path for unittest/pytest runtime breakdowns by
   module/group so future optimizations are evidence-driven.
2. Identify and implement additional fidelity-preserving slow-test reductions
   (fixture reuse, artifact caching, build reuse) without changing the
   dual-runner policy contract.
3. Add or extend test-summary/reporting artifacts with stable duration fields
   useful for trend tracking.
4. Produce a DevCovenant security/compliance due-diligence artifact covering:
   CLI command execution boundaries, local mutation surfaces, packaging,
   dependency/license posture, and CI supply-chain assumptions.
5. Validate packaged-license and installability evidence remains synchronized
   with dependency/workflow changes.
6. Record accepted risks and deferred hardening items explicitly.

**Tests and Validation**
1. Focused performance/profiling harness tests (if new code/tools are added).
2. Full `devcovenant test` before and after optimization slices.
3. Packaging/build/install validation when packaging/runtime artifacts change.

**Documentation**
1. Security/compliance due-diligence artifact (new doc or plan-linked review)
2. `devcovenant/docs/architecture.md` / `installation.md` if contracts change
3. `CHANGELOG.md`

**Acceptance Criteria**
1. Further test-speed improvements land without reducing fidelity.
2. Security/compliance posture is captured in a concrete review artifact.
3. Performance and risk claims are evidence-backed.

**Progress Notes (2026-02-27, Slice 1: repeatable test profiling artifacts)**
- Added a repeatable profiling path inside `devcovenant test` that emits
  informational per-run artifacts (`test_profile.json` and
  `test_profile.txt`) into the active run-log folder.
- Implemented profiling payload/render logic in
  `devcovenant/core/services/runtime_profile.py` with module/group
  aggregation,
  slowest-command ranking, and support for arbitrary command counts in the
  resolved test chain.
- Wired runtime metadata and summary pointers so profiling artifacts are
  discoverable from run summaries while preserving the required command
  contract and gate-status evidence model.
- Added focused regressions for service payload rendering and runtime artifact
  emission under active run-log contexts.
- API-surface delta for this slice: additive service helpers only
  (`build_test_runtime_profile_payload`, `render_test_runtime_profile_text`,
  module/group inference helpers); existing gate/test command contracts remain
  unchanged.

**Progress Notes (2026-02-27, Slice 2: slow-test reductions)**
- Implemented low-risk test-runtime reductions through artifact/build reuse in
  integration-heavy packaging tests by sharing one cached wheel build across
  stale-build and runtime-log exclusion assertions.
- Switched cached repo seed copy paths and wheel-build source staging to
  `shutil.copy` semantics (content-only copy) to reduce repeated metadata-copy
  overhead while preserving isolated per-test working trees.
- Preserved fidelity and contracts: all affected integration suites keep the
  same assertions and command surfaces, with no changes to dual-runner
  `devflow-run-gates.required_commands` behavior.
- API-surface delta for this slice: `none`; optimizations are test-harness
  internals only.

**Progress Notes (2026-02-27, Slice 3: stable duration summary fields)**
- Extended `devcovenant test` summary metadata with stable duration fields for
  trend tracking: per-command rows (`command_durations`) plus aggregate
  min/avg/max and counted duration events.
- Added concise run-summary text output for command-duration aggregates so
  operators can inspect duration drift without opening full event payloads.
- Updated workflow/architecture docs to define the new stable duration fields
  as part of the test evidence artifact contract.
- Added focused runtime regressions covering the new summary fields in
  `tests/devcovenant/core/runtime/test_execution.py`.
- API-surface delta for this slice: `none`; changes are additive test-summary
  metadata and documentation contracts.

**Progress Notes (2026-02-27, Slice 4: security/compliance due diligence)**
- Produced the required plan-linked due-diligence artifact with evidence from
  current runtime, policy, packaging, and CI contracts.
- Review: CLI command execution boundaries
  Question: Are mutation and execution boundaries explicit and policy-owned?
  Evidence:
  `devcovenant/core/runtime/execution.py` policy-runtime actions
  (`resolve-stage`, `resolve-required-test-commands`) and shared child-command
  routing.
  `devcovenant/builtin/policies/no_print_outside_output_runtime/`
  `no_print_outside_output_runtime.py`
  output boundary enforcement.
  Findings: `low`
  Risk: wrapper/policy metadata can still authorize broad external commands.
  Disposition: `accept` now, `defer` stricter allowlist hardening to Item 9.
- Review: Local mutation surfaces
  Question: Are local write surfaces explicit and expected?
  Evidence:
  `install.py`, `deploy.py`, `refresh.py`, `upgrade.py`, `undeploy.py`,
  `uninstall.py`, `update_lock.py`.
  Findings: `low`
  Risk: high-privilege local file mutation is intentional command behavior.
  Disposition: `accept` with current gate/session evidence controls.
- Review: Packaging and installability posture
  Question: Are legal/package artifacts validated and stable?
  Evidence:
  `pyproject.toml` `license-files`, `MANIFEST.in` license/log rules,
  `tests/devcovenant/test_install.py` wheel/license/installability checks.
  Findings: `low`
  Risk: packaging drift if tests/workflows are bypassed.
  Disposition: `fix now` not needed; keep mandatory gate+CI enforcement.
- Review: Dependency/license posture
  Question: Is dependency-license synchronization enforceable?
  Evidence:
  `devcovenant/builtin/policies/dependency_license_sync/`
  `dependency_license_sync.py`
  and policy-driven `update_lock` workflow.
  Findings: `medium`
  Risk: compliance depends on repository metadata quality and lock discipline.
  Disposition: `accept` with policy gates; `defer` richer provenance checks.
- Review: CI supply-chain assumptions
  Question: Are CI trust assumptions explicit?
  Evidence:
  `.github/workflows/governance-and-test.yml`, `build.yml`, `publish.yml`
  install tooling from `requirements.lock` and run gate/test/build checks.
  Findings: `medium`
  Risk: upstream action/runner and index trust remain external assumptions.
  Disposition: `defer` stronger pinning/provenance constraints to Item 9.
- Accepted risks recorded:
  1. Managed wrapper flexibility can execute repo-configured external commands.
  2. CI runner/action trust cannot be fully eliminated in current model.
- Deferred hardening recorded:
  1. Optional allowlist/policy constraints for managed rerun wrappers.
  2. Optional stricter CI action pinning/provenance controls.
- API-surface delta for this slice: `none`; artifact is governance evidence.

**Progress Notes (2026-02-27, Slice 5: packaging/license evidence sync)**
- Validated packaging/installability evidence remains synchronized by running
  focused install/package tests:
  `tests.devcovenant.test_install.GeneratedUnittestCases.test_pyproject_uses_`
  `pep639_license_metadata`,
  `test_manifest_includes_license_artifacts`,
  `test_wheel_contains_required_license_artifacts`, and
  `test_wheel_excludes_runtime_logs_but_keeps_logs_readme`.
- Validated dependency-license synchronization evidence by running
  `tests.devcovenant.builtin.policies.dependency_license_sync.`
  `test_dependency_license_sync` (14 tests), confirming report/license artifact
  alignment behavior and selector/runtime contract stability.
- Findings: `low` risk for Item 8 Task 5; no packaging/license drift detected
  relative to current dependency/workflow changes.
- API-surface delta for this slice: `none`; this is validation evidence only.

**Progress Notes (2026-02-27, Slice 6: Item 8 closure and risk register sync)**
- Completed Item 8 after confirming Tasks 1-6 are evidence-backed across
  Slices 1-5 and this closure slice.
- Confirmed accepted/deferred security/compliance entries remain explicit and
  scoped for carry-forward into the Item 9 final closure audit.
- API-surface delta for this slice: `none`; closure is governance/state
  bookkeeping only.

### Item 9 [complete]: Final Deep-System Closure Audit (RRR for the Hardening
Cycle)
**Objective:** Execute a final full-system audit over the completed remediation
cycle and record closure status with evidence.

**Depends on:** Items 2-8.

**Scope:** correctness, modularity, metadata/profile integrity, docs/contract
coherence, operator UX, performance, security/compliance, and packaging.

**Review Format (Mandatory)**
For each review area, record:
1. `Question`
2. `Evidence`
3. `Findings` (`blocker`, `high`, `medium`, `low`)
4. `Risk`
5. `Disposition` (`fix now`, `accept`, `defer`)

**Review Areas**
1. Functional correctness and regression
2. Runtime/gate/log operational behavior and debuggability
3. Launcher/bootstrap and repo-bytecode-drift behavior
4. Architecture/modularity boundaries and duplication reduction
5. Metadata/registry typing and profile/asset integrity
6. Semantics/de-BS contract integrity
7. Documentation and operator-efficiency coherence
8. Test performance and observability
9. Security/compliance and packaging/installability
10. Final risk register and closure decision
11. Public/internal API boundary integrity and package-export control

**Implementation Tasks**
1. Run a full clean gate workflow (`start`, `test`, `end`) for the closure
   slice, looping explicitly when needed.
2. Execute the final review using the format/areas above.
3. Re-run packaging/build/install validation if affected by Items 2-8.
4. Record closure status in `PLAN.md` and `CHANGELOG.md`.

**Tests and Validation**
1. Full `devcovenant test` passes.
2. `gate --end` passes cleanly.
3. Review findings and dispositions are evidence-backed and explicit.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. Optional dedicated audit report if needed

**Acceptance Criteria**
1. All blocking items (`Item 1` through `Item 9`) are `complete`.
2. Remaining risks are explicitly accepted or deferred with rationale.
3. The hardening cycle closes with a clear evidence-backed status.

**Progress Notes (2026-02-27, Slice 1: clean closure workflow baseline)**
- Executed a full clean gate workflow for the closure slice (`start`, `mid`,
  `test`, `end`) with no blocking violations.
- Established Item 9 baseline evidence for final review-area auditing and
  closure recording.
- API-surface delta for this slice: `none`; this slice captures closure
  workflow evidence only.

**Progress Notes (2026-02-27, Slice 2: final review areas 1-11)**
1. Functional correctness and regression
   Question: Do core command/gate flows still pass without regressions?
   Evidence: recent clean workflows and full test runs in
   `devcovenant/logs/20260227T140352654879Z-test`,
   `devcovenant/logs/20260227T140616774759Z-gate`;
   command chain in `devcovenant/core/runtime/execution.py`.
   Findings: `low`.
   Risk: residual regression risk from future refactors.
   Disposition: `accept`.
2. Runtime/gate/log operational behavior and debuggability
   Question: Are gate lifecycle and run artifacts explicit and debuggable?
   Evidence: lifecycle and snapshot handling in
   `devcovenant/core/flow/gate.py`,
   stream-mode controls in `devcovenant/core/runtime/output.py`,
   artifact pointers in `devcovenant/docs/workflow.md`.
   Findings: `low`.
   Risk: operator misuse of quiet mode can hide non-blocking details.
   Disposition: `accept`.
3. Launcher/bootstrap and repo-bytecode-drift behavior
   Question: Is pycache/bootstrap behavior explicit and bounded?
   Evidence: launcher bootstrap in `devcovenant/launcher_bootstrap.py`,
   runtime pycache controls in `devcovenant/core/runtime/execution.py`,
   managed-environment staging in
   `devcovenant/builtin/policies/managed_environment/`
   `managed_environment_runtime.py`.
   Findings: `low`.
   Risk: misconfigured repo metadata can still choose suboptimal paths.
   Disposition: `accept`.
4. Architecture/modularity boundaries and duplication reduction
   Question: Did modularization improve ownership boundaries?
   Evidence: extracted helpers in `devcovenant/core/flow/`
   `gate_changelog_helpers.py`, `gate_status_helpers.py`,
   `devcovenant/core/services/policy_check_runner.py`,
   `policy_runtime_actions.py`, and matching tests under
   `tests/devcovenant/core/flow/` and `tests/devcovenant/core/services/`.
   Findings: `low`.
   Risk: helper-spread can drift without boundary discipline.
   Disposition: `accept`.
5. Metadata/registry typing and profile/asset integrity
   Question: Are metadata resolution and registry contracts typed and stable?
   Evidence: metadata/runtime merge paths in
   `devcovenant/core/services/metadata.py`,
   registry/profile resolution in `devcovenant/core/services/registry.py`,
   `profile_registry.py`, policy contract typing in
   `devcovenant/core/contracts/policy.py`.
   Findings: `low`.
   Risk: profile overlay misconfiguration remains possible.
   Disposition: `accept`.
6. Semantics/de-BS contract integrity
   Question: Do command semantics and docs remain aligned?
   Evidence: gate semantics in `devcovenant/core/flow/gate.py`,
   workflow contracts in `AGENTS.md` and `devcovenant/docs/workflow.md`,
   architecture notes in `devcovenant/docs/architecture.md`.
   Findings: `low`.
   Risk: future doc drift if contract text is not updated with behavior
   changes.
   Disposition: `accept`.
7. Documentation and operator-efficiency coherence
   Question: Are operator docs aligned with artifact-first and concise output?
   Evidence: artifact triage guidance and mode behavior in
   `devcovenant/docs/workflow.md`, command/docs updates in
   `devcovenant/docs/architecture.md` and `devcovenant/docs/config.md`.
   Findings: `low`.
   Risk: verbosity tuning can regress if output paths fork again.
   Disposition: `accept`.
8. Test performance and observability
   Question: Are performance claims backed by stable runtime evidence?
   Evidence: duration and profile artifact generation in
   `devcovenant/core/runtime/execution.py`,
   profile services in `devcovenant/core/services/runtime_profile.py`,
   coverage in `tests/devcovenant/core/runtime/test_execution.py` and
   `tests/devcovenant/core/services/test_runtime_profile.py`.
   Findings: `low`.
   Risk: trend interpretation requires consistent run environments.
   Disposition: `accept`.
9. Security/compliance and packaging/installability
   Question: Are compliance and package boundaries explicitly validated?
   Evidence: dependency-license policy metadata in
   `devcovenant/builtin/policies/dependency_license_sync/`
   `dependency_license_sync.yaml`,
   packaging rules in `pyproject.toml` and `MANIFEST.in`,
   installability checks in `tests/devcovenant/test_install.py`.
   Findings: `medium`.
   Risk: external supply-chain trust (index/actions/runners) remains.
   Disposition: `defer` stricter provenance hardening.
10. Final risk register and closure decision
   Question: Is the hardening cycle ready for final go/no-go closure?
   Evidence: Item 8 accepted/deferred entries and Item 9 review notes in
   `PLAN.md`; closure workflow evidence from current gate/test logs.
   Findings: `medium`.
   Risk: final closure still depends on remaining Item 9 task completion.
   Disposition: `defer` final closure decision to Item 9 completion slice.
11. Public/internal API boundary integrity and package-export control
   Question: Are internal helpers kept internal while public entrypoints remain
   stable?
   Evidence: narrow top-level export in `devcovenant/__init__.py`,
   CLI entrypoints in `devcovenant/cli.py` and `devcovenant/__main__.py`,
   helper placement under `devcovenant/core/*`.
   Findings: `low`.
   Risk: accidental top-level re-exports could widen API surface.
   Disposition: `accept`.

**Progress Notes (2026-02-27, Slice 3: packaging/build/install rerun)**
- Re-ran packaging/installability validation for Item 9 Task 3 via
  `python3 -m unittest -v tests.devcovenant.test_install`.
- Result: `OK` (`11` tests), including wheel artifact boundary checks,
  license artifact presence checks, and install/runtime layout assertions.
- Findings: `low` risk; no packaging or installability regression detected.
- API-surface delta for this slice: `none`; validation evidence only.

**Progress Notes (2026-02-27, Slice 4: closure status and go/no-go record)**
- Marked Item 6 and Item 7 `complete` after confirming their acceptance
  criteria are evidence-backed across recorded slices and guard regressions.
- Marked Item 9 `complete` after the clean closure workflow baseline, full
  review matrix, and packaging/installability rerun all passed with explicit
  evidence.
- Closure decision: `go` for the 1.0 stabilization hardening cycle with
  residual deferred risk limited to external CI/index supply-chain trust and
  optional provenance pinning hardening.
- API-surface delta for this slice: `none`; closure is governance and status
  recording only.

## Cross-Cut Validation Matrix
- **Root-cause discipline:** preferred fixes land at the correct layer
  (runtime, launcher, profile, CI, docs) rather than policy weakening.
- **Semantics truth:** `check`, `gate`, logs, and docs/help continue to agree.
- **Evidence integrity:** changelog, gate status, run logs, and summaries
  remain trustworthy and auditable.
- **Metadata integrity:** typed/string contracts remain explicit and tested.
- **Profile integrity:** manifests, assets, overlays, and generated outputs
  stay
  synchronized.
- **Modularity:** extracted boundaries reduce duplication and maintenance risk.
- **API boundary integrity:** internal helpers stay internal unless explicitly
  promoted; stable command/runtime/engine surfaces remain contract anchors.
- **Operator efficiency:** token-economy workflow behavior remains practical
  and
  documented.
- **Security/compliance:** dependency/license/packaging/CI assumptions are
  reviewed and recorded.

## Documentation Deliverables
This plan is expected to touch only what the remediation work actually
changes:

1. `PLAN.md`
2. `CHANGELOG.md`
3. Runtime/docs/workflow/architecture docs affected by the fixes
4. `AGENTS.md` (via managed assets/refresh) only when workflow/contract text
   or policy block output changes
5. Optional security/compliance due-diligence artifact for Item 8/9

## Completion Criteria
This plan is complete only when all of the following are true:

1. Every blocking backlog item (`Item 1` through `Item 9`) is marked
   `complete`.
2. The issue register findings (`F1` through `F11`) are either resolved,
   explicitly accepted, or explicitly moved to the deferred appendix with
   rationale.
3. A final deep-system closure audit has been executed and recorded using
   `Item 9`.
4. The repository is gate-clean and evidence-backed at plan closure.

## Risk Controls
- **Scope thrash risk:** keep the backlog issue-driven; new work requires a
  finding or explicit plan amendment.
- **Refactor drift risk:** modularity splits must be behavior-preserving and
  regression-tested.
- **Policy weakening risk:** fix root-cause workflow/metadata/runtime issues
  before relaxing enforcement or allowlists.
- **Over-optimization risk:** preserve dual-runner test fidelity unless an
  explicit contract change is approved.
- **Documentation drift risk:** pair runtime/profile/CI behavior changes with
  the mapped docs in the same slice.
- **Audit shallowness risk:** final closure audit must use the mandatory
  review format, not a generic summary.

## Deferred Appendix (Non-Blocking)
These are not blocked by the current plan unless promoted via plan amendment.

- Broader critical-policy expansion beyond the current builtin critical set.
- Activation of `semantic-version-scope` (requires explicit version-governed
  workflow slice and migration posture).
- Cosmetic or breaking policy-ID renames (for example
  `last-updated-placement`) without a concrete migration need.
- Additional feature expansion unrelated to the issue register above.
