# DevCovenant Development Plan
**Last Updated:** 2026-02-09
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
3. [Completed Baseline](#completed-baseline)
4. [Immediate Outstanding Work](#immediate-outstanding-work)
5. [Secondary Outstanding Work](#secondary-outstanding-work)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Validation Routine](#validation-routine)

## Overview
- Keep this plan short, current, and dependency ordered.
- Keep history in `CHANGELOG.md`; keep requirements in `SPEC.md`.
- Mark only active work as `[not done]`.

## Workflow
- Start edits with:
  `python3 devcovenant/run_pre_commit.py --phase start`
- Implement in dependency order.
- After policy descriptor updates, run:
  `devcovenant refresh_registry`
- Run tests:
  `python3 devcovenant/run_tests.py`
- End edits with:
  `python3 devcovenant/run_pre_commit.py --phase end`
- If hooks/autofixes change files during end, rerun tests and end phase.

## Completed Baseline
- [done] Lifecycle command surface exists: `install`, `deploy`, `update`,
  `upgrade`, `refresh`, `undeploy`, `uninstall`.
- [done] Managed docs are YAML-asset driven and managed-block based.
- [done] Registry-only startup refresh behavior exists.
- [done] Policy metadata resolution writes resolved policy values into
  registry entries.
- [done] AGENTS policy block rendering is downstream from registry entries.
- [done] Changelog coverage now requires fresh top entry with labeled summary
  and explicit files list.
- [done] Changelog coverage ignores managed-doc diffs confined to DEVCOV
  managed blocks and policy markers.
- [done] `run_tests` executes configured command lists and records test status.

## Immediate Outstanding Work
1. [not done] Config-only policy activation migration (critical)
- Remove remaining runtime scope activation paths (policy/profile scopes).
- Keep activation authoritative in config (`policy_state`).
- Preserve current enabled/disabled outcomes during migration.

2. [not done] Scope-key retirement in descriptors
- Remove policy/profile scope keys from policy and profile YAMLs where they are
  still used for activation logic.
- Keep profile overlays for metadata/assets.
- Do not use overlays for activation.

3. [not done] Policy enable/disable simplification
- Unify core and custom policy activation semantics (single `enabled` model).
- Remove transitional toggles and guardrails that duplicate activation logic.

4. [not done] Legacy policy consolidation cleanup
- Remove retired policy directories and references after consolidation.
- Update maps/docs/tests/registries so removed policy IDs cannot reappear.

5. [done] AGENTS/registry hardening
- Keep registry generation descriptor-driven with resolved metadata values.
- Keep AGENTS policy block rendering deterministic from registry state.

6. [done] Stock-text legacy removal
- Remove `stock_policy_texts` files and restore-stock-text plumbing.
- Enforce descriptor `text` as the only policy prose source.

7. [done] Registry command consolidation
- Make `refresh_registry` the canonical registry regeneration command.
- Remove or deprecate legacy update-policy-registry command paths.

8. [not done] CLI module layout cleanup
- Keep CLI-exposed command modules at `devcovenant/` package root.
- Remove forwarding-wrapper patterns and duplicate same-name root/core modules.
- Preserve file-path gate command usage.

## Secondary Outstanding Work
1. [not done] Managed docs pipeline completion
- Finalize strict sync for README/SPEC/PLAN/CHANGELOG/CONTRIBUTING from YAML
  assets and managed blocks.

2. [not done] Lifecycle refinements and fallbacks
- Complete `reset-to-stock` behavior.
- Finalize version and LICENSE fallback behavior across lifecycle commands.

3. [not done] Adapter expansion and test coverage
- Continue policy-by-policy adapter extraction and dispatch tests.

4. [not done] Legacy artifact/debris removal
- Remove obsolete registry/template leftovers and stale references from docs,
  manifests, and tests.

## Acceptance Criteria
- Every immediate outstanding item has code + tests.
- `PLAN.md` and `SPEC.md` do not conflict on activation, lifecycle, or
  registry behavior.
- No removed/retired policy can be discovered in manifests, maps, registries,
  docs, or tests.
- Descriptor `text` is the only policy prose source and no stock-text legacy
  files remain in runtime paths.
- `refresh_registry` is the canonical registry regeneration command.
- File-path gate commands continue to work from repository root.
- CLI command modules do not rely on forwarding wrappers or duplicate
  same-name root/core command files.
- Gate sequence (`start -> tests -> end`) passes cleanly.

## Validation Routine
- Run gate workflow on every change.
- Verify DevCovenant policy checks pass without blocking violations.
- Verify `devcovenant refresh_registry` updates local registries as expected.
- Verify file-path gate commands still execute from repo root.
- Verify docs policies pass on final state (`last-updated-placement`,
  `documentation-growth-tracking`, `changelog-coverage`).
