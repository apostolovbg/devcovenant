# Profile Map
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
1. [Purpose](#purpose)
2. [Global Rules](#global-rules)
3. [Builtin Profile Inventory](#builtin-profile-inventory)
4. [Custom Profiles](#custom-profiles)
5. [Translator Ownership](#translator-ownership)
6. [Operational Notes](#operational-notes)

## Purpose
This map documents shipped profile contracts and ownership for 1.0.0.

## Global Rules
- `global` profile is always active at runtime.
- Additional profiles are selected by `config.profiles.active`.
- Profiles provide overlays, selectors, assets, hooks, translators.
- Profiles do not activate policies.
- Builtin/custom profile precedence is path-based.
- Same-name custom profile overrides same-name builtin profile.

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
- `docker`
- `terraform`
- `kubernetes`

## Custom Profiles
- `devcovrepo`: repository-specific overlays/assets for DevCovenant dogfooding,
  including documentation-route metadata and broader modules-test mirrors.

## Translator Ownership
Language profiles with declared translators:
- `python`
- `javascript`
- `typescript`
- `java`
- `go`
- `rust`
- `csharp`
- `dart`
- `php`
- `ruby`
- `swift`
- `objective_c`
- `sql`

Translator declarations are owned by language profile manifests and routed by
shared translator runtime.

## Operational Notes
- Profile overlays are materialized to `autogen_metadata_overlays`.
- Repo-specific additive metadata belongs in `user_metadata_overlays`.
- Repo-specific replacement metadata belongs in `user_metadata_overrides`.
- `defaults` is the shipped baseline layout profile for common repo metadata.
  Repositories can disable it and activate a custom replacement profile.
- For dependency licensing metadata: `defaults` provides generic output
  targets; language/framework profiles provide dependency selectors when
  active; `devcovrepo` adds this repository's selectors only.
- Any active profile category may contribute `devflow-run-gates` test-command
  overlays; resolved command order is preserved at runtime.
- Language profiles may declare `test_events` adapter metadata for
  `devcovenant/core/services/event.py`; that contract is separate from
  translator declarations.
- Session scoping is runtime-owned; profiles should not model policy scope
  switching metadata for bundled checks.
- Assets are created when missing and preserved when existing content is
  user-authored outside managed blocks.
- Pre-commit fragments from active profiles merge into generated
  `.pre-commit-config.yaml`, then config overlays and overrides are applied.
- `governance-and-test.yml` is refresh-generated from global template metadata,
  active profile governance fragments, and config overlays/overrides.
- `.gitignore` is generated from global template metadata plus active profile
  manifest metadata (`gitignore_fragments` or `ignore_dirs`) and
  `config.gitignore.overlays`/`config.gitignore.overrides`.
