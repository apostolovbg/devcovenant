# Policy Assets

## Table of Contents
1. Overview
2. Asset Declarations
3. Workflow

## Overview
Policy assets are files created because a policy is enabled, such as license
reports, security logs, or policy-specific README files.

Core policy behavior is profile-owned: stock policy assets should be declared
in profile manifests (`global` or other active profiles), not loaded directly
from core policy folders.

Custom policy behavior keeps a fallback path: when
`install.allow_custom_policy_asset_fallback` is true, assets declared in
`devcovenant/custom/policies/<policy>/<policy>.yaml` are loaded if that custom
policy resolves enabled via `policy_state`.

## Asset Declarations
Custom fallback assets are declared in the custom policy descriptor under the
`assets` key. Example descriptor path:
```
devcovenant/custom/policies/my_policy/my_policy.yaml
```

A typical descriptor fragment looks like:
```
assets:
  - path: THIRD_PARTY_LICENSES.md
    template: THIRD_PARTY_LICENSES.md
    mode: merge
```

Install/update treats profile asset declarations as primary. Custom policy
descriptor assets are a fallback convenience path.

## Workflow
When adding stock policy assets, declare them in profile manifests. When adding
custom policy assets without profile edits, declare them in the custom policy
descriptor and keep `install.allow_custom_policy_asset_fallback` enabled.
If a profile declares the same target path, the profile asset wins.
