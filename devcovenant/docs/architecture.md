# DevCovenant Architecture
**Last Updated:** 2026-03-31
**Project Version:** 1.0.1

## Overview
This document explains how DevCovenant is put together.
Use it when you need the internal ownership map rather than the day-to-day
operator flow.
If you only need to use the product, start with `README.md`,
`installation.md`, `config.md`, and `workflow.md` first.

## Core Layers
The main code lives under:

- `devcovenant/core/flow`
- `devcovenant/core/runtime`
- `devcovenant/core/services`
- `devcovenant/core/lib`
- `devcovenant/core/contracts`

In plain terms:

- `flow`
  gate orchestration, refresh ownership, workflow-definition resolution, and
  workflow validation

- `runtime`
  process execution, output handling, run logs, runtime ledgers, and
  namespaced command dispatch

- `services`
  settings resolution, policy execution, managed docs, tracked registry work,
  project governance, structure validation, and integrity validation

- `lib`
  shared helpers reused across the runtime

- `contracts`
  shared data objects used by the other layers

## Built-In Engine Checks
DevCovenant always runs three engine-level checks:

- workflow validation in
  `devcovenant/core/flow/workflow_validation.py`
- integrity validation in
  `devcovenant/core/services/integrity_validation.py`
- structure validation in
  `devcovenant/core/services/structure_validation.py`

These are part of the engine itself.
They are not optional inventory policies.
Repository-tweakable settings for them live in ordinary config sections such
as `paths`, `workflow`, and `integrity`.

## Evidence Flow
DevCovenant is built around recorded evidence, not only around pass/fail
checks.
The normal flow is:

1. collect and interpret repository files
2. run engine checks and configured policies
3. record evidence about what happened

The main evidence locations are:

- per-run log folders under `devcovenant/logs/`
- tracked registry state in `devcovenant/registry/registry.yaml`
- runtime session state under `devcovenant/registry/runtime/`
- managed governance output in `AGENTS.md`

## Workflow Ownership
Workflow shape is saved separately from policy state.
Core owns the reserved anchors:

- `start`
- `mid`
- `end`

Profiles own the declared workflow runs between `mid` and `end`.
Those runs define:

- whether a run is enabled or required
- how it executes
- how success is recorded
- how freshness is checked
- which reporting hooks apply

The resolver for that saved workflow definition lives in
`devcovenant/core/flow/workflow_contract.py`.
The validator for recorded workflow evidence lives in
`devcovenant/core/flow/workflow_validation.py`.

## How Policies Run
Policies combine three things:

1. descriptor settings and prose
2. runtime check code
3. optional autofix or command entry points

Checks stay read-only.
Mutation belongs either to:

- autofix during an autofix-enabled path
- explicit policy commands when an operator runs them deliberately

Checks report.
Autofix fixes.
Commands perform deliberate operations.

## Managed Docs And Generation
Managed documents are built outputs.
The managed-doc service owns:

- descriptor parsing and validation
- managed header rendering
- managed block rendering
- adoption and import rules for compatible docs
- preservation rules for authored content

The stable preservation rule is:
missing docs can be created, empty docs can be replaced, one-line docs can be
replaced, and otherwise only managed headers and managed blocks should change.
AGENTS-specific block refresh lives in
`devcovenant/core/lib/agents_blocks.py`, which owns only the generated policy
block.

## Profiles, Translators, And Assets
Profiles describe repository shape.
They may contribute:

- suffix inventories
- settings overlays
- workflow runs
- managed assets
- pre-commit fragments
- CI fragments
- translator declarations

The `asset` command reuses that same ownership model.
Plain profile assets go through the shared asset renderer.
Descriptor-driven docs go through the managed-doc renderer.

Translators stay owned by language profiles so policies can stay
language-agnostic.

## Registry Ownership
The tracked registry and runtime registry are different.

- `devcovenant/core/services/tracked_registry.py`
  owns tracked-registry paths and document I/O

- `devcovenant/core/runtime/registry.py`
  owns runtime evidence paths

- `devcovenant/core/services/manifest_inventory.py`
  owns tracked manifest inventory data

- `devcovenant/core/services/policy_registry.py`
  owns policy descriptors, script resolution, and tracked policy state

That split keeps saved setup separate from disposable runtime session state.

## Package Boundary
The published package ships the docs, builtin policies, builtin profiles,
assets, translators, and runtime modules that DevCovenant needs to operate.
That includes the shipped `devcovenant/requirements.lock` bootstrap file and
the mirrored `devcovenant/licenses/**` bundle that travels with it.
It does not ship live repository state such as:

- `devcovenant/config.yaml`
- tracked registry outputs
- runtime registry data
- timestamped log folders
- build debris

That package boundary is owned by `pyproject.toml`, `MANIFEST.in`, and the
packaging tests.
