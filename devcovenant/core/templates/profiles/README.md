# Profile Templates

## Table of Contents
1. Overview
2. Profile Manifests
3. Workflow

## Overview
Profile templates hold assets that apply when a profile is active. Each
profile folder can include a `profile.yaml` manifest plus any templates
that the manifest references. Profiles exist to tailor DevCovenant to a
language or framework without forking global policy logic. Active profiles
supply assets, file suffixes, and policy metadata overlays that shape the
install and update behavior.

## Profile Manifests
Each profile folder may contain `profile.yaml`:
```
version: 1
profile: python
category: language
assets:
  - path: requirements.in
    template: requirements.in
    mode: merge
policy_overlays:
  dependency-license-sync:
    dependency_files:
      - requirements.in
```
Profiles may also include a `.gitignore` fragment that is merged into the
repo-level `.gitignore` during install/update.

## Workflow
When adding a profile, define the manifest and add any needed templates.
DevCovenant generates `devcovenant/registry/profile_catalog.yaml` during
install/update, so no manual catalog edits are required. If a profile and a
policy both declare the same asset, the profile asset wins. Custom profile
templates live under `devcovenant/custom/templates/profiles/<profile>/` and
override core assets when paths match.
