# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.1b2
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-04-08
**DevCovenant Version:** 1.0.1b2

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to track the upstream hardening backlog for DevCovenant.
Keep items concrete, current, and tied to the canonical behavior we are
changing in DevCovenant itself.

## Table of Contents
1. [Overview](#overview)
2. [Active Workstreams](#active-workstreams)
3. [Exit Criteria](#exit-criteria)

## Overview
- Treat this plan as the reference backlog while we rewrite the environment,
  policy, metadata, and documentation contracts.
- Keep shipped builtin profiles and repo-owned custom profiles distinct.
- We do not ship custom profiles.
- Keep the plan focused on DevCovenant behavior, not on user-repo project
  implementation details.

## Active Workstreams
1. Environment-neutral admin commands
   - `install`, `upgrade`, `refresh`, `undeploy`, and `uninstall` should run
     from the interpreter or environment they are launched from and act on the
     repository or bench they point at.
   - `asset` should stay repo-bound: it must require a repository context, but
     it should not depend on a repo-local venv assumption.
   - Do not reintroduce a builtin `.venv` seed just to satisfy command wiring.
2. Policy scope by repo type
   - For normal user repos, `devcovuser` should apply `no-raw-errors` and the
     code-style policies to `tests/**` and `devcovenant/custom/**`.
   - In the DevCovenant repo itself, the repo-owned `userproject` profile
     should widen the same policies to `tests/**` and `devcovenant/**`.
   - Keep the shipped baseline generic; repo-specific scope belongs in the
     repo-owned profile metadata.
   - The code-style set under discussion is `line-length-limit`,
     `name-clarity`, `docstring-and-comment-coverage`, `security-scanner`, and
     `no-raw-errors`.
3. Silence and workflow messaging
   - Encode the silence rule in the managed AGENTS template and the repo
     `AGENTS.md`.
   - Make `gate --start` state that agents should work in silence and only
     provide a summary after work finishes.
   - After `gate --end`, stage all changes before any chat summary.
   - Keep mid-work narration out of the workflow.
4. Version and metadata sync
   - Treat the canonical version file as the single source for both the project
     version and the DevCovenant version.
   - `version-governance` should validate only; `version-sync` should
     propagate version headers and versioned manifest fields automatically.
   - The bump flow should stay one move: change the canonical version file,
     then let `gate --mid` or refresh propagate the versioned outputs.
   - Make sure custom managed docs are included in the sync surface.
5. Project metadata sync
   - Add or define a `project-metadata-sync` policy if `version-sync` is not
     the right home for non-version metadata.
   - Sync project name and description into `pyproject.toml` and any other
     manifests that expose matching keys.
   - Keep the policy extensible for other canonical identity fields such as
     homepage, repository, support, license, and authors where those keys
     exist.
   - Mirror the same canonical metadata into managed docs when a doc
     descriptor exposes those fields.
6. Builtin policy and profile scaffolding
   - Make builtin policy or profile copies obtainable as repo-owned custom
     copies with their corresponding test mirrors.
   - Copy tests into `tests/devcovenant/custom/**` using a naming scheme that
     keeps them out of default user-repo discovery unless explicitly mirrored.
   - Keep builtin tests in the builtin tree and custom tests in the custom
     tree; do not ship custom profiles.
   - The goal is to make customization repeatable, not to duplicate the builtin
     tree manually.
7. Documentation growth tracking
   - Document how `documentation-growth-tracking` wires keywords to documents
     through `doc_routes`.
   - Show a generalized example that maps a source change, its keywords, and
     the target document set.
   - Explain how to point one keyword set at multiple docs and how the policy
     keeps documentation growth deliberate.
   - Keep the example generic enough to apply outside the current repo.
8. Gate-start reminder
   - `gate --start` should print the silence reminder in normal and verbose
     mode.
   - The reminder should say that AI agents work in silence and only provide a
     summary after work is complete.

## Exit Criteria
- Environment-sensitive admin commands no longer depend on a repo-local
  managed-environment assumption, except for `asset`, which remains repo
  bound.
- Policy scope matches repo ownership: shipped user-repo profiles stay
  generic, while the DevCovenant repo can widen scope locally through its
  repo-owned profile.
- Silence and work-summary rules are explicit in the managed template, the
  repo `AGENTS.md`, and the start-gate output.
- Version bumps remain one move: canonical version file first, sync output
  second.
- Project name and description propagate through the canonical metadata path
  into manifests and managed docs.
- Customization of builtin policies and profiles has a documented path that
  also carries test mirrors into the custom tree.
- Documentation-growth tracking has a generalized wiring example that points
  real keywords at real docs.
