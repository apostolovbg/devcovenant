# Core Runtime
**Last Updated:** 2026-03-09
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Module Inventory](#module-inventory)
- [Layer Responsibilities](#layer-responsibilities)
- [Runtime Data Flow](#runtime-data-flow)
- [Contract Boundaries](#contract-boundaries)
- [Change Workflow](#change-workflow)

## Overview
`devcovenant/core/` holds the runtime implementation for command behavior,
policy execution, metadata resolution, refresh orchestration, selector logic,
and translator routing.

Think of this directory as the "engine room":
- commands call into flow/runtime modules here
- policy checks are loaded and executed from here
- run artifacts and session evidence are written through helpers here

Public user-facing contracts still live in top-level/docs surfaces:
- CLI command behavior (`devcovenant/*.py`)
- config and policy/profile contracts (`devcovenant/config.yaml`, AGENTS)
- managed docs and maps (`README.md`, `devcovenant/docs/*`, maps/spec)

## Module Inventory
- `flow/`: command-flow orchestration.
  - `gate.py`: `start`/`mid`/`end` lifecycle behavior and reconcile loops.
  - `gate_status_helpers.py`: read-only status rendering/run-pointer lookup.
  - `gate_changelog_helpers.py`: changelog top-entry/session-baseline helpers.
  - `refresh.py`: full refresh orchestration and managed-doc regeneration.
  - `session.py`: gate-session helper wiring.
- `runtime/`: process and output boundary.
  - `execution.py`: command dispatch, subprocess routing, managed re-exec.
  - `errors.py`: runtime exception normalization and explicit error rendering.
  - `output.py`: output-mode policy and channel-level stream/suppression rules.
  - `run_logging.py`: run-folder allocation and summary/log artifact contract.
  - `session_snapshot.py`: snapshot collection/diff helpers.
- `services/`: policy/profile/registry business logic.
  - `event.py`: test-event adapters and lifecycle-event recording.
  - `metadata.py`: metadata merge, normalization, typed decoding.
  - `policy_block_refresh.py`: AGENTS policy-block rendering.
  - `policy_engine.py`: policy runtime orchestration and reporting.
  - `policy_parse.py`: AGENTS `policy-def` parser/model.
  - `profile_registry.py`: profile discovery and merge inventory.
  - `registry.py`: manifest/registry read-write contracts.
  - `translator_engine.py`: language translator routing and `LanguageUnit`.
- `lib/`: shared helpers.
  - `selectors.py`: selector matching utilities.
  - `document_exemptions.py`: managed/header-only exemption fingerprints.
- `contracts/`: typed runtime contracts.
  - `errors.py`: structured error code and explicit failure payload contract.
  - `policy.py`: check/fixer/violation/runtime-action contract classes.

## Layer Responsibilities
Flow modules decide "when" work runs.
Runtime modules decide "how" commands/output/logs are executed.
Service modules decide "what" policy/profile/registry logic means.
Contract modules define typed boundaries used by the other layers.

This split keeps debugging straightforward:
1. wrong sequence -> check `flow/`
2. wrong streaming/log output -> check `runtime/`
3. wrong policy/metadata behavior -> check `services/`

## Runtime Data Flow
1. Refresh composes profile+config metadata and rebuilds registries/docs.
2. AGENTS managed policy block is rendered from resolved metadata.
3. Policy parser loads AGENTS `policy-def` payloads.
4. Policy engine resolves metadata + file scope and executes checks.
5. Gate/test flows run required commands and write run artifacts.
6. Session evidence is stored in `devcovenant/registry/local/gate_status.json`.

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
   - `devcovenant gate --mid`
   - `devcovenant test`
   - `devcovenant gate --end`
5. Keep `SPEC.md`, `PLAN.md`, and maps aligned when contracts change.
