# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1b1
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-03
**DevCovenant Version:** 1.0.1b1

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the release-QA work needed to ship the `1.0.1`
release line.
Keep items concrete, current, and focused on release readiness rather than
open-ended cleanup.

## Table of Contents
1. [Overview](#overview)
2. [Release Scope](#release-scope)
3. [Documentation Review](#documentation-review)
4. [QA Review](#qa-review)
5. [Exit Criteria](#exit-criteria)

## Overview
- Use this plan to drive one disciplined `1.0.1` release routine.
- Treat release readiness as a single go/no-go decision, not as an endless
  stream of loosely related audit reactions.
- Treat `1.0.0` as burned on PyPI and use `1.0.1` as the maintained public
  line from here.
- Use `1.0.1b1` as the explicit prerelease cut for the current release
  qualification pass.
- Keep package docs general to DevCovenant as a product. Keep repository
  operation notes in repository-owned docs only.
- Remove forward-looking blockers, stale expectations, and false historical
  narration encountered during the review.
- Keep release-QA practical by reducing avoidable duplicate work in the heavy
  lifecycle commands without weakening end-to-end coverage.
- Record landed changes in `CHANGELOG.md` and use the governed gate workflow
  for every slice.

## Release Scope
1. [done] Clear the remaining stale CLI test expectation so the targeted
   current-state audit aligns with the runtime contract.
2. [done] Clarify and document the managed-environment contract.
   Landed:
   - `.venv` is documented as the seeded default, not the only supported shape
   - the managed-environment policy and docs now describe a declared execution
     context contract
   - release QA now includes a managed-environment matrix instead of implying
     `.venv` as the whole model
3. [done] Re-audit package-facing docs for product scope and forward wording.
   Landed:
   - package docs use more product-facing wording and less repeated
     repository-internal jargon
   - ambiguous phrasing such as policy state living "in the repo" was replaced
     with clearer project-file wording
   - the package docs keep `.venv` as the seeded example without treating it as
     the whole product story
4. [done] Review repository-facing docs for operator accuracy.
   Landed:
   - root README release notes now call out the maintained public `1.0.1` line
   - trust docs align support and security scope to the same `1.0.1` line
   - repository notes stay in repository-owned docs instead of leaking into the
     packaged docs
5. [done] Tighten heavy lifecycle commands without reducing fidelity.
   Landed:
   - `refresh` now reuses one profile-registry build, avoids duplicate
     manifest normalization, and records per-phase timing details in the run
     summary artifacts
   - `install`, `deploy`, `undeploy`, `uninstall`, and `upgrade` now record
     phase timing details in the same summary artifacts
   - `undeploy` now limits repository-wide managed-doc scanning to recovery
     paths instead of using it as the normal path
   - setup-only lifecycle tests now prefer cached installed or refreshed seed
     repositories while keeping direct end-to-end lifecycle coverage where the
     command path itself is the contract under test
6. [done] Decide the `1.0.1` release form.
   Landed:
   - chose `1.0.1b1` for one explicit opt-in prerelease pass on PyPI
   - kept the stable `1.0.1` line reserved for the first maintained
     non-prerelease release after the prerelease review
   - kept the decision explicit in the release plan, changelog, and version
     bump
7. [done] Freeze non-release work once blockers are cleared.
   Landed:
   - accepted only release readiness work, correctness fixes, packaging
     checks, and documented contract alignment in the release-cut slice
   - treated unrelated cleanup as out of scope until the `1.0.1` line ships

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
   - use summary phase timings to inspect heavy lifecycle commands before
     treating a slow run as a vague test-suite problem
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
- Heavy lifecycle commands avoid duplicate no-op work where possible and leave
  timing evidence in run summaries when more optimization is needed.
- The chosen `1.0.1` release form, prerelease or direct stable, is explicit
  before publish.
- Repository docs remain truthful for repository operators.
- Packaging, installation, and clean-room checks are complete.
- The `1.0.1` release decision can end with a clear go/no-go recommendation
  and a short residual-risk list.
