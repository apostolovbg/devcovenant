# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1b4
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-16
**DevCovenant Version:** 1.0.1b4

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the current DevCovenant onboarding, evaluation, and
adoption roadmap.
Keep it concrete, dependency-ordered, and centered on the first-user
experience, not on already-completed hardening work.

## Table of Contents
1. [Overview](#overview)
2. [Planning Boundaries](#planning-boundaries)
3. [Delivery Order](#delivery-order)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)
6. [Exit Criteria](#exit-criteria)

## Overview
- Treat this plan as the active roadmap for making DevCovenant legible to
  people who do not already live inside this repository.
- Keep the front door focused on product understanding first, then operator
  ceremony, then architecture depth.
- Make the first-contact surfaces explain what DevCovenant is in plain
  language before they ask readers to absorb lifecycle details.
- Keep the plan centered on repository-level adoption: onboarding, evaluation,
  demoability, and the first custom-governance path.
- Update status markers in the same session when work lands so this file stays
  executable as a real roadmap.

## Planning Boundaries
- The root `README.md` and `devcovenant/README.md` must keep the same overall
  section order and shared core content. The root README may add repo-only
  context, but it must not fork into a different story.
- The README is the onboarding surface in the first pass. Do not hide the
  first-use story behind `devcovenant asset ...`, a generated doc lookup, or a
  separate onboarding document.
- Do not add a separate onboarding document in the first pass. If we later add
  one, it must extend a successful front door instead of compensating for a
  failed README.
- `devcovenant quickstart` must be fixed, canonical, and non-interactive. It
  must not inspect repo state, branch on conditions, or act like a wizard.
- `devcovenant demo` is the short evaluation path for beta testing, demos, and
  client conversations. It must show the product, not just restate docs.
- The custom-governance path belongs immediately after the front door, not
  before it. Users must understand the product before we ask them to extend it.

## Delivery Order
1. Rewrite both READMEs in the new shared public-facing format.
2. Make docs discoverability explicit through the README structure and docs
   map.
3. Add the fixed `devcovenant quickstart` command.
4. Add the disposable `devcovenant demo` command.
5. Add the first custom-policy / custom-profile onboarding path.

## Active Work
1. [done] Front-door README rewrite
   Goal:
   - Turn the READMEs into a public landing surface that explains DevCovenant
     to someone who has never heard the phrase "repository governance
     framework".
   Why this matters:
   - The current front door still reads too much like internal documentation.
     It asks readers to absorb lifecycle and configuration mechanics before it
     fully earns their attention with the product problem, the differentiators,
     and the payoff.
   Scope boundaries:
   - Keep the root and package READMEs in the same format and section order.
   - Keep repo-only notes in the root README only.
   - Do not assume prior knowledge of DevCovenant terminology.
   - Do not move the reader into install/deploy before value is established.
   Work to do:
   - Define the opening explanation in plain language: what DevCovenant is,
     what problem category it solves, and why repository-level governance is a
     distinct class of tool.
   - Explain what "repository governance" means in practice instead of
     assuming the term explains itself.
   - Contrast DevCovenant directly with a linter, IDE plugin, prompt pack,
     model wrapper, and AI-only coding tool.
   - Explain the repo-level contract: model/account/IDE/machine independence,
     repository-owned law, and why this matters in mixed human/AI workflows.
   - Call out the metadata and layered-ownership model as the reason the
     system reduces drift instead of just adding more YAML.
   - Surface the strongest proof points early: dogfooding, downstream usage,
     custom-governance capability, and the fact that the repo owns its own
     rules.
   - Add a short evaluation path before installation so readers can decide
     whether the tool is relevant before they absorb lifecycle details.
   - Align README phrasing with the current product positioning everywhere the
     project still sounds like a generic "self-enforcing policy system".
   Done when:
   - A new reader can understand the product and its differentiators from the
     README alone in one short reading pass.
   - The install/deploy workflow appears after the product explanation, not
     before it.
   - The root and package READMEs tell the same core story with the same
     structure.
   - The README explicitly carries the strong points we already know matter:
     repo-level governance, layered ownership, metadata API, dogfooding, and
     downstream adoption.

2. [done] Docs discoverability through the README front door
   Goal:
   - Make the existing docs easy to find from the README without requiring
     install-time asset discovery or prior knowledge of the doc tree.
   Why this matters:
   - The documentation set already has depth, but the current entry path is
     fragmented and non-intuitive. Readers can miss the right doc simply
     because they do not know which internal concept name to look for.
   Scope boundaries:
   - Keep the README as the front door in this phase.
   - Do not add a separate onboarding doc yet.
   - Use task language and reader questions, not internal module naming, for
     navigation labels.
   Work to do:
   - Add a readable docs map to the README that routes readers by question and
     task.
   - Group docs by practical intent: installation/lifecycle, workflow,
     policies/custom policies, profiles/custom profiles, architecture, and
     troubleshooting.
   - Ensure the docs map is reachable before the deep reference material and
     does not require reading the whole README first.
   - Audit doc links and headings for insider wording that makes sense only to
     someone who already knows the system.
   - Make the package README and root README route into the same doc set in the
     same order.
   - Ensure readers can discover the custom-governance documentation path
     without first understanding every policy and profile concept in depth.
   Done when:
   - A new evaluator can reach the right doc from the README without trial and
     error.
   - The docs map answers "where do I go next?" for both first-time readers and
     technically serious evaluators.
   - The README no longer depends on installed-asset discovery to make the docs
     feel navigable.

3. [not done] Fixed `devcovenant quickstart`
   Goal:
   - Add one canonical, non-interactive command that prints the standard first
     DevCovenant path in the same order every time.
   Why this matters:
   - After installation, users need one stable answer to "what do I do first?"
     without being dropped immediately into dense lifecycle documentation or a
     state-aware helper that changes shape between repos.
   Scope boundaries:
   - Keep `quickstart` fixed and non-interactive.
   - Do not inspect repo state or branch its output based on current
     conditions.
   - Do not turn the command into a wizard, setup assistant, or hidden demo.
   Work to do:
   - Add `quickstart` to the CLI command surface and help output.
   - Define the canonical output sequence: what DevCovenant is, minimal
     install/deploy flow, the gate lifecycle, where `run` fits, and where to
     read next.
   - Keep the wording synchronized with the rewritten README so the terminal
     story and docs story do not diverge.
   - Decide whether the command should print compact prose, numbered steps, or
     both, but keep the result stable and script-safe.
   - Add tests that prove the command exists, stays non-interactive, and
     renders the expected ordered guidance.
   - Verify the command works from source checkout, wheel install, and pipx
     install.
   Done when:
   - `devcovenant quickstart` prints the same ordered guidance in every repo.
   - The command is useful as an operator reminder and as a low-friction first
     contact after install.
   - CLI help, README guidance, and lifecycle docs describe the same first-use
     path.

4. [not done] Disposable `devcovenant demo`
   Goal:
   - Add a short, high-signal demo path that lets users and prospects see how
     DevCovenant works in practice in about ten minutes.
   Why this matters:
   - Beta testers and clients should not have to reverse-engineer the product
     from reference docs before they can evaluate it. A demo path is both an
     adoption tool and a sales tool.
   Scope boundaries:
   - Keep the demo disposable and safe.
   - Demonstrate normal user-repo behavior, not this repo's internal authoring
     quirks.
   - Use the demo to show governance behavior, not just command inventory.
   Work to do:
   - Define the demo repository shape and its cleanup/disposability rules.
   - Show the minimal lifecycle end to end: install, config review/deploy,
     governed change, gate flow, workflow run, and gate close.
   - Include one or two concrete policy or managed-surface moments so users see
     repository governance rather than a glorified formatter run.
   - Include one lightweight custom-governance teaser so prospects can see that
     extension is real, not hypothetical.
   - Make the demo output align with the README claims and the `quickstart`
     guidance.
   - Add tests or proof flows that ensure the demo stays stable enough for
     repeatable evaluations.
   Done when:
   - A new user can run `devcovenant demo` and come away with a concrete mental
     model of the product.
   - The demo is credible in beta testing and client conversations.
   - The demo shows repository-level governance, not just isolated checks.

5. [not done] First custom-governance path
   Goal:
   - Turn custom policy/profile work from an underdocumented capability into a
     guided second-step onboarding path.
   Why this matters:
   - One of DevCovenant's strongest differentiators is that custom governance
     is first-class. That is also the part most likely to support downstream
     integration work, but it is currently much easier to discover as
     architecture than as a guided workflow.
   Scope boundaries:
   - Land this after the front door, docs map, `quickstart`, and `demo`.
   - Keep it focused on first custom-governance outcomes, not on exhaustive
     reference coverage.
   - Use the existing metadata model and layering, not ad hoc repo-specific
     shortcuts.
   Work to do:
   - Define the first custom profile path with one concrete example.
   - Define the first custom policy path with one concrete example.
   - Explain shadowing/materialization flow where builtin policy or profile
     customization is the right entry path.
   - Explain the metadata ownership model as the authoring API: what lives in a
     builtin descriptor, what lives in repo-owned custom metadata, and what is
     generated.
   - Make sure the guidance tells users which layer to edit and why, so the
     layered-ownership model reduces drift instead of confusing authors.
   - Connect this path back to the demo and marketing story: DevCovenant is not
     only installable; it is adaptable to repo-specific law.
   Done when:
   - A downstream repo author can follow one guided path to create or shadow
     governance without reading the whole architecture first.
   - The custom-governance path is strong enough to support beta testing,
     consulting, and integration conversations.
   - The docs explain the extension surface as a usable API, not just as an
     internal implementation detail.

## Validation Routine
- Open the gate before edits, clear start-gate complaints, and keep the
  repository clean at each step of the slice.
- After each onboarding/docs slice, rerun `gate --verify` until hook-induced
  mutations converge, then run `devcovenant run`, then `gate --close`.
- When wording or public positioning changes, verify README, package README,
  CLI help, docs map, and related lifecycle docs stay aligned.
- When new commands land, verify they work from source checkout and installed
  package paths.
- Keep `CHANGELOG.md` current for each slice and stage all changes before the
  final report.

## Exit Criteria
- The README explains DevCovenant clearly enough that a new reader can grasp
  the product before installation.
- The docs are discoverable from the README without installed-asset lookup or
  insider knowledge of the doc tree.
- `devcovenant quickstart` exists as a fixed canonical first-use command.
- `devcovenant demo` exists as a short evaluation path for beta testing and
  client conversations.
- The first custom-governance path is documented clearly enough to prove that
  DevCovenant is adaptable, not just installable.
- Public language across the README, package README, CLI, and docs consistently
  describes DevCovenant as repository governance rather than as a generic
  checker bundle.
