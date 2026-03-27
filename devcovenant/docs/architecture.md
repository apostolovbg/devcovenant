# DevCovenant Architecture
**Last Updated:** 2026-03-27
**Project Version:** 1.0.0

## Overview
This document explains how DevCovenant is built.
Use it when you need to understand the runtime layers, the core invariants,
and the places where the product surface is intentionally stable.

If you only need to operate the tool, start with `README.md`,
`installation.md`, `config.md`, and `workflow.md` first.

## Layered Runtime
DevCovenant keeps its kernel code under:

- `devcovenant/core/flow`

- `devcovenant/core/runtime`

- `devcovenant/core/services`

- `devcovenant/core/lib`

- `devcovenant/core/contracts`

The practical split is:

- `flow`

  Lifecycle orchestration such as gate phases, refresh ownership, command
  sequencing, and workflow-evidence validation.

- `runtime`

  Execution, output, run logging, runtime evidence paths, and command
  dispatch.

- `services`

  Shared runtime services such as metadata resolution, policy execution,
  managed docs, and tracked-registry handling.

- `lib`

  Supporting helpers that are reused across the runtime.

- `contracts`

  Typed contract objects and static contract definitions used by the runtime.

## Evidence Flow
DevCovenant is built around evidence, not only around checks.
The normal flow is:

1. repository files are collected and interpreted
2. policies and core invariants evaluate that state
3. commands record evidence artifacts about what happened

The important evidence surfaces are:

- per-run log folders under `devcovenant/logs/`

- tracked registry state under `devcovenant/registry/registry.yaml`

- runtime session state under `devcovenant/registry/runtime/`

- managed policy and governance output in `AGENTS.md`

## Core Invariants Versus Policies
Not every rule in DevCovenant is a policy.

Core invariants are DevCovenant-owned runtime boundaries.
They define behavior the engine itself depends on, such as:

- gate evidence sequencing

- repository structure expectations

- DevCovenant integrity checks

Customizable policies are the repository-facing enforcement units.
They can be enabled, disabled, and tuned through config and profiles.
Examples include changelog coverage, line length, and dependency management.

That split matters because it keeps non-optional engine behavior out of the
same conceptual bucket as repo-specific governance choices.
It also means the package artifact has to ship the core invariant descriptor
YAMLs under `devcovenant/core/contracts/invariants/`, because deploy and
other runtime paths resolve those descriptors from the installed package, not
from a source-only checkout assumption.

The implementation ownership now follows that split more honestly as well.
`devcovenant/core/flow/gate_status_validation.py` and
`devcovenant/core/flow/workflow_validation.py` own workflow-evidence parsing
and enforcement, while `devcovenant/core/services/integrity_validation.py`
and `devcovenant/core/services/structure_validation.py` stay focused on
descriptor/registry integrity and required-repo-shape checks.
That keeps flow truth out of service-layer "guard" islands without changing
the stable invariant ids that repositories already know.

## Workflow Contract Model
Workflow structure now has its own contract instead of being inferred from
customizable policy state.

Core owns the reserved workflow anchors:

- `start`
- `mid`
- `end`

Profiles own declared workflow phases between `mid` and `end`.
Those phase declarations define:

- whether a phase is enabled or required
- phase ordering metadata
- how the phase runs
- the success contract used to mark it complete
- summary/reporting metadata used when the phase is recorded

That reporting metadata is now declarative as well.
If a phase needs richer behavior, profiles declare it through recording hooks
such as:

- `output_mode_config_field`
- `event_adapter_group`
- `write_runtime_profile`

Core then executes the same generic workflow-phase machinery for every phase.
It does not branch on `phase_id == "tests"` to decide whether output,
event capture, or run-profile artifacts should exist.

That split is intentional.
Policies can still require things about source layout or test structure, but a
customizable policy should not be the thing that makes gate mechanics work at
all.

## Policy Runtime Model
Policies combine three things:

1. descriptor metadata
2. runtime check code
3. optional autofix behavior

Policy checks stay read-only.
Mutation belongs either to:

- autofixers during an autofix-enabled check path

- explicit policy commands when a human runs them deliberately

That boundary is intentional.
Checks report.
Autofix fixes.
Commands perform explicit operations.

Workflow phases are different.
They are recorded execution obligations, not policy checks.
That is why core owns `devcovenant run` and `devcovenant phase run <id>`,
while profiles declare the actual required phases under the tracked workflow
contract.

## Managed Docs And Generation
Managed documents are a first-class part of the architecture.
The shared managed-doc runtime owns:

