# Configuration

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Config Structure](#config-structure)
- [Profiles and Overrides](#profiles-and-overrides)
- [Examples](#examples)

## Overview
`devcovenant/config.yaml` captures the active profiles, metadata overrides,
and install/update knobs. The file is tracked in the repo so CI and other
contributors use the same enforcement settings. Generated registry files
can be rebuilt, but config stays under version control.
When the file is missing, DevCovenant seeds a generic stub from the
`global` profile asset and marks it as generic until reviewed.

## Workflow
1. Choose profiles that match the repo tech stack.
2. Add overrides for policies that need custom selectors or enforcement.
3. Set `install.generic_config: false` once the config is reviewed so
   `devcovenant deploy` can run.
4. Keep the config file committed so the same rules apply in CI.

## Config Structure
The core sections are:
- `profiles.active` for the profile list.
- `doc_assets` for autogen vs. user-managed doc lists.
- `autogen_metadata_overrides` for profile-derived metadata overlays.
- `user_metadata_overrides` for per-policy overrides applied last.
- `policy_state` for authoritative policy on/off activation.
- `freeze_core_policies` to copy policy logic into custom overlays.
- `pre_commit` for `.pre-commit-config.yaml` enablement and overrides.
- `install.generic_config` to guard deploys until the config is reviewed.
- `install.allow_custom_policy_asset_fallback` for custom policy asset
  fallback from custom policy descriptors when profile assets do not supply
  those files.

## Profiles and Overrides
Overrides merge in the order: policy defaults, profile overlays, then
config overrides (autogen first, user last). Config overrides replace
targeted keys rather than appending. This lets a repo adjust a policy
without editing core files or the policy descriptor.
For dependency and license tracking, the active profiles supply the
`dependency-license-sync` manifest list; use config overrides when your
repo has custom manifest names.
Version tracking defaults also come from profiles (for example, the
global profile sets baseline readme/license files while custom profiles
can override the `version_file`). Use config overrides to point
`version-sync` at a different file or document set.
Changelog coverage can be tuned by setting `summary_verbs` (the allowed
action verbs for Change/Why/Impact summaries) and adding `skipped_globs`
entries such as `*_old.*` when backup artifacts should not trigger logging.
Pre-commit config is built from profile fragments (global first), then
merged with `pre_commit.overrides` from config. Profile `ignore_dirs`
are converted into an `exclude` regex so hooks skip the same paths.
Stock policy assets are profile-owned, while custom policies can still load
descriptor assets when `install.allow_custom_policy_asset_fallback` is true.

## Examples
```yaml
profiles:
  active:
    - global
    - python
    - docker
user_metadata_overrides:
  changelog-coverage:
    enforcement: active
    summary_verbs:
      - update
      - updated
      - fix
      - fixed
    skipped_globs:
      - "*_old.*"
  dependency-license-sync:
    dependency_files:
      - requirements.in
      - requirements.lock
pre_commit:
  enabled: true
  overrides:
    repos:
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.6.0
        hooks:
          - id: check-toml
```
