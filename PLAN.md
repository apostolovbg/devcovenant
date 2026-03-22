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
- Remove template residue, placeholder language, and repo-insider phrasing
  from public package surfaces.
- Explain what a thing is, why it exists, what it controls, and when to use
  it.
- Keep config comments practical, concrete, and directly useful at the point
  of reading.
- Expand abbreviations on first use in each document.
- Treat undocumented behavior, half-documented behavior, repeated material
  without a clear reason, placeholder text, and fancy wording that hides the
  meaning as product defects.

## Active Work
1. [not done] Fix The Public Package And Compliance Baseline.
   Goal:
   - make the shipped package, package metadata, and legal/compliance surfaces
     look accurate, finished, and professional before deeper release
     hardening.
   Why this matters:
   - the current audit found that the public README surfaces still look
     template-derived, the package metadata is sparse, and the third-party
     license inventory is out of sync with the actual declared and locked
     dependencies.
   Work to do:
   - move public project identity into `project-governance` so
     `project_name` and `project_description` are the source of truth for
     shipped README and package-metadata surfaces
   - replace placeholder public package identity text such as `# Project Name`
     on shipped README surfaces through that shared identity source instead of
     repo-specific descriptor overrides
   - decide the correct long-description source for package distribution and
     ensure the public package README is the surface that buyers and users see
   - add an explicit `[build-system]` table and tighten packaging metadata so
     it reflects a mature distributed Python package
   - add missing project metadata such as URLs, maintainers/authors,
     classifiers, and similar buyer-facing package context where appropriate
   - make the third-party license inventory deterministic and correct against
     current declared and locked dependencies
   - add small public-package quality fixes that materially improve the first
     impression, such as a clear version-reporting command surface if it still
     remains missing
   Done when:
   - package metadata, README surfaces, and install experience look like a real
     released product rather than a template-derived internal tool
   - public identity is governed from one repo-owned metadata source rather
     than duplicated across README and package config surfaces
   - the third-party license report matches actual dependency inputs exactly
   - build, smoke-install, and packaging checks still pass
2. [not done] Standardize Dependency-Management Operations And Policy-Born
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
   Work to do:
   - promote `devflow-run-gates`, `devcov-structure-guard`, and
     `devcov-integrity-guard` into first-class core modules/contracts rather
     than ordinary policies
   - surface their resolved metadata in the right first-class places,
     including `config` documentation and the after-workflow,
     before-policy DevCovenant block in `AGENTS.md`
   - keep those invariant surfaces intentionally non-casual and
     non-customizable so the engine's own trust boundary is not treated like
     an optional repo policy
   - keep core lifecycle commands such as `gate` as first-class DevCovenant
     commands rather than letting them drift into policy-born command
     semantics
   - converge `dependency-license-sync` into one `dependency-management`
     policy that owns dependency operations and compliance artifacts together
   - keep the check path read-only so policy checks only detect/report drift
     and never mutate files directly
   - formalize policy runtime actions as an explicit contract with action ids,
     payload/result shapes, mutating vs read-only behavior, and error rules
   - formalize policy-born CLI commands so policies can declare commands,
     arguments, help text, aliases, visibility rules, and namespaced entry
     points through one standard interface
   - formalize autofixer delegation so autofixers may invoke policy runtime
     actions, while normal policy checks may not
   - formalize autofix-aware policy messaging so a policy can surface one
     remediation path when autofix is enabled and another when autofix is off
   - replace one-off wrapper commands such as `update_lock` with the formal
     policy-command surface, while preserving compatibility aliases only where
     they are still useful
   - document and test the command/autofix/check boundary so custom policies
     can expose operations without special-case CLI code
   Done when:
   - DevCovenant core invariants are clearly separate from customizable
     policy surfaces
   - `gate` remains a first-class core command and no longer reads like a
     policy-born command
   - one `dependency-management` policy owns dependency refresh and
     dependency-compliance behavior coherently
   - checks stay read-only, autofix owns automatic mutation, and explicit
     policy commands own manual mutation
   - policy-born commands, policy runtime actions, and autofix delegation are
     formally specified, documented, and test-backed
   - dependency-management no longer depends on one-off CLI wrapper behavior
3. [not done] Add Security, Privacy, Support, And Disclosure Surfaces.
   Goal:
   - make DevCovenant trustworthy from the outside, not only technically sound
     on the inside.
   Why this matters:
   - the current audit found no clear security-reporting surface, no explicit
     privacy/data-handling statement, no support/maintenance posture, and no
     buyer-facing explanation of what local runtime evidence artifacts do,
     and do not, store.
   Work to do:
   - add a real `SECURITY.md` with vulnerability reporting and disclosure rules
   - add a privacy/data-handling document that explains local run logs,
     registry runtime state, session snapshots, cleanup, and the absence of
     outbound telemetry
   - add a support/maintenance posture so users and buyers know what is
     supported and how issues are handled
   - add any other trust-surface files needed for a credible public repository
     and package, such as conduct/ownership guidance where that improves
     external clarity
   - harden runtime evidence handling where needed, including secret/redaction
     review for run logs and snapshots
   - triage Bandit output into real fixes, justified false positives, and any
     scanner baselines or suppressions that must be explicit rather than
     accidental
   - remove real hardening defects surfaced by the current scanner pass, such
     as runtime use of `assert` in non-test logic where explicit checks are
     safer and clearer
   Done when:
   - the repository has credible security, privacy, and support surfaces
   - runtime evidence behavior is documented and intentionally bounded
   - security scanner output is either fixed or explicitly justified
4. [not done] Harden Release, Supply Chain, And Assurance.
   Goal:
   - raise release and supply-chain posture to current expectations for a
     professional Python package.
   Why this matters:
   - the current audit found basic build/test/publish hygiene, but not the
     stronger assurance layers now expected for externally credible software:
     trusted publishing, attestations, SBOMs, explicit security scanning, and
     supportable compatibility claims.
   Work to do:
   - replace long-lived token-based PyPI upload with trusted publishing if
     practical for this release model
   - place dependency refresh, dependency inventory, and related operator
     workflows on the standardized `dependency-management` policy/command
     surface rather than on one-off wrapper entrypoints
   - add provenance/attestation support to package publication
   - add SBOM generation or an equivalent explicit software-inventory artifact
     strategy
   - integrate `pip-audit` and `bandit` into the project’s normal assurance
     surface in a way that is deterministic and useful rather than noisy
   - add dependency update automation or an equally explicit dependency-review
     discipline
   - tighten CI so it proves the supported Python-version claim with a real
     compatibility matrix rather than a loose single-version check
   - document how DevCovenant interprets scanner disagreements when one source
     flags a package and another does not
   Done when:
   - release automation emits stronger supply-chain evidence
   - dependency and static-security scanning are part of normal quality gates
   - supported-version claims are backed by explicit CI evidence
5. [not done] Run Final Store-Bought QA Closure.
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
- Verify `bandit -r devcovenant` is either clean or reduced to explicitly
  justified, documented residual findings.
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
- Verify support, security, privacy, and release-assurance surfaces are
  mutually consistent.
