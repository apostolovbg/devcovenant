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
   - the repo-specific `devcovrepo` profile now contributes CI proof through
     `ci_and_test` metadata by extending the main `ci-and-test` job with the
     repo's scanner steps and adding one dependent
     `build-and-install-test` job, so the generated workflow proves the
     documented installed-CLI path without pushing Python-package assumptions
     back into the language-agnostic global workflow template
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

5. [done] Finish The Documentation Polish Pass.
   What landed:
   - the openings of `config.md`, `project_governance.md`, `registry.md`,
     `contracts.md`, and `policies.md` were rewritten to keep the explicit
     contract markers the package tests expect while shifting the reading
     experience back toward direct operator questions and concrete decisions
   - the surviving references to `devcovenant/docs/contracts.md` now behave
     more like a doc-map pointer and less like repeated administrative throat
     clearing at the top of every page
   - the registry docs now frame tracked versus runtime-local registry state
     as a practical debugging choice, and the configuration docs now frame
     `devcovenant/config.yaml` as the place where a human decides active repo
     behavior instead of as a generic ownership lecture
   - the contract index itself now tells readers to start in the concrete page
     they need and use `contracts.md` as a map, which keeps the stable
     contract-home model without letting it dominate the whole doc set
   What is now true:
   - the detailed docs still satisfy the current contract-index tests
   - the remaining meta wording is deliberate and lighter
   - the package docs read more like direct technical references and less like
     contract-administration notes

6. [done] Run The Final Store-Bought QA Closure Again.
   What landed:
   - reran the outside-in audit across the live docs, config, registry,
     workflow surfaces, package metadata, command naming, and packaged README
     contract
   - verified that the packaged `devcovenant/README.md` now behaves like a
     real public package surface: it keeps the `pipx` install story, keeps
     the governed workflow guidance, and rewrites public doc links into
     package-safe GitHub URLs instead of shipping broken repo-relative links
   - rebuilt sdist and wheel from a temp copy that preserved tracked package
     docs while excluding runtime debris, confirmed the build stayed
     warning-free, and ran `twine check` successfully on both artifacts
   - confirmed the built artifacts no longer carry removed-command residue or
     stale CI naming such as `update_lock`, `governance-and-test`, or
     Dependabot config, while still shipping the intended package docs and
     tracked `README` surfaces
   - confirmed the live doc and config surfaces now tell the same story as the
     runtime and profile metadata, with no substantive contradictions found in
     the final picky-eye pass
   What is now true:
   - the final external-style audit no longer finds substantive documentation,
     code, or packaging mismatches
   - DevCovenant now reads as polished, consistent, and intentionally
     packaged enough to move into release-candidate preparation

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
