# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Development Stance:** active-development
**Versioning Mode:** versioned
**Last Updated:** 2026-03-21
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->

Use this plan to reduce documentation fragmentation, restore command and test
speed, and then freeze the simplified resulting contracts deliberately.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Writing Direction](#writing-direction)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)

## Overview
- The previous roadmap correctly identified several contracts that need to be
  frozen, but the current audit showed two more urgent problems:
  - the documentation set has become too fragmented and repetitive
  - DevCovenant command and test runtime has become materially slower
- This roadmap therefore starts by reducing structural complexity before it
  freezes more behavior in place.
- Keep the current managed-document preservation contract unless an explicit
  plan item changes it:
  - missing docs may be created from descriptors
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change
- Keep normative truth centralized. Explanatory docs may teach and guide, but
  they must not become alternate competing sources of truth.
- Treat repeated YAML loading, repeated full-flow test work, overlapping docs,
  and unclear authority boundaries as product debt, not as normal growth.

## Workflow
- Work in dependency order unless a real blocker forces reordering.
- Prefer removing structural causes of slowness or drift before polishing the
  surfaces built on top of them.
- Keep each item concrete enough that another person can continue it without
  reconstructing hidden context.
- When an item is complete, rewrite it to state what landed and what is now
  true because of it.

## Writing Direction
- Write for people who need both quick operational guidance and detailed
  explanation.
- Make the docs operator-oriented and explanatory at the same time.
- Prefer `how DevCovenant works in a repository`, `how to use DevCovenant in a
  repository`, and `how to integrate DevCovenant into a repository` over
  soft marketing phrasing.
- Remove insider shorthand when a concrete phrase is clearer.
- Explain what a thing is, why it exists, what it controls, and when to use
  it.
- Keep config comments practical, concrete, and directly useful at the point
  of reading.
- Expand abbreviations on first use in each document.
- Treat undocumented behavior, half-documented behavior, repeated material
  without a clear reason, and fancy wording that hides the meaning as product
  defects.

## Active Work
1. [not done] Eliminate Repeated Runtime Loading And Restore Check/Gate Speed.
   Goal:
   - remove the structural causes that make `check`, `refresh`, and gate runs
     repeatedly reload the same large YAML state.
   Why this matters:
   - current `check`/gate cost is dominated by repeated registry, profile,
     config, and descriptor loading rather than by one clean pass through the
     actual rule logic.
   Work to do:
   - establish one reliable timing baseline for `check`, `gate --mid`,
     `gate --end`, and `refresh`
   - identify and remove repeated loads of tracked registry, profile registry,
     config, and managed-doc descriptor state inside one command run
   - introduce shared loaded-state or caching boundaries where repeated reads
     are currently happening
   - keep command behavior identical while reducing duplicate parse/load work
   - document the resulting runtime ownership clearly enough that future work
     does not reintroduce the same problem
   Done when:
   - `check` and gate runs are measurably faster on the same repo state
   - repeated registry/profile/config/descriptor loading inside one command is
     materially reduced
   - tests cover the new runtime boundaries so performance fixes do not become
     hidden behavior changes
2. [not done] Reduce Test Runtime Without Weakening Coverage.
   Goal:
   - bring the full test workflow back to a reasonable runtime while keeping
     coverage strong.
   Why this matters:
   - each test runner is now slow on its own, which makes the standard
     workflow costly even before counting that both runners execute.
   Work to do:
   - profile which test families are slow because they repeatedly run full
     refresh, deploy, upgrade, install, or other command-style flows
   - split heavy integration behavior from cheaper contract-level behavior
     where the expensive full-flow run is not needed
   - reduce repeated setup and repeated full command execution in refresh,
     deploy, upgrade, and managed-doc tests
   - make sure the same behavior is not proven expensively in multiple places
     without a clear reason
   - keep one clear place for full end-to-end lifecycle proof while making the
     rest of the suite more targeted
   Done when:
   - the slowest test families are materially faster
   - the standard `devcovenant test` runtime is materially reduced
   - coverage remains explicit, understandable, and not weakened by hidden
     test removal
3. [not done] Rebuild The Documentation Information Architecture.
   Goal:
   - reduce fragmentation, repetition, and navigation burden across the docs
     while keeping the documentation more explanatory, not less.
   Why this matters:
   - the docs are currently mostly coherent, but too many documents explain
     adjacent parts of the same ideas, which makes the whole set harder to
     read and harder to maintain.
   Work to do:
   - inventory the documentation set by purpose: operator entrypoint,
     normative contract, detailed explanation, reference, repo-internal note
   - decide which documents are the primary homes for workflow, installation,
     config, profiles, policies, architecture, registry, and project
     governance material
   - reduce repeated explanation across `README.md`, `devcovenant/README.md`,
     and the main docs so each document has a clearer job
   - tighten cross-linking so docs point to the primary home of a topic
     instead of re-explaining the same thing everywhere
   - revise doc-route expectations if they are forcing too much duplicated
     writing into too many documents at once
   Done when:
   - each major topic has a clear primary home
   - repeated material is reduced materially without making docs terse again
   - readers can find workflow, config, policy, and architecture truth more
     quickly with less cross-document repetition
4. [not done] Freeze The Simplified Product Contracts.
   Goal:
   - formalize the major contracts only after the runtime and documentation
     surfaces have been simplified enough to freeze cleanly.
   Why this matters:
   - freezing a fragmented or slow system too early would just preserve drift
     and complexity in a more official form.
   Work to do:
   - freeze the managed-documents contract
   - freeze the managed-document descriptor schema
   - freeze the bootstrap/install/deploy/refresh/upgrade contract
   - freeze the public config contract
   - freeze the project-governance contract
   - freeze the registry contract
   - freeze the documentation writing contract
   - freeze the policy descriptor contract
   - freeze the version-governance adapter contract
   - freeze the gate and run-artifact contract
   - for each frozen contract, land:
     - one normative spec
     - code validation or enforcement where appropriate
     - direct tests
     - explanatory docs that point back to the normative spec
   Done when:
   - the major product contracts are explicit, centralized, and testable
   - explanatory docs point back to the normative contract instead of
     competing with it
   - the resulting contracts reflect the simplified runtime and documentation
     architecture rather than the older fragmented shape

## Validation Routine
- Verify timing baselines are recorded before and after performance work.
- Verify `check`, gate runs, and `devcovenant test` become measurably faster
  where the plan says they should.
- Verify each documentation change reduces duplication or clarifies ownership,
  rather than moving the same text around pointlessly.
- Verify each frozen contract produces one normative specification.
- Verify explanatory docs point back to the normative contract instead of
  competing with it.
- Verify direct tests cover contract scenarios rather than only happy-path
  flows.
- Verify `devcovenant test` passes after each slice.
- Verify `devcovenant check` passes after each slice.
