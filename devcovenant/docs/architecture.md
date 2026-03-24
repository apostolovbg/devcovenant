# DevCovenant Architecture
**Last Updated:** 2026-03-24
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

  Lifecycle orchestration such as gate phases, refresh ownership, and command
  sequencing.

- `runtime`

  Execution, output, run logging, error normalization, and command dispatch.

- `services`

  Shared runtime services such as metadata resolution, policy execution,
  managed docs, registry handling, and invariant helpers.

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

## Profiles, Translators, And Assets
Profiles describe repository shape.
They can contribute:

- suffix inventories

- metadata overlays

- managed assets

- pre-commit fragments

- translator declarations

Translators are owned by language profiles.
They keep policies language-agnostic by translating source into normalized
units instead of forcing each policy to parse each language separately.
The profile-registry service resolves those profile inventories in a
deterministic sorted order before tracked registry state is written, so the
same repo does not rewrite generated files differently on macOS, Linux, or
Windows just because the filesystem returned directories in a different order.

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
