# DevCovenant Profiles

## Overview
This directory holds the stock profiles after the catalog reduction. Each
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
A policy runs for a profile when the profile lists it under `policies:`.
Policy `profile_scopes` document intent but do not auto-activate. Overlays
supply per-profile settings (suffixes, required commands, dependency files).

## Workflow expectations
Managed docs and policies are kept in sync via `devcovenant/run_pre_commit.py`
(start/tests/end). When adding or editing profiles, refresh POLICY_MAP and
PROFILE_MAP and run the gate sequence before committing.

## Workflow
- Run `python3 devcovenant/run_pre_commit.py --phase start` before edits.
- Make changes and keep POLICY_MAP/PROFILE_MAP aligned with the active
  profiles.
- Run `python3 devcovenant/run_tests.py`.
- Finish with `python3 devcovenant/run_pre_commit.py --phase end`.
