# Policy Assets

## Table of Contents
1. Overview
2. Asset Declarations
3. Workflow

## Overview
Policy assets are files created because a policy is enabled, such as license
reports, security logs, or policy-specific README files. Assets live under each
policy at `devcovenant/core/policies/<policy>/assets/` and are installed only
when the policy is active and its profile scopes match the repo's active
profiles. Custom overrides live under
`devcovenant/custom/policies/<policy>/assets/` and take precedence.

## Asset Declarations
Policy assets are declared in a per-policy manifest named `policy_assets.yaml`
inside each policy assets folder. Example:
```
devcovenant/core/policies/dependency_license_sync/assets/policy_assets.yaml
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
`devcovenant/registry/local/policy_assets.yaml` so the registry reflects the
active asset map.

## Workflow
When adding or adjusting a policy asset, update the policy assets manifest, add
or refresh the asset file, and ensure install/update logic can resolve the
path. If a profile declares the same asset, the profile wins to keep
framework-specific assets prioritized over generic policy defaults.
