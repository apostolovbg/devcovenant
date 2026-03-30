# Registry
**Last Updated:** 2026-03-30
**Project Version:** 1.0.1

## Overview
This document is the normative home for the registry contract.
Keep `devcovenant/docs/contracts.md` nearby when you need the stable document
map for the rest of the package surfaces.

DevCovenant uses `devcovenant/registry/` for generated state.
Some of that state is tracked and durable.
Some of it is runtime-local and disposable.
Use this page when you need to answer one practical debugging question:
is the thing I am looking at part of the repository's resolved contract, or is
it only local evidence about recent command runs?

Working rule:
read the registry when you need to understand resolved state,
but do not hand-edit generated registry files.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the tracked registry.
It stores deterministic governance state such as:

1. resolved policy metadata
2. active project-governance state
3. active profile inventory
4. managed-doc and generation state
5. profile-provided generation fragments
6. the resolved `workflow_contract`
7. tracked inventory and resolution traces used for auditing and debugging

Packaging and policy-runtime changes can legitimately update tracked-registry
hashes even when the visible behavior change is elsewhere.
That is normal evidence of a real contract change, not registry noise.

Tracked registry state records the resolved workflow contract as well.
That includes:
- the reserved anchors `start`, `mid`, and `end`
- the declared runs coming from active profiles
- the run ids the engine must enforce
- the validated ordering produced from `after`, `before`, and `order`
- the freshness rules and recording hooks attached to those runs

If active profiles contribute generated workflow fragments or proof-job
fragments, the tracked registry records the resolved workflow metadata they
contribute.
That includes generated GitHub Actions job structure and action-version
inputs and workflow-level environment values that later render into
`.github/workflows/ci.yml`.
If active profiles contribute managed-environment metadata, tracked state
records that resolved execution contract too.
That includes the selected interpreter expectations, command templates such as
`{current_python}` / `{managed_python}`, and cleanup-protected roots the
runtime actually uses.

Separately from tracked registry state, the same refresh pass may also
regenerate output surfaces such as `.gitignore`, `.pre-commit-config.yaml`,
and `.github/workflows/ci.yml`.
Those files are related to the tracked registry, but they are not themselves
embedded as giant blobs inside the registry.
The registry records the resolved inputs and ownership, while the generated
files carry the rendered surface.
That includes active-profile `ignore_dirs` contributions.
Refresh records them in tracked profile metadata before rendering shared
exclude surfaces such as `.gitignore` and `.pre-commit-config.yaml`.

The helper ownership matches that split:
- `devcovenant/core/services/tracked_registry.py` owns tracked-registry paths
  and tracked-registry document I/O
- `devcovenant/core/services/policy_registry.py` owns policy descriptors,
  script resolution, and tracked policy state
- `devcovenant/core/services/manifest_inventory.py` owns tracked inventory
  persistence for required paths plus the available-doc and enabled-doc
  inventory views
- `devcovenant/core/flow/workflow_contract.py` owns workflow-contract
  normalization and run resolution

Commit tracked-registry changes when they are the result of real repo changes.

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:
- `gate_status.json`
- `workflow_session.json`
- latest-run pointers
- session snapshot companions

This state is about current or recent command history, not about the stable
repo contract.
It is also the registry surface cleaned by `devcovenant clean --registry`
and by the registry portion of `devcovenant clean --all`.
Tracked registry state in `devcovenant/registry/registry.yaml` is preserved.

The runtime path contract is configured through ordinary config sections,
primarily `paths.*`.
That means `gate_status_file` and `workflow_session_file` are just runtime path
knobs in config, not a separate engine metadata family.
They must still remain repo-relative paths under
`devcovenant/registry/runtime/` so runtime evidence stays disposable and local.

## Gate Status And Workflow Session
`gate_status.json` is the short gate lifecycle ledger.
It records gate start/end state and the pre-commit evidence those anchors
require.

`workflow_session.json` records the declared workflow runs for the active
session, their pass/fail state, their freshness evidence, and the snapshots
used to decide whether a run is still fresh.
`gate --status` reads both files so it can report the real public lifecycle
stage, including `mid`, without pretending the workflow is only
`start -> run -> end`.

The tracked counterpart to that runtime state is `workflow_contract` in
`devcovenant/registry/registry.yaml`.
That tracked section records the resolved anchors, run order, and run metadata.
The runtime registry records whether the current or last session actually
satisfied that contract.

## Managed Docs And Maps
Tracked managed-doc entries record descriptor paths, enablement,
authoritative/import-source state, governance-header flags, and body
fingerprints.
They do not try to duplicate full rendered document bodies.

Tracked inventory is separate from tracked managed-doc descriptors:
- managed-doc entries describe the winning descriptor for each target path
- tracked inventory records which managed docs are available and which are
  enabled for this repo

That same tracked state also feeds generated governance surfaces such as:
- `AGENTS.md`
- `PROFILE_MAP.md`
- `POLICY_MAP.md`

For `AGENTS.md`, the runtime renders the managed workflow block, the
project-governance block, and the resolved policy block.
The AGENTS helper ownership is:
- `devcovenant/core/lib/agents_blocks.py` for policy-block rendering helpers
- `devcovenant/core/services/managed_docs.py` for managed-doc sync and block
  placement
- `devcovenant/core/services/project_governance.py` for project-governance
  section content

## When To Read Which Surface
Read `registry.yaml` when you need to understand:
1. resolved metadata
2. active profiles
3. managed-doc ownership and descriptor state
4. which workflow runs are configured and why
5. which profile contributed a generated workflow fragment or other generation
   input
6. which cleanup targets came from profiles versus which protected roots came
   from runtime-owned sources

Read `registry/runtime/` when you need to understand:
- whether a gate session is open
- whether `mid` or `end` has been satisfied
- whether workflow evidence is fresh
- which run failed most recently
- which run log folder belongs to the active slice

## Practical Debug Rule
If the question is "what is the repo contract?", read the tracked registry.
If the question is "what happened during this slice?", read the runtime
registry and run logs.

That split is what keeps DevCovenant debuggable instead of turning every file
under `devcovenant/registry/` into one undifferentiated pile of state.
