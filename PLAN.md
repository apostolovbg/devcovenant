# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1.dev1
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-02
**DevCovenant Version:** 1.0.1.dev1

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track active implementation work.
Keep items dependency-ordered, concrete, and current.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Writing Direction](#writing-direction)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)

## Overview
- Use `PLAN.md` for active multi-slice work, not for durable product
  requirements.
- Record durable project requirements in `SPEC.md` when the repository uses
  SPEC.

- Record completed slice history in `CHANGELOG.md`.

- Mark completed items as `[done]` and outstanding items as `[not done]`.

- Prefer one roadmap that people can execute over a long wish list of vague
  intentions.

## Workflow
- Work in dependency order unless a real blocker forces reordering.

- Keep each item concrete enough that another person can continue it.

- Update status in the same session when work lands.

- Split very large themes into numbered items with clear closure criteria.

## Writing Direction
- State what the work is, why it matters, what has to happen, and how you
  will know it is done.
- Prefer plain language over slogans.

- Use bullets for requirements and acceptance checks.

- Treat vague work items as unfinished planning, not as good enough
  planning.

## Active Work
1. [not done] Release-readiness review and hardening for the orphaned
   prerelease line.
   Goal:
   - finish one industry-standard pre-release QA review and any blocking
     hardening needed to ship the next real public release after orphaning
     the branch.
   Why this matters:
   - the prerelease line needs to ship from a source tree that is
     operationally clean, contract-stable, packaging-correct, CI/publish-safe,
     and free of accidental fallback behavior.
   - this review must be one slice, not a five-slice roadmap, so release
     readiness is judged as one coherent go/no-go decision instead of a queue
     of loosely related mini-projects.
   - orphaning removes the value of historical narrative, so the repo must be
     self-explanatory and self-consistent from the current tree alone.
   Work to do:
   - run one read-only release-readiness audit across the entire repo:
     runtime, packaging, docs, generated assets, workflow automation, publish
     automation, and governed config.
   - verify the public contract surfaces as one coherent release system:
     CLI commands, gate workflow, managed-environment behavior, config knobs,
     generated docs, and package metadata.
   - verify package artifacts as artifacts, not only as source:
     `sdist`, `wheel`, installed proof repo, and `pipx` proof repo.
   - verify environment handling across every supported style of execution
     environment:
     repo `.venv`, explicit interpreter targets, external env roots,
     bench-like env roots, and current-interpreter bootstrap hosts used only
     until the declared target environment exists.
   - verify child command execution is interpreter-driven where required, so
     gate/workflow behavior does not depend on accidental `PATH` contents.
   - audit `Governance`, `Build`, and `Publish` together:
     source workflow ownership, action versions, Node 24 posture, artifact
     handoff, provenance handoff, permissions, and run-ID publish flow.
   - verify Publish is release-safe:
     it must publish validated CI artifacts, not rebuild a divergent tree, and
     it must work for the exact artifact set that Build proves.
   - audit package docs for package scope only:
     no repository-specific `devcovrepo` narration, no local-release
     operational
     notes, and no history-dependent guidance that will look absurd after the
     orphan step.
   - audit repo docs and editable notes for release operator clarity:
     root `README.md`, `AGENTS.md`, trust docs, and
     repository-specific workflow notes must stay accurate for the repository
     while package docs stay generic.
   - run a defallback/de-BS sweep as part of the same review:
     remove silent legacy fallbacks, stale compatibility bridges, dead aliases,
     history talk, and half-migrated contract language encountered in the
     audit.
   - verify project-governance ownership and config ownership surfaces:
     only real human knobs belong in config; derived or engine-owned behavior
     stays under the hood and is documented where operators actually need it.
   - verify release metadata identity end-to-end:
     package name, project-governance identity, `pyproject.toml`, generated
     docs, editable install metadata, `*.egg-info`/`*.dist-info`, and publish
     outputs must agree on `devcovenant` as the canonical machine identity.
   - verify security and supply-chain release posture:
     dependency inventory, license report, SBOM, provenance, trust docs, and
     publish inputs/outputs must all be present and current.
   - run the full governed validation loop on the hardened tree:
     `gate --start`, `gate --mid`, `run`, `gate --end`, `check`, plus any
     release-proof commands needed to validate build and publish surfaces.
   - produce one explicit release-readiness verdict at the end:
     blockers, non-blocking risks, exact fixes landed in the same slice, and a
     final go/no-go recommendation for orphaning plus the next real public
     release.
   Done when:
   - the review has been executed as one slice and the blocker list is empty.
   - all source-owned workflow surfaces are aligned and green:
     Governance, Build, and Publish inputs/outputs all match the current
     release contract.
   - package identity is stable and lowercase `devcovenant` across metadata,
     artifacts, and installed proof environments.
   - the package docs are package-generic, the repository docs are
     repository-specific where needed, and no pre-orphan history narration
     remains in the active release-facing docs.
   - managed-environment behavior is proven against the supported
     every-style-environment matrix instead of only the happy-path `.venv`
     case.
   - release artifacts and release evidence are reproducible from the current
     tree without depending on local accidents or stale ignored outputs.
   - the final governed tree passes `devcovenant check`, and the release
     review can end with a justified go/no-go recommendation for orphaning and
     shipping the next real public release.

## Validation Routine
- Verify checks and tests pass.

- Verify generated artifacts are synchronized after refresh.

- Verify documentation and changelog were updated where behavior changed.

- Verify `devcovenant check` passes after the slice closes.
