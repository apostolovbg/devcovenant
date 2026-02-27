# Registry Files

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Local Registry Contents](#local-registry-contents)
- [Global Registry Assets](#global-registry-assets)
- [Examples](#examples)

## Overview
The local registry tracks policy hashes, resolved metadata, and refresh
state. DevCovenant regenerates these files during refresh so they stay
in sync with policy descriptors and profile overlays. Treat the
registry as a cache: do not edit it by hand.

## Workflow
1. Run `refresh` to rebuild registry and managed state.
2. Inspect the registry when debugging policy loading or overrides.
3. Use the gate workflow (`start -> mid -> test -> end`) for edit slices.
4. Commit registry changes alongside the code they represent.

## Local Registry Contents
The main files under `devcovenant/registry/local/` are:
- `policy_registry.yaml` for policy hashes and resolved metadata.
- `profile_registry.yaml` for the active profile inventory.
- `manifest.json` for lifecycle tracking and notices.
- `gate_status.json` for gate session lifecycle and test run state.

Lifecycle notes:
- `gate --start` and `gate --end` write lifecycle state.
- `gate --mid` performs required pre-test checks without lifecycle writes.

## Global Registry Assets
The global registry directory under `devcovenant/registry/global/` is a
reserved package-level extension namespace.
It stays stable for future shared registry assets and does not currently hold
required runtime data.

## Examples
To inspect the metadata for a policy:
```bash
rg -n "changelog-coverage" devcovenant/registry/local/policy_registry.yaml
```

For a human-readable view of the active metadata, consult the policy
block in `AGENTS.md`, which mirrors the resolved registry values.
