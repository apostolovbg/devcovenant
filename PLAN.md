# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Development Stance:** active-development
**Versioning Mode:** versioned
**Last Updated:** 2026-03-22
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->

Use this plan to turn DevCovenant from a technically serious internal tool into
a polished, externally credible, store-bought-looking product.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Writing Direction](#writing-direction)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)

## Overview
- The earlier performance, documentation-architecture, and contract-freezing
  work remains valid and should be preserved.
- The current external QA audit changes the next priority:
  - DevCovenant is functionally strong
  - DevCovenant is not yet polished enough to feel commercially finished
- The main gaps are now:
  - public package presentation that still looks template-derived
  - legal/compliance surfaces that are incomplete or out of sync
  - dependency-management behavior that still spans policy logic, runtime
    helpers, and one-off command wrappers without one formal contract
  - core DevCovenant invariants still live in policy land even though they
    define the engine's own non-optional trust boundary
  - security/privacy/support trust surfaces that are too thin
  - release/supply-chain assurance that is still below current best practice
- This roadmap therefore focuses on external readiness, standardization, and
  professional finish rather than on more internal refactoring.
- Keep the current managed-document preservation contract unless an explicit
  plan item changes it:
  - missing docs may be created from descriptors
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change

## Workflow
- Work in dependency order unless a real blocker forces reordering.
- Fix externally visible trust defects before secondary polish.
- Prefer objective evidence over vague reassurance:
  - package metadata
  - shipped docs
  - license artifacts
  - scanner output
  - build and publish workflows
- Keep each item concrete enough that another person can continue it without
  reconstructing hidden context.
- When an item is complete, rewrite it to state what landed and what is now
  true because of it.

## Writing Direction
- Write for technically serious readers who still need clear product surfaces.
- Keep docs operator-oriented and explanatory at the same time.
- Keep `README.md` and the packaged `devcovenant/README.md` as operator-first
  entrypoints, not as sprawling handbooks.
- Prefer fewer, stronger detailed docs whose titles match their contents
  cleanly over a larger set of partially overlapping references.
- Treat managed document templates as real document blueprints, not placeholder
  stubs or terse one-pagers; generated docs should start from a useful,
  substantial baseline.
- Remove template residue, placeholder language, and repo-insider phrasing
  from public package surfaces.
- Remove artistic, rhetorical, and self-conscious documentation prose that
  makes text sound polished while hiding what it actually says.
- Explain what a thing is, why it exists, what it controls, and when to use
  it.
- Keep paragraphs and lists breathable: avoid dense bullet walls, avoid
  long runs of tightly packed `-` bullets without spacing when the material
  is substantive, and prefer structures that are easy to scan under load.
- Keep config comments practical, concrete, and directly useful at the point
  of reading.
- Expand abbreviations on first use in each document.
- Treat undocumented behavior, half-documented behavior, repeated material
  without a clear reason, placeholder text, and fancy wording that hides the
  meaning as product defects.

## Active Work
1. [done] Fix The Public Package And Compliance Baseline.
   Goal:
   - make the shipped package, package metadata, and legal/compliance surfaces
     look accurate, finished, and professional before deeper release
     hardening.
   Why this matters:
   - the current audit found that the public README surfaces still look
     template-derived, the package metadata is sparse, and the third-party
     license inventory is out of sync with the actual declared and locked
     dependencies.
   Completed work:
   - moved public project identity into `project-governance` so
     `project_name` and `project_description` now drive shipped README and
     package-metadata surfaces
   - replaced placeholder public package identity such as `# Project Name`
     through that shared governance-owned identity source rather than through
     repo-specific descriptor overrides
   - chose the packaged `devcovenant/README.md` surface as the distribution
     long description so PyPI and installed-package readers see the same
     public README contract
   - added and validated the explicit `[build-system]` table plus richer
     package metadata such as project URLs and maintainer-facing metadata
   - made the third-party license inventory deterministic and accurate
     against current declared and locked dependencies, including local
     license-text artifacts
   - kept the CLI (command-line interface) version-reporting surface present
     as part of the public package baseline
   Outcome:
   - package metadata, README surfaces, and install experience now read like
     a real released product rather than a template-derived internal tool
   - public identity is governed from one repo-owned metadata source rather
     than duplicated across README and package config surfaces
   - the third-party license report matches actual dependency inputs exactly
   - build/package validation and the standard smoke-install test coverage
     still pass
2. [done] Standardize Dependency-Management Operations And Policy-Born
   Commands.
   Goal:
   - separate core DevCovenant invariants from customizable policies, then
     replace the current ad hoc dependency-license/runtime/command split with
     one coherent, customizable `dependency-management` policy contract.
   Why this matters:
   - dependency work now spans lock refresh, dependency inventory, license
     artifact generation, report synchronization, and a one-off wrapper
     command, but DevCovenant still lacks a formal policy-born command
     interface and a formal policy runtime-action contract.
   - at the same time, `devflow-run-gates`, `devcov-structure-guard`, and
     `devcov-integrity-guard` are not really repo-customizable policies; they
     are core DevCovenant invariants, and keeping them as policies would make
     core commands such as `gate` look like policy-born commands under the new
     command model.
   Completed work:
   - promoted `devflow-run-gates`, `devcov-structure-guard`, and
     `devcov-integrity-guard` into first-class core invariant contracts under
     `devcovenant/core/contracts/invariants/` and core runtime/service
     implementations under `devcovenant/core/services/`
   - surfaced resolved core-invariant metadata through the right first-class
     places: top-level `config.core_invariants`, tracked registry
     `core-invariants`, and the dedicated after-workflow, before-policy
     DevCovenant block in `AGENTS.md`
   - stopped treating those invariants as ordinary `policy_state` toggles and
     separated their profile-fed metadata from ordinary policy overlays by
     introducing profile `core_invariant_overlays`
   - kept `gate` as a first-class core command by moving required-test
     command resolution onto the `devflow-run-gates` invariant helper instead
     of leaving it as ad hoc policy-runtime behavior
   - converged `dependency-license-sync` into one
     `dependency-management` policy that now owns dependency refresh,
     dependency inventory, and license/report synchronization together
   - kept policy checks read-only while formalizing mutation through two
     explicit paths only:
     autofix invoking declared policy runtime actions, and manual
     namespaced policy commands invoking the same declared runtime actions
   - formalized policy runtime actions and policy-born commands with declared
     action metadata, command metadata, argument parsing, namespaced
     `devcovenant policy <policy> <command>` entrypoints, and compatibility
     validation against descriptor declarations
   - formalized autofix-aware dependency-management messaging so the policy
     advises manual commands when autofix is off and points at the same
     runtime action path when autofix is on
   - retire the one-off `update_lock` command entirely and use only the
     formal namespaced policy command surface such as
     `devcovenant policy dependency-management refresh-all`
   - updated docs, profile manifests, generated surfaces, and direct tests so
     custom policies now have one explicit command/autofix/check boundary to
     follow
   Outcome:
   - DevCovenant core invariants are clearly separate from customizable
     policies
   - `gate` remains a first-class core command instead of drifting into
     policy-command semantics
   - one `dependency-management` policy now owns dependency refresh and
     dependency-compliance behavior coherently
   - checks stay read-only, autofix owns automatic mutation, and explicit
     policy commands own manual mutation
   - policy-born commands, policy runtime actions, autofix delegation, and
     autofix-aware remediation messaging are now documented and test-backed
   - dependency-management no longer depends on a one-off wrapper contract or
     any backward-compatibility alias for `update_lock`
3. [done] Add Security, Privacy, Support, And Disclosure Surfaces.
   Goal:
   - make DevCovenant trustworthy from the outside, not only technically sound
     on the inside.
   Why this matters:
   - the current audit found no clear security-reporting surface, no explicit
     privacy/data-handling statement, no support/maintenance posture, and no
     buyer-facing explanation of what local runtime evidence artifacts do,
     and do not, store.
   Completed work:
   - added first-class public trust surfaces in the repository root:
     `SECURITY.md`, `PRIVACY.md`, and `SUPPORT.md`
   - documented vulnerability reporting, disclosure expectations, support
     scope, and data-handling boundaries in operator-facing language instead of
     leaving those expectations implicit
   - updated the public `README.md` entrypoint to surface those trust docs as
     part of the normal product-facing documentation map
   - hardened run-log persistence by redacting obvious secret-like values from
     structured `run.json` command arguments and structured metadata before
     they are written to disk
   - kept the run-log fidelity contract explicit by documenting that
     `stdout.log`, `stderr.log`, and `tail.txt` remain faithful command-output
     artifacts rather than content-aware secret scrubbers
   - documented the session-snapshot boundary explicitly: path-and-hash style
     session evidence, not full source-file contents
   - replaced runtime `assert` use in the documentation-growth policy with
     explicit configuration-violation handling so optimized Python execution
     and static-analysis tools see the same behavior
   - added direct regression tests for run-log redaction and for missing
     documentation-growth required options
   - reran Bandit and recorded the current triage stance explicitly: the real
     runtime defect was fixed, subprocess boundary warnings remain review
     surfaces, and obvious secret-literal false positives are now treated as
     explicit scanner noise rather than silent unknowns
   Outcome:
   - the repository now has credible public security, privacy, and support
     surfaces
   - runtime evidence behavior is documented in both public trust docs and the
     frozen workflow contract
   - structured run metadata no longer persists obvious secret-like values
     blindly
   - bundled policy configuration validation is clearer and safer under static
     analysis
   - the security review story is now explicit enough to support the next
     release-hardening work instead of relying on tacit maintainer knowledge
4. [done] Harden Release, Supply Chain, And Assurance.
   Goal:
   - raise release and supply-chain posture to current expectations for a
     professional Python package.
   Why this matters:
   - the current audit found basic build/test/publish hygiene, but not the
     stronger assurance layers now expected for externally credible software:
     trusted publishing, attestations, SBOMs, explicit security scanning, and
     supportable compatibility claims.
   Completed work:
   - upgraded the generated `governance-and-test` workflow template to run
     the full gate lifecycle on Python `3.14`, a focused compatibility matrix
     on Python `3.10` through `3.13`, and an assurance job that runs
     `pip-audit` plus `bandit`
   - added `bandit.yaml` so Bandit now skips the low-signal `B105`
     secret-literal heuristic while keeping real subprocess-boundary findings
     reviewable
   - tightened the remaining reviewed subprocess / exec boundaries with
     targeted `# nosec` annotations and simplified `update_lock` so Bandit can
     stay clean without hiding the real process boundaries
   - added weekly dependency-review automation through
     `.github/dependabot.yml` for both GitHub Actions and Python package
     metadata at the repository root
   - extended `build.yml` and `publish.yml` to generate a reproducible
     CycloneDX SBOM from `requirements.lock` plus `pyproject.toml`
   - replaced long-lived token-based PyPI upload with trusted publishing via
     `pypa/gh-action-pypi-publish@release/v1`
   - documented the release-assurance story in the workflow, installation,
     profile, and security docs, including how DevCovenant interprets scanner
     disagreements and what PyPI-side trusted-publisher setup is required
   Outcome:
   - release automation now emits stronger supply-chain evidence instead of
     only build and smoke-install proof
   - dependency and static-security scanning are part of the normal assurance
     surface
   - supported-version claims are backed by explicit CI evidence rather than a
     loose single-version check
   - publish automation now uses a modern PyPI trust model instead of a
     long-lived secret token
5. [not done] Rebuild The Documentation Set For Human Readability.
   Goal:
   - turn the documentation set into a smaller, clearer, easier-to-scan
     system where the operator path is obvious, detailed docs are fewer and
     better owned, and every major document says exactly what its title
     promises.
   Why this matters:
   - the current docs are still one of DevCovenant's biggest product-quality
     liabilities: they are too fragmented, too meta, too repetitive, and too
     dense to read comfortably under real operator or maintainer pressure.
   - the current `README.md` still behaves like a mixed handbook/reference/map
     instead of a clean operator entrypoint, while several detailed docs bleed
     into neighboring topics and carry contract-bookkeeping prose that weakens
     their value as explanations.
   - this hurts both first impressions and day-to-day usability, even when the
     underlying technical behavior is strong.
   Work to do:
   - redefine the documentation architecture explicitly:
     which docs exist, which docs are removed or merged, and which doc is the
     single primary home for each major topic
   - turn `README.md` and therefore packaged `devcovenant/README.md` into
     clearly operator-first entrypoints:
     quick orientation, quick install/integration, quick command flow, and a
     concise outward map to deeper docs
   - reduce the number of detailed docs where they are split too finely or
     overlapping, and merge or retire docs whose scope is too thin to justify
     a separate page
   - rewrite detailed docs so their titles and contents match tightly:
     `workflow` should be workflow, `installation` should be installation,
     `profiles` should be profiles, and so on, without each page half-owning
     adjacent topics
   - remove repeated "primary home", "normative home", and similar
     meta-documentation bookkeeping language from reader-facing prose unless it
     is truly necessary for understanding the product contract
   - strip out rhetorical flourishes, artistic-literary wording, and
     documentation-system self-reference where plain technical prose would
     explain the behavior better
   - revise formatting conventions for readability:
     fewer dense bullet walls, more short paragraphs, better list spacing, and
     less reliance on full document tables of contents where a shorter document
     would read better without one
   - keep operator-oriented and explanatory writing together, but do it through
     structure and clarity rather than by talking about "learning" or
     "teaching"
   - review and rewrite the managed template set across builtin and relevant
     custom profile assets so `README`, `SPEC`, `PLAN`, and related
     managed-doc assets reinforce the same documentation architecture instead
     of pushing the docs back toward sprawl
   - require those templates to produce detailed, genuinely useful documents
     rather than terse one-pagers, placeholder stubs, or minimally expanded
     shells that still need the reader to guess the intended shape
   - align template formatting as well as topic ownership so generated docs do
     not keep reintroducing dense bullet rhythm, poor spacing, or other
     readability problems after refresh or upgrade
   - use the local `copernican` repository as a comparative benchmark for
     information architecture:
     narrower topic ownership, clearer entrypoint-vs-reference separation, and
     more concrete prose, while still avoiding its own weaker habits where
     they are not worth copying
   - document the resulting architecture plainly so future work does not drift
     back into document sprawl
   Done when:
   - `README.md` is unmistakably an operator entrypoint rather than a mixed
     handbook/reference hybrid
   - the detailed docs are fewer, clearer, and each one has an obvious owned
     topic that matches its title
   - repeated topic spillover is materially reduced across the docs set
   - the writing is concrete, explanatory, and direct rather than fluffy,
     artistic, or repo-insiderish
   - the formatting is noticeably easier to scan under normal working
     conditions
   - the managed templates and live docs reinforce the same smaller, clearer
     documentation architecture
   - managed document templates across profiles now generate substantial,
     reader-useful documents instead of terse scaffolds
6. [not done] Run Final Store-Bought QA Closure.
   Goal:
   - verify that DevCovenant now feels professionally packaged, externally
     trustworthy, and operationally consistent across code, docs, packaging,
     and release automation.
   Why this matters:
   - a polished product is not just a collection of fixes; it is a coherent
     whole that says the same thing in the package metadata, the README, the
     legal/compliance surfaces, the security docs, the workflows, and the
     shipped artifacts.
   Work to do:
   - rerun the third-party QA audit with the same breadth:
     functionality, packaging, security, privacy, legal/compliance,
     documentation, and release posture
   - verify that the rebuilt documentation set is now readable, correctly
     scoped, consistent with titles, and aligned with the operator-entrypoint
     model rather than only technically complete
   - verify there is no remaining template residue, contradictory public
     messaging, or inaccurate legal/security artifact
   - verify scanner output, package metadata, build artifacts, and docs tell
     the same story
   - produce a concise release-readiness checklist for future releases so this
     polish does not regress
   Done when:
   - a fresh outside-in audit no longer finds obvious package, compliance,
     security-trust, or release-assurance gaps
   - DevCovenant can reasonably be described as store-bought in finish, not
     just in technical seriousness

## Validation Routine
- Verify `devcovenant gate --mid`, `devcovenant test`, and
  `devcovenant gate --end` pass after each slice.
- Verify `devcovenant check` remains clean once the gate session is closed.
- Verify `bandit -q -c bandit.yaml -r devcovenant` remains clean.
- Verify `pip-audit -r requirements.lock` remains clean.
- Verify build and packaging checks still pass after public-package changes.
- Verify dependency-management command, autofix, and check behavior follow the
  documented mutation boundary:
  - checks inspect/report only
  - autofixers may invoke policy runtime actions
  - explicit policy commands may mutate when run manually
- Verify legal/compliance artifacts match actual dependency and package state,
  not a stale approximation.
- Verify public docs and package metadata read like a finished product and not
  like a template-derived internal tool.
- Verify the docs set is small enough, readable enough, and clearly owned
  enough that operators can find the right page without navigating a maze of
  near-overlapping references.
- Verify support, security, privacy, and release-assurance surfaces are
  mutually consistent.
