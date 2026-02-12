# DevCovenant Profiles

## Overview
This directory holds the stock profiles after the profile set reduction. Each
profile folder contains `<name>.yaml`, optional assets, and a gitignore
fragment. Profiles provide metadata through `policy_overlays`; policy
activation is config-only via `policy_state`.

## Table of Contents
- How profiles are organized
- Activation rules
- Workflow expectations

## How profiles are organized
Profiles live in `devcovenant/core/profiles/<name>/`. Only the following
profiles remain: global, docs, devcovuser, python,
javascript, typescript, java, go, rust, php, ruby, csharp, sql, docker,
terraform, kubernetes, fastapi, frappe, dart, flutter, swift, objective-c.

## Activation rules
A policy is activated by config `policy_state`. Profiles provide policy
metadata overlays and assets (suffixes, required commands, dependency files)
without directly toggling policy activation.

Stock policy assets are supplied by profile `assets` declarations. Custom
policy behavior is still configurable via profile overlays and custom policy
code, but asset materialization remains profile-owned and create-if-missing.

## Workflow expectations
Managed docs and policies are kept in sync via the canonical gate sequence
(`devcovenant check --start` / `devcovenant test` /
`devcovenant check --end`). When adding or editing profiles, rerun refresh
and the gate sequence so registries and managed docs stay synchronized.

## Workflow
- Run `devcovenant check --start` before edits.
- Make changes and rerun `devcovenant refresh` after profile edits.
- Run `devcovenant test`.
- Finish with `devcovenant check --end`.
