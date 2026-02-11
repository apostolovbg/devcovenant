# DevCovenant Development Plan
**Last Updated:** 2026-02-11
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This file tracks active implementation work. `SPEC.md` is the source of
truth for behavior and requirements.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Audit Baseline](#audit-baseline)
4. [Remaining 0.2.6 Work](#remaining-026-work)
5. [Deferred Work](#deferred-work)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Validation Routine](#validation-routine)

## Overview
- This plan is a rewrite aligned to the current `SPEC.md` state.
- Keep this plan dependency-ordered and status-explicit.
- Keep release history in `CHANGELOG.md`, not here.

## Workflow
- Start edit sessions with `devcovenant check --start`.
- Implement tasks in order from this plan.
- Run `devcovenant refresh` after descriptor/profile/config changes.
- Run `devcovenant test`.
- End with `devcovenant check --end`.
- If end hooks/autofixers modify files, rerun test and end until clean.

## Audit Baseline
- [done] Public command surface is narrowed to:
  `check`, `test`, `install`, `deploy`, `upgrade`, `refresh`,
  `undeploy`, `uninstall`, and `update_lock`.
- [done] Public CLI flags are minimal and command-scoped.
- [done] Managed docs are YAML-template driven with managed-block refresh.
- [done] Registry-to-AGENTS render flow is in place.
- [done] Policy activation is config-driven (`policy_state`).
- [done] Scope-key retirement work landed in descriptors/manifests.
- [done] Legacy stock policy text restore path was removed.
- [done] Tests run via both `pytest` and `python3 -m unittest discover`.

## Remaining 0.2.6 Work
1. [not done] Refresh internals de-legacy pass
- Remove remaining legacy naming and references to
  `refresh_registry`/`refresh_policies`/`refresh_all` from runtime messages,
  docs, and tests where they leak old command semantics.
- Keep one canonical operator command: `devcovenant refresh`.
- Ensure suggestions in engine/policies point to `devcovenant refresh`.

2. [not done] Root-command vs core-helper boundary cleanup
- Keep user-action command modules at `devcovenant/` root as real
  implementations.
- Move/retain helper logic in `devcovenant/core/` only.
- Remove stale internal `--target` plumbing from lifecycle helpers where
  current-repo execution is sufficient and required by SPEC.

3. [not done] Lifecycle simplification hardening
- Remove residual dead branches tied to retired command variants and retired
  mode switches.
- Confirm `check --start` and `check --end` remain the only gate entrypoints.
- Preserve file-path command usage for root commands.

4. [not done] Managed-doc and template drift cleanup
- Keep managed-doc templates YAML-only and generic.
- Remove stale references to removed templates/artifacts in tests/docs.
- Keep refresh behavior block-scoped for existing docs and stock text scoped
  to missing/empty/placeholder targets.

5. [not done] Test-suite completion for 0.2.6
- [done] Finalize `modules-need-tests` as a repo-wide metadata-driven
  full-audit rule for all in-scope non-test modules with tests required under
  configured `tests/` roots.
- [done] Enforce `devcovrepo` metadata so `devcovenant/**` is mirrored under
  `tests/devcovenant/**`.
- [done] Enforce `devcovuser` metadata so only `devcovenant/custom/**` is
  mirrored
  under `tests/devcovenant/custom/**`.
- [done] Keep non-DevCovenant module tests user-structured under `tests/`
  (no forced mirror layout).
- [not done] Continue migration of remaining pytest-style-only modules into
  explicit
  unit-style suites while preserving pytest execution.
- [not done] Add missing adapter unit tests for core policy adapters.
- [done] Add regression coverage for the metadata-driven mirror behavior.

6. [not done] Packaging and artifact residue cleanup
- Remove obsolete residual artifacts still present in tree
  (for example, retired GPL template leftovers) when not used by runtime.
- Verify manifests and packaging rules contain only active artifacts.
- Keep runtime registry state under `devcovenant/registry/local`.

7. [not done] Pre-commit config refactor finalization
- Finish the profile-fragment merge audit described in
  `SPEC.md` (Pre-commit configuration by profile).
- Verify manifest/profile-registry/pre-commit outputs stay aligned.
- Add regression cases for representative profile combinations.

## Deferred Work
1. [not done] 0.2.7 metadata DSL expansion
- Continue moving reusable policy metadata knobs from hard-coded logic into
  descriptor/profile/config-driven structures.
- Keep custom policy escape hatches intact for repo-specific behavior.

## Acceptance Criteria
- `PLAN.md` remains aligned to the current `SPEC.md`.
- Remaining 0.2.6 work items are implemented with tests.
- Runtime/help/docs contain no operator-facing legacy refresh command names.
- Lifecycle internals are current-repo oriented without public target flags.
- Adapter coverage exists and runs in both pytest and unittest flows.
- Gate sequence (`start -> tests -> end`) passes cleanly.

## Validation Routine
- Run: `devcovenant check --start`.
- Run: `devcovenant test`.
- Run: `devcovenant check --end`.
- Validate `devcovenant refresh` as the only operator refresh command.
- Validate `python3 devcovenant/check.py --start` and
  `python3 devcovenant/check.py --end`.
- Validate docs policies and changelog coverage on the final tree.
