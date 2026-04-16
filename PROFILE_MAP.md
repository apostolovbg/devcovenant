# Profile Map
**Doc ID:** PROFILE_MAP
**Doc Type:** reference-map
**Project Version:** 1.0.1b4
**Last Updated:** 2026-04-16
**DevCovenant Version:** 1.0.1b4

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PROFILE_MAP.md` to track profile inventory and ownership below
this block.
<!-- DEVCOV:END -->

## Table of Contents
1. [Purpose](#purpose)
2. [Global Rules](#global-rules)
3. [Builtin Profile Inventory](#builtin-profile-inventory)
4. [Custom Profiles](#custom-profiles)
5. [Translator Ownership](#translator-ownership)
6. [Operational Notes](#operational-notes)

## Purpose
This map lists the shipped profiles and who owns them.

## Global Rules
- `global` profile is always active at runtime.
- Additional profiles are selected by `config.profiles.active`.
- Profiles provide overlays, selectors, assets, hooks, and translators.
- Profiles do not activate policies.
- Builtin/custom profile precedence is path-based.
- Same-name custom profile fully shadows the builtin profile with that name.
- When a custom profile shadows a builtin one, the builtin profile is ignored
  instead of being merged.

## Builtin Profile Inventory
Baseline:
- `global`
- `defaults`
- `docs`
- `devcovuser`

Language profiles:
- `python`
- `javascript`
- `typescript`
- `java`
- `go`
- `rust`
- `opencl`
- `csharp`
- `php`
- `ruby`
- `dart`
- `swift`
- `objective_c`
- `sql`

Framework profiles:
- `fastapi`
- `frappe`
- `flutter`

Ops/tooling profiles:
- `github`
- `docker`
- `terraform`
- `kubernetes`

## Custom Profiles
- `userproject`: this repository's same-name custom override of the
  builtin bootstrap template, carrying DevCovenant's repository-specific
  CI, documentation routes, broader source-to-test mirrors, and root trust
  docs such as `SECURITY.md`, `PRIVACY.md`, and `SUPPORT.md`.
- `restapi`: reusable API (application programming interface) governance
  profile that tightens API-focused documentation routes, security scope,
  and test coverage expectations, and seeds `docs/api.md`, `docs/auth.md`,
  and `docs/errors.md` assets.

## Translator Ownership
Language profiles with declared translators:
- `python`
- `javascript`
- `typescript`
- `java`
- `go`
- `rust`
- `opencl`
- `csharp`
- `dart`
- `php`
- `ruby`
- `swift`
- `objective_c`
- `sql`

Translator declarations are owned by language profile manifests and routed
by the shared translator runtime.

## Operational Notes
- Profile overlays are materialized to `autogen_metadata_overlays`.
- Repo-specific additive metadata belongs in `user_metadata_overlays`.
- Repo-specific replacement metadata belongs in `user_metadata_overrides`.
- Inherited values should stay inherited from the other active profiles.
  Do not restate them in a copied same-name shadow profile.
- `defaults` is the shipped baseline layout profile for common repo metadata.
  Repositories can disable it and activate a custom replacement profile.
- For dependency licensing metadata: `defaults` provides generic output
  targets; language/framework profiles provide dependency selectors when
  active; this repository's custom `userproject` profile adds only the
  repo-specific deltas.
- Any active profile category may contribute declared `workflow_runs`;
  core resolves them in deterministic order from the tracked workflow
  definition.
- Language profiles may declare `run_events` adapter metadata for the
  relevant workflow run through `devcovenant/core/run_events.py`; that is
  separate from translator declarations.
- Session scoping is runtime-owned; profiles should not model policy scope
  switching metadata for bundled checks.
- Assets are created when missing and preserved when existing content is
  user-authored outside managed blocks.
- Pre-commit fragments from active profiles merge into generated
  `.pre-commit-config.yaml`, then config overlays and overrides are applied.
- `ci.yml` is refresh-generated when an active profile owns
  `ci_and_test_template`, normally the builtin `github` profile, then active
  profile governance fragments and config overlays/overrides are merged on
  top.
- `.gitignore` is generated from global template metadata plus active profile
  manifest metadata (`gitignore_fragments` or `ignore_dirs`) and
  `config.gitignore.overlays`/`config.gitignore.overrides`.
