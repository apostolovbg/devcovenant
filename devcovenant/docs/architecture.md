# DevCovenant Architecture
**Last Updated:** 2026-03-30
**Project Version:** 1.0.0

## Overview
This document explains how DevCovenant is built.
Use it when you need the internal ownership map rather than the operator flow.
If you only need to use the product, start with `README.md`,
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
  lifecycle orchestration, gate stages, refresh ownership, workflow contract
  resolution, and workflow validation

- `runtime`
  process execution, output policy, run logging, runtime ledgers, and
  namespaced command dispatch

- `services`
  metadata resolution, policy execution, managed docs, tracked registry,
  project governance, structure validation, and integrity validation

- `lib`
  shared helpers reused across the runtime

- `contracts`
  typed contract objects shared by the other layers

## Built-In Runtime Checks
DevCovenant has three built-in runtime checks that are always part of the
engine's own behavior:

- workflow validation in
  `devcovenant/core/flow/workflow_validation.py`
- integrity validation in
  `devcovenant/core/services/integrity_validation.py`
- structure validation in
  `devcovenant/core/services/structure_validation.py`

These checks are not configurable policy inventory.
They are part of the runtime's own trust boundary.
Repository-tweakable knobs for them live in ordinary config sections such as
`paths`, `workflow`, and `integrity`.

## Evidence Flow
DevCovenant is built around evidence, not only around checks.
The normal flow is:

1. repository files are collected and interpreted
2. built-in runtime checks and configurable policies evaluate that state
3. commands record evidence artifacts about what happened

The main evidence surfaces are:

- per-run log folders under `devcovenant/logs/`
- tracked registry state in `devcovenant/registry/registry.yaml`
- runtime session state under `devcovenant/registry/runtime/`
- managed governance output in `AGENTS.md`

## Workflow Ownership
Workflow structure has its own contract instead of being inferred from policy
state.
Core owns the reserved anchors:

- `start`
- `mid`
- `end`

Profiles own declared workflow runs between `mid` and `end`.
Those runs define:

- whether a run is enabled or required
- how it executes
- how success is recorded
- how freshness is evaluated
- which reporting hooks apply to it

The resolver for that contract lives in
`devcovenant/core/flow/workflow_contract.py`.
The validator for recorded workflow evidence lives in
`devcovenant/core/flow/workflow_validation.py`.

## Policy Runtime Model
Policies combine three things:

1. descriptor metadata
2. runtime check code
3. optional autofix or command surfaces

Checks stay read-only.
Mutation belongs either to:

- autofix during an autofix-enabled check path
- explicit policy commands when an operator runs them deliberately

That boundary is intentional.
Checks report.
Autofix fixes.
Commands perform deliberate operations.

## Managed Docs And Generation
Managed documents are first-class runtime outputs.
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
`devcovenant/core/lib/agents_blocks.py`, which now owns the generated policy
block only.

## Profiles, Translators, And Assets
Profiles describe repository shape.
They may contribute:

- suffix inventories
- metadata overlays
- workflow runs
- managed assets
- pre-commit fragments
- CI fragments
- translator declarations

The `asset` command reuses that same ownership model.
Plain profile assets go through the shared asset renderer.
Descriptor-backed docs go through the managed-doc renderer.

Translators stay owned by language profiles so policies can stay
language-agnostic.

## Registry Ownership
The tracked registry and runtime registry are different surfaces.

- `devcovenant/core/services/tracked_registry.py`
  owns tracked-registry paths and document I/O

- `devcovenant/core/runtime/registry.py`
  owns runtime evidence paths

- `devcovenant/core/services/manifest_inventory.py`
  owns tracked manifest inventory data

- `devcovenant/core/services/policy_registry.py`
  owns policy descriptors, script resolution, and tracked policy state

That split keeps durable contract state separate from disposable runtime
session state.

## Package Boundary
The published package ships the docs, builtin policies, builtin profiles,
assets, translators, and runtime modules that DevCovenant needs to operate.
It does not ship live repository state such as:

- `devcovenant/config.yaml`
- tracked registry outputs
- runtime registry data
- timestamped log folders
- build debris

That packaging contract is owned by `pyproject.toml`, `MANIFEST.in`, and the
packaging tests.
