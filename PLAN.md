# DevCovenant Development Plan
**Last Updated:** 2026-02-12
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan tracks the current 0.2.6 dedrift backlog directly from `SPEC.md`.
`SPEC.md` remains behavior source of truth. This file keeps implementation
order, status, and validation scope explicit.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Decisions Locked](#decisions-locked)
4. [Active 0.2.6 Backlog](#active-026-backlog)
5. [Deferred 0.2.7 Work](#deferred-027-work)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Validation Routine](#validation-routine)

## Overview
- Scope: close remaining 0.2.6 drift where runtime behavior differs from
  `SPEC.md`.
- Inputs: current `SPEC.md` plus the latest mismatch audit.
- Rule: execute in order, mark status explicitly, and keep the plan current.

## Workflow
- Start each edit session with `devcovenant check --start`.
- Implement items in this plan order unless superseded by spec decisions.
- Run `devcovenant refresh` after descriptor/profile/config edits.
- Run `devcovenant test`.
- End each edit session with `devcovenant check --end`.

## Decisions Locked
- [done] `install` is lightweight only: copy `devcovenant/` and seed generic
  config.
- [done] Existing installs are upgrade-directed, non-interactive.
- [done] `check --start` and `check --end` run full refresh before gates.
- [done] Public command surface stays:
  `check`, `test`, `install`, `deploy`, `upgrade`, `refresh`, `undeploy`,
  `uninstall`, `update_lock`.

## Active 0.2.6 Backlog
1. [done] SPEC dedrift for install and lifecycle semantics
- Requirement source: lifecycle model in `SPEC.md`.
- Deliverables:
  - Keep install lightweight-only semantics.
  - Document deploy-only destructive cleanup scope.
  - Align runtime artifact generation wording with full-refresh paths.

2. [done] Canonical generic install config seeding
- Requirement source: install model and generic config requirements.
- Gap: source-tree install can inherit non-generic active profiles.
- Deliverables:
  - Force canonical generic defaults on install.
  - Keep `install.generic_config: true` and `devcov_core_include: false`.
  - Add regression tests for deterministic generic config output.

3. [done] Deploy-only cleanup for user-mode repos
- Requirement source: deploy behavior for `devcov_core_include: false`.
- Resolved: deploy now applies cleanup only for user-mode activation.
- Deliverables:
  - On deploy only, delete `devcovenant/custom/policies/**`.
  - On deploy only, delete `tests/devcovenant/core/**`.
  - On deploy only, delete `devcovenant/custom/profiles/devcovrepo/**`.
  - Keep `upgrade` and `refresh` non-destructive for custom content.

4. [done] Lifecycle registry generation boundaries
- Requirement source: install/deploy/upgrade/refresh/check contracts.
- Resolved: lifecycle boundary behavior is enforced and regression-tested.
- Deliverables:
  - Keep install limited to core + generic config + manifest scaffold.
  - Ensure deploy/upgrade end with full `refresh`.
  - Keep check start/end full refresh behavior and CI-safe execution.

5. [done] `update_lock` repo-root execution
- Requirement source: command matrix and lock refresh behavior.
- Resolved: `update_lock` resolves repository root and always reconciles
  Python lock output instead of short-circuiting on cached input hashes.
- Deliverables:
  - Resolve repo root via shared command runtime.
  - Execute lock and license refresh against resolved repo root.
  - Remove `requirements.in` hash-cache skip path from Python lock refresh.
  - Add tests for invocation from subdirectories.
  - Add tests that prove Python lock refresh still attempts reconciliation
    when `requirements.in` content is unchanged.

6. [done] Full generated-config refresh alignment
- Requirement source: refresh config autogen section requirements.
- Resolved: refresh now regenerates all required config autogen sections
  (profiles.generated, devcov_core_paths, autogen metadata overlays, and
  managed doc autogen list) while preserving user override fields.
- Deliverables:
  - Refresh all required generated config sections.
  - Preserve user-controlled override fields.
  - Add unit tests for merge/update behavior.

7. [done] Close-loop SPEC-vs-reality audit
- Requirement source: plan governance quality.
- Resolved: re-audited command surface, lifecycle semantics, activation model,
  and runtime parser behavior against `SPEC.md`.
- Deliverables:
  - Re-run full mismatch audit after items 2-6.
  - Resolve remaining drift or defer explicitly with rationale.
  - Keep this plan as single active dedrift backlog.

13. [done] Path-valued metadata normalization in runtime policy options
- Requirement source: policy execution reliability in `SPEC.md`.
- Resolved: generated autogen overrides now emit scalar path keys as strings,
  and runtime override loading flattens legacy singleton list values for
  singular path keys before policy checks consume them.
- Deliverables:
  - Normalize path-valued policy options to scalar file paths before checkers
    consume them.
  - Add regressions for `semantic-version-scope` and `version-sync` ensuring
    no runtime warning path-type errors.
  - Keep metadata-driven list selectors intact while preserving scalar path
    options for file-based settings.

14. [done] Mode-less profile assets and dedicated config refresh pipeline
- Requirement source: refresh architecture dedrift in `SPEC.md`.
- Resolved: profile assets no longer use `mode`; asset materialization is
  create-if-missing only, while generated artifacts and config autogen are
  handled by dedicated refresh logic.
- Deliverables:
  - Removed `mode` handling branches and legacy generator-mode asset logic
    from runtime profile asset materialization.
  - Updated profile manifests/docs to drop `mode` fields and describe
    deterministic create-if-missing asset behavior.
  - Converted config refresh to a dedicated pipeline that preserves user-owned
    values, regenerates autogen sections every refresh, and writes the
    commented template structure.

8. [done] AGENTS multi-block ownership dedrift
- Requirement source: documentation management block semantics in `SPEC.md`.
- Resolved: AGENTS now treats top managed block, workflow block, and policy
  block as separate managed units with generated markers.
- Deliverables:
  - Added `DEVCOV-WORKFLOW` managed block support in refresh rendering.
  - Removed marker literals from AGENTS descriptor `body`.
  - Preserved editable notes while normalizing legacy second `DEVCOV` block.
  - Updated changelog coverage managed-block detection and undeploy cleanup
    for workflow markers.

9. [done] AGENTS-first runtime parser dedrift
- Requirement source: policy execution semantics in `SPEC.md`.
- Resolved: engine runtime now parses policy definitions from AGENTS policy
  blocks and treats registry data as hash/diagnostic state only.
- Deliverables:
  - Switch runtime policy loading to parse `AGENTS.md` policy blocks.
  - Use AGENTS resolved `enabled` values as runtime activation state.
  - Keep registry as synchronized hash/diagnostic state, not runtime authority.
  - Add regressions that fail if runtime path bypasses AGENTS parser.

10. [done] CONTRIBUTING descriptor managed-block dedrift
- Requirement source: managed-doc marker generation contract in `SPEC.md`.
- Resolved: `CONTRIBUTING.yaml` no longer duplicates managed block marker/
  content text in descriptor `body`.
- Deliverables:
  - Remove managed block marker/content literals from descriptor `body`.
  - Keep managed block content only in descriptor `managed_block`.
  - Verify refresh renders a single generated managed block in
    `CONTRIBUTING.md`.

11. [done] Descriptor-driven managed-block metadata dedrift
- Requirement source: documentation management block semantics in `SPEC.md`.
- Resolved: managed block `Doc ID` / `Doc Type` / `Managed By` lines are now
  generated from descriptor metadata fields instead of copied from descriptor
  `managed_block` text.
- Deliverables:
  - Added renderer support to compose managed block metadata from
    `doc_id`/`doc_type`/`managed_by`.
  - Normalized global doc descriptors to remove duplicated metadata lines from
    `managed_block` text and align `doc_type` values.
  - Updated managed-doc-assets policy enforcement to reject metadata-line
    duplication inside descriptor `managed_block`.
  - Added unit tests for generated-metadata pass behavior and duplication
    rejection.

12. [done] Profile policy-activation list removal
- Requirement source: policy activation architecture in `SPEC.md`.
- Resolved: profile manifests no longer carry `policies:` activation lists;
  activation is config-only via `policy_state`.
- Deliverables:
  - Removed `policies:` keys from all core/custom profile manifests.
  - Updated profile docs/examples to describe overlays-only profile metadata.
  - Extended profile manifest tests to reject `policies` activation keys.

## Deferred 0.2.7 Work
1. [not done] Metadata DSL expansion
- Continue moving reusable runtime knobs from hardcoded logic into metadata.
- Keep custom policy/profile escape hatches explicit.

## Acceptance Criteria
- Active 0.2.6 backlog items are completed with unit coverage.
- Runtime behavior matches `SPEC.md` for lifecycle and command execution.
- Generated docs/registries pass policy enforcement without blocking errors.
- Gate sequence (`start -> test -> end`) passes cleanly.

## Validation Routine
- Run `devcovenant check --start`.
- Run `devcovenant test`.
- Run `devcovenant check --end`.
- Validate command help remains command-scoped.
- Validate `devcovenant refresh` as canonical full-refresh command.
