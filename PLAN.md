# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Last Updated:** 2026-03-19
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->

<!-- DEVCOV:END -->

Use this plan to track active implementation work. Keep items
dependency-ordered, factual, and current.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Active Work](#active-work)
4. [Validation Routine](#validation-routine)

## Overview
- Record durable requirements in `SPEC.md` when your repo uses SPEC.
- Record change history in `CHANGELOG.md`.
- Mark completed items as `[done]` and outstanding items as `[not done]`.
- Document behavior is strict:
  - missing docs may be created from assets/templates
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change
  - an empty managed block is still a managed block and must keep its
    `<!-- DEVCOV:BEGIN -->` / `<!-- DEVCOV:END -->` markers
- These same document rules must hold across `refresh`, `install`, `deploy`,
  `upgrade`, and gate-triggered refresh/autofix paths.

## Workflow
- Work in dependency order unless an explicit blocker requires reordering.
- Keep each item concrete and testable.
- Update status in the same session when work lands.

## Active Work
1. [done] Managed Document Preservation Hardening.
   Restore exact document-preservation behavior across refresh/install/deploy/
   upgrade/gate paths so existing non-empty, non-one-line docs keep their
   authored body content while DevCovenant updates only managed headers and
   explicit managed blocks.
2. [not done] Docs And Contract Harmonization.
   Remove repo-specific product wording such as the `version-governance`
   `release slices` note, make the README model explicit
   (`README.md` is the authored source and `devcovenant/README.md` is the
   synced repo-only-pruned projection), and align managed-doc-assets wording
   with the real doc/asset synchronization contract.
3. [not done] Strictness, Naming, And Final Closure.
   Clean the remaining misleading fallback/legacy naming where runtime is
   already strict, then re-run the anti-bullshit audit and close the plan
   only when docs, assets, policies, and runtime tell the same story.

## Validation Routine
- Verify checks and tests pass.
- Verify generated artifacts are synchronized after refresh.
- Verify documentation and changelog were updated where behavior changed.
- Verify `devcovenant check` passes after the slice closes.
