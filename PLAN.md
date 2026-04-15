# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1b3
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-15
**DevCovenant Version:** 1.0.1b3

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the upstream hardening backlog for DevCovenant.
Keep items concrete, current, and tied to the canonical behavior we are
changing in DevCovenant itself.

## Table of Contents
1. [Overview](#overview)
2. [Workstreams](#workstreams)
3. [Exit Criteria](#exit-criteria)

## Overview
- Treat this plan as the reference backlog while we rewrite the environment,
  policy, metadata, and documentation contracts.
- Keep shipped builtin profiles generic and keep repo-owned custom copies
  explicit.
- Builtin policy and profile test coverage should stay non-discoverable until
  a repository explicitly materializes it under `tests/devcovenant/custom/**`.
- Keep the plan focused on DevCovenant behavior, not on user-repo project
  implementation details.
- Keep status markers current; mark completed workstreams `[x]` as soon as
  code and docs land so the backlog stays current.

## Workstreams
1. [x] Environment-neutral admin commands
   - `install`, `upgrade`, `refresh`, `custom`, `undeploy`, and
     `uninstall` should run from the interpreter or environment they are
     launched from and act on the repository or bench they point at.
   - `asset` should stay repo-bound: it must require a repository context, but
     it should not depend on a repo-local venv assumption.
   - Do not reintroduce a builtin `.venv` seed just to satisfy command wiring.
2. [x] Policy scope by repo type
   - For normal user repos, `devcovuser` should apply `no-raw-errors` and the
     code-style policies to `tests/**` and `devcovenant/custom/**`.
   - In the DevCovenant repo itself, the repo-owned `userproject` profile
     should widen the same policies to `tests/**` and `devcovenant/**`.
   - Keep the shipped baseline generic; repo-specific scope belongs in the
     repo-owned profile metadata.
   - The code-style set under discussion is `line-length-limit`,
     `name-clarity`, `docstring-and-comment-coverage`, `security-scanner`, and
     `no-raw-errors`.
3. [x] Silence and workflow messaging
   - Encode the silence rule in the managed AGENTS template and the repo
     `AGENTS.md`.
   - Make `gate --open` state that agents should work in silence and only
     provide a summary after work finishes.
   - After `gate --close`, stage all changes before any chat summary.
   - Keep mid-work narration out of the workflow.
4. [x] Version and metadata sync
   - Treat the canonical version file as the single source for both the project
     version and the DevCovenant version.
   - `version-governance` should validate only; `version-sync` should
     propagate version headers and versioned manifest fields automatically.
   - The bump flow should stay one move: change the canonical version file,
     then let `gate --verify` or refresh propagate the versioned outputs.
   - Make sure custom managed docs are included in the sync surface.
5. [x] Project metadata sync
   - Keep the canonical version file as the source of truth and let
     `version-sync` propagate it to project manifests, managed-doc
     `DevCovenant Version` headers, changelog headers, and other declared
     version-bearing targets.
   - Keep project name and description synchronized through the existing
     refresh and managed-doc rendering path, not a new policy surface.
   - Leave the metadata model declarative so future repo-owned identity
     fields stay configurable instead of hardcoded.
6. [x] Builtin policy/profile customization and test blueprints
   - Ship builtin policy and profile test coverage as non-discoverable
     blueprint metadata in the packaged descriptor tree rather than as
     default-discoverable `tests/**` modules.
   - Add `devcovenant custom --policy <name> --do|--undo` and
     `devcovenant custom --profile <name> --do|--undo` so a repository can
     promote a builtin policy or profile into repo-owned custom copies and
     retract those copies again.
   - `--do` should copy the builtin descriptor into `devcovenant/custom/...`,
     materialize the declared test mirrors under
     `tests/devcovenant/custom/...`, and then run refresh so the registry and
     generated outputs stay aligned.
   - `--undo` should delete the repo-owned custom copy, remove the materialized
     test mirrors, and run refresh so the builtin default becomes active
     again.
   - Add a repo-local custom policy that checks descriptor blueprints and the
     materialized test scripts stay synchronized after any change to either
     side.
   - Keep the materialized mirrors under `tests/devcovenant/custom/**` so they
     are discoverable in the repository only when the custom layer explicitly
     opts into them.
7. [x] Documentation growth tracking
   - Document how `documentation-growth-tracking` wires user-facing selectors
     and `doc_routes` into the doc update contract.
   - Show a generalized example that maps a source change, its keywords, and
     the target document set.
   - Explain how to point one keyword set at multiple docs and how the policy
     keeps documentation growth deliberate.
   - Keep the example generic enough to apply outside the current repo.
8. [x] Gate-open reminder
   - `gate --open` prints the silence reminder in normal and verbose mode.
   - The reminder says that AI agents work in silence and only provide a
     summary after work is complete.

## Exit Criteria
- Environment-sensitive admin commands no longer depend on a repo-local
  managed-environment assumption, except for `asset`, which remains repo
  bound.
- Policy scope matches repo ownership: shipped user-repo profiles stay
  generic, while the DevCovenant repo can widen scope locally through its
  repo-owned profile.
- Silence and work-summary rules are explicit in the managed template, the
  repo `AGENTS.md`, and the open-gate output.
- Version bumps remain one move: canonical version file first, sync output
  second.
- Project name and description propagate through the canonical metadata path
  into manifests and managed docs.
- Customization of builtin policies and profiles has a documented `custom`
  do/undo path that materializes and removes mirrored tests in
  `tests/devcovenant/custom/**` without making the builtin package's test
  blueprints discoverable by default.
- Documentation-growth tracking has a generalized wiring example that points
  real keywords at real docs.
