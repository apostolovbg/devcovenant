# DevCovenant Development Plan
**Last Updated:** 2026-02-11
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan is rebuilt from `SPEC.md` plus the latest SPEC-vs-reality audit.
`SPEC.md` remains behavior source of truth; this file tracks execution order,
status, and acceptance for dedrift work.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Alignment Snapshot](#alignment-snapshot)
4. [Active 0.2.6 Dedrift Backlog](#active-026-dedrift-backlog)
5. [Deferred 0.2.7 Work](#deferred-027-work)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Validation Routine](#validation-routine)

## Overview
- Scope: close remaining 0.2.6 gaps where runtime behavior differs from
  `SPEC.md`.
- Inputs: `SPEC.md` requirements + merged drift findings that were in
  `DRIFT.md`.
- Rule: implement in dependency order and keep statuses explicit.

## Workflow
- Start edit sessions with `devcovenant check --start`.
- Implement tasks in this plan order.
- Run `devcovenant refresh` after descriptor/profile/config edits.
- Run `devcovenant test`.
- End with `devcovenant check --end`.
- If hooks/autofixers change files, rerun `test` and `check --end` until
  clean.

## Alignment Snapshot
- [done] Public command surface is constrained to:
  `check`, `test`, `install`, `deploy`, `upgrade`, `refresh`, `undeploy`,
  `uninstall`, and `update_lock`.
- [done] Root command modules are real implementations; no root shims.
- [done] Managed docs are YAML-template driven with managed-block refresh.
- [done] AGENTS policy block is registry-rendered downstream.
- [done] Policy activation is config-driven (`policy_state`).
- [done] Legacy stock policy text restore path is removed.
- [done] Tests run as `python3 -m unittest discover -v` then `pytest`.
- [done] `update_lock` is metadata-driven and policy-integrated for license
  artifact refresh.

## Active 0.2.6 Dedrift Backlog
1. [not done] `check --start/--end` full-refresh parity
- Requirement source: `SPEC.md` full-refresh-at-check-start contract.
- Gap: gate entry paths bypass full refresh before pre-commit gate run.
- Deliverables:
  - Run full `refresh_repo(...)` before both `--start` and `--end` phases.
  - Keep gate metadata recording behavior unchanged.
  - Add/adjust unit tests for start/end refresh invocation order.

2. [not done] `install` upgrade prompt when source is newer
- Requirement source: install/upgrade model in `SPEC.md`.
- Gap: install does not prompt to run upgrade first when packaged source is
  newer than repo core.
- Deliverables:
  - Add version comparison and prompt/flow for `upgrade` handoff.
  - Cover prompt path and non-prompt path with unit tests.

3. [not done] `install` existing-artifact confirmation
- Requirement source: install safety behavior in `SPEC.md`.
- Gap: install proceeds directly without explicit uninstall confirmation.
- Deliverables:
  - Detect existing DevCovenant artifacts.
  - Refuse to proceed unless user confirms uninstall prompt flow.
  - Add unit tests for deny/accept branches.

4. [not done] install mode semantics (`auto`, `empty`)
- Requirement source: installation requirements in `SPEC.md`.
- Gap: command exposes only a single behavior.
- Deliverables:
  - Implement mode handling and defaults as specified.
  - Keep CLI command-scoped help clean.
  - Add unit coverage for each mode path.

5. [not done] profile-driven pre-commit fragment merge
- Requirement source: pre-commit configuration by profile in `SPEC.md`.
- Gap: no merge engine currently applies per-profile pre-commit fragments.
- Deliverables:
  - Implement merge order: global baseline -> active profile fragments ->
    config overrides.
  - Regenerate `.pre-commit-config.yaml` on deploy/upgrade/refresh.
  - Record resolved hook set in manifest metadata.
  - Add regression tests for representative profile combinations.

6. [not done] `.gitignore` generation and merge lifecycle
- Requirement source: installation and undeploy requirements in `SPEC.md`.
- Gap: refresh/deploy do not regenerate `.gitignore`; undeploy does not
  revert generated fragments.
- Deliverables:
  - Implement generated fragment synthesis from global/profile/OS assets.
  - Preserve user-managed entries under preserved block semantics.
  - Implement undeploy cleanup for generated fragments.
  - Add unit tests for generate/merge/revert flows.

7. [not done] packaging manifest dedrift
- Requirement source: packaging rules in `SPEC.md`.
- Gap: `MANIFEST.in` still includes repo-root managed docs that spec forbids.
- Deliverables:
  - Remove forbidden root managed docs from `MANIFEST.in` includes.
  - Keep required package metadata files and `devcovenant/` docs/assets.
  - Add/adjust packaging manifest unit checks.

8. [not done] close-loop dedrift verification
- Requirement source: plan governance quality.
- Gap: remaining drift must be re-audited after implementation.
- Deliverables:
  - Re-run SPEC-vs-reality audit after items 1-7.
  - Resolve any residual mismatches or log them as explicit deferred items.
  - Keep this plan as the single dedrift backlog document.

## Deferred 0.2.7 Work
1. [not done] Metadata DSL expansion
- Continue moving reusable policy/runtime knobs from hardcoded logic into
  descriptor/profile/config-driven structures.
- Keep custom policy and custom profile escape hatches explicit.

## Acceptance Criteria
- Active 0.2.6 backlog items are implemented with unit coverage.
- `PLAN.md` remains aligned with current `SPEC.md`.
- Runtime behavior matches spec for install/deploy/upgrade/refresh/check/test.
- Generated docs and registries pass policy enforcement with no blocking
  violations.
- Gate sequence (`start -> test -> end`) passes cleanly.

## Validation Routine
- Run `devcovenant check --start`.
- Run `devcovenant test`.
- Run `devcovenant check --end`.
- Validate command help remains command-scoped.
- Validate `devcovenant refresh` as canonical operator refresh command.
- Validate changelog coverage and managed-doc policies on final tree.
