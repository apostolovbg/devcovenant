# Policy Assets

## Table of Contents
1. Overview
2. Asset Declarations
3. Workflow

## Overview
Policy assets are files created because a policy is enabled, such as license
reports, security logs, or policy-specific README files.

Policy asset materialization is profile-owned: declare assets in profile
manifests (`global` or other active profiles), not in policy descriptors.

## Asset Declarations
Declare policy-owned files in profile manifests. Example profile path:
```
devcovenant/core/profiles/python/python.yaml
```

A typical asset fragment looks like:
```
assets:
  - path: THIRD_PARTY_LICENSES.md
    template: THIRD_PARTY_LICENSES.md
```

Refresh/deploy apply active profile assets in profile order.

## Workflow
When adding policy assets, declare them in profile manifests and rerun
`devcovenant refresh`. If multiple active profiles target the same missing
path, the later profile in `profiles.active` wins. Existing files are
preserved.
