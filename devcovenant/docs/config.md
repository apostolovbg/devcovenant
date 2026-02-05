# Configuration

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Config Structure](#config-structure)
- [Profiles and Overrides](#profiles-and-overrides)
- [Examples](#examples)

## Overview
`devcovenant/config.yaml` captures the active profiles, policy overrides,
and install/update knobs. The file is tracked in the repo so CI and other
contributors use the same enforcement settings. Generated registry files
can be rebuilt, but config stays under version control.

## Workflow
1. Choose profiles that match the repo tech stack.
2. Add overrides for policies that need custom selectors or enforcement.
3. Keep the config file committed so the same rules apply in CI.

## Config Structure
The core sections are:
- `profiles.active` for the profile list.
- `policy_overrides` for per-policy metadata overrides.
- `autogen_do_not_apply` to disable a policy by default.
- `manual_force_apply` to force a policy on.
- `freeze_core_policies` to copy policy logic into custom overlays.

## Profiles and Overrides
Overrides merge in the order: policy defaults, profile overlays, then
config overrides. This lets a repo adjust a policy without editing core
files or the policy descriptor.

## Examples
```yaml
profiles:
  active:
    - global
    - python
    - docker
policy_overrides:
  changelog-coverage:
    enforcement: active
  dependency-license-sync:
    dependency_files:
      - requirements.in
      - requirements.lock
```
