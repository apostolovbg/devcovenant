# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1b5
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-27
**DevCovenant Version:** 1.0.1b5

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the b5 product slice.
The b5 slice closes the current audit findings around profile taxonomy,
custom-governance docs, demo quality, quickstart's role, CLI/help wording,
main-branch link policy, SPEC alignment, and UTC-safe proof data.
It is not about adding more surface area for its own sake. It is about
making DevCovenant understandable to outsiders without turning the README
into marketing copy or pretending that a quickstart command is the real
onboarding path.

## Table of Contents
1. [Overview](#overview)
2. [Planning Boundaries](#planning-boundaries)
3. [Delivery Order](#delivery-order)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)
6. [Exit Criteria](#exit-criteria)

## Overview
- Treat this plan as the current roadmap for the next legibility pass.
- Keep the front door technical: explain the product, the repository-level
  contract, and the custom-governance model without drifting into a sales
  page.
- Treat `devcovuser` as the always-active baseline for every DevCovenant
  user, and treat `userproject` as the repo-specific starter layer; do not
  blur those roles.
- Make the demo the real evaluation surface. It should show repository
  governance, owned fixes, and custom shadowing in one coherent path.
- Keep `quickstart` secondary. If it remains at all, it should be a terse,
  static operator reminder rather than a second onboarding story.
- Make the custom-governance docs explain what actually gets copied,
  shadowed, materialized, and undone.
- Keep all repository-facing links on the `main` branch absolute URL; do
  not use tag-based doc links or stale branch refs in README, package docs,
  or generated surfaces.
- If the shipped public command surface changes, update `SPEC.md` instead of
  leaving command or role drift behind.
- Update status markers in the same session when work lands so this file
  stays executable as a real roadmap.

## Planning Boundaries
- The root `README.md` and `devcovenant/README.md` must keep the same core
  story and section order. The root README may add repo-only notes, but it
  must not become a different document.
- The README stays a technical front door. It should explain what DevCovenant
  is, why repository governance matters, and where the operator should go
  next, but it should not become a pure marketing page.
- Do not add a separate onboarding document in b5. The front door, demo, and
  custom-governance docs must do the onboarding work together.
- `devcovenant demo` is the evaluation path for people who want to see the
  tool work. It should demonstrate a realistic governance problem, an owned
  fix, and a successful close, not a toy smoke test that looks like unit
  tests.
- The demo may use a disposable repository, but it must not leave a temp repo
  behind and it must not depend on hidden manual inspection to make sense.
- `devcovenant quickstart` may remain only if it is obviously lightweight,
  static, and secondary. It must not pretend to be a full onboarding flow or
  compete with `demo`.
- Custom-governance docs must stay metadata-driven. They should describe the
  extension surface the way the code uses it, not with hardcoded prose that
  can drift from the descriptors.
- `devcovuser` is the always-active user baseline for every user; `userproject`
  is the repo-specific starter profile, not a language translator profile or
  a blanket test-bearing layer.
- Only blueprint-bearing policy/profile families materialize mirrored tests;
  skeleton profiles such as `userproject` do not imply a test mirror.
- All repo-facing markdown and image links must point to the `main` branch
  absolute URL, not to tags or stale branch names.
- Keep `SPEC.md` honest about any shipped public command or role changes so
  the source-of-truth command surface stays aligned with the docs.

## Delivery Order
1. Normalize the profile taxonomy and public vocabulary so `devcovuser`,
   `userproject`, language profiles, and tooling profiles are not blurred.
2. Expand the custom-governance docs and align `SPEC.md` with the shipped
   command surface and materialization rules.
3. Replace the demo with a meaningful governance proof and UTC-safe proof
   data.
4. Recast the front door as a technical introduction plus route map.
5. Demote `quickstart` to a secondary reminder or remove it from the
   onboarding story.
6. Normalize repo-facing links to `main` and reconcile the installed,
   documentation, and test surfaces.

## Active Work
1. [done] Normalize the profile taxonomy and public vocabulary
   Goal:
   - Make the always-active `devcovuser` baseline, the repo-specific
     `userproject` starter layer, and the language/tooling profiles distinct
     in docs and command wording.
   Why this matters:
   - Downstream users need a single vocabulary for which layer is baseline,
     which layer is repo-owned starter, and which profiles may carry
     translator modules or generated test mirrors. The public surface and
     `SPEC.md` have to match that vocabulary.
   Scope boundaries:
   - Treat `devcovuser` as the always-active user baseline for every
     DevCovenant user.
   - Treat `userproject` as the skeleton repo-specific profile layer.
   - Do not describe `userproject` as a generic test-bearing layer;
     mirrored tests belong only to blueprint-bearing policy/profile families
     that actually ship them.
   - Keep public command wording honest about `demo` and `quickstart`; if
     the shipped command surface changes, `SPEC.md` must be updated instead
     of left stale.
   - Keep repository-facing links on the `main` branch absolute URL, not
     tag-based URLs.
   Work to do:
   - Align the root README, package README, CLI help, and `SPEC.md`
     terminology with the taxonomy.
   - Clarify which profiles may carry translators and which profiles
     intentionally do not need tests.
   - Replace any wording that implies `userproject` is the downstream
     baseline or a translator-bearing language profile.
   Done when:
   - A reader can tell, from one pass, what `devcovuser`, `userproject`,
     language profiles, and tooling profiles do.
   - The public command and doc vocabulary no longer contradict `SPEC.md`.

2. [done] Expand the custom-governance docs into the real operator guide
   Goal:
   - Make the extension surface understandable on its own so custom policy
     and profile work is a guided path instead of an architecture puzzle.
   Why this matters:
   - Custom governance is one of DevCovenant's strongest differentiators and
     one of the most likely integration points for downstream repos and
     consulting work. The docs should explain the path clearly enough that a
     repo author can start there without reverse-engineering the code.
   Scope boundaries:
   - Keep the explanation metadata-driven and truthful to the materialization
     model.
   - Do not invent new commands, extra file families, or hidden path rules.
   - Keep builtin and custom surfaces distinct: builtin blueprints stay in the
     shipped tree, while repo-owned copies and mirrors live under the custom
     surface and `tests/devcovenant/custom/**`.
   - Do not imply that skeleton profiles such as `userproject` need mirrored
     tests or translator modules.
   Work to do:
   - Expand `devcovenant/custom/README.md` into a first-stop extension
     overview that explains shadowing, materialization, and the standard
     downstream layer stack.
   - Expand `devcovenant/custom/profiles/README.md` so it explains what a
     copied builtin profile contains, why `userproject` is the common first
     repo-owned starter layer, and where `python` or `python_venv` fit.
   - Expand `devcovenant/custom/policies/README.md` so it explains builtin
     shadowing, policy ownership, and the test-blueprint mirror that appears
     only when a builtin policy is promoted into the custom tree and ships a
     blueprint.
   - Expand `devcovenant/docs/customization.md` with one concrete first custom
     profile path and one concrete first custom policy path.
   - Update the surrounding docs (`docs/policies.md`, `docs/profiles.md`,
     `docs/config.md`, and any routing pages that point there) so the
     custom-governance story is discoverable from multiple entry points.
   - Explain clearly which layer to edit, which layer to inherit, and which
     materialized files are generated when a builtin policy or profile is
     shadowed.
   Done when:
   - A downstream repo author can answer "which file do I edit first?" for a
     profile or policy customization without guessing.
   - The docs explain `devcovenant custom --policy NAME --do` and
     `devcovenant custom --profile NAME --do` as materialization commands,
     not as magical side effects.
   - The docs clearly say that builtin test blueprints are shipped as
     descriptors or YAML-managed metadata and materialize into custom test
     mirrors only when the repo opts into the shadow copy.

3. [done] Replace the demo with a real governance proof
   Goal:
   - Show DevCovenant doing actual governance work in a short, repeatable
     scenario that a skeptic can follow.
   Why this matters:
   - The current demo shape is too close to a test run. It proves that the
     commands execute, but it does not strongly prove why DevCovenant is
     different from a glorified validation harness.
   Scope boundaries:
   - Keep the demo disposable and safe.
   - Do not keep the temporary repository after exit.
   - Use a normal-user-repo story, not DevCovenant's own authoring quirks.
   - Keep the transcript concise enough that a human can follow the point of
     the demo without reading a test log.
   Work to do:
   - Define one realistic drift scenario that produces a meaningful complaint
     or mismatch.
   - Show the owned fix path for that problem through the repo's governance
     files instead of by manual surgery.
   - Include one custom-governance moment so the demo proves that
     `devcovenant custom` and mirrored tests are real, not hypothetical.
   - Show the normal lifecycle in a way that highlights the product story:
     install, review/deploy, gate open, verify, run, gate close.
   - Generate any changelog/date fixtures from current UTC data or avoid
     hardcoded dated entries altogether so the proof does not rot at midnight.
   - Print a short transcript of the interesting state transitions so the
     output reads like a proof, not like a unittest session.
   Done when:
   - A new user can run `devcovenant demo` and see a concrete governance
     problem, the repository-owned fix path, and a clean close.
   - The demo proves repository-level governance and custom extensibility
     rather than just test execution.
   - `tests/devcovenant/test_demo.py` exercises the governance story instead
     of only asserting helper call order.

4. [done] Recast the front door as a technical introduction plus route map
   Goal:
   - Keep the README useful to someone who has never heard the phrase
     "repository governance framework" without making it read like a pitch
     deck.
   Why this matters:
   - DevCovenant's value is easiest to miss when the first page assumes the
     reader already knows the vocabulary. The front door has to explain the
     product category, the repository-level contract, and the layered
     ownership model before it asks the reader to install anything.
   Scope boundaries:
   - Keep root and package READMEs aligned on the same core story.
   - Keep repo-only notes in the root README only.
   - Do not turn the README into a separate marketing artifact.
   - Do not add a separate onboarding document as a substitute for a weak
     README.
   - Keep root and package README links on the `main` branch absolute URL,
     not tag-based URLs.
   Work to do:
   - Explain DevCovenant in plain language as a repository governance
     framework, not just a linter or a prompt pack.
   - Surface the strongest differentiators early: repo-owned law, layered
     ownership, metadata-driven extension, model/account/IDE/machine
     independence, and dogfooding.
   - Keep the install/deploy/lifecycle material after the value proposition
     instead of burying the product explanation under ceremony.
   - Route readers into the custom-governance docs and the demo without
     forcing them to discover the path by trial and error.
   Done when:
   - A serious outsider can read the README once and understand what kind of
     tool DevCovenant is, why it exists, and where to go next.
   - The README still feels like a technical repository guide, not a
     marketing landing page.

5. [done] Demote `quickstart` to a secondary reminder or remove it from the
   onboarding story
   Goal:
   - Stop treating `quickstart` as the thing that teaches people DevCovenant
     when the README and demo are already meant to do that job.
   Why this matters:
   - A static quickstart can be useful as a reminder, but it does not justify
     carrying the onboarding burden if it merely repeats the README.
   Scope boundaries:
   - If the command remains, it must stay non-interactive and deterministic.
   - Do not make it state-aware, environment-aware, or location-aware.
   - Do not turn it into a wizard or a pseudo-demo.
   - Do not let it compete with the demo as the evaluation path.
   Work to do:
   - Decide whether the command remains as a terse operator reminder or is
     reduced further.
   - If it remains, shorten it so it is clearly a small utility instead of a
     second onboarding flow.
   - Update CLI help and docs so the command is presented honestly.
   - Remove duplicate onboarding claims from any doc surface that still gives
     `quickstart` too much weight.
   Done when:
   - Users do not need `quickstart` to understand DevCovenant.
   - The command, if kept, is obviously secondary to the README and demo.
   - The docs no longer imply that `quickstart` is the main evaluation path.

6. [done] Normalize repo-facing links to `main` and reconcile the installed,
   documentation, and test surfaces
   Goal:
   - Keep every repository-facing link on the `main` branch absolute URL and
     reconcile the public docs, installed package docs, and tests after the
     b5 story changes.
   Why this matters:
   - The product story only helps if the same story appears everywhere a user
     is likely to look, and the link policy has to stay uniform so users do
     not hit tag-specific or stale branch URLs.
   Scope boundaries:
   - Keep the source of truth in repository docs and code, not in ad hoc
     release notes or one-off explanations.
   - Respect the forward-only compatibility policy when deciding whether to
     preserve or remove old wording.
   Work to do:
   - Replace any branch- or tag-specific links in the root README, package
     README, custom docs, installation docs, and generated docs with
     absolute `main` URLs.
   - Re-audit the root README, package README, custom docs, demo, quickstart,
     CLI help, and any generated docs for consistent language.
   - Update tests or proof flows if the public story of a command changes.
   - Keep the changelog current for each completed slice.
   - Confirm the plan still matches `SPEC.md` after the docs are rewritten.
   Done when:
   - The public story is consistent across the repository and installed
     package.
   - No command or doc surface is overstating its role in onboarding.
   - No repository-facing markdown or image link points to a tag or stale
     branch name.

## Validation Routine
- Open the gate before edits, clear start-gate complaints, and keep the
  repository clean at each step of the slice.
- After each b5 docs or command slice, rerun `gate --verify` until any
  hook-induced mutations converge, then run `devcovenant run`, then
  `gate --close`.
- When wording or public positioning changes, verify the root README,
  package README, custom-governance docs, CLI help, `SPEC.md`, and related
  lifecycle docs stay aligned.
- When link policy changes, verify the root README, package README, custom
  docs, generated docs, and image links all resolve to the `main` branch
  absolute URL.
- When the demo or quickstart changes, verify the source checkout, wheel
  install, and `pipx` install paths all still tell the same story.
- Keep `CHANGELOG.md` current for each slice and stage all changes before the
  final report.

## Exit Criteria
- b5 is ready when an outsider can distinguish `devcovuser` from
  `userproject`, find the custom-governance docs without guesswork, see
  `demo` prove a real governance story with UTC-safe data, and stop
  depending on `quickstart` as the primary onboarding path.
- The README remains technical, the demo remains a proof, and the custom
  docs explain the extension surface as a usable API rather than as an
  internal implementation detail.
- All repository-facing links point to the `main` branch absolute URL, not
  to tags or stale branch refs.
