# Common Policy Patches
**Last Updated:** 2026-01-11
**Version:** 0.2.0

Patch scripts override built-in policy metadata without modifying the core
policy scripts. Each patch is typically a Python file named after the policy
id, such as `line_length_limit.py`. For static overrides, JSON or YAML files
with the same basename are also supported.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Patch API](#patch-api)
4. [Examples](#examples)

## Overview
Use patches when you want to adjust built-in policy behavior without editing
core scripts. Patch scripts run before policy metadata is finalized and after
`config.yaml`, so they are a clean, repo-local override layer.

## Workflow
1. Create a patch file named after the policy id.
2. Implement one of the supported patch entry points (Python) or supply a
   JSON/YAML dict for static overrides.
3. Run the standard DevCovenant workflow to validate changes.

## Patch API
Patch scripts can provide overrides in one of three ways:
- `PATCH`: a module-level dict of overrides.
- `get_patch() -> dict`: return an overrides dict.
- `patch_options(options, policy, context, repo_root) -> dict`: compute
  overrides dynamically. Use whichever subset of arguments you need.

The returned dict maps directly to policy option keys:
```
{
  "max_length": 100,
  "exclude_globs": ["vendor/**"],
}
```

## Examples
- Change the line-length limit for a repo-specific rule set.
- Adjust `include_prefixes` to narrow a policy to a submodule.
- Compute options dynamically based on the repo or policy metadata.
