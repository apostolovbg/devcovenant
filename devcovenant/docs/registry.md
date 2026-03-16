# Registry Files
**Last Updated:** 2026-03-15
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Tracked Registry](#tracked-registry)
- [Runtime Registry](#runtime-registry)
- [Gate Status Contract](#gate-status-contract)
- [Lifecycle](#lifecycle)
- [Validation and Integrity](#validation-and-integrity)
- [Workflow](#workflow)

## Overview
DevCovenant uses one visible registry root under `devcovenant/registry/`.
Tracked governance metadata lives in `registry.yaml`, while disposable runtime
state lives under `devcovenant/registry/runtime/`.

Treat generated registry files as:
- diagnostics
- reproducibility artifacts
- synchronization evidence for integrity checks

Manual edits are unsupported and typically interpreted as drift.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the only tracked registry artifact.
Changes to that file are routed here by documentation-growth-tracking because
this document is the user-facing explanation of the tracked registry contract.
It includes:
- discovered policy IDs
- descriptor/script paths and hashes
- resolved metadata snapshots
- per-key metadata resolution trace (`metadata_resolution`)
- structured override-replacement diagnostics (`metadata_warnings`)
- typed runtime metadata view (`runtime_metadata_options`)
- typed config-override view (`runtime_config_overrides`)
- merged runtime-effective option view (`runtime_effective_options`)
- discovered profile inventory and active-profile state
- tracked inventory data used by refresh and integrity checks

Metadata trace intent:
- `metadata` remains the final effective string-map used for policy/runtime
  loading contracts
- `metadata_resolution` explains how each effective key was composed across
  descriptor, profile overlay, config overlay, config override, and
  policy-state layers
- `metadata_warnings` records destructive override cases where an override
  replaced inherited non-empty values; this is an audit aid, not a silent
  autofix
- typed runtime option views make the final policy surface inspectable without
  re-deriving values by hand

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:
- `gate_status.json`
- `session_snapshot.json`
- `latest.json`

Runtime registry files are:
- untracked
- disposable
- local to the current machine/session/branch context

Cleanup rule:
- `devcovenant clean --registry` removes runtime registry residue only
- `devcovenant clean --logs` removes disposable run-log directories only
- tracked files such as `devcovenant/registry/registry.yaml`,
  `devcovenant/registry/README.md`, and `devcovenant/logs/README.md`
  remain outside cleanup scope

## Gate Status Contract
`gate_status.json` is the concise workflow session ledger used by
gate-aware policies. It is also a core evidence artifact in the gate-session
evidence family.

Heavy session payloads live in the companion
`devcovenant/registry/runtime/session_snapshot.json` file. That companion
stores:
- `session_start_snapshot`
- optional `session_baseline_snapshot`
- `session_end_snapshot`
- `last_run_snapshot`
- `document_exemption_baseline`
- full normalized `test_events`

Key evidence families:
- concise lifecycle timestamps and command records
- open/closed session state
- pointer metadata for the companion session snapshot
- changelog snapshot anchors/fingerprints
- heavy session baseline/snapshot evidence in `session_snapshot.json`
- test lifecycle event payloads in `session_snapshot.json`

Relationship to run-log evidence artifacts:
- `gate_status.json` stores concise lifecycle/session evidence
- `session_snapshot.json` stores heavy snapshot/baseline evidence
- `latest.json` stores the latest run-pointer metadata for status helpers
- `devcovenant/logs/<run-id>-<command>/` stores per-command run evidence
- use both together when reconstructing what happened in a work slice

Operational rule:
- do not delete or rewrite runtime registry files during an active session
  unless a recovery procedure explicitly requires it

## Lifecycle
Tracked registry regeneration occurs on full refresh paths:
- `devcovenant refresh`
- `devcovenant deploy`
- `devcovenant upgrade`
- gate pre-commit phases (`devcovenant gate --start` / `--end`) through the
  gate-owned `check` orchestration path

Gate status evolves on:
- `devcovenant gate --start`
- `devcovenant gate --mid` (non-lifecycle checks only; no status writes)
- `devcovenant test`
- `devcovenant gate --end`
- `devcovenant gate --status` (read-only inspection; no ledger writes)

Session snapshot companion data evolves on:
- `devcovenant gate --start`
- `devcovenant test`
- `devcovenant gate --end`

Registry behavior expectations:
- deterministic for unchanged tracked inputs
- aligned with current descriptors/profiles/config
- validated by integrity policies and gate workflow
- recreated explicitly by refresh-producing commands when missing
- kept out of package payloads even though install/refresh/upgrade recreate
  the tracked registry structure inside a repository

## Validation and Integrity
`devcov-integrity-guard` validates registry state against active policy source
and runtime expectations.

When drift is detected:
1. run `devcovenant refresh`
2. rerun `devcovenant test`
3. rerun `devcovenant gate --end`

If drift persists:
- verify descriptor/profile edits were completed
- verify managed blocks were not manually edited
- verify refresh ran from repository root

## Workflow
1. Change descriptor/profile/config inputs.
2. Run refresh to regenerate tracked registry artifacts.
3. Inspect `devcovenant/registry/runtime/` for live session state only.
4. Run tests to update session evidence as needed.
5. Run end gate to validate synchronized clean state.
