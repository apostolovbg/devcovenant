# Registry
**Last Updated:** 2026-03-31
**Project Version:** 1.0.1.dev1

## Overview
DevCovenant uses `devcovenant/registry/` for generated state.
Some of that state is tracked in git.
Some of it is local working state that helps DevCovenant manage an open or
recent work slice.

The practical question is simple:
are you looking for the repository's saved DevCovenant setup, or are you
looking for local evidence about recent command runs?

Use the tracked registry for the saved setup.
Use the runtime registry for local working state.
Do not hand-edit generated registry files.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the tracked registry.
It stores things such as:
1. the active policy settings DevCovenant resolved
2. project-governance state
3. the active profile inventory
4. managed-doc and generation state
5. the resolved workflow definition
6. tracked inventory information used for debugging and audits

Tracked-registry changes are normal when you change profiles, policy settings,
managed docs, workflow generation, packaging inputs, or other DevCovenant-owned
setup.
That is not noise by itself.
It is often the recorded result of a real repository change.

The tracked registry also records the resolved workflow definition.
That includes:
- the reserved anchors `start`, `mid`, and `end`
- the declared runs from active profiles
- the run order DevCovenant must enforce
- freshness and recording settings for those runs

If active profiles contribute workflow fragments or generated-file inputs, the
tracked registry records the resolved inputs that later render into generated
files such as `.gitignore`, `.pre-commit-config.yaml`, and
`.github/workflows/ci.yml` when a CI-owner profile is active.
That includes generated values such as `devcov_core_paths` and profile-owned
CI fragments, so registry diffs often reflect real scan-boundary or workflow
input changes.
It also records repo-owned custom policy metadata, including package mirror
contracts such as a shipped `devcovenant/requirements.lock` and
`devcovenant/licenses/**` that mirror canonical repo-root artifacts,
including the root `LICENSE`.

## Runtime Registry
`devcovenant/registry/runtime/` stores local working state such as:
- `gate_status.json`
- `workflow_session.json`
- latest-run pointers
- session snapshot companions

This is about local command history, not the saved repository setup.
It is the part cleaned by `devcovenant clean --registry` and by the registry
portion of `devcovenant clean --all`.
The tracked registry in `devcovenant/registry/registry.yaml` is preserved.

## Gate Status And Workflow Session
`gate_status.json` records gate-stage state and the pre-commit evidence tied to
those stages.

`workflow_session.json` records the declared runs for the open session,
whether they passed, and whether the results are still fresh.

`devcovenant gate --status` reads both files so it can tell you where the work
slice stands.

The tracked counterpart to that local state is the workflow section named
`workflow_contract` in `devcovenant/registry/registry.yaml`.
That section says what the workflow should be.
The runtime registry says whether the open or last session satisfied it.

## Managed Docs And Maps
Tracked managed-doc entries record which descriptor won for each target
path and whether that doc is enabled.
They do not try to copy full rendered document bodies into the registry.

That tracked state also feeds generated files such as:
- `AGENTS.md`
- `PROFILE_MAP.md`
- `POLICY_MAP.md`

## Which Registry Should You Read?
Read `devcovenant/registry/registry.yaml` when you need to know:
- which profiles are active
- which workflow runs exist
- which managed docs are enabled
- which profile contributed a generated input
- which saved DevCovenant settings are in force

Read `devcovenant/registry/runtime/` when you need to know:
- whether a gate session is open
- whether `mid` or `end` has been satisfied
- whether workflow evidence is still fresh
- which run failed most recently
- which run-log folder belongs to the active slice

## Practical Rule
If the question is "what should this repository be doing?", read the tracked
registry.
If the question is "what happened during this work slice?", read the runtime
registry and the run logs.
