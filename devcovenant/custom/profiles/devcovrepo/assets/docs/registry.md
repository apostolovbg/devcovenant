# Registry Files

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Local Registry Contents](#local-registry-contents)
- [Global Registry Assets](#global-registry-assets)
- [Examples](#examples)

## Overview
The local registry tracks policy hashes, metadata, and refresh state.
DevCovenant regenerates these files during refresh so they stay in sync
with policy descriptors and profile overlays. Treat the registry as a
cache: do not edit it by hand.

## Workflow
1. Run refresh or update to rebuild the local registry.
2. Inspect the registry when debugging policy loading or overrides.
3. Commit registry changes alongside the code they represent.

## Local Registry Contents
The main files under `devcovenant/registry/local/` are:
- `policy_registry.yaml` for policy hashes and resolved metadata.
- `profile_registry.yaml` for the active profile inventory.
- `manifest.json` for install/update tracking and notices.
- `test_status.json` for devflow gate/test run state.

## Global Registry Assets
The global registry directory under `devcovenant/registry/global/` ships
canonical assets such as policy replacement rules.
These files are part of the package and do not change per repo.

## Examples
To inspect the metadata for a policy:
```bash
rg -n "changelog-coverage" devcovenant/registry/local/policy_registry.yaml
```
