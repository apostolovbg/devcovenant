# Core Profiles

## Table of Contents
- [Overview](#overview)
- [Profile Responsibilities](#profile-responsibilities)
- [Manifest Schema](#manifest-schema)
- [Translator Declarations](#translator-declarations)
- [Asset Materialization Rules](#asset-materialization-rules)
- [Workflow](#workflow)

## Overview
Core profiles are shipped under `devcovenant/core/profiles/<name>/`.

Profiles are metadata and asset providers. They do not activate policies.
Policy activation authority is `config.policy_state`.

Shipped baseline split:
- `global`: universal hooks/assets baseline
- `defaults`: common repo-layout metadata defaults

## Profile Responsibilities
Profiles may provide:
- metadata overlays
- selector metadata
- asset templates
- pre-commit hook fragments
- translator declarations (language profiles only)

Any active profile category may contribute policy overlays such as
`devflow-run-gates.required_commands`.

## Manifest Schema
Each profile directory contains `<name>.yaml` manifest.
Common keys include:
- `profile`
- `category`
- `suffixes`
- `ignore_dirs`
- optional `gitignore_fragments`
- optional `gitignore_template` (global baseline template)
- optional `governance_template` (global workflow template)
- optional `governance_and_test` (workflow fragment overlay)
- `policy_overlays`
- `assets`
- `pre_commit`
- optional `translators`

Custom profiles with the same profile name override core profiles.

## Translator Declarations
Only language profiles declare translators.
Declaration fields include:
- `id`
- `extensions`
- `can_handle` strategy and entrypoint
- `translate` strategy and entrypoint

Translator entrypoint paths are validated as profile-contained paths.

## Asset Materialization Rules
During deploy/upgrade/refresh:
- missing assets are created from templates
- existing non-one-line files are preserved
- managed blocks are refreshed where document contracts require it

Generated assets include `.pre-commit-config.yaml`, `.gitignore`, and managed
docs selected by active profile metadata.
`.gitignore` is generated from global template fragments plus per-profile
manifest fragments and config overlays; profiles do not ship `.gitignore`
asset files.
Global template source:
`devcovenant/core/profiles/global/assets/gitignore.yaml`.
`.github/workflows/governance-and-test.yml` is generated from the global
workflow template plus active-profile governance fragments and config
overlays/overrides.

## Workflow
1. Edit profile manifest and assets.
2. Run `devcovenant refresh`.
3. Verify with `devcovenant test`.
4. Finalize with `devcovenant gate --end`.
