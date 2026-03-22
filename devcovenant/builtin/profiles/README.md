# Builtin Profiles
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Profile Responsibilities](#profile-responsibilities)
- [Manifest Schema](#manifest-schema)
- [Translator Declarations](#translator-declarations)
- [Asset Materialization Rules](#asset-materialization-rules)
- [Workflow](#workflow)

## Overview
Builtin profiles are shipped under
`devcovenant/builtin/profiles/<name>/`.

Profiles are metadata and asset providers. They do not activate policies.
Policy activation authority is `config.policy_state`.
This README documents folder contracts and ownership boundaries, not the
current profile inventory. For the active builtin/custom profile catalog, use
`PROFILE_MAP.md`.

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
- optional `core_invariant_overlays`
- `assets`
- `pre_commit`
- optional `translators`

Custom profiles with the same profile name override builtin profiles.

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
`devcovenant/builtin/profiles/global/assets/gitignore.yaml`.
`.github/workflows/governance-and-test.yml` is generated from the global
workflow template plus active-profile governance fragments and config
overlays/overrides.

## Workflow
1. Edit profile manifest and assets.
2. Run `devcovenant refresh`.
3. Run `devcovenant gate --start`.
4. Run `devcovenant gate --mid` until clean.
5. Verify with `devcovenant test`.
6. Finalize with `devcovenant gate --end`.
