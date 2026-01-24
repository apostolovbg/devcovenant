# Policy Templates

## Table of Contents
1. Overview
2. Asset Declarations
3. Workflow

## Overview
Policy templates are assets that exist because a policy is enabled, such as
security logs, license reports, or policy-specific README files. These are
scoped to a policy id and installed only when the policy is active and its
profile scopes match the repo's active profiles.

## Asset Declarations
Policy assets are declared in a per-policy manifest named
`policy_assets.yaml` inside each policy template folder. Example:
```
devcovenant/core/templates/policies/dependency-license-sync/policy_assets.yaml
```

A typical manifest looks like:
```
version: 1
policy: dependency-license-sync
assets:
  - path: THIRD_PARTY_LICENSES.md
    template: THIRD_PARTY_LICENSES.md
    mode: merge
```

Install/update compiles all per-policy manifests into
`devcovenant/registry/policy_assets.yaml` so the registry reflects the active
asset map. Templates live under `devcovenant/core/templates/policies/<policy>/`
and may be overridden by custom templates with the same path.
## Workflow
When adding or adjusting a policy template, update the policy assets map,
add the template file, and ensure the install/update logic can resolve the
path. If a profile also declares the same asset, the profile wins to keep
framework-specific assets prioritized over generic policy defaults.
