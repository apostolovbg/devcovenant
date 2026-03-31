# Core Runtime
**Last Updated:** 2026-03-31
**Project Version:** 1.0.1.dev1

## Table of Contents
- [Overview](#overview)
- [Module Inventory](#module-inventory)
- [Layer Responsibilities](#layer-responsibilities)
- [Runtime Data Flow](#runtime-data-flow)
- [Contract Boundaries](#contract-boundaries)
- [Workflow](#workflow)

## Overview
`devcovenant/core/` holds the runtime implementation for command behavior,
policy execution, metadata resolution, refresh orchestration, selector logic,
and translator routing.

Think of this directory as the engine room:
- commands call into flow/runtime modules here
- policy checks are loaded and executed from here
- run artifacts and session evidence are written through helpers here

Public user-facing contracts still live in top-level and package-doc surfaces:
- CLI command behavior (`devcovenant/*.py`)
- config and governance behavior (`devcovenant/config.yaml`, `AGENTS.md`)
- package docs and managed docs (`README.md`, `devcovenant/docs/*`)

## Module Inventory
- `flow/`: command-flow orchestration.
  - `gate.py`: `start`/`mid`/`end` lifecycle behavior and reconcile loops.
  - `gate_status_helpers.py`: read-only status rendering and
    run-pointer lookup.
  - `gate_status_validation.py`: gate-status payload parsing and schema
    validation.
  - `gate_changelog_helpers.py`: changelog top-entry/session-baseline helpers.
  - `policy_check_context.py`: gate/session-derived check-context assembly for
    policy runs.
  - `refresh.py`: full refresh orchestration and managed-doc regeneration.
  - `session.py`: gate-session helper wiring.
  - `workflow_contract.py`: workflow-run contract resolution and
    normalization.
  - `workflow_validation.py`: flow-owned workflow-evidence validation.
- `runtime/`: process and output boundary.
  - `event.py`: run-event adapters and lifecycle-event recording.
  - `execution.py`: command dispatch, subprocess routing, managed re-exec.
  - `errors.py`: runtime exception normalization and explicit error rendering.
  - `output.py`: output-mode policy and channel-level stream/suppression rules.
  - `policy_commands.py`: namespaced policy-command parsing and invocation
    helpers.
  - `policy_reporting.py`: policy-check output formatting and threshold
    summaries.
  - `policy_runtime_actions.py`: policy-action loading and dispatch helpers.
  - `registry.py`: runtime evidence-path ownership for gate/session ledgers.
  - `run_logging.py`: run-folder allocation and summary/log artifact contract.
  - `session_snapshot.py`: snapshot collection and diff helpers.
  - `workflow_session.py`: workflow-session payload persistence.
- `services/`: policy/profile/registry business logic.
  - `asset_materialization.py`: shared asset-command resolution and rendering
    for plain profile assets and managed docs.
  - `integrity_validation.py`: engine-owned integrity checks for descriptor,
    registry, and gate-integrity state.
  - `manifest_inventory.py`: tracked inventory defaults and required-repo
    manifest persistence.
  - `managed_docs.py`: descriptor-backed managed-doc synchronization.
  - `metadata.py`: metadata merge, normalization, typed decoding.
  - `policy_engine.py`: policy runtime orchestration and reporting.
  - `policy_parse.py`: AGENTS `policy-def` parser and model.
  - `policy_registry.py`: policy descriptors, script resolution, and tracked
    policy hash/state management.
  - `profile_registry.py`: profile discovery and merge inventory.
  - `project_governance.py`: project-governance state resolution and AGENTS
    guidance rendering.
  - `structure_validation.py`: engine-owned repository-structure checks.
  - `tracked_registry.py`: tracked-registry path and document ownership.
  - `translator_engine.py`: language translator routing and `LanguageUnit`.
- `lib/`: shared helpers.
  - `agents_blocks.py`: AGENTS policy-block rendering helpers.
  - `document_exemptions.py`: managed/header-only exemption fingerprints.
  - `selectors.py`: selector matching utilities.
- `contracts/`: typed runtime contracts.
  - `errors.py`: structured error-code and explicit failure payload contract.
  - `policy.py`: check/fixer/violation/runtime-action contract classes.

## Layer Responsibilities
Flow modules decide when work runs.
Runtime modules decide how commands, output, and logs are executed.
Service modules decide what policy/profile/registry logic means.
Contract modules define typed boundaries used by the other layers.

This split keeps debugging straightforward:
1. wrong sequence -> check `flow/`
2. wrong streaming/log output -> check `runtime/`
3. wrong policy/metadata behavior -> check `services/`

## Runtime Data Flow
1. Refresh composes profile and config metadata and rebuilds registries/docs.
2. AGENTS managed workflow/governance/policy content is rendered from resolved
   state.
3. The policy parser loads AGENTS `policy-def` payloads.
4. The policy engine resolves metadata and file scope and executes checks.
5. Gate/run flows execute runs and write run artifacts.
6. Session evidence is stored under `devcovenant/registry/runtime/`,
   including `gate_status.json` and `workflow_session.json`.

## Contract Boundaries
Tier-A user contracts live outside this directory and include:
- CLI behavior
- config schema
- managed-doc formats
- AGENTS workflow and policy-block schema

Tier-B extension contracts include:
- policy script and fixer interfaces
- profile manifest schema
- translator declaration schema
- shared language-unit payload shape

Tier-C data contracts include on-disk registry/state payloads.

Tier-D internals include helper organization and module internals in this
folder; those may refactor as long as Tier-A/B/C behavior stays stable.

## Workflow
1. Update the target runtime module.
2. Update mirrored tests under `tests/devcovenant/core/`.
3. Update docs affected by behavior changes.
4. Run the gate sequence:
   - `devcovenant gate --start`
   - `devcovenant gate --mid`
   - `devcovenant run`
   - `devcovenant gate --end`
5. Keep `SPEC.md`, `PLAN.md`, and the reference maps aligned when contracts
   change.
