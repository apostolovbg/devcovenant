# Translators

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Translator Declarations](#translator-declarations)
- [Translator Runtime](#translator-runtime)
- [Design Guidelines](#design-guidelines)
- [Example Pattern](#example-pattern)

## Overview
Translators isolate language-specific parsing in language profiles.
Policies remain language-agnostic and consume normalized language units
from the shared translator runtime.

## Workflow
1. Add or update a language profile translator declaration.
2. Implement translator entrypoints referenced by profile metadata.
3. Add or extend translator tests for target language behavior.

## Translator Declarations
Translator declarations are owned by language profile manifests and include:
- `id`
- `extensions`
- `can_handle`
- `translate`

## Translator Runtime
`devcovenant/core/services/translator_engine.py` resolves translators from
active language profiles by extension and entrypoint routing metadata.

## Design Guidelines
- Keep translator behavior deterministic and profile-scoped.
- Return normalized structures consumed by policy runtime.
- Avoid policy-specific branching inside translator implementations.

## Example Pattern
A policy check requests translation through the shared runtime:
```python
unit = context.translator_runtime.translate(path)
violations = policy_check(unit, metadata)
```
The policy script formats and reports violations from normalized data.
