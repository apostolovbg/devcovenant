# DevCovenant Profiles

## Overview
This directory holds the stock profiles after the profile set reduction. Each
profile folder contains `profile.yaml`, optional assets, and a gitignore
fragment. Profiles activate policies explicitly through the `policies:` list
plus `policy_overlays` for per-profile metadata. Global policies apply to all
profiles automatically.

## Table of Contents
- How profiles are organized
- Activation rules
- Workflow expectations

## How profiles are organized
Profiles live in `devcovenant/core/profiles/<name>/`. Only the following
profiles remain: global, docs, data, suffixes, devcovuser, python,
javascript, typescript, java, go, rust, php, ruby, csharp, sql, docker,
terraform, kubernetes, fastapi, frappe, dart, flutter, swift, objective-c.

## Activation rules
A policy is activated by config `policy_state`. Profiles provide policy
metadata overlays and assets (suffixes, required commands, dependency files)
without directly toggling policy activation.

Stock policy assets are supplied by profile `assets` declarations. Custom
policies can still ship fallback assets in
`devcovenant/custom/policies/<policy>/<policy>.yaml` when
`install.allow_custom_policy_asset_fallback` is enabled.

## Workflow expectations
Managed docs and policies are kept in sync via the canonical gate sequence
(`devcovenant check --start` / `devcovenant test` /
`devcovenant check --end`). When adding or editing profiles, refresh
POLICY_MAP and PROFILE_MAP and run the gate sequence before committing.

## Workflow
- Run `devcovenant check --start` before edits.
- Make changes and keep POLICY_MAP/PROFILE_MAP aligned with the active
  profiles.
- Run `devcovenant test`.
- Finish with `devcovenant check --end`.
