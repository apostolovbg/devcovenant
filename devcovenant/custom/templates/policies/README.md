# Custom Policy Templates

## Table of Contents
1. Overview
2. Declaring Assets
3. Workflow

## Overview
Custom policy templates override core policy assets when paths match. Use
this directory to ship repo-specific policy documents or configuration
files without forking DevCovenant core. Examples include custom security
logs, alternate license reports, or a policy-specific README that captures
how your team interprets a rule.

## Declaring Assets
Register custom assets by adding a per-policy manifest at:
`devcovenant/custom/templates/policies/<policy>/policy_assets.yaml`

Example:
```yaml
assets:
  - path: docs/README.md
    template: README.md
    mode: replace
```

Templates should live alongside the manifest under
`devcovenant/custom/templates/policies/<policy>/`. Custom policy manifests
override core manifests when the policy id matches.
## Workflow
Add or adjust the template, update the policy assets map, and keep the
policy id consistent. Custom policy assets are applied only when the
policy is enabled and in scope. After changes, run the DevCovenant gates
so the manifest, registry, and changelog stay synchronized.
