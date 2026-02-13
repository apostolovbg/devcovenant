# DevCovenant Development Plan
**Last Updated:** 2026-02-13
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan replaces the prior dedrift backlog and drives the API-freeze and
runtime-consolidation workstream defined in `SPEC.md`.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Locked Decisions](#locked-decisions)
4. [API-Freeze Backlog](#api-freeze-backlog)
5. [Acceptance Criteria](#acceptance-criteria)
6. [Validation Routine](#validation-routine)

## Overview
- Scope: freeze DevCovenant contracts while keeping additive extensibility.
- Priority: remove runtime/API fragmentation and align language handling on
  profile-owned translators + shared `LanguageUnit`.
- Constraint: `policy_state` in `config.yaml` remains the sole activation
  authority.
- Rule: implement target-state behavior directly (forward-only): no legacy
  fallbacks and no anti-legacy policing logic unless explicitly requested.

## Workflow
- Run `devcovenant gate --start` before edits.
- Implement items in backlog order unless superseded by a newer SPEC decision.
- Run `devcovenant refresh` after spec/profile/runtime contract edits.
- Run `devcovenant test`.
- Run `devcovenant gate --end`.

## Locked Decisions
- [done] Policy activation is config-only (`policy_state`).
- [done] Core/custom profile origin is inferred by path.
- [done] Translators are owned by language profiles.
- [done] Framework/ops/tooling/repo profiles do not select translators.
- [done] Runtime parses AGENTS policy block; registry remains diagnostic/hash
  state and AGENTS compile source.
- [done] Forward-only implementation applies: remove old paths from code/docs;
  do not add dedicated legacy fallback paths or anti-legacy rejection checks.

## API-Freeze Backlog
1. [done] Amend SPEC for API freeze charter and additive extension policy.
- Deliverables:
  - Explicit contract freeze language.
  - Explicit additive-only minor-version rule.
  - Explicit migration requirement for breaking changes.

2. [done] Implement full `policy_state` materialization on refresh.
- Deliverables:
  - Rebuild `policy_state` as full alphabetical map of effective policy IDs.
  - Preserve existing boolean states.
  - Seed new entries from resolved `enabled` defaults.
  - Drop stale policy IDs no longer discovered.

3. [done] Implement profile contract boundaries in runtime behavior.
- Deliverables:
  - Use profile manifests for overlays/assets/hooks and file selectors only.
  - Keep activation resolved solely from `policy_state`.
  - Keep core/custom distinction path-inferred without extra type keys.

4. [done] Add language-profile translator declaration schema.
- Deliverables:
  - Define translator declaration fields in profile YAML schema.
  - Validate declaration shape during refresh/runtime loading.
  - Ensure only language profiles can declare translators.

5. [done] Build centralized translator runtime in core.
- Deliverables:
  - Build extension-based candidate routing from active language profiles.
  - Run `can_handle` candidate arbitration.
  - Emit deterministic violations for no-match and multi-match cases.

6. [done] Introduce shared `LanguageUnit` model.
- Deliverables:
  - Define normalized, policy-agnostic output structure.
  - Route all language-aware policy parsing through this structure.

7. [done] Migrate language-aware policies off per-policy adapter maps.
- Deliverables:
  - Migrate `name_clarity`, `security_scanner`,
    `docstring_and_comment_coverage`, and `modules_need_tests` to translator
    runtime + `LanguageUnit`.
  - Remove per-policy extension->adapter routing logic.

8. [done] Pre-commit profile ownership cleanup.
- Deliverables:
  - Keep global hook baseline in `global` profile.
  - Move language-specific hooks to corresponding language profiles.
  - Keep generated pre-commit as authoritative artifact.

9. [not done] Consolidate scattered core responsibilities.
- Deliverables:
  - Consolidate runtime responsibilities into stable core runtime domains:
    policy, metadata, profile, translator, refresh, registry.
  - Remove legacy/duplicate internals absorbed by the new domains.
  - Keep CLI-exposed scripts at package root.

10. [done] Add conformance/contract test suite.
- Deliverables:
  - Assert full alphabetical `policy_state` refresh behavior with state
    preservation.
  - Assert translator ownership by language profiles only.
  - Assert language-aware policy execution goes through shared translator
    runtime behavior.

11. [done] Align test lifecycle contract in `modules-need-tests`.
- Deliverables:
  - Define test ownership as current-behavior validation of corresponding
    scripts/modules.
  - Require test updates alongside script changes.
  - Require test removal when corresponding scripts/modules are removed.

12. [not done] SPEC-vs-reality closure audit after implementation.
- Deliverables:
  - Re-audit runtime behavior vs amended SPEC.
  - Resolve residual drift or explicitly defer with rationale.

13. [done] Split gate lifecycle from check command.
- Deliverables:
  - Move start/end pre-commit workflow to `gate --start|--end`.
  - Keep `check` focused on policy execution with `--nofix` and
    `--norefresh`.
  - Update docs/templates/workflow guidance to use `gate` for start/end.

## Acceptance Criteria
- API contracts are explicit in SPEC and enforced in code.
- Refresh produces deterministic, full, alphabetical `policy_state`.
- Language-aware policies run through centralized translator runtime and shared
  `LanguageUnit`.
- No per-policy adapter routing remains in migrated policies.
- Core runtime responsibilities are consolidated and duplicate internals
  removed.
- Contract tests pass and block regressions.

## Validation Routine
- Run `devcovenant gate --start`.
- Run `devcovenant refresh` after each milestone item.
- Run `devcovenant test`.
- Run `devcovenant gate --end`.
