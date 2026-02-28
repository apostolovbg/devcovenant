# Policies

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Policy Descriptor Anatomy](#policy-descriptor-anatomy)
- [Scripts, Autofix, Translators](#scripts-autofix-translators)
- [Custom Policies](#custom-policies)

## Overview
Policies are the enforcement units in DevCovenant. Each policy has a YAML
descriptor that documents its purpose and metadata, plus a script that
implements the check. Policies are activated by config `policy_state`,
while profiles provide metadata overlays.

## Workflow
1. Edit the policy descriptor to update metadata and prose.
2. Implement or adjust the policy script in the policy directory.
3. Add/update translators when the logic needs language-aware behavior.
4. Add tests under `tests/devcovenant/...` mirroring the policy path.

## Policy Descriptor Anatomy
Policy descriptors live in `devcovenant/builtin/policies/<id>/` and are
normalized into AGENTS and the local registry. Example metadata:
```yaml
id: changelog-coverage
severity: error
auto_fix: false
enabled: true
```
Profiles supply policy-specific metadata such as dependency manifest lists
(`dependency-license-sync`), version-sync file lists, selector scopes, or
explicit-error controls (for example `no-raw-errors` booleans and selectors).
Config overrides can adjust those values without editing the policy
descriptor.

## Scripts, Autofix, Translators
- `policy.py` implements the check.
- `autofix/` holds auto-fix helpers when the policy supports fixes.
- Translators are declared by active language profiles and invoked through
  the shared translator runtime.
Policy scripts consume `LanguageUnit` output and do not dispatch
language-specific routing directly.
`no-raw-errors` is a builtin Python policy that flags bare `except`,
generic `raise Exception(...)`, and silent `except Exception: pass`
handlers so failures stay explicit at runtime boundaries.

## Custom Policies
Custom policies live under `devcovenant/custom/policies/<id>/` and use the
same descriptor/script model as builtin policies. They are activated through
config `policy_state` after discovery/refresh, with metadata tuned through
profile overlays or config overrides.
