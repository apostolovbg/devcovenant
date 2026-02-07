# Policies

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Policy Descriptor Anatomy](#policy-descriptor-anatomy)
- [Scripts, Fixers, Adapters](#scripts-fixers-adapters)
- [Custom Policies](#custom-policies)

## Overview
Policies are the enforcement units in DevCovenant. Each policy has a YAML
descriptor that documents its purpose and metadata, plus a script that
implements the check. Policies are activated by config `policy_state`,
while profiles provide metadata overlays. Every policy still appears in
`AGENTS.md` with its resolved
metadata and `enabled` flag.

## Workflow
1. Edit the policy descriptor to update metadata and prose.
2. Implement or adjust the policy script in the policy directory.
3. Add adapters when the logic needs language-specific behavior.
4. Add tests under `tests/devcovenant/...` mirroring the policy path.

## Policy Descriptor Anatomy
Policy descriptors live in `devcovenant/core/policies/<id>/` and are
resolved into AGENTS and the local registry. Example metadata:
```yaml
id: changelog-coverage
severity: error
auto_fix: false
enabled: true
```
Profiles supply policy-specific metadata such as dependency manifest lists
(`dependency-license-sync`), version-sync file lists, or selector scopes.
Config overrides can adjust those values without editing the policy
descriptor. Resolution order is policy defaults → profile overlays → config
overrides; the resolved map is written into `AGENTS.md` so readers can see
the working values without inspecting the registry.

## Scripts, Fixers, Adapters
- `policy.py` implements the check.
- `fixers/` holds auto-fix helpers when the policy supports fixes.
- `adapters/` contains language-specific logic, keyed by profile names.
The policy script selects the adapter based on active profiles and falls
back to a safe default when no adapter is available.

## Custom Policies
Custom policies live under `devcovenant/custom/policies/<id>/` and are
opt-in via custom profiles or config overrides. Use them to extend or
replace stock behavior without editing core policy code.
