# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** breaking-allowed
**Versioning Mode:** versioned
**Last Updated:** 2026-03-24
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->

Use this plan to close the remaining pre-release gaps surfaced by the final
read-only audit and then rerun the release-closure audit from a cleaner,
truer, more intentional baseline.

## Table of Contents
1. [Overview](#overview)
2. [Working Rules](#working-rules)
3. [Writing Direction](#writing-direction)
4. [Active Remediation](#active-remediation)
5. [Validation Routine](#validation-routine)

## Overview
- The large stabilization work is already done and should be preserved:
  - project governance now uses `stage`, `maintenance_stance`,
    `compatibility_policy`, and `versioning_mode`
  - dependency-management is one coherent policy surface
  - security, privacy, and support surfaces exist
  - CI and release assurance are materially stronger than before
  - the documentation set is much smaller and more usable than it was
- The repo is now in remediation mode, not invention mode.
- The final read-only audit narrowed the remaining gaps to five specific
  product-finish problems:
  - the packaged README still uses repo-relative public links that are wrong
    for PyPI
  - the live generated `devcovenant/config.yaml` comment scaffold drifted from
    the current asset/runtime truth
  - local package builds still emit MANIFEST and package-discovery warnings
  - the machine-install story is no longer explicit enough now that `pipx`
    looks like the right public install path
  - the detailed docs still carry too much contract-index and
    "normative home" language
- The next full outside-in audit should happen only after those issues are
  corrected.
- Keep the current managed-document preservation contract unless an explicit
  plan item changes it:
  - missing docs may be created from descriptors
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change

## Working Rules
- Work in dependency order unless a real blocker forces reordering.
- Keep remediation narrow and audit-backed.
- Fix source-of-truth drift before polishing wording around it.
- Prefer objective evidence over vague reassurance:
  - package metadata
  - shipped docs
  - license artifacts
  - scanner output
  - build and publish workflows
- Treat build warnings as defects, not harmless background noise.
- When root and packaged doc surfaces need to differ, make the split explicit
  and refresh-stable instead of depending on accidental drift.
- Do not regress the current command/runtime contracts while fixing public
  polish.
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

## Active Remediation
1. [done] Fix The Packaged README Public-Link Contract.
   What landed:
   - the repo-specific `readme-sync` policy now rewrites repo-relative public
     Markdown links in the packaged `devcovenant/README.md` from
     `pyproject.toml` repository metadata instead of hardcoding one upstream
     repository URL into shared policy logic
   - the root `README.md` remains repository-friendly and repo-relative, while
     the packaged README becomes PyPI-safe through the refresh-owned sync step
   - the owning policy, docs, registry text, and tests now explain and enforce
     the metadata-driven link contract
   - local package proof now shows the built sdist README and wheel metadata
     contain package-safe absolute links and no longer contain broken
     repo-relative public links
   What is now true:
   - the packaged README is usable on PyPI
   - the split between root and packaged README surfaces is intentional and
     refresh-stable
   - forks can keep packaged README links correct by updating package metadata
     instead of patching repo-specific runtime code

2. [done] Reconcile Generated Config Commentary With Runtime Truth.
   What landed:
   - the refresh-owned config comment renderer now matches the active global
     config asset for both cleanup and `ci_and_test` sections
   - the live generated `devcovenant/config.yaml` now explains cleanup
     protection in terms of runtime-owned critical paths and
     managed-environment metadata instead of claiming a hardcoded `.venv`
     safety rule
   - the old `Governance-and-test generation` header is gone from the live
     generated config and has been replaced with the correct
     `CI-and-test workflow generation` wording
   - the refresh regression suite now checks both the updated config
     commentary and the intentional empty-managed-block contract for
     `README.md` and `devcovenant/README.md`
   What is now true:
   - the live generated config comments match the current asset/runtime truth
   - the packaged and root README managed blocks stay empty by design
   - a refresh rerun preserves the corrected commentary deterministically

3. [done] Make The Package Build Warning-Free.
   What landed:
   - `MANIFEST.in` now describes only the source artifacts that really belong
     in the source distribution instead of carrying stale exclude and prune
     rules that fired warnings when those paths were absent
   - `pyproject.toml` now uses explicit setuptools package-data declarations
     for the shipped runtime docs, built-in profile assets, built-in policy
     descriptors, and tracked package READMEs instead of relying on ambiguous
     implicit package-data scanning
   - the packaging regression suite now checks the explicit package-data
     contract and the simplified manifest contract in addition to the existing
     wheel-content assertions
   - the package build proof was rerun until `python -m build` completed
     without MANIFEST or package-discovery warnings
   What is now true:
   - local package builds are quiet as well as successful
   - the wheel still excludes runtime logs, runtime registry state, test
     trees, and stale build debris while keeping the packaged docs and
     built-in assets that DevCovenant needs at runtime
   - the packaging boundary is now explicit in both metadata and docs instead
     of being enforced by warning-prone side effects

4. [done] Standardize The Public Install Story Around `pipx`.
   What landed:
   - the public install surfaces now present a clear split between ordinary
     machine installation and source-checkout development:
     `pipx` for installed CLI use, repository-managed environment or source
     checkout for DevCovenant contributors and unreleased runtime work
   - `README.md`, the packaged `devcovenant/README.md`,
     `devcovenant/docs/installation.md`, troubleshooting guidance, workflow
     guidance, profile docs, and `SUPPORT.md` now tell the same story about
     how to install, upgrade, and troubleshoot the CLI without blurring that
     machine-install path with `devcovenant install` inside a governed
     repository
   - the repo-specific `devcovrepo` profile now contributes an
     `installed-cli-smoke` CI job through `ci_and_test` metadata, so the
     generated `ci-and-test` workflow proves the documented installed-CLI path
     without pushing Python-package assumptions back into the language-agnostic
     global workflow template
   - the profile-registry regression suite now locks that repo-specific CI
     proof into the workflow contract, and the package-doc wording remains
     neutral about repo-specific profile names while still documenting the CI
     boundary clearly
   - a fresh installed-CLI proof now exists for the current artifact set:
     a wheel built from a temp copy of the working tree was installed with
     `pipx`, `devcovenant --version` reported `1.0.0`, and the installed CLI
     ran `devcovenant gate --status` successfully
   What is now true:
   - the public docs consistently present `pipx` as the preferred machine
     install path
   - contributor docs still clearly distinguish source development from
     installed-CLI usage
   - installed-CLI proof now lives in both release validation and repo-specific
     CI instead of in ad hoc local notes

5. [not done] Finish The Documentation Polish Pass.
   Goal:
   - make the docs read like product docs instead of contract-administration
     notes.
   Why this matters:
   - the docs were restructured successfully, but the audit still found too
     much contract-index and "normative home" phrasing in pages that should be
     direct operator references.
   Work to do:
   - rewrite the openings of the detailed docs that still lead with meta
     contract language instead of task or concept framing
   - trim repeated "use this together with..." and "normative home" wording
     where it adds governance bookkeeping but not reader value
   - keep the contract map explicit in `contracts.md`, but stop making every
     detailed page sound like an extension of that index
   - reread the operator path from `README.md` into installation, workflow,
     config, and troubleshooting to make sure the tone stays practical
   - keep the docs short enough to scan under pressure while still explaining
     everything they own
   Done when:
   - the detailed docs open with direct task or concept framing
   - the contract map stays available without dominating the reader experience
   - the remaining meta phrasing is deliberate and minimal

6. [not done] Run The Final Store-Bought QA Closure Again.
   Goal:
   - rerun the full external-style audit after remediation and confirm that the
     remaining gaps are actually gone.
   Why this matters:
   - the previous audit already did its job: it found the remaining issues.
     The next audit should confirm closure, not rediscover the same defects.
   Work to do:
   - rerun the read-only audit across docs, code, config, registry, workflows,
     packaging, trust surfaces, and release posture
   - verify the packaged README behaves like a real public package surface
   - verify the live config comments tell the same story as the runtime and
     source assets
   - verify the build is warning-free, `twine check` passes, and artifact
     contents match the documented product surface
   - verify there is no remaining stale naming, removed-command residue, or
     contradictory public messaging
   - produce a concise release-readiness checklist from the final clean audit
   Done when:
   - a fresh audit finds no substantive documentation, code, or packaging
     mismatches
   - DevCovenant reads as polished, consistent, and intentionally packaged

7. [not done] Prepare The Release-Candidate Cut.
   Goal:
   - turn the remediated tree into a release candidate only after the final
     audit is clean.
   Why this matters:
   - release mechanics are easier to trust after the repo truth is stable.
     History rewriting or orphaning before then only hides work in progress.
   Work to do:
   - confirm that the current `1.0.0`, `stable`, `active`, and
     `breaking-allowed` governance state is still the intended public truth
   - rerun the governed gate/test cycle and packaging checks on the exact
     release-candidate tree
   - decide whether any branch-history cleanup or orphaning is still desired,
     and do it only after the release-candidate tree is already proven
   - rerun a short post-history-change smoke audit if the tree identity changes
   - then publish from the already-audited release candidate
   Done when:
   - the release candidate is clean, audited, and truthfully labeled
   - any optional history cleanup happens after, not before, release proof

## Validation Routine
- For every remediation slice, run:
  1. `devcovenant gate --mid`
  2. `devcovenant test`
  3. `devcovenant gate --end`
  4. `devcovenant check`
- For packaged-surface work, also run:
  1. `python -m build`
  2. `twine check dist/*`
  3. wheel and sdist smoke installs
- For public-install work, also run:
  1. `pipx` install from a built artifact
  2. installed-CLI smoke checks such as `--version`, `-h`, and one safe
     operational command
  3. verification that the documented end-user install path matches the path
     the release process actually proved
- Keep `bandit` and `pip-audit` clean unless a reviewed, documented exception
  is explicitly introduced.
- Treat packaging warnings as failures for this plan, even if the build exits
  successfully.
- Keep `CHANGELOG.md` and any touched operator docs aligned with the actual
  remediated behavior.
