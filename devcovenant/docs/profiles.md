# Profiles

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Profile Anatomy](#profile-anatomy)
- [Assets and Overlays](#assets-and-overlays)
- [Examples](#examples)

## Overview
Profiles describe stack slices (language, framework, tooling) and contribute
three things: file suffixes, materialized assets, and policy metadata
overlays. Profile manifests do not activate policies directly.
Policy activation is config-only through `policy_state`.

## Workflow
1. Start with `global`, then add only profiles the repo needs.
2. Tune behavior with profile `policy_overlays` and config metadata overrides.
3. Use `policy_state` in config to enable/disable policies explicitly.

## Profile Anatomy
A profile descriptor lives at `devcovenant/core/profiles/<name>/<name>.yaml`
or `devcovenant/custom/profiles/<name>/<name>.yaml`.

Typical keys:
- `profile`, `category`
- `suffixes`, `ignore_dirs`
- `assets` (target path + template)
- `policy_overlays`
- optional `pre_commit` fragments

## Assets and Overlays
Profile assets are applied in `profiles.active` order:
- each asset is created only when the target is missing.
- existing files are preserved.
- generated runtime artifacts (registries/config autogen/pre-commit/gitignore)
  are handled by dedicated refresh routines, not profile asset entries.

Overlays are metadata-only and merge before config overrides
(`autogen_metadata_overrides`, then `user_metadata_overrides`).

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
  dependency-license-sync:
    dependency_files:
      - requirements.in
      - requirements.lock
      - pyproject.toml
```
