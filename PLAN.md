# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Development Stance:** active-development
**Versioning Mode:** versioned
**Last Updated:** 2026-03-20
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
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
1. [not done] Rename And Clarify Repository Integration Signals.
   Replace `devcov_core_include` with `developer_mode`, make it `true` for
   the DevCovenant repo and `false` for ordinary user repos by default, and
   replace vague `generic_config` wording with an explicit config-review
   state such as `config_review_pending`.
2. [not done] Build A Managed-Docs Service.
   Consolidate managed-document behavior into one core service that owns doc
   discovery, descriptor loading, enable/disable resolution,
   creation/adoption/preservation rules, managed header rendering, managed
   block rendering, and seeded-doc import behavior instead of spreading that
   logic across multiple flows and checks.
3. [not done] Make Document Governance Fully Descriptor-Driven.
   Remove hardcoded document special cases by letting document descriptors
   declare project-governance header presence, any dedicated governance
   section, managed-block content, default enablement, and builtin/custom doc
   inventory behavior.
4. [not done] Support Optional And Custom Managed Docs.
   Allow additional managed docs from custom templates, allow builtin managed
   docs to be turned off except for `AGENTS.md`, and prove the behavior by
   making `PROFILE_MAP.md` and `POLICY_MAP.md` custom managed docs supplied
   by the `devcovrepo` profile.
5. [not done] Document Initial Integration And Bootstrap Clearly.
   Fully document empty-repo install, seeded-doc install, existing-repo
   install, config review, deploy, first gate cycle, and the exact reasons
   those steps exist, including clearer inline guidance inside
   `devcovenant/config.yaml`.
6. [not done] Expand Documentation From Terse To Teaching-Quality.
   Rewrite operator-shorthand docs into explanatory docs that teach what a
   feature is, why it exists, how it behaves, when to use it, and how it
   relates to adjacent DevCovenant concepts.

## Validation Routine
- Verify checks and tests pass.
- Verify generated artifacts are synchronized after refresh.
- Verify documentation and changelog were updated where behavior changed.
- Verify `devcovenant check` passes after the slice closes.
