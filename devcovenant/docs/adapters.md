# Adapters

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Adapter Locations](#adapter-locations)
- [Design Guidelines](#design-guidelines)
- [Example Pattern](#example-pattern)

## Overview
Adapters isolate language-specific logic inside a policy. Instead of
embedding per-language checks directly in the policy script, adapters keep
those rules in `adapters/<language>.py` so the core policy stays generic.

## Workflow
1. Add a new adapter file for the target language or framework.
2. Register the adapter in the policy script's dispatch logic.
3. Add or extend tests for the adapter behavior.

## Adapter Locations
Adapters live under:
`devcovenant/core/policies/<policy>/adapters/<profile>.py`.
Use profile names like `python`, `javascript`, or `fastapi` so dispatch can
key off the active profile list.

## Design Guidelines
- Keep adapter APIs narrow and data-oriented.
- Return structured results that the policy script can format.
- Avoid reading config directly inside adapters; pass metadata down from
  the policy check.

## Example Pattern
A policy check can load the adapter based on the active profiles:
```python
adapter = resolve_adapter(active_profiles)
violations = adapter.check(paths, metadata)
```
The policy script decides how to format and report those violations.
