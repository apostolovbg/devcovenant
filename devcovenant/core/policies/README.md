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
Policy assets are declared in the policy descriptor itself under the `assets`
key. Example descriptor path:
```
devcovenant/core/policies/dependency_license_sync/dependency_license_sync.yaml
```

A typical descriptor fragment looks like:
```
assets:
  - path: THIRD_PARTY_LICENSES.md
    template: THIRD_PARTY_LICENSES.md
    mode: merge
```

Install/update reads the descriptor assets directly; there is no separate
policy-asset registry.

## Workflow
When adding or adjusting a policy asset, update the policy descriptor, add
or refresh the asset file, and ensure install/update logic can resolve the
path. If a profile declares the same asset, the profile wins to keep
framework-specific assets prioritized over generic policy defaults.
