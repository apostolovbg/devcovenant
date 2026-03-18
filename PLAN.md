# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Last Updated:** 2026-03-18
**DevCovenant Version:** 1.0.0

This plan replaces the completed registry-layout roadmap with the next
future-facing program: turn version handling into a first-class,
scheme-neutral DevCovenant framework across policy, docs, package surfaces,
and project lifecycle governance.

The baseline has already shifted:
- `version-governance` now replaces `semantic-version-scope`
- scheme adapters now exist for SemVer, CalVer, integer, PEP 440, and
  custom repo-defined schemes
- `version-sync` now delegates parsing and equality to
  `version-governance`

The remaining work is the full plug-in across the rest of the product:
- remove leftover SemVer assumptions outside the new framework
- enforce ecosystem/package legality where manifests need stricter rules
- define a clean project-governance model for stage, stance, and
  intentionally unversioned lifecycle state without overloading
  `version-governance`
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
- Create a clean `project-governance` layer for stage, development stance,
  codename, build identity, and intentionally unversioned lifecycle state.
- Keep the 1.x architecture forward-only: no fallback SemVer parsing, no
  duplicate compatibility policies, and no hidden scheme-specific shortcuts.

### Baseline Truths Preserved
- `version-governance` owns repo version semantics.
- `project-governance` will own project-phase and stance metadata without
  redefining version semantics.
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
- `project-governance`
  - governs project phase, development stance, codename, build identity,
    and versioning mode
  - stays orthogonal to `version-governance` and may coexist with it
  - provides the governed model for intentionally unversioned repos without
    forcing fake numbered versions

### Design Rules
- Version semantics flow from `version-governance` outward.
- Equality and ordering must come from the active scheme adapter, not from
  ad-hoc regexes in unrelated policies.
- Ecosystem legality is a separate concern from repo-level equality.
- Codenames, stages, and build identities are not versions, but they are
  legitimate governed project metadata.
- Intentionally unversioned repos should render an explicit non-version
  label, not a fake numbered version.

## Scope and Principles
### In Scope
- remaining version readers and validators across builtins and generated
  surfaces
- package/ecosystem legality rules for version-bearing manifests
- schema-neutral doc/header handling where version strings appear
- defaults/profile assumptions that still encode SemVer expectations
- `project-governance` design and implementation
- tests/docs for the completed version-stack contract
- downstream proof in real managed repos

### Guiding Principles
- Prefer one version framework over many local parsers.
- Prefer explicit scheme adapters over generic if/else growth.
- Prefer explicit legality checks over implicit ecosystem assumptions.
- Prefer explicit `project-governance` metadata over fake
  numbered-version placeholders.
- Prefer forward-only architecture over compatibility layers.
- Prefer exact ownership boundaries between repo version semantics and
  packaging semantics.

## Issue Register
### High
- `V0`: some remaining policies, docs, or repo defaults may still encode
  SemVer assumptions outside `version-governance`.
- `V1`: package-facing version surfaces can now stay in sync under custom
  schemes without proving they are legal for their packaging ecosystem.
- `V2`: DevCovenant has no first-class orthogonal governance layer for
  project phase, development stance, codename, build identity, and
  intentionally unversioned state.
- `V3`: docs need a single explicit explanation of how project governance,
  repo version schemes, and package legality fit together.

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
- `V8`: how broad `project-governance` v1 should be beyond stage, stance,
  codename, build identity, and versioning mode.
- `V9`: which ecosystems get first-class legality adapters in the initial
  pass after Python/PEP 440.

## Non-Negotiable Constraints
- No edits inside managed `<!-- DEVCOV* -->` blocks.
- No restoration of `semantic-version-scope` as a compatibility alias.
- No hidden SemVer fallback parser paths outside `version-governance`.
- No fake numbered-version placeholders when a repo is intentionally
  unversioned.
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
3. Design and implement `project-governance` after version and package
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

