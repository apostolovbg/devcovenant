# DevCovenant Development Plan
**Last Updated:** 2026-02-14
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan is the execution backlog for the 0.2.6 API-freeze phase.
The goal is to make runtime behavior, extension contracts, and data contracts
explicit, stable, and implementation-aligned with `SPEC.md`.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Operating Rules](#operating-rules)
4. [Contract Surfaces](#contract-surfaces)
5. [Target Core Layout](#target-core-layout)
6. [Implementation Backlog](#implementation-backlog)
7. [Acceptance Criteria](#acceptance-criteria)
8. [Validation Cycle](#validation-cycle)

## Overview
- Scope: finish 0.2.6 API freeze and remove remaining SPEC-vs-reality drift.
- Standard: forward-only implementation of the current contract.
- Constraint: no legacy fallbacks and no active anti-legacy policing logic
  unless a policy explicitly requires such behavior.

## Workflow
- Start with `python3 -m devcovenant gate --start`.
- Implement one backlog item at a time against `SPEC.md`.
- Run `python3 -m devcovenant refresh` when contract docs/schema change.
- Run `python3 -m devcovenant test` before closing the work cycle.
- Finish with `python3 -m devcovenant gate --end`.

## Operating Rules
- `policy_state` in `devcovenant/config.yaml` is the only policy activation
  authority.
- Policy lifecycle `status` metadata is retired from runtime contracts.
- Policy replacements migrate `policy_state` keys during `upgrade`.
- Profiles provide overlays/assets/hooks/selectors; profiles do not activate
  policies.
- Translators are declared by language profiles and routed through the shared
  translator runtime.
- CLI-exposed command modules stay at `devcovenant/` package root.
- Tests are current-behavior artifacts and must be updated or deleted when
  their target modules change or are removed.

## Contract Surfaces
- Tier A (user contract): CLI command behavior/flags, config schema,
  managed-doc block schema, AGENTS policy-block schema.
- Tier B (extension contract): policy/fixer interfaces, profile manifest
  schema, translator declaration schema, `LanguageUnit` schema.
- Tier C (data contract): registry/state file schemas under
  `devcovenant/registry/local` and `devcovenant/registry/global`.
- Tier D (internal runtime): orchestration/runtime internals under
  `devcovenant/core/*_runtime.py`.

## Target Core Layout
- Runtime orchestration modules:
  - `policy_runtime.py`
  - `metadata_runtime.py`
  - `profile_runtime.py`
  - `translator_runtime.py`
  - `refresh_runtime.py`
  - `registry_runtime.py`
  - `selector_runtime.py`
  - `gate_runtime.py`
  - `execution_runtime.py`
- Contract module:
  - `policy_contracts.py`

## Implementation Backlog
1. [done] Establish API freeze charter and contract-surface matrix in SPEC.
- Deliverables:
  - Explicit Tier A/B/C/D definitions.
  - Explicit forward-only rule in spec language.

2. [done] Consolidate runtime orchestration under explicit `*_runtime.py`
   ownership.
- Deliverables:
  - Migrate orchestration responsibilities into the target runtime set.
  - Remove overlapping legacy runtime modules.

3. [done] Remove policy-freeze workflow and artifacts.
- Deliverables:
  - Remove policy-freeze runtime/doc/test references.
  - Keep custom-policy copy workflow as the replacement pattern.

4. [done] Freeze command model around `check`, `gate`, `test`, and lifecycle
   commands.
- Deliverables:
  - `gate --start|--end` handles gate recording and pre-commit execution.
  - `check` keeps `--nofix` and `--norefresh` behavior only.

5. [done] Move translator ownership to language profiles and remove
   per-policy adapter ownership.
- Deliverables:
  - Language profiles declare translator routing metadata.
  - Policy execution requests translation through runtime.

6. [done] Narrow package-level Python API exports to explicit contracts.
- Deliverables:
  - Define and document explicit exports in `devcovenant/__init__.py`.
  - Keep runtime internals non-public by default.
  - Align tests/docs with the narrowed import surface.

7. [done] Complete Tier A contract tests.
- Deliverables:
  - CLI command/flag behavior tests for frozen commands.
  - Config schema and managed-doc block contract tests.
  - AGENTS policy-block schema tests.

8. [done] Complete Tier B contract tests.
- Deliverables:
  - Policy/fixer callable contract tests via `policy_contracts.py` types.
  - Profile manifest schema contract tests.
  - Translator declaration and `LanguageUnit` contract tests.

9. [done] Complete Tier C contract tests.
- Deliverables:
  - Registry file schema and generation invariant tests.
  - Policy/profile registry synchronization tests.
  - Test-status/gate state schema tests.

10. [done] Close remaining responsibility drift in core modules.
- Deliverables:
  - Eliminate duplicate code paths for profile, registry, selector,
    metadata, and refresh responsibilities.
  - Fold AGENTS policy-block parse logic into runtime ownership and remove
    standalone `parser.py`.
  - Keep `policy_contracts.py` contract-only by usage.

11. [done] Remove policy `status` lifecycle semantics and use replacement
    metadata as policy-state migrations.
- Deliverables:
  - Drop runtime `status` handling from policy parsing/execution and registry
    schema.
  - Remove `status` from generated AGENTS policy-def metadata.
  - Migrate replacement flow to `config.policy_state` key rewrites in
    `upgrade`.
  - Skip replacement-key migration when a custom policy override exists for
    the replaced policy id.

12. [not done] Run full SPEC-vs-reality audit and resolve remaining 0.2.6
    drift.
- Deliverables:
  - Enumerate unresolved drift against current `SPEC.md`.
  - Fix or explicitly defer each item with rationale.
  - Mark backlog complete only when no unresolved 0.2.6 drift remains.

13. [not done] Finalize 0.2.6 release readiness.
- Deliverables:
  - Clean docs/registry/config refresh behavior.
  - Passing gated workflow (`gate --start`, `test`, `gate --end`).
  - Updated changelog entries for completed backlog work.

## Acceptance Criteria
- Contract boundaries are explicit and enforced by tests for Tier A/B/C.
- Runtime internals are not treated as public API.
- Translator routing is metadata-driven via language profile declarations.
- Command behavior matches the frozen CLI contract.
- SPEC and runtime behavior are aligned with no unresolved 0.2.6 drift.

## Validation Cycle
- Run `python3 -m devcovenant gate --start` before edits.
- Run targeted unittests for touched contract surfaces.
- Run `python3 -m devcovenant refresh` after contract/schema edits.
- Run `python3 -m devcovenant test`.
- Run `python3 -m devcovenant gate --end`.
