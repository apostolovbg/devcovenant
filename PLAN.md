# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1.dev1
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-03
**DevCovenant Version:** 1.0.1.dev1

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the release-QA work needed to ship the next beta.
Keep items concrete, current, and focused on release readiness rather than
open-ended cleanup.

## Table of Contents
1. [Overview](#overview)
2. [Release Scope](#release-scope)
3. [Documentation Review](#documentation-review)
4. [QA Review](#qa-review)
5. [Exit Criteria](#exit-criteria)

## Overview
- Use this plan to drive one disciplined beta-release routine.
- Treat release readiness as a single go/no-go decision, not as an endless
  stream of loosely related audit reactions.
- Keep package docs general to DevCovenant as a product. Keep repository
  operation notes in repository-owned docs only.
- Remove forward-looking blockers, stale expectations, and false historical
  narration encountered during the review.
- Record landed changes in `CHANGELOG.md` and use the governed gate workflow
  for every slice.

## Release Scope
1. [done] Clear the remaining stale CLI test expectation so the targeted
   current-state audit aligns with the runtime contract.
2. [not done] Re-audit package-facing docs for product scope and forward
   wording.
   Work:
   - remove repository-only narration from packaged docs
   - remove unnecessary internal jargon where plain language is enough
   - remove history-dependent phrasing such as `now`, `previously`, `used to`,
     and other transition narration unless a migration surface explicitly
     requires it
   - remove `in this repo` language from package docs when the correct scope is
     the general DevCovenant user experience
3. [not done] Review repository-facing docs for operator accuracy.
   Work:
   - confirm `README.md`, `AGENTS.md`, and trust docs stay truthful for this
     repository
   - keep repository workflow notes separate from packaged-product guidance
4. [not done] Freeze non-release work once blockers are cleared.
   Work:
   - accept only correctness bugs, packaging failures, CI failures, doc lies,
     and release blockers until the beta ships

## Documentation Review
- Audit these package-facing surfaces first:
  - `devcovenant/README.md`
  - `devcovenant/docs/installation.md`
  - `devcovenant/docs/workflow.md`
  - `devcovenant/docs/profiles.md`
  - `devcovenant/docs/policies.md`
  - `devcovenant/docs/config.md`
- Audit the managed documentation sources under
  `devcovenant/custom/profiles/devcovrepo/assets/docs/` so source, generated,
  and live docs stay aligned.
- For each doc surface, check:
  - product scope versus repository scope
  - unnecessary internal terminology
  - stale history or transition phrasing
  - forward-only wording
  - runtime/prose contract alignment

## QA Review
1. Functional QA
   - verify `install`, `refresh`, `gate`, `run`, `upgrade`, and managed
     bootstrap flows
2. Clean-room QA
   - test from a fresh clone with no pre-existing `.venv`
   - verify no ghost files or unintended generated artifacts appear
3. Managed-Environment Matrix QA
   - verify the seeded local `.venv` path
   - verify a declared non-venv local interpreter path
   - verify a declared system/native interpreter repository
   - verify one declared bench-managed or container-managed representative case
4. Packaging QA
   - build `sdist` and `wheel`
   - install built artifacts into a clean environment
   - smoke-test the installed CLI
5. Compatibility QA
   - confirm forward-only contract cleanup
   - confirm no stale aliases, bridges, or tests pinned to obsolete wording
6. Documentation QA
   - verify packaged docs are user-facing, general, and present-tense
   - verify generated mirrors match their sources
7. Release QA
   - verify changelog, version headers, CI status, and release evidence
   - run `devcovenant gate --start`, `devcovenant gate --mid`,
     `devcovenant run`, and `devcovenant gate --end`

## Exit Criteria
- The blocker list is empty or explicitly accepted for beta.
- The governed workflow passes on the release candidate tree.
- Package docs are general to DevCovenant and free of repository-only or
  history-dependent wording.
- The managed-environment support boundary is documented and validated across
  the release QA matrix instead of being implied by the seeded `.venv`
  example alone.
- Repository docs remain truthful for repository operators.
- Packaging, installation, and clean-room checks are complete.
- The beta decision can end with a clear go/no-go recommendation and a short
  residual-risk list.