- descriptor parsing

- descriptor validation

- preservation rules

- managed header rendering

- managed block rendering

- adoption of compatible seeded docs

- replacement of known old generic scaffolds

The key preservation rule is stable:
missing docs can be created, empty docs can be replaced, one-line docs can be
replaced, and otherwise only managed headers and managed blocks should change.
The AGENTS-specific block scaffolding and rendering helpers now live under
`devcovenant/core/lib/agents_blocks.py`, which keeps descriptor loading in the
service layer while moving managed-block rendering out of the services
grab-bag.
The same ownership test now applies inside the engine:
metadata resolution remains in `devcovenant/core/services/metadata.py`
because it is a real cross-cutting domain service, while event-adapter loading
and policy-check summary rendering moved into `core/runtime/` because those
modules are about execution-time recording and output. The same split now
applies to namespaced policy-command dispatch: command-definition parsing and
runtime-action invocation live in `core/runtime/` because they are execution
plumbing, while the policy engine remains in `core/services/` because it still
owns policy meaning and orchestration.

## Profiles, Translators, And Assets
Profiles describe repository shape.
They can contribute:

- suffix inventories

- metadata overlays

- managed assets

- workflow phases

- pre-commit fragments

- translator declarations

Translators are owned by language profiles.
They keep policies language-agnostic by translating source into normalized
units instead of forcing each policy to parse each language separately.
The profile-registry service resolves those profile inventories in a
deterministic sorted order before tracked registry state is written, so the
same repo does not rewrite generated files differently on macOS, Linux, or
Windows just because the filesystem returned directories in a different order.

## Registry Ownership
The tracked registry now has to represent two different kinds of truth:

- durable resolved contract state
- runtime session evidence

Tracked contract state lives in `devcovenant/registry/registry.yaml`, including
`workflow_contract`.
That section records the reserved anchors, the declared phases resolved from
active profiles, and which phase ids are currently required.
The resolver for that tracked workflow contract now lives in
`devcovenant/core/flow/workflow_contract.py`, which keeps phase-contract
normalization on the workflow side instead of leaving it in the services
grab-bag.
Tracked path ownership now lives in
`devcovenant/core/services/tracked_registry.py`.

Runtime workflow state lives in
`devcovenant/registry/runtime/workflow_session.json`.
That file records:

- the active or last session id
- anchor results
- declared phase results
- last-run session bindings
- phase freshness snapshots

`gate_status.json` still exists beside it, but it now focuses on gate lifecycle
and pre-commit evidence instead of trying to be the whole workflow model.
Runtime path ownership for those evidence files lives in
`devcovenant/core/runtime/registry.py`.

Policy-local runtime state should stay under runtime-owned namespaces such as
`devcovenant/registry/runtime/` unless a policy explicitly declares another
working location.
That keeps mutable state out of policy source folders and preserves the source
versus runtime boundary.

## Output And Error Boundaries
All user-visible command output goes through the runtime output boundary.
That keeps console behavior, run logs, and normalized errors aligned.

Unhandled runtime exceptions are normalized into explicit user-facing errors,
while the run logs keep the deeper diagnostic detail.

Cleanup shows how the layers cooperate:

- profile and config metadata describe cleanup targets

- the cleanup service resolves and prunes those targets

- runtime context injects protected paths such as the active clean run folder

- managed-environment runtime contributes generic environment-safe roots

- execution summary rendering records what was removed and which protected
  roots were skipped

That keeps deletion rules configurable without letting cleanup destroy the
toolchain or its own active evidence.

## Contract Map
The stable contract surfaces live in these docs:

- `installation.md`
  for lifecycle commands and first-time activation
- `workflow.md`
  for gate sequence and run-artifact behavior
- `config.md`
  for the public config surface and project-governance settings
- `profiles.md`
  for profiles, assets, overlays, and translators
- `policies.md`
  for policy descriptors, runtime actions, policy commands, and autofix
  boundaries
- `refresh.md`
  for refresh ownership and managed-doc behavior
- `registry.md`
  for tracked and runtime registry state

## What Should Stay Stable
The exact implementation may continue to change, but these ideas should stay
stable:

- the gate workflow remains the backbone of governed repository work

- evidence artifacts remain first-class output

- core invariants remain separate from customizable policies

- managed docs remain descriptor-driven and preservation-aware

- profiles remain the main reusable metadata and asset surface

- workflow structure remains a formal tracked/runtime contract instead of an
  accidental side effect of enabled policies
