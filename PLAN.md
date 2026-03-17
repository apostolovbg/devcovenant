# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Last Updated:** 2026-03-17
**DevCovenant Version:** 1.0.0

This plan replaces the completed registry-layout roadmap with the next
future-facing program: turn version handling into a first-class,
scheme-neutral DevCovenant framework across policy, docs, package surfaces,
and pre-release repo lifecycle.

The baseline has already shifted:
- `version-governance` now replaces `semantic-version-scope`
- scheme adapters now exist for SemVer, CalVer, integer, PEP 440, and
  custom repo-defined schemes
- `version-sync` now delegates parsing and equality to
  `version-governance`

The remaining work is the full plug-in across the rest of the product:
- remove leftover SemVer assumptions outside the new framework
- enforce ecosystem/package legality where manifests need stricter rules
- define a clean pre-version identity model for repos that are not yet on a
  real release version
- keep the whole stack forward-only, with no fallback compatibility paths

## Table of Contents
1. [Overview](#overview)
2. [Target Model](#target-model)
3. [Scope and Principles](#scope-and-principles)
4. [Issue Register](#issue-register)
5. [Non-Negotiable Constraints](#non-negotiable-constraints)
6. [Workflow](#workflow)
7. [Execution Order](#execution-order)
8. [Ordered Backlog](#ordered-backlog)
9. [Validation Matrix](#validation-matrix)
10. [Documentation Deliverables](#documentation-deliverables)
11. [Completion Criteria](#completion-criteria)
12. [Risk Controls and Non-Goals](#risk-controls-and-non-goals)

## Overview
### Status Vocabulary
- `pending`: not yet implemented.
- `complete`: implemented, tested, documented where needed, gated, and
  staged.
- `deferred`: intentionally out of scope for this cycle.

### Plan Purpose
- Treat version semantics as a shared framework, not a SemVer-only special
  case.
- Make all builtins and managed surfaces either scheme-neutral or explicitly
  scheme-aware through `version-governance`.
- Separate repo-level version governance from ecosystem-specific package
  legality.
- Create a clean path for repos that are still pre-version and only have a
  codename, stage, build identifier, or `Unreleased` lifecycle.
- Keep the 1.x architecture forward-only: no fallback SemVer parsing, no
  duplicate compatibility policies, and no hidden scheme-specific shortcuts.

### Baseline Truths Preserved
- `version-governance` owns repo version semantics.
- `version-sync` owns synchronization of declared version surfaces.
- `check` remains the read-only audit command.
- `gate` owns lifecycle writes and never runs tests internally.
- Package ecosystems may impose stricter legality than the repo's chosen
  canonical version scheme.

## Target Model
### Final Version Responsibilities
- `version-governance`
  - validates the repo's chosen version scheme
  - owns scheme-specific parsing, normalization, ordering, and optional bump
    behavior
- `version-sync`
  - reads configured version surfaces
  - compares them using the active `version-governance` scheme
  - does not hardcode SemVer parsing rules
- ecosystem/package legality
  - validates that packaging-facing version surfaces are legal for their
    ecosystem
  - examples: Python package metadata, npm package manifests, future adapter
    targets
- pre-version identity
  - governs repos that do not yet have a real release version
  - owns stage/codename/build identity instead of overloading
    `version-governance`

### Design Rules
- Version semantics flow from `version-governance` outward.
- Equality and ordering must come from the active scheme adapter, not from
  ad-hoc regexes in unrelated policies.
- Ecosystem legality is a separate concern from repo-level equality.
- Codenames and build identities are not versions.
- Repos without a real version should have an explicit governed state, not a
  fake placeholder version.

## Scope and Principles
### In Scope
- remaining version readers and validators across builtins and generated
  surfaces
- package/ecosystem legality rules for version-bearing manifests
- schema-neutral doc/header handling where version strings appear
- defaults/profile assumptions that still encode SemVer expectations
- pre-version repo identity design and implementation
- tests/docs for the completed version-stack contract
- downstream proof in real managed repos

### Guiding Principles
- Prefer one version framework over many local parsers.
- Prefer explicit scheme adapters over generic if/else growth.
- Prefer explicit legality checks over implicit ecosystem assumptions.
- Prefer explicit pre-version state over fake release versions.
- Prefer forward-only architecture over compatibility layers.
- Prefer exact ownership boundaries between repo version semantics and
  packaging semantics.

## Issue Register
### High
- `V0`: some remaining policies, docs, or repo defaults may still encode
  SemVer assumptions outside `version-governance`.
- `V1`: package-facing version surfaces can now stay in sync under custom
  schemes without proving they are legal for their packaging ecosystem.
- `V2`: DevCovenant has no first-class governed state for repos that are
  still pre-version and only have stage/codename/build identity.
- `V3`: docs need a single explicit explanation of how repo version schemes,
  package legality, and pre-version identity fit together.

### Medium
- `V4`: generated managed docs and examples still need a version-stack sweep
  for wording that implies SemVer by default.
- `V5`: custom profiles and repo-local policies may still assume SemVer in
  metadata examples or custom checks.
- `V6`: future scheme-specific bump semantics need a clear extension path so
  non-SemVer schemes do not inherit major/minor/patch language by accident.

### Decision Items
- `V7`: whether package legality belongs inside `version-sync` role handling
  or in a separate dedicated policy.
- `V8`: whether pre-version identity is best modeled as a new policy such as
  `project-identity` or a broader release-lifecycle policy.
- `V9`: which ecosystems get first-class legality adapters in the initial
  pass after Python/PEP 440.

## Non-Negotiable Constraints
- No edits inside managed `<!-- DEVCOV* -->` blocks.
- No restoration of `semantic-version-scope` as a compatibility alias.
- No hidden SemVer fallback parser paths outside `version-governance`.
- No fake version placeholders for pre-version repos when identity is the
  real concern.
- No deletion of historical changelog entries.
- `check` remains read-only.
- `gate` commands never run tests internally.
- All slices end with tests, gate closure, and staging.

## Workflow
This plan follows the repository workflow contract in `AGENTS.md`.
Every implementation slice in this plan uses the same closure pattern:

1. Use the managed environment.
2. Run `devcovenant gate --start` before edits.
3. Clear start-gate complaints before feature work.
4. Implement one coherent slice.
5. Run `devcovenant gate --mid` before tests.
6. Run focused tests when useful, then run `devcovenant test`.
7. Run `devcovenant gate --end`.
8. If `gate --end` introduces changes or complaints, loop explicitly until
   clean.
9. Stage all changes for the completed slice.

Operator notes:
- Prefer run artifacts for diagnosis before ad-hoc redirects.
- Keep updates concise: what changed, what passed or failed, and the next
  step.
- Normal-mode streaming is acceptable when concise.

## Execution Order
1. Audit and neutralize the remaining version-reading assumptions first.
2. Lock the package/ecosystem legality model next.
3. Design and implement pre-version identity after version and package
   boundaries are explicit.
4. Sweep docs/examples/tests only after the code contract is stable.
5. Prove the result in this repo and then in downstream managed repos.

## Ordered Backlog
### Item 1 [complete]: Sweep Remaining Version Readers and Assumptions
**Objective:** Ensure every remaining version-aware policy, generated surface,
and default profile path is either scheme-neutral or delegated through
`version-governance`.

**Depends on:** none.

**Addresses:** `V0`, `V4`, `V5`.

**Scope:** policy readers, refresh/rendered headers, docs examples, custom
profile examples, generated config comments, and any leftover SemVer-centric
extractors or naming.

**Implementation Tasks**
1. Audit builtins, generated docs, and profile defaults for leftover SemVer
   assumptions.
2. Replace remaining local version regexes or SemVer-named extractors with
   scheme-neutral readers or `version-governance` delegation.
3. Sweep generated/config/template wording so it describes version formats
   generically unless a scheme is intentionally named.
4. Audit custom-profile examples and repo-local metadata for stale SemVer
   defaults.

**Tests and Validation**
1. Focused version-stack audit tests.
2. Focused refresh/rendered-doc tests.
3. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. `devcovenant/docs/policies.md`
4. `devcovenant/docs/profiles.md`
5. `devcovenant/docs/config.md`
6. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. No builtin policy or managed doc surface depends on SemVer parsing unless
   it is intentionally specific to a SemVer-only concern.
2. Default profile examples are scheme-neutral.
3. Remaining SemVer mentions are intentional and documented.

**Closure Notes**
1. Removed the hidden generic SemVer baseline from `defaults` and required
   `version-governance.scheme` explicitly when version governance or
   version-sync resolution is used.
2. Moved this repository's SemVer-specific defaults into `devcovrepo` and
   clarified docs/runtime wording so DevCovenant package upgrade comparison is
   distinct from governed repo version semantics.
3. Closed the slice with focused version-stack regressions, refresh-driven
   managed-surface convergence, and the full gated workflow.

### Item 2 [pending]: Add Ecosystem and Package Legality Enforcement
**Objective:** Keep repo version equality flexible while enforcing stricter
package-manifest legality where ecosystems require it.

**Depends on:** Item 1.

**Addresses:** `V1`, `V7`, `V9`.

**Scope:** Python package metadata first, then the adapter pattern for future
manifest ecosystems.

**Implementation Tasks**
1. Decide whether package legality lives inside `version-sync` role handling
   or in a dedicated companion policy.
2. Implement Python package legality using a PEP 440 adapter for packaging
   surfaces such as `pyproject.toml`.
3. Add metadata that can declare ecosystem-specific legality per synced
   surface or role.
4. Keep repo-level custom schemes allowed while failing illegal package
   manifest values explicitly.
5. Define the extension path for future ecosystems without falling back to
   generic string checks.

**Tests and Validation**
1. Focused legality tests for Python package manifests.
2. Cross-scheme sync tests proving repo equality can differ from package
   legality.
3. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. `devcovenant/docs/policies.md`
4. `devcovenant/docs/config.md`
5. `devcovenant/docs/installation.md`
6. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. Python package version surfaces fail when they violate PEP 440 even if
   the repo's chosen scheme is otherwise valid.
2. Repo-level version governance remains scheme-neutral.
3. The extension path for future package ecosystems is explicit.

### Item 3 [pending]: Introduce Governed Pre-Version Identity
**Objective:** Create a first-class governed model for repos that are not yet
on a real release version.

**Depends on:** Item 2.

**Addresses:** `V2`, `V3`, `V8`.

**Scope:** lifecycle stage, codename, build identity, and the boundary between
`Unreleased` repo state and real release versions.

**Implementation Tasks**
1. Choose the policy shape for pre-version identity.
2. Define metadata for stage/codename/build identity without calling those
   values versions.
3. Define how pre-version repos relate to `version-governance` and
   `version-sync`.
4. Define how changelog structure and managed docs should behave before the
   first real version exists.
5. Implement the policy and wire it into defaults/docs only where intended.

**Tests and Validation**
1. Focused lifecycle/pre-version policy tests.
2. Cross-policy tests for interaction with `version-governance` and
   `version-sync`.
3. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. `devcovenant/docs/policies.md`
4. `devcovenant/docs/workflow.md`
5. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. Repos can be explicitly governed before adopting a real release version.
2. Codenames and build identifiers are not treated as fake versions.
3. The transition from pre-version identity to real version governance is
   documented and test-covered.

### Item 4 [pending]: Expand Scheme-Specific Governance Semantics
**Objective:** Grow the framework beyond simple equality so scheme-specific
ordering and bump rules remain intentional and explicit.

**Depends on:** Item 3.

**Addresses:** `V6`.

**Scope:** bump semantics, canonicalization rules, release marker behavior,
and future scheme adapters.

**Implementation Tasks**
1. Review current `enforce_bumping` behavior across builtin schemes.
2. Split generic bump enforcement from scheme-specific bump semantics where
   needed.
3. Define explicit extension points for scheme-specific release markers,
   scope rules, or canonicalization.
4. Add tests that prove non-SemVer schemes do not inherit
   major/minor/patch language accidentally.

**Tests and Validation**
1. Focused adapter/bump tests.
2. Cross-scheme governance tests.
3. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. `devcovenant/docs/policies.md`
4. `devcovenant/docs/config.md`
5. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. Builtin schemes expose only the bump semantics they actually support.
2. Generic bump enforcement is still available where ordering exists.
3. The framework can grow new schemes without copying SemVer language.

### Item 5 [pending]: Final Docs, Audit, and Downstream Proof
**Objective:** Close the version-stack program with a full docs sweep and
real-repo proof.

**Depends on:** Items 1-4.

**Addresses:** `V3`, `V4`, `V5`.

**Scope:** docs, generated surfaces, tests, local proof, and downstream proof
in at least one managed repo.

**Implementation Tasks**
1. Sweep package docs, root docs, managed headers, and examples for the final
   version-stack contract.
2. Run a deliberate audit for leftover SemVer wording or fallback logic.
3. Rebuild/reinstall DevCovenant locally.
4. Prove the workflow in this repo.
5. Prove the workflow in `dlmc` or another managed downstream repo.

**Tests and Validation**
1. Full `devcovenant test`.
2. `devcovenant gate --mid` and `devcovenant gate --end`.
3. Downstream `upgrade`, `refresh`, `check`, `clean`, and gate proof.

**Documentation**
1. All touched docs.
2. `PLAN.md`
3. `CHANGELOG.md`

**Acceptance Criteria**
1. The version-stack contract is documented once and consistently.
2. This repo passes the full workflow cleanly.
3. At least one downstream managed repo proves the result operationally.

## Validation Matrix
### Local Repo
- focused version-governance tests
- focused version-sync tests
- focused refresh/rendered-doc tests
- focused package-legality tests when introduced
- focused pre-version identity tests when introduced
- `devcovenant test`
- `devcovenant gate --mid`
- `devcovenant gate --end`

### Downstream Proof
- rebuild and reinstall the local package
- `devcovenant upgrade`
- `devcovenant refresh`
- `devcovenant check`
- `devcovenant clean`
- `devcovenant gate --status`

## Documentation Deliverables
- `PLAN.md`
- `CHANGELOG.md`
- `README.md`
- `AGENTS.md`
- `devcovenant/README.md`
- `devcovenant/docs/architecture.md`
- `devcovenant/docs/config.md`
- `devcovenant/docs/installation.md`
- `devcovenant/docs/policies.md`
- `devcovenant/docs/profiles.md`
- `devcovenant/docs/registry.md`
- `devcovenant/docs/workflow.md`

## Completion Criteria
This program is complete only when:
1. DevCovenant has one clear version framework for repo-level version
   semantics.
2. Package-manifest legality is enforced explicitly where ecosystems require
   it.
3. Pre-version repos have a governed lifecycle that does not misuse fake
   versions.
4. Docs and defaults no longer assume SemVer unless a surface intentionally
   requires it.
5. The local repo and at least one downstream managed repo prove the result
   operationally.

## Risk Controls and Non-Goals
### Risk Controls
- Keep ecosystem legality separate from repo version equality.
- Avoid overloading `version-governance` with pre-version identity.
- Avoid custom-adapter growth that bypasses test coverage or explicit config.
- Prefer adapter extension points over regex sprawl.
- Keep policy text generic unless a specific ecosystem or scheme truly needs
  to be named.

### Non-Goals
- Do not restore `semantic-version-scope`.
- Do not force one global version scheme on all repositories.
- Do not treat codenames or build tags as interchangeable with real
  release versions.
- Do not add fallback parsers for legacy version strings outside the
  configured scheme adapters.
