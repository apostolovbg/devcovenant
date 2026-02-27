# Core Runtime
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Module Inventory](#module-inventory)
- [Runtime Data Flow](#runtime-data-flow)
- [Contract Boundaries](#contract-boundaries)
- [Change Workflow](#change-workflow)

## Overview
`devcovenant/core/` holds the runtime implementation for command behavior,
policy execution, metadata resolution, refresh orchestration, selector logic,
and translator routing.

This directory is implementation territory. Public user-facing contracts are
defined by CLI surface, config schema, managed docs, and policy/profile
manifests in `SPEC.md`.

## Module Inventory
- `flow/`: gate and refresh orchestration flow.
  - `gate.py`: start/end gate orchestration, rerun control, status recording.
  - `refresh.py`: full refresh orchestration.
  - `session.py`: session helpers and snapshot-related flow glue.
- `runtime/`: process execution and filesystem/session runtime boundaries.
  - `execution.py`: command execution, managed-environment reruns, and test
    command runtime.
  - `session_snapshot.py`: snapshot persistence and comparison helpers.
- `services/`: policy/profile/registry/metadata business logic.
  - `event.py`: test event adapters and emission helpers.
  - `metadata.py`: policy metadata resolution and normalization.
  - `policy_block_refresh.py`: AGENTS policy-block materialization.
  - `policy_engine.py`: policy loading/check/fixer orchestration.
  - `policy_parse.py`: policy-definition parser and text model.
  - `profile_registry.py`: profile discovery/merging/translator declarations.
  - `registry.py`: manifest/registry read-write contracts.
  - `translator_engine.py`: translator routing and `LanguageUnit` handling.
- `lib/`: shared helpers used across policies and runtime.
  - `selectors.py`: selector normalization and watchlist helpers.
- `contracts/`:
  - `policy.py`: check/fixer/violation contracts and runtime-action models.

Directory contracts:
- `policies/`: legacy compatibility namespace for pre-builtin policy paths.
- `profiles/`: legacy compatibility namespace for pre-builtin profile paths.

## Runtime Data Flow
1. Refresh builds registries and materializes managed assets.
2. AGENTS policy block is compiled from resolved policy metadata.
3. Runtime parsing reads AGENTS policy definitions.
4. Metadata layers are applied in the documented precedence order.
5. Policies execute, optionally calling translator runtime for language units.
6. Gate runtime records evidence under `devcovenant/registry/local/`.

## Contract Boundaries
Tier-A user contracts live outside this directory and include:
- CLI behavior
- config schema
- managed doc formats
- AGENTS policy-block schema

Tier-B extension contracts include:
- policy script and fixer interfaces
- profile manifest schema
- translator declaration schema
- shared language-unit payload shape

Tier-C data contracts include on-disk registry/state payloads.

Tier-D internals include helper organization and module internals in this
folder; those may refactor as long as Tier-A/B/C behavior stays stable.

## Workflow
1. Update target runtime module.
2. Update mirrored tests under `tests/devcovenant/core/`.
3. Update docs affected by behavior changes.
4. Run the gate sequence:
   - `devcovenant gate --start`
   - `devcovenant test`
   - `devcovenant gate --end`
5. Keep `SPEC.md`, `PLAN.md`, and maps aligned when contracts change.
