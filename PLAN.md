# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Development Stance:** active-development
**Versioning Mode:** versioned
**Last Updated:** 2026-03-20
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->

Use this plan to track active implementation work. Keep items
dependency-ordered, factual, and current.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Writing Direction](#writing-direction)
4. [Active Work](#active-work)
5. [Validation Routine](#validation-routine)

## Overview
- Record durable requirements in `SPEC.md` when your repo uses SPEC.
- Record change history in `CHANGELOG.md`.
- Mark completed items as `[done]` and outstanding items as `[not done]`.
- Document behavior is strict:
  - missing docs may be created from assets/templates
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change
  - an empty managed block is still a managed block and must keep its
    `<!-- DEVCOV:BEGIN -->` / `<!-- DEVCOV:END -->` markers
- These same document rules must hold across `refresh`, `install`, `deploy`,
  `upgrade`, and gate-triggered refresh/autofix paths.
- This roadmap is now focused on three broad outcomes:
  - make DevCovenant easier to understand without prior insider knowledge
  - make configuration and managed-document behavior easier to maintain
  - make documentation more concrete, practical, and explanatory

## Workflow
- Work in dependency order unless an explicit blocker requires reordering.
- Keep each item concrete and testable.
- Update status in the same session when work lands.

## Writing Direction
- Write for learning humans, not only for experienced operators.
- Prefer concrete wording over insider shorthand.
- Replace vague terms such as `implementation`, `internals`, or
  `core paths` when a clearer phrase exists.
- Explain what a feature is, why it exists, what it changes, and when to
  use it.
- In `devcovenant/config.yaml`, make comments practical and explanatory
  without turning every key into a repetitive canned formula.
- Use examples when they remove ambiguity.
- Treat undocumented behavior, half-documented behavior, and
  hard-to-interpret wording as real product debt.

## Active Work
1. [done] Rename And Clarify Repository Integration Signals.
   Goal:
   - replace vague bootstrap and self-hosting names with names that explain
     what the setting is for
   Completed work:
   - replaced `devcov_core_include` with `developer_mode`
   - replaced `install.generic_config` with `install.config_reviewed`
   - made the review flag read naturally:
     - `false` after install
     - `true` once a human has reviewed the config and deploy may proceed
   - updated runtime behavior, tests, config comments, and user docs to use
     the new names
   Follow-through still expected in later items:
   - keep improving the wording around `developer_mode` so it says plainly
     that it is for developing DevCovenant itself rather than for normal
     user repos
2. [done] Build A Managed-Docs Service.
   Goal:
   - stop spreading document logic across `install`, `deploy`, `refresh`,
     policies, and special-case helpers
   Completed work:
   - created `devcovenant/core/services/managed_docs.py` as the shared owner
     for managed-doc descriptor loading, validation, seed adoption,
     preservation rules, and managed header/block rendering
   - rewired `refresh` to use that service for managed-doc selection and
     document synchronization instead of owning the document engine locally
   - rewired `install` to use the same service for first-install seed
     detection instead of keeping a separate managed-doc identity parser
   - rewired `managed_doc_assets` to use the same shared descriptor and
     document helpers so the integrity check follows the same contract as
     refresh/install
   - added direct service tests and kept the existing refresh/install/doc
     checks green against the centralized runtime
   Outcome:
   - document behavior now has one clear runtime owner
   - refresh/install/check flows call the same service instead of
     re-implementing core rules
   - future document features can build on one service boundary instead of
     adding new spaghetti paths
3. [done] Make Document Governance Fully Descriptor-Driven.
   Goal:
   - move shared document behavior into descriptors while keeping AGENTS as
     the one explicit special-case document
   Why this matters:
   - common docs should not need hidden code knowledge to gain or change
     headers, seed-import behavior, or asset-authority rules
   Completed work:
   - taught managed-doc descriptors to declare shared doc-engine behavior such
     as target path, project-governance header opt-in, seed import, and
     authoritative-source status
   - rewired the common managed-doc engine and `managed-doc-assets` policy to
     read those shared behaviors from descriptors instead of fixed doc lists
     and one-off header decisions
   - kept AGENTS explicit and special: its workflow block, policy block, and
     dedicated project-governance section remain AGENTS-specific runtime
     behavior rather than generic metadata for every managed doc
   Outcome:
   - ordinary managed docs now share one descriptor-driven contract
   - AGENTS stays the one deliberate exception instead of dragging the whole
     document engine into AGENTS-style complexity
4. [done] Support Optional And Custom Managed Docs.
   Goal:
   - make the document system useful beyond the fixed builtin set
   Why this matters:
   - repos need room for their own managed docs
   - builtin docs should not all be mandatory forever
   - the current system is too rigid for real-world variation
   Completed work:
   - extended the managed-doc runtime to resolve descriptors from the global
     asset root plus any active profile asset roots
   - kept `AGENTS.md` mandatory while letting other builtin docs be turned
     off by `doc_assets.autogen` / `doc_assets.user`
   - added custom managed-doc descriptors for `PROFILE_MAP.md` and
     `POLICY_MAP.md` under the `devcovrepo` profile and activated them in
     this repository
   - kept the same preservation rules for builtin and custom docs:
     missing docs may be created, empty and one-line docs may be replaced,
     and real authored body content is preserved outside managed regions
   - rewired authoritative managed-doc checks to follow enabled descriptors
     instead of a fixed builtin-only list
   Outcome:
   - optional builtin docs and custom managed docs now share one runtime path
   - repositories can add profile-owned managed docs without hacking the
     common document engine
   - `AGENTS.md` remains the one default managed doc DevCovenant truly
     depends on
5. [done] Document Initial Integration And Bootstrap Clearly.
   Goal:
   - make the first-time integration flow understandable to someone who does
     not already know DevCovenant
   Why this matters:
   - the current install/deploy/bootstrap story still makes too many readers
     infer hidden rules
   Work to do:
   - document empty-repo install clearly
   - document seeded-doc install clearly
   - document existing-repo install clearly
   - document config review and why deploy is blocked before review
   - document the first gate cycle and why the order matters
   - rewrite `devcovenant/config.yaml` comments so they are practical,
     concrete, and easy to follow
   Writing direction for this item:
   - explain what `developer_mode` is for in plain language
   - explain repo-only development paths and tests directly
   - remove insider wording that forces readers to reverse-engineer intent
   Done when:
   - a new user can understand the bootstrap path from the docs and config
     comments alone
   - the config file reads like a practical operating guide, not a vague
     metadata dump
6. [not done] Expand Documentation From Terse To Teaching-Quality.
   Goal:
   - turn the documentation set from terse operator notes into product
     documentation that teaches
   Why this matters:
   - readers should not need insider context to understand DevCovenant
   - "every word is familiar but the sentence is still unclear" is not
     acceptable documentation quality
   Work to do:
   - expand core docs with clearer explanations, examples, and rationale
   - replace compressed insider wording with plain language
   - connect related concepts so readers can see how install, deploy, docs,
     profiles, policies, and governance fit together
   - make the docs friendlier to people who are learning software workflow
     discipline while learning DevCovenant
   Done when:
   - the main docs explain both how to use DevCovenant and why the workflow
     exists
   - the docs stop assuming prior DevCovenant knowledge
   - the docs become concrete enough that users can operate the tool without
     guesswork

## Validation Routine
- Verify checks and tests pass.
- Verify generated artifacts are synchronized after refresh.
- Verify documentation and changelog were updated where behavior changed.
- Verify `devcovenant check` passes after the slice closes.
