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
implements the check. Policies are activated only when a profile lists
them.

## Workflow
1. Edit the policy descriptor to update metadata and prose.
2. Implement or adjust the policy script in the policy directory.
3. Add adapters when the logic needs language-specific behavior.
4. Add tests under `tests/devcovenant/...` mirroring the policy path.

## Policy Descriptor Anatomy
Policy descriptors live in `devcovenant/core/policies/<id>/` and are
normalized into AGENTS and the local registry. Example metadata:
```yaml
id: changelog-coverage
severity: error
auto_fix: false
apply: true
profile_scopes:
  - global
```

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
