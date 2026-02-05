# Profiles

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Profile Anatomy](#profile-anatomy)
- [Assets and Overlays](#assets-and-overlays)
- [Examples](#examples)

## Overview
Profiles describe the tech stack slices DevCovenant should enforce. Each
profile declares file suffixes, assets to materialize, and policies to
activate. Profiles do not inherit from each other; every profile must list
its own policies and overlays explicitly.
The DevCovenant repo activates the `devcovrepo` profile for repo-only
policies and documentation tracking.

## Workflow
1. Start with `global` plus the language profiles you need.
2. Add framework profiles (for example, `fastapi`) when relevant.
3. Use `policy_overlays` inside the profile to tune policy selectors.

## Profile Anatomy
A profile descriptor lives under `devcovenant/core/profiles/<name>/` and
includes `<name>.yaml` plus any asset templates. The YAML includes:
- `profile` name and `category`.
- `suffixes` for file types.
- `assets` to materialize into the target repo.
- `policies` to activate.
- `policy_overlays` for per-policy metadata.

## Assets and Overlays
Assets are path-template pairs, rendered with a `mode` that controls how
files are merged or replaced. Overlays apply after policy defaults so each
profile can adjust selectors without rewriting the policy descriptor.

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
    mode: merge
policies:
  - name-clarity
  - dependency-license-sync
policy_overlays:
  dependency-license-sync:
    dependency_files:
      - requirements.in
      - requirements.lock
```
