# Registry Files
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Local Registry Contracts](#local-registry-contracts)
- [Gate Status Contract](#gate-status-contract)
- [Global Registry Namespace](#global-registry-namespace)
- [Lifecycle](#lifecycle)
- [Validation and Integrity](#validation-and-integrity)
- [Workflow](#workflow)

## Overview
Registry files are generated runtime contracts, not handwritten source files.
They exist to make runtime resolution and gate evidence inspectable.

Treat local registry files as:
- diagnostics
- reproducibility artifacts
- synchronization evidence for integrity checks

Manual edits are unsupported and typically interpreted as drift.

## Local Registry Contracts
`devcovenant/registry/local/` contains:
- `policy_registry.yaml`
- `profile_registry.yaml`
- `manifest.json`
- `gate_status.json`
- `audit_digest.json` (machine-readable informational digest)
- `audit_digest.txt` (short human-readable informational digest)

`policy_registry.yaml` includes:
- discovered policy IDs
- descriptor/script paths and hashes
- resolved metadata snapshots
- builtin/custom origin indicators (`origin`)

`profile_registry.yaml` includes:
- discovered profiles and source roots
- active-profile state
- merged manifest-derived metadata
- translator and test-event declaration data

`manifest.json` includes:
- generated artifact inventory
- lifecycle bookkeeping metadata
- refresh-oriented notifications/contracts

`audit_digest.json` / `audit_digest.txt` include:
- low-token workflow/policy inspection summaries for operators/tooling
- execution-order and enabled-policy snapshots derived from AGENTS + registry
- explicit non-canonical notice (`AGENTS.md` remains canonical law)

## Gate Status Contract
`gate_status.json` is the workflow session ledger used by gate-aware policies.
It is also a core evidence artifact in the gate-session evidence family.

Key evidence families:
- start/end gate timestamps and command records
- start gate resets stale end-phase pre-commit fields on new sessions
- open/closed session state
- test command execution evidence
- session baseline metadata
- changelog snapshot anchors/fingerprints
- test lifecycle events emitted by adapters

Why this matters:
- session-aware policies (for example changelog coverage) rely on this file to
  compute scope correctly
- devflow gate enforcement validates sequence evidence from this ledger
- start/end commands refuse invalid transitions to prevent hidden state loss

Relationship to run-log evidence artifacts:
- `gate_status.json` stores lifecycle/session evidence
- `devcovenant/logs/<run-id>-<command>/` stores per-command run evidence
- use both together when reconstructing what happened in a work slice

Operational rule:
- do not delete or rewrite this file during an active session unless recovery
  procedure explicitly requires it

## Global Registry Namespace
`devcovenant/registry/global/` is reserved as the stable namespace for shipped
global registry assets.

Current runtime uses lightweight global payloads, but the namespace remains the
forward-compatible anchor for packaged/global contracts.

## Lifecycle
Local registry regeneration occurs on full refresh paths:
- `devcovenant refresh`
- `devcovenant deploy`
- `devcovenant upgrade`
- gate pre-commit phases (`devcovenant gate --start` / `--end`) through the
  gate-owned local `check` orchestration path

Audit digest behavior:
- digest artifacts regenerate with policy-registry refresh paths
- digest artifacts are informational only; they do not replace AGENTS workflow
  reading requirements

Gate status evolves on:
- `devcovenant gate --start`
- `devcovenant test`
- `devcovenant gate --end`
- `devcovenant gate --status` (read-only inspection; no ledger writes)

Registry behavior expectations:
- deterministic for unchanged inputs
- aligned with current descriptors/profiles/config
- validated by integrity policies and gate workflow
- `gate --status` may report malformed ledger state, but it must not repair or
  rewrite the file implicitly

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
2. Run refresh to regenerate local registry artifacts.
3. Run tests to update session evidence as needed.
4. Run end gate to validate synchronized clean state.
