# Registry State
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Local Registry](#local-registry)
- [Global Registry](#global-registry)
- [Lifecycle and Ownership](#lifecycle-and-ownership)
- [Troubleshooting Notes](#troubleshooting-notes)
- [Workflow](#workflow)

## Overview
`devcovenant/registry/` stores generated state used by refresh, checks,
integrity checks, and gate evidence.

Local files are runtime-generated diagnostics and contracts. Do not manually
edit generated payloads.

## Local Registry
`devcovenant/registry/local/` contains runtime state for the active repo:
- `policy_registry.yaml`: resolved policy metadata, hashes, and script paths.
- `profile_registry.yaml`: discovered profile inventory and translator
  declarations.
- `manifest.json`: installed/generated asset tracking and lifecycle metadata.
- `gate_status.json`: start/test/end gate evidence and timestamps.

## Global Registry
`devcovenant/registry/global/` is a shipped namespace for stable shared
registry assets.

Current runtime behavior keeps this namespace lightweight, but it remains
reserved for future global registry contracts and extension points.

## Lifecycle and Ownership
Registry regeneration occurs during full-refresh paths:
- `devcovenant refresh`
- `devcovenant deploy`
- `devcovenant upgrade`
- gate pre-commit phases (`devcovenant gate --start`,
  required non-lifecycle `devcovenant gate --mid`, and
  `devcovenant gate --end`) through gate-owned check orchestration

Ownership model:
- local registry files are generated state
- global registry files are shipped package assets

## Troubleshooting Notes
If integrity checks report registry drift:
1. Run `devcovenant refresh`.
2. Re-run `devcovenant test`.
3. Re-run `devcovenant gate --end`.

If drift persists, compare AGENTS policy block content against
`policy_registry.yaml` and verify descriptor/profile edits were refreshed.

## Workflow
1. Run refresh-producing command.
2. Confirm registry outputs are regenerated.
3. Run `devcovenant gate --mid` before tests in active sessions.
4. Validate with tests and end gate.