### Item 2 [complete]: Add Ecosystem and Package Legality Enforcement
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

**Closure Notes**
1. Kept package legality inside `version-sync` role handling through new
   `role_legality_schemes` metadata instead of introducing a second
   overlapping policy.
2. Seeded Python package manifests with `package_manifest=>pep440` legality
   while preserving repo-level equality through the active
   `version-governance` scheme.
3. Closed the slice with focused legality regressions, refresh-driven
   managed-surface convergence, and the full gated workflow.

### Item 3 [complete]: Introduce Orthogonal Project Governance
**Objective:** Create a first-class `project-governance` policy for project
phase, development stance, codename, build identity, and intentionally
unversioned lifecycle state.

**Depends on:** Item 2.

**Addresses:** `V2`, `V3`, `V8`.

**Scope:** project stage, development stance, versioning mode, codename,
build identity, managed-header behavior, and unversioned changelog flow.

**Implementation Tasks**
1. Define `project-governance` metadata for stage, development stance,
   versioning mode, codename, and build identity.
2. Keep `project-governance` orthogonal to `version-governance` and
   `version-sync`.
3. Define managed-header behavior so ordinary docs keep the compact
   `Project Version` line while `AGENTS.md` gets richer project-governance
   headers.
4. Define how intentionally unversioned repos render `Project Version`
   labels and how `CHANGELOG.md` uses `## Unreleased`.
5. Implement the policy and wire it only into intended docs/config surfaces.

**Tests and Validation**
1. Focused `project-governance` policy tests.
2. Cross-policy tests for interaction with `version-governance` and
   unversioned/versioned header rendering.
3. Focused refresh/changelog tests for `## Unreleased` and `AGENTS.md`
   project-governance headers.
4. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`
3. `devcovenant/docs/policies.md`
4. `devcovenant/docs/workflow.md`
5. `devcovenant/docs/architecture.md`

**Acceptance Criteria**
1. `project-governance` can coexist with `version-governance`.
2. Intentionally unversioned repos can render explicit non-version labels
   without fake numbered versions.
3. Extra project-governance header lines appear only where intended,
   starting with `AGENTS.md`.
4. `CHANGELOG.md` supports the unversioned `## Unreleased` flow cleanly.

**Closure Notes**
1. Introduced a first-class `project-governance` policy with explicit
   lifecycle metadata for `stage`, `development_stance`,
   `versioning_mode`, and optional `codename` / `build_identity`.
2. Wired refresh, managed-doc validation, changelog helpers, and
   changelog-coverage through the same project-governance runtime so
   `AGENTS.md` can render richer governance headers while intentionally
   unversioned repos use explicit non-version labels plus `## Unreleased`.
3. Closed the slice with focused project-governance/refresh/changelog
   regressions, refresh-driven managed-surface convergence, and the full
   gated workflow.

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
- focused `project-governance` tests when introduced
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
3. `project-governance` exists as an orthogonal lifecycle layer,
   including intentionally unversioned repos without fake numbered
   versions.
4. Docs and defaults no longer assume SemVer unless a surface intentionally
   requires it.
5. The local repo and at least one downstream managed repo prove the result
   operationally.

## Risk Controls and Non-Goals
### Risk Controls
- Keep ecosystem legality separate from repo version equality.
- Avoid overloading `version-governance` with `project-governance`
  concerns.
- Avoid custom-adapter growth that bypasses test coverage or explicit config.
- Prefer adapter extension points over regex sprawl.
- Keep policy text generic unless a specific ecosystem or scheme truly needs
  to be named.

### Non-Goals
- Do not restore `semantic-version-scope`.
- Do not force one global version scheme on all repositories.
- Do not treat codenames, stages, or build tags as interchangeable with
  real release versions.
- Do not force `project-governance` to masquerade as version governance.
- Do not add fallback parsers for legacy version strings outside the
  configured scheme adapters.
