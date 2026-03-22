# Profiles

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Profile Anatomy](#profile-anatomy)
- [Assets and Overlays](#assets-and-overlays)
- [Examples](#examples)

## Overview
Profiles describe stack slices (language, framework, tooling) and contribute
four things: file suffixes, materialized assets, policy metadata overlays,
and core-invariant metadata overlays. Profile manifests do not activate
policies directly.
Policy activation is config-only through `policy_state`.
Core invariants are configured separately through `core_invariants`.

## Workflow
1. Start with `global`, then add only profiles the repo needs.
2. Tune behavior with profile `policy_overlays`,
   `core_invariant_overlays`, and config metadata overrides.
3. Use `policy_state` in config to enable/disable policies explicitly.

## Profile Anatomy
A profile descriptor lives at `devcovenant/builtin/profiles/<name>/<name>.yaml`
or `devcovenant/custom/profiles/<name>/<name>.yaml`.

Typical keys:
- `profile`, `category`
- `suffixes`, `ignore_dirs`
- `assets` (target path + template)
- `policy_overlays`
- `core_invariant_overlays`
- optional `pre_commit` fragments

Profile-owned metadata is the preferred place for operational values.
For example, `defaults` can set `no-raw-errors` selector/boolean defaults,
language profiles can declare `devflow-run-gates` required test commands
through `core_invariant_overlays`, and repo profiles (for example
`devcovuser`/`devcovrepo`) can narrow scope.

## Assets and Overlays
Profile assets are applied in `profiles.active` order:
- each asset is created only when the target is missing.
- existing files are preserved.
- generated runtime artifacts (registries/config autogen/pre-commit/gitignore)
  are handled by dedicated refresh routines, not profile asset entries.

Overlays are metadata-only and merge before config overrides
(`autogen_metadata_overrides`, then `user_metadata_overrides`).
`policy_overlays` feed normal customizable policies.
`core_invariant_overlays` feed DevCovenant-owned invariants such as
`devflow-run-gates`. Route metadata can still send invariant descriptor
changes to architecture docs without turning those invariants into policies.

## Examples
```yaml
version: 1
profile: python
category: language
suffixes:
  - .py
assets:
  - path: pyproject.toml
    template: pyproject.toml
policy_overlays:
  dependency-management:
    dependency_role_files:
      - intent=>requirements.in
      - resolved=>requirements.lock
      - package_manifest=>pyproject.toml
core_invariant_overlays:
  devflow-run-gates:
    required_commands:
      - python3 -m unittest discover -v
      - pytest
```
