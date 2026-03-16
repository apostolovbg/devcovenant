# Registry Files

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Tracked Registry](#tracked-registry)
- [Runtime Registry](#runtime-registry)
- [Examples](#examples)

## Overview
DevCovenant uses one visible registry root under `devcovenant/registry/`.
Tracked governance metadata lives in `registry.yaml`, while disposable runtime
state lives under `devcovenant/registry/runtime/`.
Treat generated registry files as DevCovenant-owned artifacts: do not edit
them by hand.

## Workflow
1. Run `refresh` to rebuild tracked registry state and managed outputs.
2. Inspect `devcovenant/registry/registry.yaml` when debugging policy loading,
   overlays, or override resolution.
3. Inspect `devcovenant/registry/runtime/` when debugging a live gate session
   or latest-run pointer behavior.
4. Use the gate workflow (`start -> mid -> test -> end`) for edit slices.
5. Commit `registry.yaml` changes alongside the code they represent.

## Tracked Registry
`devcovenant/registry/registry.yaml` stores deterministic repo governance
metadata, including:
- policy hashes, origin data, and resolved metadata
- profile inventory and active-profile state
- tracked inventory data used by refresh/integrity checks

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:
- `gate_status.json` for gate lifecycle state
- `latest.json` for the latest run pointer
- future session snapshot files when gate runtime needs bulk companion data

Lifecycle notes:
- `gate --start` and `gate --end` write lifecycle state.
- `gate --mid` performs required pre-test checks without lifecycle writes.

## Examples
To inspect the metadata for a policy:
```bash
rg -n "changelog-coverage" devcovenant/registry/registry.yaml
```

For a human-readable view of the active metadata, consult the policy block in
`AGENTS.md`, which mirrors the resolved registry values.
