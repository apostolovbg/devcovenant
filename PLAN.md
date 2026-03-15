# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Last Updated:** 2026-03-15
**DevCovenant Version:** 1.0.0

This plan replaces the completed hardening-cycle roadmap with the current
strict no-fallback remediation program. The goal is simple: if DevCovenant
supports a behavior, it should support it explicitly and own it cleanly. If a
behavior exists only as compatibility glue, recovery magic, hidden flags,
runtime guessing, or documentation drift from older designs, we remove it.

The audit that seeded this plan found that the repository has already removed
most large legacy trees, but still carries targeted fallback behavior in gate
snapshots, managed-environment reruns, runtime authority lookup, cleanup
compatibility shims, `gate --status` recovery scanning, hidden `check` flags,
package export indirection, source-checkout launcher bytecode drift, and
several docs/tests that still preserve those contracts. This plan closes those
seams in dependency order and ends with a full downstream proof in a user
repo.

## Table of Contents
1. [Overview](#overview)
2. [Scope and Principles](#scope-and-principles)
3. [Issue Register](#issue-register)
4. [Non-Negotiable Constraints](#non-negotiable-constraints)
5. [Workflow](#workflow)
6. [Execution Order](#execution-order)
7. [Ordered Backlog](#ordered-backlog)
8. [Validation Matrix](#validation-matrix)
9. [Documentation Deliverables](#documentation-deliverables)
10. [Completion Criteria](#completion-criteria)
11. [Risk Controls and Non-Goals](#risk-controls-and-non-goals)

## Overview
### Status Vocabulary
- `pending`: not yet implemented.
- `complete`: implemented, tested, documented where needed, gated, and staged.
- `deferred`: intentionally out of scope for this cycle.

### Plan Purpose
- Remove remaining fallback and compatibility behavior from the 1.0.0 codebase.
- Make runtime authority explicit instead of inferred or recovered.
- Align CLI behavior, policy/runtime behavior, docs, and tests to the same
  strict contract.
- Prove the resulting package behavior in a downstream managed repo.

### Baseline Truths Preserved
- `check` is the read-only audit command.
- `gate` owns lifecycle writes and never runs tests internally.
- `core` owns program internals; `builtin` owns shipped policy/profile content.
- `python3 -m devcovenant` remains a supported launcher form unless an
  explicit backlog item changes that contract.
- No repo-root bootstrap files or startup hooks will be introduced to solve
  launcher/pycache behavior.

## Scope and Principles
### In Scope
- CLI command contracts.
- Launcher contract and pycache ownership.
- Runtime authority lookup and bootstrap behavior.
- Gate/session snapshot handling.
- Managed-environment execution behavior.
- Cleanup behavior.
- `gate --status` behavior.
- Package-export surfaces.
- Test-event adapter behavior.
- Root/package/docs wording and test expectations.
- Downstream package validation in `dlmc`.

### Guiding Principles
- Prefer explicit failure over silent fallback.
- Keep one authority for each runtime decision.
- Keep alternate supported behaviors explicit, documented, and tested.
- Do not retain compatibility code without a present-tense support promise.
- Remove fallback-oriented tests when the fallback is removed.

## Issue Register
### High
- `D0`: source-checkout `python3 -m devcovenant` can recreate repo-local
  bytecode before DevCovenant gains runtime control, and repo-root bootstrap
  files are not an acceptable fix.
- `D1`: legacy gate snapshot migration is still live through
  `legacy_numstat` handling.
- `D2`: managed-environment still supports wrapper rerun fallback through
  `managed_rerun_commands`.
- `D3`: managed-environment runtime still falls back to parsing `AGENTS.md`
  when the local registry is missing.

### Medium
- `D4`: `check` still accepts hidden legacy compatibility flags.
- `D5`: `gate --status` still scans recent log folders as a fallback pointer
  recovery path.
- `D6`: `clean` still preserves a legacy empty-placeholder override contract.
- `D7`: package-layer `__init__` files still present compatibility-export
  indirection.
- `D8`: runtime config still uses compatibility-style inference for selected
  engine options.
- `D9`: docs and tests still describe and preserve removed or unwanted
  fallback behavior.

### Decision Items
- `D10`: keep `python3 -m devcovenant` as an explicit alternate launcher form,
  but stop framing it as fallback behavior.
- `D11`: replace the hidden generic test-event fallback adapter with an
  explicit declared behavior.

## Non-Negotiable Constraints
- No edits inside managed `<!-- DEVCOV* -->` blocks.
- No silent command-contract flips outside the explicit plan items below.
- No deletion of historical changelog entries.
- `check` remains read-only.
- `gate` commands never run tests internally.
- Repo hygiene issues found during slices are cleared before continuing.
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
1. Reset the baseline and capture the live no-fallback starting point.
2. Lock the launcher/pycache contract before removing deeper fallback seams,
   so the rest of the cycle does not rely on fake bootstrap assumptions.
3. Remove the most invasive runtime compatibility behavior next:
   gate-session migration and managed-environment fallbacks.
4. Remove smaller command/runtime fallback seams next.
5. Simplify remaining package/runtime surfaces so the architecture reads as
   forward-only, not transitional.
6. Sweep docs/tests so the written contract matches the code contract.
7. Prove the result in this repo and then in `dlmc`.

## Ordered Backlog
### Item 1 [complete]: Baseline Cleanup and Delegacy Audit Reset
**Objective:** Start the no-fallback cycle from a clean, explicit baseline.

**Depends on:** none.

**Addresses:** supports all items.

**Implementation Tasks**
1. Remove live repo bytecode drift and any equivalent hygiene noise that would
   pollute the delegacy work.
2. Run read-only `check` and confirm the remaining findings are actual
   fallback/delegacy findings, not incidental hygiene drift.
3. Record the strict no-fallback issue register in `PLAN.md` and the current
   session in `CHANGELOG.md`.

**Tests and Validation**
1. `devcovenant check`
2. `devcovenant gate --start`

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`

**Acceptance Criteria**
1. The cycle starts from a known-clean baseline.
2. The active plan reflects the no-fallback program, not the completed prior
   roadmap.

**Closure Notes (2026-03-15)**
- Confirmed that the repo starts this cycle without lingering
  `devcovenant/__pycache__` drift, but a read-only source-checkout
  `devcovenant check` still recreated repo-local bytecode under
  `devcovenant/__pycache__`.
- Confirmed that the remaining live baseline issue is a real delegacy/root
  cause, not generic repo hygiene noise.
- Replaced the prior completed roadmap with the strict no-fallback issue
  register and dependency-ordered backlog now governing the next slices.

### Item 2 [complete]: Lock Launcher and Pycache Strictness
**Objective:** Make the launcher contract explicit and resolve source-checkout
bytecode drift without repo-root bootstrap files.

**Depends on:** Item 1.

**Addresses:** `D0`, supports `D8`, `D10`.

**Scope:** launcher behavior, pycache routing, source-checkout command truth,
and docs/tests for supported launcher forms.

**Implementation Tasks**
1. Define the strict launcher contract for this cycle: keep `devcovenant` and
   `python3 -m devcovenant` as supported forms, but do not rely on repo-root
   bootstrap files, startup hooks, or fake in-package pre-import fixes.
2. Audit the current launcher/pycache flow and remove any wording or code
   assumptions that imply source-tree bytecode drift can be prevented from too
   late in startup.
3. Implement a non-repo-root solution for pycache discipline where DevCovenant
   can honestly own it, or narrow the no-drift guarantee to the launcher forms
   that can control startup early enough.
4. Seed explicit config and docs wording for launcher expectations and pycache
   behavior.
5. Add focused regressions that prove the chosen launcher contract, reject
   repo-root bootstrap files as a solution, and document the supported
   behavior honestly.

**Tests and Validation**
1. Focused launcher/bootstrap tests.
2. Focused execution-runtime tests for pycache behavior.
3. Full `devcovenant test`.

**Documentation**
1. `PLAN.md`
2. `README.md`
3. `devcovenant/README.md`
4. `devcovenant/docs/installation.md`
5. `devcovenant/docs/architecture.md`
6. `devcovenant/docs/workflow.md`
7. `CHANGELOG.md`

**Acceptance Criteria**
1. The launcher/pycache contract is explicit, tested, and documented.
2. No repo-root bootstrap file or startup hook is required.
3. Later no-fallback items no longer depend on ambiguous bootstrap behavior.

**Closure Notes (2026-03-15)**
- Deleted the in-package `devcovenant/launcher_bootstrap.py` helper and
  removed the `cli.py` / `__main__.py` startup calls that implied DevCovenant
  could own pre-import launcher-process bytecode routing from inside the
  package.
- Kept `devcovenant` and `python3 -m devcovenant` as supported launcher forms,
  but narrowed the zero-drift promise honestly: source-checkout launcher-
  process bytecode control belongs to shell or CI `PYTHONPYCACHEPREFIX`, not
  to repo-root startup hooks or in-package bootstrap tricks.
- Made runtime pycache routing and repo bytecode cleanup depend on explicit
  `engine.pycache_prefix_enabled` config rather than runtime profile
  inference; refresh still seeds that key explicitly for `devcovrepo`.
- Added launcher-contract and explicit-opt-in pycache regressions, and updated
  root, package, config, workflow, installation, architecture, profile, and
  troubleshooting docs to match the strict launcher boundary.

### Item 3 [complete]: Remove Legacy Gate-Snapshot Compatibility
**Objective:** Delete all live migration paths for pre-current gate snapshot
payloads.

**Depends on:** Item 2.

**Addresses:** `D1`.

**Scope:** session snapshot capture, snapshot style detection, change-state
construction, and gate payload validation.

**Implementation Tasks**
1. Remove `legacy_numstat` style support from session snapshot helpers.
2. Remove epoch-based migration bridging used only for old snapshot payloads.
3. Remove `legacy_snapshot_compat` reason codes and related branch handling.
4. Make stale/old gate payloads fail explicitly with guidance to run a fresh
   `devcovenant gate --start`.
5. Remove obsolete tests that preserve migration behavior and add strict
   failure-path regressions.

**Tests and Validation**
1. Focused runtime/session snapshot tests.
2. Focused policy check-context tests.
3. Full `devcovenant test`.

**Documentation**
1. `devcovenant/docs/workflow.md`
2. `devcovenant/docs/architecture.md`
3. `CHANGELOG.md`

**Acceptance Criteria**
1. No live `legacy_numstat` runtime path remains.
2. Old payloads fail explicitly instead of being migration-bridged.
3. Tests no longer protect compatibility behavior that the product no longer
   supports.

**Closure Notes (2026-03-15)**
- Removed the legacy snapshot migration bridge from
  `devcovenant/core/runtime/session_snapshot.py` and the execution-layer
  delegate in `devcovenant/core/runtime/execution.py`.
- Changed snapshot-style handling so legacy multi-tab rows are classified as
  unsupported and fail with an explicit fresh-start instruction instead of
  falling back to epoch-based path discovery.
- Removed the legacy rendering/reason-code path from
  `devcovenant/core/services/policy_check_context.py`, so open and closed
  sessions now reject stale payloads directly.
- Replaced the old migration-preserving tests with strict rejection
  regressions and updated the workflow/architecture docs to say that only the
  current filesystem-hash gate snapshot format is supported.

### Item 4 [complete]: Remove Managed-Environment Fallback Behavior
**Objective:** Make managed-environment execution strict and single-authority.

**Depends on:** Item 3.

**Addresses:** `D2`, `D3`.

**Scope:** managed-environment runtime resolution, CLI re-exec behavior, policy
metadata/runtime authority, and docs/tests for wrapper reruns.

**Implementation Tasks**
1. Remove `managed_rerun_commands` support from runtime, docs, and tests.
2. Remove the `resolve-rerun-command` runtime action and any CLI dispatch that
   consumes it.
3. Remove `AGENTS.md` parsing fallback for managed-environment runtime
   resolution and require the local policy registry as the sole runtime
   authority.
4. Make managed-environment failures explicit and operator-actionable.
5. Update profile/config docs so managed-environment behavior is described as
   strict preparation plus explicit failure, not wrapper fallback.

**Tests and Validation**
1. Focused managed-environment runtime tests.
2. Focused CLI tests.
3. Full `devcovenant test`.

**Documentation**
1. `README.md`
2. `devcovenant/README.md`
3. `devcovenant/docs/installation.md`
4. `devcovenant/docs/config.md`
5. `devcovenant/docs/workflow.md`
6. `devcovenant/docs/troubleshooting.md`
7. `CHANGELOG.md`

**Acceptance Criteria**
1. No wrapper rerun fallback remains.
2. No runtime AGENTS parsing fallback remains for managed-environment
   behavior.
3. Managed-environment failure modes are explicit and documented.

**Closure Notes (2026-03-15)**
- Removed `managed_rerun_commands` support from managed-environment runtime,
  CLI dispatch, descriptor metadata, docs, and tests.
- Removed the `resolve-rerun-command` runtime action and the related
  execution-runtime helper surface.
- Removed `AGENTS.md` parsing fallback from managed-environment runtime.
  Local policy registry is now the only runtime authority, and missing
  registry state fails explicitly with `devcovenant refresh` guidance.
- Tightened managed-environment failure behavior so missing or
  non-executable managed interpreters stop with explicit operator-actionable
  errors instead of attempting wrapper reruns.

### Item 5 [complete]: Remove Hidden Command and Cleanup Compatibility
**Objective:** Delete remaining command-level fallback and compatibility seams.

**Depends on:** Item 4.

**Addresses:** `D4`, `D5`, `D6`, supports `D8`.

**Scope:** `check`, `clean`, `gate --status`, and runtime option resolution.

**Implementation Tasks**
1. Remove hidden legacy `check` flags (`--nofix`, `--norefresh`).
2. Remove latest-run pointer recovery scanning from `gate --status` and rely
   only on owned pointer artifacts.
3. Remove the clean empty-placeholder compatibility exception.
4. Stop inferring selected runtime options from compatibility-style fallback
   rules where explicit config should be required.
5. Seed explicit config/template values for any runtime settings whose
   fallback is removed.
6. Update tests and docs accordingly.

**Tests and Validation**
1. Focused `check`, `clean`, `gate --status`, and execution-runtime tests.
2. Full `devcovenant test`.

**Documentation**
1. `devcovenant/docs/config.md`
2. `devcovenant/docs/workflow.md`
3. `devcovenant/docs/architecture.md`
4. `CHANGELOG.md`

**Acceptance Criteria**
1. `check` exposes only its real contract.
2. `gate --status` does not scan log folders as recovery logic.
3. `clean` no longer preserves legacy placeholder behavior.
4. Runtime option ownership is explicit in config/templates.

**Closure Notes (2026-03-15)**
- Removed hidden `check` flags (`--nofix`, `--norefresh`) so the audit-only
  command exposes only its real CLI contract.
- Removed latest-run recovery scanning from `gate --status`; status now reads
  only the owned latest-run pointer artifact.
- Removed the clean all-empty-placeholder compatibility exception so
  replacement semantics are fully explicit.
- Removed `engine.tests_output_mode -> engine.output_mode` fallback. Test
  output mode is now owned explicitly by config/template values.
- Updated docs and focused regressions for `check`, `clean`,
  `gate --status`, and execution-runtime option resolution.

### Item 6 [complete]: Remove Transitional Package and Event Compatibility
**Objective:** Make package surfaces and event behavior read as intentional,
not transitional.

**Depends on:** Item 5.

**Addresses:** `D7`, `D10`, `D11`.

**Scope:** package `__init__` exports, launcher framing, and test-event
adapter behavior.

**Implementation Tasks**
1. Remove compatibility-export `__getattr__` indirection from package-layer
   `__init__` files and convert internal imports to direct module imports.
2. Keep `python3 -m devcovenant` as a supported launcher form, but remove all
   fallback framing from code comments and docs.
3. Replace the hidden generic test-event fallback adapter with an explicit
   declared behavior.
4. Decide and document whether unmatched test commands are skipped explicitly
   or handled by a declared generic adapter.
5. Update tests so they protect the new explicit behavior only.

**Tests and Validation**
1. Focused package/import tests.
2. Focused test-event runtime tests.
3. Full `devcovenant test`.

**Documentation**
1. `README.md`
2. `devcovenant/README.md`
3. `devcovenant/docs/architecture.md`
4. `devcovenant/docs/installation.md`
5. `devcovenant/docs/policies.md`
6. `CHANGELOG.md`

**Acceptance Criteria**
1. Package surfaces no longer describe or implement compatibility-export
   indirection.
2. Alternate launcher forms are described as supported forms, not fallbacks.
3. Test-event handling is explicit and intentionally configured.

**Closure Notes (2026-03-15)**
- Removed lazy `__getattr__` compatibility indirection from the layered
  `devcovenant/core/*/__init__.py` packages and shifted internal callers to
  concrete module imports instead of package-export shims.
- Kept `python3 -m devcovenant` and equivalent launcher forms as supported
  entrypoints, but removed remaining fallback framing from the workflow and
  installation narrative.
- Replaced the hidden generic test-event fallback with explicit behavior:
  unmatched test commands are skipped unless a profile declares
  `generic_test_event_adapter_factory` intentionally.
- Added focused package-namespace and test-event regressions, and updated
  README/package/profile/architecture docs to describe the explicit runtime
  contract only.

### Item 7 [complete]: Full Docs and Tests Delegacy Sweep
**Objective:** Remove stale fallback/compatibility narration and obsolete test
coverage across the repo.

**Depends on:** Items 2-6.

**Addresses:** `D9`, consolidates `D10` and `D11`.

**Scope:** root docs, package docs, `devcovenant/docs/*`, config assets,
profile assets, and tests that still encode removed fallback behavior.

**Implementation Tasks**
1. Sweep all docs for fallback/compatibility language that no longer reflects
   product behavior.
2. Remove outdated examples and troubleshooting guidance built around removed
   fallback paths.
3. Remove tests that preserve removed compatibility behavior.
4. Add or update strict-behavior tests where needed so the new contract is
   visible and stable.
5. Re-run documentation route/quality checks and fix any fallout.

**Tests and Validation**
1. Focused doc-generation/refresh tests.
2. Focused CLI/runtime tests touched by the sweep.
3. Full `devcovenant test`.

**Documentation**
1. `README.md`
2. `devcovenant/README.md`
3. `devcovenant/docs/architecture.md`
4. `devcovenant/docs/config.md`
5. `devcovenant/docs/installation.md`
6. `devcovenant/docs/workflow.md`
7. `devcovenant/docs/troubleshooting.md`
8. `devcovenant/docs/policies.md`
9. `devcovenant/docs/profiles.md`
10. `CHANGELOG.md`

**Acceptance Criteria**
1. Docs describe the current strict product truth.
2. Tests no longer preserve deleted fallback behavior.
3. Documentation routes and quality checks remain green.

**Closure Notes (2026-03-15)**
- Swept the remaining package and workflow docs so they describe explicit
  supported behavior instead of transitional fallback language.
- Tightened installation, profiles, troubleshooting, workflow, and
  architecture wording around alternate launcher use, stage bootstrap,
  snapshot ownership, and helper-surface ownership.
- Cleaned stale transition-oriented test narration while preserving the
  active strict-behavior assertions that still matter for the current
  runtime contract.
- Kept only intentional current-behavior references in tests and docs;
  historical or deleted-path narration was removed where it no longer helped
  explain the live 1.0.0 baseline.

### Item 8 [pending]: Full Validation and Downstream Proof
**Objective:** Prove the strict no-fallback baseline operationally in both this
repo and a downstream managed repo.

**Depends on:** Items 1-7.

**Addresses:** validates the full program.

**Scope:** full repo validation, package rebuild/reinstall, and downstream
`dlmc` proof.

**Implementation Tasks**
1. Run a final repo-wide review of remaining `fallback`, `legacy`, and
   `compatibility` references and classify survivors as intentional wording or
   defects.
2. Rebuild and reinstall the local package from the current repo state.
3. Validate this repo with the full gate workflow.
4. Validate `dlmc` with:
   - `devcovenant upgrade`
   - `devcovenant refresh`
   - `devcovenant clean --build` / `--cache` / `--all`
   - `devcovenant check`
   - `devcovenant gate --status`
5. Inspect downstream run artifacts and confirm no removed fallback path is
   still required in practice.
6. Record closure evidence in the changelog and close the plan.

**Tests and Validation**
1. Full `devcovenant test`.
2. Full gate cycle in this repo.
3. Downstream operational proof in `dlmc`.

**Documentation**
1. `PLAN.md`
2. `CHANGELOG.md`

**Acceptance Criteria**
1. The package works without relying on removed fallback behavior.
2. The downstream user-repo path is clean.
3. The plan can be marked complete with evidence.

## Validation Matrix
- Item 1: `check`, `gate --start`
- Item 2: launcher/bootstrap + execution-runtime focused tests, full suite
- Item 3: snapshot + check-context focused tests, full suite
- Item 4: managed-environment runtime/CLI focused tests, full suite
- Item 5: `check`/`clean`/`gate --status` focused tests, full suite
- Item 6: import/event focused tests, full suite
- Item 7: refresh/docs/CLI focused tests, full suite
- Item 8: full suite, full gate cycle, downstream `dlmc` proof

## Documentation Deliverables
- `PLAN.md`
- `CHANGELOG.md`
- `README.md`
- `devcovenant/README.md`
- `devcovenant/docs/architecture.md`
- `devcovenant/docs/config.md`
- `devcovenant/docs/installation.md`
- `devcovenant/docs/workflow.md`
- `devcovenant/docs/troubleshooting.md`
- `devcovenant/docs/policies.md`
- `devcovenant/docs/profiles.md`

## Completion Criteria
1. No live runtime or command path relies on compatibility or fallback logic
   that the product no longer intends to support.
2. Launcher and pycache behavior are explicit and do not rely on repo-root
   bootstrap files.
3. Runtime authority for the affected behaviors is explicit and singular.
4. Docs and tests match the strict product truth.
5. Full repo validation passes.
6. Downstream `dlmc` validation passes.

## Risk Controls and Non-Goals
### Risk Controls
- Remove one compatibility cluster at a time and rerun focused regressions
  before the full suite.
- Keep alternate supported behavior only when it is explicitly named,
  documented, and tested as supported behavior.
- Reject repo-root bootstrap files and hidden startup hooks as a launcher
  remedy.
- Treat user-repo validation as mandatory, not optional.

### Non-Goals
- This cycle does not redesign the policy model or the gate workflow.
- This cycle does not change the public release version on its own.
- This cycle does not add new convenience fallbacks to replace the removed
  ones.
